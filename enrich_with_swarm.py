"""
Enrich existing a16z Crunchbase data with The Swarm API fields
Adds industry, headcount, market cap, funding, and other business metrics
"""
import json
import time
from datetime import datetime
from a16z_swarm_scraper import search_company_swarm, get_company_details_swarm

def main():
    """Enrich Crunchbase data with Swarm API"""
    start_time = time.time()
    
    # Load existing Crunchbase-enriched data
    print("📂 Loading a16z_portfolio_complete.json (Crunchbase data)...")
    with open("a16z_portfolio_complete.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    companies = data["companies"]
    print(f"✅ Loaded {len(companies)} companies\n")
    
    print("=" * 100)
    print("🐝 ENRICHING WITH THE SWARM API (Industry, Headcount, Market Cap, Funding, etc.)")
    print("=" * 100)
    print()
    
    enriched_count = 0
    not_found_count = 0
    
    for idx, company in enumerate(companies, 1):
        company_name = company.get("name", "")
        
        print(f"[{idx}/{len(companies)}] {company_name:50}", end=" ")
        
        if not company_name:
            print("⚠️  No name")
            continue
        
        # Search for company in The Swarm
        company_ids = search_company_swarm(company_name)
        
        if company_ids:
            # Get detailed info for the first match
            details = get_company_details_swarm(company_ids[0])
            
            if details:
                # Add Swarm data (keeping existing Crunchbase HQ and year)
                company["swarm_industry"] = details.get("industry", "")
                company["swarm_headcount"] = details.get("headcount", "")
                company["size_class"] = details.get("size_class", "")
                company["total_funding_usd"] = details.get("total_funding_usd", 0)
                company["last_round_type"] = details.get("last_round_type", "")
                company["last_round_amount_usd"] = details.get("last_round_amount_usd", 0)
                company["market_cap"] = details.get("market_cap", 0)
                company["ipo_date"] = details.get("ipo_date", "")
                company["ipo_year"] = details.get("ipo_year", "")
                company["ownership_status"] = details.get("ownership_status", "")
                company["ownership_status_detailed"] = details.get("ownership_status_detailed", "")
                company["is_public"] = details.get("is_public", False)
                company["is_acquired"] = details.get("is_acquired", False)
                company["is_exited_swarm"] = details.get("is_exited", False)
                company["customer_types"] = details.get("customer_types", "")
                company["stock_exchange"] = details.get("stock_exchange", "")
                
                # If Swarm has better summary, add it
                if details.get("summary"):
                    company["summary"] = details.get("summary", "")
                
                industry = company["swarm_industry"][:20] if company["swarm_industry"] else "N/A"
                headcount = f"{company['swarm_headcount']:,}" if company['swarm_headcount'] else "N/A"
                
                print(f"✅ Industry: {industry:20} Employees: {headcount:8}")
                enriched_count += 1
            else:
                print(f"⚠️  Found but no data")
        else:
            print(f"❌ Not found")
            not_found_count += 1
        
        # Rate limiting
        if idx % 10 == 0:
            print(f"\n⏸️  Pausing 2s (processed {idx} companies)...\n")
            time.sleep(2)
        else:
            time.sleep(0.5)
    
    # Save enriched data
    data["enrichment_sources"] = ["Crunchbase", "The Swarm"]
    data["last_swarm_enrichment"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    output_file = "a16z_portfolio_full_enriched.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    # Print summary
    elapsed_time = time.time() - start_time
    
    print("\n" + "=" * 100)
    print(f"✅ Enriched {enriched_count}/{len(companies)} companies with Swarm data")
    print("=" * 100)
    print()
    print(f"✅ Saved {len(companies)} companies to {output_file}")
    print()
    print(f"📊 Final Statistics:")
    print(f"  Total companies: {len(companies)}")
    print(f"  Companies with Swarm data: {enriched_count} ({enriched_count*100//len(companies)}%)")
    print(f"  Companies not found: {not_found_count}")
    print(f"  Time elapsed: {elapsed_time/60:.1f} minutes")
    print()
    
    # Show sample enriched companies
    enriched_companies = [c for c in companies if c.get("swarm_industry") or c.get("swarm_headcount")]
    if enriched_companies:
        print(f"📋 Sample fully enriched companies (Crunchbase + Swarm):")
        for company in enriched_companies[:10]:
            name = company.get("name", "N/A")[:30]
            hq = company.get("headquarters", "N/A")[:35]
            year = company.get("investment_year", "N/A")
            industry = company.get("swarm_industry", "N/A")[:20]
            headcount = company.get("swarm_headcount", 0)
            headcount_str = f"{headcount:,}" if headcount else "N/A"
            market_cap = company.get("market_cap", 0)
            
            # Format market cap
            if market_cap and market_cap > 0:
                if market_cap >= 1e9:
                    mc_str = f"${market_cap/1e9:.1f}B"
                elif market_cap >= 1e6:
                    mc_str = f"${market_cap/1e6:.1f}M"
                else:
                    mc_str = f"${market_cap:,.0f}"
            else:
                mc_str = "N/A"
            
            print(f"  • {name:30} | {hq:35} | {year:4} | {industry:20} | {headcount_str:8} | MCap: {mc_str}")

if __name__ == "__main__":
    main()
