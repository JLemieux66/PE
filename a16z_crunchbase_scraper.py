"""
A16z Portfolio Scraper with Crunchbase Enrichment
Uses Crunchbase API to get headquarters and founding year
"""
import asyncio
import json
import requests
from playwright.async_api import async_playwright
from datetime import datetime
import time


CRUNCHBASE_API_KEY = "7631ec690653f0055ea43a1169f12787"
CRUNCHBASE_BASE_URL = "https://api.crunchbase.com/v4/data"


def search_company_crunchbase(company_name):
    """
    Search for company in Crunchbase and return details
    
    Args:
        company_name: Company name to search
        
    Returns:
        dict: Company details (headquarters, founded_year, etc)
    """
    try:
        # Search for the company using autocomplete endpoint
        search_url = f"{CRUNCHBASE_BASE_URL}/autocompletes"
        params = {
            "query": company_name,
            "collection_ids": "organizations",
            "user_key": CRUNCHBASE_API_KEY
        }
        
        response = requests.get(search_url, params=params, timeout=10)
        
        if response.status_code != 200:
            return {}
        
        data = response.json()
        
        # Get first matching entity
        if data.get("entities") and len(data["entities"]) > 0:
            entity = data["entities"][0]
            entity_id = entity.get("identifier", {}).get("permalink") or entity.get("identifier", {}).get("uuid")
            
            if entity_id:
                # Get full company details
                return get_company_details_crunchbase(entity_id)
        
        return {}
        
    except Exception as e:
        print(f" CB Error: {str(e)[:50]}")
        return {}


def get_company_details_crunchbase(entity_id):
    """
    Get detailed company information from Crunchbase
    
    Args:
        entity_id: Crunchbase entity ID or permalink
        
    Returns:
        dict: Company details
    """
    try:
        details_url = f"{CRUNCHBASE_BASE_URL}/entities/organizations/{entity_id}"
        params = {
            "user_key": CRUNCHBASE_API_KEY,
            "field_ids": "location_identifiers,founded_on,short_description"
        }
        
        response = requests.get(details_url, params=params, timeout=10)
        
        if response.status_code != 200:
            return {}
        
        data = response.json()
        properties = data.get("properties", {})
        
        # Extract headquarters from location_identifiers
        hq = ""
        location_ids = properties.get("location_identifiers", [])
        if location_ids and len(location_ids) > 0:
            # Get city and region
            city = next((loc.get("value") for loc in location_ids if loc.get("location_type") == "city"), "")
            region = next((loc.get("value") for loc in location_ids if loc.get("location_type") == "region"), "")
            
            if city and region:
                hq = f"{city}, {region}"
            elif city:
                hq = city
            elif region:
                hq = region
        
        # Extract founded year
        founded_on = properties.get("founded_on", {})
        founded_year = ""
        if founded_on and isinstance(founded_on, dict):
            value = founded_on.get("value", "")
            if value and len(value) >= 4:
                founded_year = value[:4]
        
        return {
            "headquarters": hq,
            "founded_year": founded_year,
            "description": properties.get("short_description", "")
        }
        
    except Exception as e:
        print(f" Details Error: {str(e)[:50]}")
        return {}


async def scrape_a16z_with_crunchbase():
    """Scrape a16z portfolio and enrich with Crunchbase data"""
    
    async with async_playwright() as p:
        print("🚀 Launching browser...")
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        url = "https://a16z.com/portfolio/"
        print(f"📄 Loading {url}...")
        
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(5000)
        
        print("📊 Extracting base company data from a16z...")
        
        # Get basic data from a16z
        companies = await page.evaluate("""
            () => {
                const companies = [];
                const elements = document.querySelectorAll('.company-grid-item');
                
                elements.forEach(el => {
                    const name = el.getAttribute('data-name');
                    const dataFilterBy = el.getAttribute('data-filter-by') || '';
                    const companyId = el.getAttribute('data-id');
                    const statusEl = el.querySelector('.builder-title span');
                    const statusText = statusEl ? statusEl.textContent.trim() : '';
                    
                    const status = dataFilterBy.includes('sts_Exits') ? 'Exit' : 
                                   dataFilterBy.includes('sts_Active') ? 'Active' : 'Unknown';
                    
                    const sectors = [];
                    const stages = [];
                    dataFilterBy.split(';').forEach(part => {
                        if (part.startsWith('cat_')) sectors.push(part.substring(4));
                        if (part.startsWith('stgi_')) stages.push(part.substring(5));
                    });
                    
                    if (name) {
                        companies.push({
                            name,
                            sector: sectors.join(', '),
                            status,
                            exit_details: statusText,
                            stage: stages.join(', '),
                            company_id: companyId
                        });
                    }
                });
                
                return companies;
            }
        """)
        
        await browser.close()
        
        print(f"✅ Found {len(companies)} companies\n")
        
        # Enrich with Crunchbase
        print("🔍 Enriching with Crunchbase data...")
        print("=" * 80)
        
        enriched_count = 0
        
        for i, company in enumerate(companies):
            print(f"[{i+1}/{len(companies)}] {company['name'][:35]:<35}", end=" ")
            
            # Search Crunchbase
            cb_data = search_company_crunchbase(company['name'])
            
            if cb_data:
                company['headquarters'] = cb_data.get('headquarters', '')
                company['investment_year'] = cb_data.get('founded_year', '')  # Using founded year as proxy
                if not company.get('description'):
                    company['description'] = cb_data.get('description', '')
                
                if cb_data.get('headquarters') or cb_data.get('founded_year'):
                    enriched_count += 1
                    print(f"✅ HQ: {cb_data.get('headquarters', 'N/A')[:20]:<20} Year: {cb_data.get('founded_year', 'N/A')}")
                else:
                    print("⚠️  Found but no HQ/year")
            else:
                company['headquarters'] = ''
                company['investment_year'] = ''
                company['description'] = ''
                print("❌ Not found")
            
            # Rate limiting - be nice to Crunchbase
            if (i + 1) % 10 == 0:
                print(f"\n⏸️  Pausing 2s (processed {i+1} companies)...\n")
                time.sleep(2)
            else:
                time.sleep(0.5)
        
        print("\n" + "=" * 80)
        print(f"✅ Enriched {enriched_count}/{len(companies)} companies with Crunchbase data")
        print("=" * 80)
        
        return companies


async def main():
    print("=" * 80)
    print("A16Z PORTFOLIO SCRAPER - WITH CRUNCHBASE ENRICHMENT")
    print("=" * 80 + "\n")
    
    companies = await scrape_a16z_with_crunchbase()
    
    output = {
        "pe_firm": "Andreessen Horowitz",
        "extraction_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_companies": len(companies),
        "current_portfolio": len([c for c in companies if c['status'] == 'Active']),
        "exited_portfolio": len([c for c in companies if c['status'] == 'Exit']),
        "companies": companies
    }
    
    output_file = "a16z_portfolio_complete.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Saved {len(companies)} companies to {output_file}\n")
    
    # Stats
    with_hq = sum(1 for c in companies if c.get('headquarters'))
    with_year = sum(1 for c in companies if c.get('investment_year'))
    
    print(f"📊 Final Statistics:")
    print(f"  Total companies: {len(companies)}")
    print(f"  Companies with HQ: {with_hq} ({100*with_hq//len(companies)}%)")
    print(f"  Companies with year: {with_year} ({100*with_year//len(companies)}%)")
    
    print(f"\n📋 Sample enriched companies:")
    for c in [c for c in companies if c.get('headquarters')][:10]:
        print(f"  • {c['name'][:30]:<30} | {c.get('headquarters', 'N/A')[:20]:<20} | Founded: {c.get('investment_year', 'N/A')}")


if __name__ == "__main__":
    asyncio.run(main())
