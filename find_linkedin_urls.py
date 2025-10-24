"""
Find and populate LinkedIn URLs for companies missing them
Uses Google search or direct LinkedIn search to find company LinkedIn profiles
"""
import asyncio
import re
from playwright.async_api import async_playwright
from database_models import get_session, PortfolioCompany
from sqlalchemy import func
import time


async def search_linkedin_url(page, company_name, website=None):
    """
    Search for company LinkedIn URL using multiple strategies
    
    Args:
        page: Playwright page object
        company_name: Name of the company
        website: Optional company website for verification
        
    Returns:
        str: LinkedIn URL or None
    """
    try:
        # Strategy 1: Try constructing LinkedIn URL directly
        # Convert company name to LinkedIn format (lowercase, spaces to hyphens)
        linkedin_slug = company_name.lower().replace(' ', '-').replace(',', '').replace('.', '').replace('&', 'and')
        potential_url = f'https://www.linkedin.com/company/{linkedin_slug}'
        
        # Test if the URL exists
        try:
            response = await page.goto(potential_url, wait_until="domcontentloaded", timeout=8000)
            await page.wait_for_timeout(1000)
            
            # Check if we got a valid company page (not a 404 or redirect to search)
            current_url = page.url
            if 'linkedin.com/company/' in current_url and '/search/' not in current_url:
                print(f"  ✅ Found (direct): {current_url}")
                return current_url.split('?')[0].split('#')[0]
        except:
            pass
        
        # Strategy 2: Try DuckDuckGo search
        search_query = f'site:linkedin.com/company {company_name}'
        duckduckgo_url = f'https://duckduckgo.com/?q={search_query.replace(" ", "+")}'
        
        try:
            await page.goto(duckduckgo_url, wait_until="domcontentloaded", timeout=8000)
            await page.wait_for_timeout(2000)
            
            # Look for LinkedIn URLs in results
            links = await page.query_selector_all('a[href*="linkedin.com/company"]')
            
            for link in links:
                href = await link.get_attribute('href')
                if href and 'linkedin.com/company/' in href:
                    # Extract clean LinkedIn URL
                    match = re.search(r'(https?://[^/]*linkedin\.com/company/[^/&?\s]+)', href)
                    if match:
                        linkedin_url = match.group(1)
                        linkedin_url = linkedin_url.split('?')[0].split('&')[0]
                        print(f"  ✅ Found (search): {linkedin_url}")
                        return linkedin_url
        except:
            pass
        
        # Strategy 3: Try Bing search as fallback
        search_query = f'{company_name} linkedin company'
        bing_url = f'https://www.bing.com/search?q={search_query.replace(" ", "+")}'
        
        try:
            await page.goto(bing_url, wait_until="domcontentloaded", timeout=8000)
            await page.wait_for_timeout(1500)
            
            links = await page.query_selector_all('a[href*="linkedin.com/company"]')
            
            for link in links:
                href = await link.get_attribute('href')
                if href and 'linkedin.com/company/' in href:
                    match = re.search(r'(https?://[^/]*linkedin\.com/company/[^/&?\s]+)', href)
                    if match:
                        linkedin_url = match.group(1)
                        linkedin_url = linkedin_url.split('?')[0].split('&')[0]
                        print(f"  ✅ Found (Bing): {linkedin_url}")
                        return linkedin_url
        except:
            pass
        
        print(f"  ⚠️  No LinkedIn URL found")
        return None
        
    except Exception as e:
        print(f"  ❌ Error searching: {str(e)[:100]}")
        return None


async def find_missing_linkedin_urls(limit=50, delay_seconds=3):
    """
    Find and update LinkedIn URLs for companies missing them
    
    Args:
        limit: Maximum number of companies to process
        delay_seconds: Delay between searches to avoid rate limiting
    """
    session = get_session()
    
    try:
        # Get companies without LinkedIn URLs
        companies = session.query(PortfolioCompany).filter(
            (PortfolioCompany.linkedin_url == None) | 
            (PortfolioCompany.linkedin_url == '')
        ).limit(limit).all()
        
        total = len(companies)
        print(f"\n📊 Found {total} companies without LinkedIn URLs")
        print(f"🔍 Processing up to {limit} companies...")
        print("=" * 70)
        
        if total == 0:
            print("✅ All companies already have LinkedIn URLs!")
            return
        
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            updated_count = 0
            
            for idx, company in enumerate(companies, 1):
                print(f"\n[{idx}/{total}] {company.name}")
                
                # Search for LinkedIn URL
                linkedin_url = await search_linkedin_url(
                    page, 
                    company.name, 
                    company.website
                )
                
                if linkedin_url:
                    # Update database
                    company.linkedin_url = linkedin_url
                    session.commit()
                    updated_count += 1
                    print(f"  💾 Updated database")
                
                # Rate limiting delay
                if idx < total:
                    print(f"  ⏳ Waiting {delay_seconds}s before next search...")
                    await asyncio.sleep(delay_seconds)
            
            await browser.close()
        
        print("\n" + "=" * 70)
        print(f"✅ Completed!")
        print(f"📊 Updated {updated_count} out of {total} companies")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        session.rollback()
        
    finally:
        session.close()


async def find_linkedin_for_specific_firm(pe_firm_name, limit=100, delay_seconds=3):
    """
    Find LinkedIn URLs for companies from a specific PE firm
    
    Args:
        pe_firm_name: Name of the PE firm (e.g., "Vista Equity Partners")
        limit: Maximum number of companies to process
        delay_seconds: Delay between searches
    """
    session = get_session()
    
    try:
        # Get companies from specific firm without LinkedIn URLs
        companies = session.query(PortfolioCompany).join(
            PortfolioCompany.pe_firm
        ).filter(
            PortfolioCompany.pe_firm.has(name=pe_firm_name),
            (PortfolioCompany.linkedin_url == None) | 
            (PortfolioCompany.linkedin_url == '')
        ).limit(limit).all()
        
        total = len(companies)
        print(f"\n📊 Found {total} {pe_firm_name} companies without LinkedIn URLs")
        print(f"🔍 Processing up to {limit} companies...")
        print("=" * 70)
        
        if total == 0:
            print(f"✅ All {pe_firm_name} companies already have LinkedIn URLs!")
            return
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            updated_count = 0
            
            for idx, company in enumerate(companies, 1):
                print(f"\n[{idx}/{total}] {company.name}")
                
                linkedin_url = await search_linkedin_url(
                    page, 
                    company.name, 
                    company.website
                )
                
                if linkedin_url:
                    company.linkedin_url = linkedin_url
                    session.commit()
                    updated_count += 1
                    print(f"  💾 Updated database")
                
                if idx < total:
                    await asyncio.sleep(delay_seconds)
            
            await browser.close()
        
        print("\n" + "=" * 70)
        print(f"✅ Completed {pe_firm_name}!")
        print(f"📊 Updated {updated_count} out of {total} companies")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        session.rollback()
        
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
    print("🔍 LinkedIn URL Finder")
    print("=" * 70)
    
    # Show current stats
    asyncio.run(show_linkedin_stats())
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--firm" and len(sys.argv) > 2:
            firm_name = sys.argv[2]
            limit = int(sys.argv[3]) if len(sys.argv) > 3 else 100
            print(f"\n🎯 Finding LinkedIn URLs for {firm_name} companies...")
            asyncio.run(find_linkedin_for_specific_firm(firm_name, limit=limit))
        else:
            limit = int(sys.argv[1])
            print(f"\n🔍 Finding LinkedIn URLs for up to {limit} companies...")
            asyncio.run(find_missing_linkedin_urls(limit=limit))
    else:
        # Default: process 50 companies
        print("\n🔍 Finding LinkedIn URLs for up to 50 companies...")
        print("💡 Tip: Use 'python find_linkedin_urls.py 100' to process more")
        print("💡 Tip: Use 'python find_linkedin_urls.py --firm \"Vista Equity Partners\" 50' for specific firm")
        asyncio.run(find_missing_linkedin_urls(limit=50))
    
    # Show updated stats
    print("\n")
    asyncio.run(show_linkedin_stats())
