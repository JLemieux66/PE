"""
Complete Enrichment Pipeline for Portfolio Companies (v2 - Many-to-Many Schema)
Automatically finds LinkedIn URLs using SerperDev and enriches with Crunchbase data
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import asyncio
import aiohttp
import re
import os
from typing import Optional
from dotenv import load_dotenv
from src.models.database_models_v2 import Company, PEFirm, get_session
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
        
        if details.get('linkedin_url') and not company.linkedin_url:
            company.linkedin_url = details['linkedin_url']
        
        if details.get('description') and not company.description:
            company.description = details['description']
        
        # Parse headquarters into city/state/country
        if details.get('headquarters'):
            hq = details['headquarters']
            parts = [p.strip() for p in hq.split(',')]
            
            if len(parts) >= 3:
                company.city = parts[0]
                company.state_region = parts[1]
                company.country = parts[2]
            elif len(parts) == 2:
                company.city = parts[0]
                company.country = parts[1]
            elif len(parts) == 1:
                company.country = parts[0]
        
        # Update industry category from Crunchbase categories
        if details.get('industry_category') and not company.industry_category:
            company.industry_category = details['industry_category']
        
        return True
        
    except Exception as e:
        print(f"   ⚠️  Crunchbase error: {e}")
        return False


async def find_linkedin_url(session: aiohttp.ClientSession, company_name: str, website: Optional[str] = None) -> Optional[str]:
    """
    Find company LinkedIn URL using SerperDev API
    """
    if not SERPER_API_KEY:
        return None
    
    try:
        # Build search query
        if website:
            domain = website.replace('http://', '').replace('https://', '').split('/')[0]
            query = f"{company_name} {domain} site:linkedin.com/company"
        else:
            query = f"{company_name} site:linkedin.com/company"
        
        # Make API request
        url = "https://google.serper.dev/search"
        payload = {
            "q": query,
            "num": 3
        }
        headers = {
            'X-API-KEY': SERPER_API_KEY,
            'Content-Type': 'application/json'
        }
        
        async with session.post(url, json=payload, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                
                # Check organic results
                organic = data.get('organic', [])
                for result in organic:
                    link = result.get('link', '')
                    if 'linkedin.com/company/' in link:
                        # Clean up the URL
                        clean_url = link.split('?')[0]  # Remove query params
                        return clean_url
            
            return None
            
    except Exception as e:
        print(f"   ⚠️  SerperDev error: {e}")
        return None


async def enrich_companies(pe_firm_name: Optional[str] = None, limit: Optional[int] = None, skip_linkedin=False, skip_crunchbase=False):
    """
    Enrich companies with LinkedIn URLs and Crunchbase data
    
    Args:
        pe_firm_name: Optional PE firm name to filter by
        limit: Optional limit on number of companies to process
        skip_linkedin: Skip LinkedIn URL enrichment
        skip_crunchbase: Skip Crunchbase enrichment
    """
    
    session = get_session()
    
    try:
        # Query companies - now from Company table (v2 schema)
        query = session.query(Company)
        
        if pe_firm_name:
            # Filter companies that have investments from this PE firm
            query = query.join(Company.investments).join(PEFirm).filter(
                PEFirm.name == pe_firm_name
            )
        
        if limit:
            companies = query.limit(limit).all()
        else:
            companies = query.all()
        
        total = len(companies)
        
        if total == 0:
            print("No companies found to enrich!")
            return
        
        print("=" * 70)
        print(f"PORTFOLIO COMPANY ENRICHMENT")
        print("=" * 70)
        if pe_firm_name:
            print(f"PE Firm: {pe_firm_name}")
        print(f"Total companies to process: {total}")
        if skip_linkedin:
            print("⏭️  Skipping LinkedIn enrichment")
        if skip_crunchbase:
            print("⏭️  Skipping Crunchbase enrichment")
        print("=" * 70)
        
        linkedin_found = 0
        crunchbase_enriched = 0
        
        # Process companies
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
