from query_database import PortfolioQuery
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from database_models import PortfolioCompany

DATABASE_URL = "sqlite:///pe_portfolio.db"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

print("=" * 80)
print("STANDARDIZED STATUS DISTRIBUTION")
print("=" * 80)

results = session.query(
    PortfolioCompany.status, 
    func.count(PortfolioCompany.id)
).group_by(PortfolioCompany.status).all()

total = sum([count for _, count in results])

for status, count in sorted(results, key=lambda x: x[1], reverse=True):
    percentage = count / total * 100
    print(f"  {status:20} {count:5} companies ({percentage:.1f}%)")

print(f"\nTotal: {total} companies")

# Show breakdown by PE firm
print("\n" + "=" * 80)
print("STATUS BY PE FIRM")
print("=" * 80)

firms = ['Vista Equity Partners', 'TA Associates', 'Andreessen Horowitz']
for firm_name in firms:
    pq = PortfolioQuery()
    companies = pq.get_companies_by_pe_firm(firm_name)
    
    active = len([c for c in companies if c.status == 'Active'])
    exited = len([c for c in companies if c.status == 'Exit'])
    unknown = len([c for c in companies if c.status == 'Unknown'])
    total_firm = len(companies)
    
    print(f"\n{firm_name}:")
    print(f"  Active:  {active:4} ({active/total_firm*100:.1f}%)")
    print(f"  Exit:    {exited:4} ({exited/total_firm*100:.1f}%)")
    print(f"  Unknown: {unknown:4} ({unknown/total_firm*100:.1f}%)")
    print(f"  Total:   {total_firm:4}")

session.close()
