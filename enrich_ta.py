"""
Enrich TA Associates data with Crunchbase and Swarm APIs
"""
import json
import time
from datetime import datetime
from crunchbase_helpers import search_company_crunchbase, get_company_details_crunchbase
from a16z_swarm_scraper import search_company_swarm, get_company_details_swarm

def main():
    """Enrich TA data"""
    start_time = time.time()
    
    # Load existing TA data
    print("📂 Loading ta_portfolio_complete.json...")
    with open("ta_portfolio_complete.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    companies = data["companies"]
    print(f"✅ Loaded {len(companies)} companies\n")
    
    print("=" * 100)
    print("🔍 ENRICHING WITH CRUNCHBASE + SWARM APIs")
    print("=" * 100)
    print()
    
    enriched_count = 0
    
    for idx, company in enumerate(companies, 1):
        company_name = company.get("name", "")
        
        print(f"[{idx}/{len(companies)}] {company_name:50}", end=" ")
        
        if not company_name:
            print("⚠️  No name")
            continue
        
        # Step 1: Crunchbase for HQ and founding year (if not already present)
        if not company.get("headquarters"):
            cb_results = search_company_crunchbase(company_name)
            if cb_results:
                cb_details = get_company_details_crunchbase(cb_results[0])
                if cb_details:
                    company["headquarters"] = cb_details.get("headquarters", "")
                    company["investment_year"] = cb_details.get("founded_year", "")
                    if cb_details.get("description") and not company.get("description"):
                        company["description"] = cb_details.get("description", "")
        
        # Step 2: Swarm for industry, headcount, market cap, etc.
        swarm_ids = search_company_swarm(company_name)
        if swarm_ids:
            swarm_details = get_company_details_swarm(swarm_ids[0])
            if swarm_details:
                company["swarm_industry"] = swarm_details.get("industry", "")
                company["size_class"] = swarm_details.get("size_class", "")
                company["total_funding_usd"] = swarm_details.get("total_funding_usd", 0)
                company["last_round_type"] = swarm_details.get("last_round_type", "")
                company["last_round_amount_usd"] = swarm_details.get("last_round_amount_usd", 0)
                company["market_cap"] = swarm_details.get("market_cap", 0)
                company["ipo_date"] = swarm_details.get("ipo_date", "")
                company["ipo_year"] = swarm_details.get("ipo_year", "")
                company["ownership_status"] = swarm_details.get("ownership_status", "")
                company["ownership_status_detailed"] = swarm_details.get("ownership_status_detailed", "")
                company["is_public"] = swarm_details.get("is_public", False)
                company["is_acquired"] = swarm_details.get("is_acquired", False)
                company["is_exited_swarm"] = swarm_details.get("is_exited", False)
                company["customer_types"] = swarm_details.get("customer_types", "")
                company["stock_exchange"] = swarm_details.get("stock_exchange", "")
                if swarm_details.get("summary"):
                    company["summary"] = swarm_details.get("summary", "")
                
                hq = company.get("headquarters", company.get("hq", "N/A"))[:30]
                year = company.get("investment_year", "N/A")
                industry = company["swarm_industry"][:20] if company["swarm_industry"] else "N/A"
                
                print(f"✅ HQ: {hq:30} Year: {year:4} Industry: {industry:20}")
                enriched_count += 1
            else:
                print(f"⚠️  Crunchbase only")
        else:
            print(f"⚠️  No enrichment")
        
        # Rate limiting
        if idx % 10 == 0:
            print(f"\n⏸️  Pausing 2s (processed {idx} companies)...\n")
            time.sleep(2)
        else:
            time.sleep(0.5)
    
    # Save enriched data
    data["enrichment_sources"] = ["Crunchbase", "The Swarm"]
    data["last_enrichment"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    output_file = "ta_portfolio_full_enriched.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    # Print summary
    elapsed_time = time.time() - start_time
    
    print("\n" + "=" * 100)
    print(f"✅ Enriched {enriched_count}/{len(companies)} companies")
    print("=" * 100)
    print()
    print(f"✅ Saved to {output_file}")
    print(f"⏱️  Time elapsed: {elapsed_time/60:.1f} minutes")

if __name__ == "__main__":
    main()
