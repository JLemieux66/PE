"""
Enrich a16z portfolio with The Swarm API data
Uses The Swarm API to get company information including headquarters and founding dates
"""
import asyncio
import json
import time
from datetime import datetime
import requests
from playwright.async_api import async_playwright

# The Swarm API Configuration
SWARM_API_KEY = "EdTGzUL6Eu9gNPnUn2NtA1q2mZ8LHwgc10s2ohvj"
SWARM_BASE_URL = "https://bee.theswarm.com"
SWARM_SEARCH_URL = f"{SWARM_BASE_URL}/companies/search"
SWARM_FETCH_URL = f"{SWARM_BASE_URL}/companies/fetch"

# Headers for The Swarm API
SWARM_HEADERS = {
    "Content-Type": "application/json",
    "x-api-key": SWARM_API_KEY
}

# a16z portfolio page
A16Z_URL = "https://a16z.com/portfolio/"


def search_company_swarm(company_name):
    """
    Search for a company in The Swarm API
    
    Args:
        company_name: Name of the company to search
        
    Returns:
        list: List of company IDs matching the search
    """
    try:
        payload = {
            "query": {
                "match": {
                    "company_info.name": company_name
                }
            }
        }
        
        response = requests.post(
            SWARM_SEARCH_URL,
            headers=SWARM_HEADERS,
            json=payload,
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"    ❌ Search failed: {response.status_code}")
            return []
        
        data = response.json()
        ids = data.get("ids", [])
        total_count = data.get("totalCount", 0)
        
        if total_count > 0:
            print(f"    🔍 Found {total_count} matches, using first result")
            return ids[:1]  # Return only the first ID (most relevant)
        
        return []
        
    except Exception as e:
        print(f"    ❌ Search error: {str(e)}")
        return []


def get_company_details_swarm(company_id):
    """
    Get detailed company information from The Swarm API
    
    Args:
        company_id: The Swarm company ID
        
    Returns:
        dict: Company details
    """
    try:
        payload = {
            "ids": [company_id]
            # Don't specify fields to get all available data
        }
        
        response = requests.post(
            SWARM_FETCH_URL,
            headers=SWARM_HEADERS,
            json=payload,
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"    ❌ Fetch failed: {response.status_code}")
            return {}
        
        data = response.json()
        
        # The response contains results array
        results = data.get("results", [])
        if results and len(results) > 0:
            company_info = results[0].get("company_info", {})
            business_data = company_info.get("business_data", {})
            funding = company_info.get("funding", {})
            workforce = company_info.get("workforce", {})
            financing_profile = business_data.get("financing_profile", {})
            
            # Extract headquarters from locations array
            hq = ""
            locations = company_info.get("locations", [])
            if locations:
                # Find primary location or use first one
                primary_location = next((loc for loc in locations if loc.get("is_primary")), locations[0])
                hq = primary_location.get("name", "")
            
            # Extract founded year from founded date
            founded_year = ""
            founded = company_info.get("founded", "")
            if founded:
                # Extract year from ISO date (e.g., "2007-01-01T00:00:00Z" -> "2007")
                if len(founded) >= 4:
                    founded_year = founded[:4]
            
            # Extract funding information
            total_funding = funding.get("total_funding_usd", 0)
            last_round = funding.get("last_round", {})
            last_round_type = last_round.get("last_round_type", "")
            last_round_amount = last_round.get("last_round_amount_usd", 0)
            
            # Extract business metrics
            market_cap = financing_profile.get("market_cap", 0)
            ipo_date = financing_profile.get("ipo_date", "")
            ipo_year = ipo_date[:4] if ipo_date and len(ipo_date) >= 4 else ""
            
            ownership_status = business_data.get("ownership_status", "")
            ownership_detailed = business_data.get("ownership_status_detailed", "")
            is_public = "ipo" in ownership_detailed.lower() or "public" in ownership_detailed.lower()
            is_acquired = business_data.get("is_acquired", False)
            is_exited = business_data.get("is_exited", False)
            
            return {
                "headquarters": hq,
                "founded_year": founded_year,
                "description": company_info.get("description", ""),
                "summary": company_info.get("summary", ""),
                "website": company_info.get("website", ""),
                "industry": company_info.get("industry", ""),
                "headcount": workforce.get("headcount", ""),
                "size_class": company_info.get("size", {}).get("class", ""),
                "total_funding_usd": total_funding,
                "last_round_type": last_round_type,
                "last_round_amount_usd": last_round_amount,
                "market_cap": market_cap,
                "ipo_date": ipo_date,
                "ipo_year": ipo_year,
                "ownership_status": ownership_status,
                "ownership_status_detailed": ownership_detailed,
                "is_public": is_public,
                "is_acquired": is_acquired,
                "is_exited": is_exited,
                "customer_types": ", ".join(business_data.get("customer_types", [])),
                "stock_exchange": business_data.get("stock_exchange", "")
            }
        
        return {}
        
    except Exception as e:
        print(f"    ❌ Fetch error: {str(e)}")
        return {}


async def scrape_a16z_portfolio():
    """Scrape a16z portfolio page to get all companies"""
    print("🚀 Starting a16z portfolio scraper...")
    print(f"📍 URL: {A16Z_URL}\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("📄 Loading portfolio page...")
        await page.goto(A16Z_URL, wait_until="domcontentloaded", timeout=60000)
        
        # Wait for company grid to load
        await page.wait_for_selector(".company-grid-item", timeout=30000)
        
        # Extract all companies
        companies = await page.evaluate("""
            () => {
                const items = document.querySelectorAll('.company-grid-item');
                return Array.from(items).map(item => ({
                    name: item.dataset.companyName || '',
                    sector: item.dataset.sector || '',
                    status: item.dataset.status || '',
                    exit_details: item.dataset.exitDetails || '',
                    stage: item.dataset.stage || '',
                    company_id: item.dataset.companyId || ''
                }));
            }
        """)
        
        await browser.close()
        
        print(f"✅ Found {len(companies)} companies\n")
        return companies


async def main():
    """Main function to scrape and enrich a16z portfolio with The Swarm data"""
    start_time = time.time()
    
    # Step 1: Scrape a16z portfolio
    companies = await scrape_a16z_portfolio()
    
    if not companies:
        print("❌ No companies found!")
        return
    
    # Step 2: Enrich with The Swarm API data
    print("=" * 80)
    print("🐝 ENRICHING WITH THE SWARM API")
    print("=" * 80)
    print()
    
    enriched_count = 0
    not_found_count = 0
    
    for idx, company in enumerate(companies, 1):
        company_name = company.get("name", "")
        
        print(f"[{idx}/{len(companies)}] {company_name:40}", end=" ")
        
        # Search for company in The Swarm
        company_ids = search_company_swarm(company_name)
        
        if company_ids:
            # Get detailed info for the first match
            details = get_company_details_swarm(company_ids[0])
            
            if details:
                # Add enriched data to company
                company["headquarters"] = details.get("headquarters", "")
                company["investment_year"] = details.get("founded_year", "")
                company["description"] = details.get("description", "")
                company["summary"] = details.get("summary", "")
                company["website"] = details.get("website", "")
                company["industry"] = details.get("industry", "")
                company["headcount"] = details.get("headcount", "")
                company["size_class"] = details.get("size_class", "")
                
                # Financial data
                company["total_funding_usd"] = details.get("total_funding_usd", 0)
                company["last_round_type"] = details.get("last_round_type", "")
                company["last_round_amount_usd"] = details.get("last_round_amount_usd", 0)
                company["market_cap"] = details.get("market_cap", 0)
                company["ipo_date"] = details.get("ipo_date", "")
                company["ipo_year"] = details.get("ipo_year", "")
                
                # Business metrics
                company["ownership_status"] = details.get("ownership_status", "")
                company["ownership_status_detailed"] = details.get("ownership_status_detailed", "")
                company["is_public"] = details.get("is_public", False)
                company["is_acquired"] = details.get("is_acquired", False)
                company["is_exited"] = details.get("is_exited", False)
                company["customer_types"] = details.get("customer_types", "")
                company["stock_exchange"] = details.get("stock_exchange", "")
                
                hq_display = company["headquarters"][:40] if company["headquarters"] else "N/A"
                year_display = company["investment_year"] if company["investment_year"] else "N/A"
                industry_display = company["industry"][:20] if company["industry"] else "N/A"
                
                print(f"✅ HQ: {hq_display:40} Year: {year_display:4} Industry: {industry_display:20}")
                enriched_count += 1
            else:
                print(f"⚠️  Found but no data")
        else:
            print(f"❌ Not found")
            not_found_count += 1
        
        # Rate limiting - be respectful to The Swarm API
        if idx % 10 == 0:
            print(f"\n⏸️  Pausing 2s (processed {idx} companies)...\n")
            time.sleep(2)
        else:
            time.sleep(0.5)
    
    # Step 3: Save enriched data
    output_data = {
        "pe_firm": "Andreessen Horowitz",
        "extraction_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_companies": len(companies),
        "current_portfolio": sum(1 for c in companies if c.get("status", "").lower() == "active"),
        "exited_portfolio": sum(1 for c in companies if c.get("status", "").lower() == "exit"),
        "companies": companies
    }
    
    output_file = "a16z_portfolio_swarm.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    # Print summary
    elapsed_time = time.time() - start_time
    
    print("\n" + "=" * 80)
    print(f"✅ Enriched {enriched_count}/{len(companies)} companies with The Swarm data")
    print("=" * 80)
    print()
    print(f"✅ Saved {len(companies)} companies to {output_file}")
    print()
    print(f"📊 Final Statistics:")
    print(f"  Total companies: {len(companies)}")
    print(f"  Companies enriched: {enriched_count} ({enriched_count*100//len(companies)}%)")
    print(f"  Companies not found: {not_found_count}")
    print(f"  Time elapsed: {elapsed_time/60:.1f} minutes")
    print()
    
    # Show sample enriched companies
    enriched_companies = [c for c in companies if c.get("headquarters") or c.get("investment_year")]
    if enriched_companies:
        print(f"📋 Sample enriched companies:")
        for company in enriched_companies[:10]:
            hq = company.get("headquarters", "N/A")[:35]
            year = company.get("investment_year", "N/A")
            industry = company.get("industry", "N/A")[:20]
            headcount = company.get("headcount", "N/A")
            market_cap = company.get("market_cap", 0)
            
            # Format market cap
            if market_cap and market_cap > 0:
                if market_cap >= 1e9:
                    market_cap_str = f"${market_cap/1e9:.1f}B"
                elif market_cap >= 1e6:
                    market_cap_str = f"${market_cap/1e6:.1f}M"
                else:
                    market_cap_str = f"${market_cap:,.0f}"
            else:
                market_cap_str = "N/A"
            
            print(f"  • {company['name']:30} | {hq:35} | {year:4} | {industry:20} | Employees: {headcount:6} | Market Cap: {market_cap_str}")


if __name__ == "__main__":
    asyncio.run(main())
