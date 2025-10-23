from query_database import PortfolioQuery

pq = PortfolioQuery()

print("=" * 80)
print("ENRICHMENT DATA CONSISTENCY VERIFICATION")
print("=" * 80)

firms = [
    ("Vista Equity Partners", "Vista"),
    ("TA Associates", "TA"),
    ("Andreessen Horowitz", "a16z")
]

for firm_name, short_name in firms:
    companies = pq.get_companies_by_pe_firm(firm_name)
    enriched = [c for c in companies if c.swarm_industry]
    
    print(f"\n{short_name} Sample Companies:")
    print("-" * 80)
    
    for c in enriched[:3]:
        mcap = f"${c.market_cap/1e9:.2f}B" if c.market_cap and c.market_cap > 0 else "Private"
        print(f"\n  {c.name}")
        print(f"    HQ: {c.headquarters}")
        print(f"    Year: {c.investment_year or 'N/A'}")
        print(f"    Industry: {c.swarm_industry}")
        print(f"    Market Cap: {mcap}")
        if c.ipo_year:
            print(f"    IPO: {c.ipo_year}")
        if c.ownership_status:
            print(f"    Status: {c.ownership_status}")

print("\n" + "=" * 80)
print("ENRICHMENT STATISTICS")
print("=" * 80)

for firm_name, short_name in firms:
    companies = pq.get_companies_by_pe_firm(firm_name)
    total = len(companies)
    with_industry = len([c for c in companies if c.swarm_industry])
    with_hq = len([c for c in companies if c.headquarters])
    with_year = len([c for c in companies if c.investment_year])
    
    print(f"\n{short_name}:")
    print(f"  Total Companies: {total}")
    print(f"  With HQ: {with_hq} ({with_hq/total*100:.1f}%)")
    print(f"  With Founding Year: {with_year} ({with_year/total*100:.1f}%)")
    print(f"  With Industry: {with_industry} ({with_industry/total*100:.1f}%)")

print("\n" + "=" * 80)
