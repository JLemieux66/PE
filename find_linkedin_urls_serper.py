"""
Find and populate LinkedIn URLs for companies using SerperDev API
Much faster and more reliable than web scraping
"""
import asyncio
import aiohttp
import re
import os
from dotenv import load_dotenv
from database_models import get_session, PortfolioCompany, PEFirm
from sqlalchemy import func
from typing import Optional

load_dotenv()

SERPER_API_KEY = os.getenv('SERPER_API_KEY')


async def search_linkedin_with_serper(session: aiohttp.ClientSession, company_name: str, website: Optional[str] = None) -> Optional[str]:
    """
    Search for company LinkedIn URL using SerperDev API
    
    Args:
        session: aiohttp session
        company_name: Name of the company
        website: Optional company website for better accuracy
        
    Returns:
        str: LinkedIn URL or None
    """
    try:
        # Build search query
        query = f'site:linkedin.com/company "{company_name}"'
        if website:
            domain = website.replace('http://', '').replace('https://', '').split('/')[0]
            query += f' {domain}'
        
        # Call SerperDev API
        url = "https://google.serper.dev/search"
        headers = {
            'X-API-KEY': SERPER_API_KEY,
            'Content-Type': 'application/json'
        }
        payload = {
            'q': query,
            'num': 5  # Get top 5 results
        }
        
        async with session.post(url, json=payload, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                
                # Check organic results
                organic = data.get('organic', [])
                for result in organic:
                    link = result.get('link', '')
                    if 'linkedin.com/company/' in link:
                        # Extract clean LinkedIn URL
                        match = re.search(r'(https?://[^/]*linkedin\.com/company/[^/&?\s]+)', link)
                        if match:
                            linkedin_url = match.group(1).split('?')[0].split('#')[0]
                            return linkedin_url
                
                return None
            else:
                print(f"  ⚠️  API error: {response.status}")
                return None
                
    except Exception as e:
        print(f"  ❌ Error: {str(e)[:100]}")
        return None


async def try_direct_linkedin_url(session: aiohttp.ClientSession, company_name: str) -> Optional[str]:
    """
    Try constructing LinkedIn URL directly and verify it exists
    
    Args:
        session: aiohttp session
        company_name: Name of the company
        
    Returns:
        str: LinkedIn URL if valid, None otherwise
    """
    try:
        # Convert company name to LinkedIn format
        linkedin_slug = company_name.lower()
        # Clean up the slug
        linkedin_slug = linkedin_slug.replace(' ', '-')
        linkedin_slug = linkedin_slug.replace(',', '')
        linkedin_slug = linkedin_slug.replace('.', '')
        linkedin_slug = linkedin_slug.replace('&', 'and')
        linkedin_slug = linkedin_slug.replace('inc', '')
        linkedin_slug = linkedin_slug.replace('llc', '')
        linkedin_slug = linkedin_slug.replace('ltd', '')
        linkedin_slug = re.sub(r'-+', '-', linkedin_slug)  # Replace multiple dashes with single
        linkedin_slug = linkedin_slug.strip('-')
        
        potential_url = f'https://www.linkedin.com/company/{linkedin_slug}'
        
        # Quick HEAD request to check if URL exists
        async with session.head(potential_url, allow_redirects=True, timeout=aiohttp.ClientTimeout(total=5)) as response:
            # Check if we got a valid response and didn't redirect to search
            if response.status == 200 and 'linkedin.com/company/' in str(response.url):
                return str(response.url).split('?')[0].split('#')[0]
        
        return None
        
    except:
        return None


async def find_linkedin_url(session: aiohttp.ClientSession, company_name: str, website: Optional[str] = None) -> Optional[str]:
    """
    Find LinkedIn URL using multiple strategies
    
    Args:
        session: aiohttp session
        company_name: Company name
        website: Optional website
        
    Returns:
        LinkedIn URL or None
    """
    # Strategy 1: Try direct URL construction (fastest)
    direct_url = await try_direct_linkedin_url(session, company_name)
    if direct_url:
        print(f"  ✅ Found (direct): {direct_url}")
        return direct_url
    
    # Strategy 2: Use SerperDev API (most reliable)
    if SERPER_API_KEY:
        serper_url = await search_linkedin_with_serper(session, company_name, website)
        if serper_url:
            print(f"  ✅ Found (SerperDev): {serper_url}")
            return serper_url
    else:
        print(f"  ⚠️  SERPER_API_KEY not found in .env")
    
    print(f"  ⚠️  No LinkedIn URL found")
    return None


async def process_batch(companies, batch_size=10):
    """
    Process companies in batches using SerperDev API
    
    Args:
        companies: List of companies to process
        batch_size: Number of concurrent requests
    """
    db_session = get_session()
    
    try:
        total = len(companies)
        updated_count = 0
        
        # Create aiohttp session
        async with aiohttp.ClientSession() as session:
            for i in range(0, total, batch_size):
                batch = companies[i:i + batch_size]
                
                # Process batch concurrently
                tasks = []
                for company in batch:
                    idx = i + batch.index(company) + 1
                    print(f"\n[{idx}/{total}] {company.name}")
                    tasks.append(find_linkedin_url(session, company.name, company.website))
                
                # Wait for all tasks in batch
                results = await asyncio.gather(*tasks)
                
                # Update database
                for company, linkedin_url in zip(batch, results):
                    if linkedin_url:
                        company.linkedin_url = linkedin_url
                        updated_count += 1
                        print(f"  💾 Updated database")
                
                # Commit batch
                db_session.commit()
                
                # Small delay between batches to avoid rate limits
                if i + batch_size < total:
                    print(f"\n⏳ Batch complete, waiting 2 seconds before next batch...")
                    await asyncio.sleep(2)
        
        print("\n" + "=" * 70)
        print(f"✅ Completed!")
        print(f"📊 Updated {updated_count} out of {total} companies")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        db_session.rollback()
        
    finally:
        db_session.close()


async def find_all_missing_linkedin_urls(batch_size=10):
    """
    Find LinkedIn URLs for ALL companies missing them
    
    Args:
        batch_size: Number of concurrent requests (default 10)
    """
    session = get_session()
    
    try:
        # Get ALL companies without LinkedIn URLs
        companies = session.query(PortfolioCompany).filter(
            (PortfolioCompany.linkedin_url == None) | 
            (PortfolioCompany.linkedin_url == '')
        ).all()
        
        total = len(companies)
        print(f"\n📊 Found {total} companies without LinkedIn URLs")
        print(f"🔍 Processing ALL companies in batches of {batch_size}...")
        print(f"💡 This will take approximately {(total / batch_size * 0.5) / 60:.1f} minutes")
        print("=" * 70)
        
        if total == 0:
            print("✅ All companies already have LinkedIn URLs!")
            return
        
        await process_batch(companies, batch_size)
        
    finally:
        session.close()


async def find_linkedin_for_firm(pe_firm_name: str, batch_size=10):
    """
    Find LinkedIn URLs for companies from a specific PE firm
    
    Args:
        pe_firm_name: Name of the PE firm
        batch_size: Number of concurrent requests
    """
    session = get_session()
    
    try:
        # Get companies from specific firm without LinkedIn URLs
        firm = session.query(PEFirm).filter(PEFirm.name.ilike(f"%{pe_firm_name}%")).first()
        
        if not firm:
            print(f"❌ PE firm not found: {pe_firm_name}")
            return
        
        companies = session.query(PortfolioCompany).filter(
            PortfolioCompany.pe_firm_id == firm.id,
            (PortfolioCompany.linkedin_url == None) | 
            (PortfolioCompany.linkedin_url == '')
        ).all()
        
        total = len(companies)
        print(f"\n📊 Found {total} {firm.name} companies without LinkedIn URLs")
        print(f"🔍 Processing in batches of {batch_size}...")
        print("=" * 70)
        
        if total == 0:
            print(f"✅ All {firm.name} companies already have LinkedIn URLs!")
            return
        
        await process_batch(companies, batch_size)
        
    finally:
        session.close()


async def show_linkedin_stats():
    """Show statistics about LinkedIn URL coverage"""
    session = get_session()
    
    try:
        total_companies = session.query(func.count(PortfolioCompany.id)).scalar()
        
        with_linkedin = session.query(func.count(PortfolioCompany.id)).filter(
            (PortfolioCompany.linkedin_url != None) & 
            (PortfolioCompany.linkedin_url != '')
        ).scalar()
        
        without_linkedin = total_companies - with_linkedin
        coverage = (with_linkedin / total_companies * 100) if total_companies > 0 else 0
        
        print("\n" + "=" * 70)
        print("📊 LinkedIn URL Coverage Statistics")
        print("=" * 70)
        print(f"Total companies:          {total_companies:,}")
        print(f"With LinkedIn URLs:       {with_linkedin:,} ({coverage:.1f}%)")
        print(f"Without LinkedIn URLs:    {without_linkedin:,}")
        print("=" * 70)
        
        # Show breakdown by PE firm
        from database_models import PEFirm
        firms = session.query(PEFirm).all()
        
        print("\n📊 Breakdown by PE Firm:")
        print("-" * 70)
        
        for firm in firms:
            firm_total = session.query(func.count(PortfolioCompany.id)).filter(
                PortfolioCompany.pe_firm_id == firm.id
            ).scalar()
            
            firm_with_linkedin = session.query(func.count(PortfolioCompany.id)).filter(
                PortfolioCompany.pe_firm_id == firm.id,
                (PortfolioCompany.linkedin_url != None) & 
                (PortfolioCompany.linkedin_url != '')
            ).scalar()
            
            firm_coverage = (firm_with_linkedin / firm_total * 100) if firm_total > 0 else 0
            
            print(f"{firm.name:30s}: {firm_with_linkedin:4d}/{firm_total:4d} ({firm_coverage:5.1f}%)")
        
        print("=" * 70)
        
    finally:
        session.close()


if __name__ == "__main__":
    import sys
    
    print("\n" + "=" * 70)
    print("🔍 LinkedIn URL Finder (SerperDev API)")
    print("=" * 70)
    
    # Check for API key
    if not SERPER_API_KEY:
        print("\n⚠️  WARNING: SERPER_API_KEY not found in .env file!")
        print("💡 Add SERPER_API_KEY=your_key_here to .env")
        print("💡 Get free API key at: https://serper.dev")
        print("\n📌 Will fall back to direct URL construction only")
    else:
        print(f"\n✅ SerperDev API key found")
    
    # Show current stats
    asyncio.run(show_linkedin_stats())
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--firm" and len(sys.argv) > 2:
            firm_name = sys.argv[2]
            batch_size = int(sys.argv[3]) if len(sys.argv) > 3 else 10
            print(f"\n🎯 Finding LinkedIn URLs for {firm_name} companies...")
            print(f"📦 Batch size: {batch_size}")
            asyncio.run(find_linkedin_for_firm(firm_name, batch_size=batch_size))
        elif sys.argv[1] == "--all":
            batch_size = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            print(f"\n🔍 Finding LinkedIn URLs for ALL companies...")
            print(f"📦 Batch size: {batch_size} concurrent requests")
            asyncio.run(find_all_missing_linkedin_urls(batch_size=batch_size))
        else:
            print(f"\n❌ Unknown command: {sys.argv[1]}")
            print("\n💡 Usage:")
            print("  python find_linkedin_urls_serper.py --all [batch_size]")
            print("  python find_linkedin_urls_serper.py --firm \"Vista Equity Partners\" [batch_size]")
    else:
        print("\n💡 Usage:")
        print("  python find_linkedin_urls_serper.py --all              # Process all companies")
        print("  python find_linkedin_urls_serper.py --all 20           # Process all with batch size 20")
        print("  python find_linkedin_urls_serper.py --firm \"Vista\"    # Process specific firm")
        print("\n📌 Run with --all flag to start processing")
    
    # Show updated stats
    if len(sys.argv) > 1 and sys.argv[1] in ["--all", "--firm"]:
        print("\n")
        asyncio.run(show_linkedin_stats())
