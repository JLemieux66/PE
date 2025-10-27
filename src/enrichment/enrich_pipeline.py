"""
Complete Enrichment Pipeline for Portfolio Companies
Automatically finds LinkedIn URLs using SerperDev and enriches with Crunchbase data
"""

import asyncio
import aiohttp
import re
import os
from typing import Optional
from dotenv import load_dotenv
from src.models.database_models import PortfolioCompany, PEFirm, get_session
from src.enrichment.crunchbase_helpers import (
    search_company_crunchbase, 
    get_company_details_crunchbase,
    CRUNCHBASE_API_KEY
)

load_dotenv()
SERPER_API_KEY = os.getenv('SERPER_API_KEY')


def get_crunchbase_api_key():
    """Return the Crunchbase API key"""
    return CRUNCHBASE_API_KEY


def enrich_company_with_crunchbase(company, session):
    """Enrich a company with Crunchbase data including LinkedIn URL and industry"""
    try:
        # Search for company
        results = search_company_crunchbase(company.name)
        if not results or len(results) == 0:
            return False
        
        entity_id = results[0]
        if not entity_id:
            return False
        
        # Get company details
        details = get_company_details_crunchbase(entity_id)
        if not details:
            return False
        
        # Update company fields
        if details.get('revenue_range') and not company.revenue_range:
            company.revenue_range = details['revenue_range']
        
        if details.get('employee_count') and not company.employee_count:
            company.employee_count = details['employee_count']
        
        # Parse location into city/state if headquarters is provided
        if details.get('headquarters'):
            if ', ' in details['headquarters']:
                parts = details['headquarters'].split(', ')
                if len(parts) == 2:
                    if not company.city:
                        company.city = parts[0].strip()
                    if not company.state_region:
                        company.state_region = parts[1].strip()
        
        if details.get('description') and not company.description:
            company.description = details['description']
        
        # Update LinkedIn URL from Crunchbase
        if details.get('linkedin_url') and not company.linkedin_url:
            company.linkedin_url = details['linkedin_url']
        
        # Update industry_category from Crunchbase categories
        if details.get('industry_category') and not company.industry_category:
            company.industry_category = details['industry_category']
        
        return True
        
    except Exception as e:
        print(f"      Error enriching: {e}")
        return False


async def find_linkedin_url(http_session: aiohttp.ClientSession, company_name: str, company_website: Optional[str] = None) -> Optional[str]:
    """Find LinkedIn URL for a company using SerperDev API"""
    try:
        # Build search query
        query = f'site:linkedin.com/company "{company_name}"'
        if company_website:
            domain = company_website.replace('http://', '').replace('https://', '').split('/')[0]
            query += f' {domain}'
        
        # Call SerperDev API
        url = "https://google.serper.dev/search"
        headers = {
            'X-API-KEY': SERPER_API_KEY,
            'Content-Type': 'application/json'
        }
        payload = {
            'q': query,
            'num': 5
        }
        
        async with http_session.post(url, json=payload, headers=headers) as response:
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
                return None
                
    except Exception as e:
        print(f"      ⚠️  Error: {str(e)[:50]}")
        return None


async def enrich_companies(pe_firm_name=None, limit=None):
    """Find LinkedIn URLs and enrich companies with Crunchbase data"""
    
    print("=" * 70)
    print("PORTFOLIO COMPANY ENRICHMENT PIPELINE")
    print("=" * 70)
    
    # Check API keys
    if not SERPER_API_KEY:
        print("\n⚠️  Warning: SERPER_API_KEY not set in .env file")
        print("   LinkedIn URL discovery will be skipped")
        skip_linkedin = True
    else:
        skip_linkedin = False
    
    if not get_crunchbase_api_key():
        print("\n⚠️  Warning: CRUNCHBASE_API_KEY not set")
        print("   Crunchbase enrichment will be skipped")
        skip_crunchbase = True
    else:
        skip_crunchbase = False
    
    session = get_session()
    
    try:
        # Build query for companies needing enrichment
        query = session.query(PortfolioCompany)
        
        if pe_firm_name:
            firm = session.query(PEFirm).filter_by(name=pe_firm_name).first()
            if not firm:
                print(f"\n❌ PE Firm '{pe_firm_name}' not found")
                return
            query = query.filter_by(pe_firm_id=firm.id)
            print(f"\n🎯 Target: {pe_firm_name} companies")
        
        # Get companies without LinkedIn URLs, Crunchbase data, or industry_category
        companies = query.filter(
            (PortfolioCompany.linkedin_url == None) | 
            (PortfolioCompany.linkedin_url == '') |
            (PortfolioCompany.revenue_range == None) |
            (PortfolioCompany.industry_category == None)
        ).all()
        
        if limit:
            companies = companies[:limit]
        
        total = len(companies)
        
        if total == 0:
            print("\n✅ All companies are already enriched!")
            return
        
        print(f"\n📊 Found {total} companies to enrich")
        
        linkedin_found = 0
        crunchbase_enriched = 0
        
        # Process companies (no need for HTTP session anymore - Crunchbase has LinkedIn)
        for i, company in enumerate(companies, 1):
            print(f"\n[{i}/{total}] {company.name}")
            updated = False
            
            # Enrich with Crunchbase (includes LinkedIn, revenue, employees, industry, etc.)
            needs_enrichment = (
                not company.revenue_range or 
                not company.employee_count or 
                not company.linkedin_url or
                not company.industry_category
            )
            
            if not skip_crunchbase and needs_enrichment:
                print(f"   🔍 Enriching with Crunchbase...")
                
                # Track if LinkedIn was missing before
                had_linkedin = bool(company.linkedin_url)
                
                enriched = enrich_company_with_crunchbase(company, session)
                if enriched:
                    crunchbase_enriched += 1
                    updated = True
                    
                    # Check if we got LinkedIn URL
                    if not had_linkedin and company.linkedin_url:
                        linkedin_found += 1
                        print(f"   ✅ Crunchbase enriched (including LinkedIn: {company.linkedin_url})")
                    else:
                        print(f"   ✅ Crunchbase enriched")
                else:
                    print(f"   ❌ Crunchbase data not found")
                    
                    # Fallback to SerperDev for LinkedIn if Crunchbase failed and we have the API key
                    if not skip_linkedin and not company.linkedin_url:
                        print(f"   🔍 Trying SerperDev for LinkedIn...")
                        async with aiohttp.ClientSession() as http_session:
                            linkedin_url = await find_linkedin_url(http_session, company.name, company.website)
                            if linkedin_url:
                                company.linkedin_url = linkedin_url
                                linkedin_found += 1
                                updated = True
                                print(f"   ✅ Found: {linkedin_url}")
                            else:
                                print(f"   ❌ LinkedIn URL not found")
            else:
                if not skip_crunchbase:
                    print(f"   ✓ Already fully enriched")
            
            # Save progress after each company
            if updated:
                try:
                    session.commit()
                except Exception as e:
                    print(f"   ⚠️  Error saving: {e}")
                    session.rollback()
            
            # Progress update every 50 companies
            if i % 50 == 0:
                print(f"\n📈 Progress: {i}/{total} companies processed")
                print(f"   LinkedIn URLs found: {linkedin_found}")
                print(f"   Crunchbase enriched: {crunchbase_enriched}")
        
        print("\n" + "=" * 70)
        print("ENRICHMENT COMPLETE")
        print("=" * 70)
        print(f"✅ Processed: {total} companies")
        if not skip_linkedin:
            print(f"🔗 LinkedIn URLs found: {linkedin_found}")
        if not skip_crunchbase:
            print(f"📊 Crunchbase enriched: {crunchbase_enriched}")
        
    except Exception as e:
        print(f"\n❌ Error during enrichment: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


async def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enrich portfolio companies with LinkedIn and Crunchbase data')
    parser.add_argument('--firm', type=str, help='PE firm name to enrich (optional)')
    parser.add_argument('--limit', type=int, help='Limit number of companies to process')
    
    args = parser.parse_args()
    
    await enrich_companies(pe_firm_name=args.firm, limit=args.limit)


if __name__ == "__main__":
    asyncio.run(main())
