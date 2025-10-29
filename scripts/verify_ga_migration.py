"""
Verify General Atlantic migration to v2 schema
"""
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.database_models_v2 import Company, PEFirm, CompanyPEInvestment

# Database connection
engine = create_engine(os.environ['DATABASE_URL'])
Session = sessionmaker(bind=engine)
session = Session()

print("\n" + "="*80)
print("GENERAL ATLANTIC MIGRATION VERIFICATION")
print("="*80)

# Get General Atlantic
ga = session.query(PEFirm).filter(PEFirm.name == "General Atlantic").first()

# Total count
total = session.query(CompanyPEInvestment).filter(
    CompanyPEInvestment.pe_firm_id == ga.id
).count()

print(f"\n📊 Total General Atlantic investments: {total}")

# Sample companies with enrichment data
print("\n📋 Sample companies with enrichment:")
companies = session.query(Company, CompanyPEInvestment).join(
    CompanyPEInvestment
).filter(
    CompanyPEInvestment.pe_firm_id == ga.id
).limit(10).all()

for company, investment in companies:
    print(f"\n   • {company.name}")
    if company.website:
        print(f"     Website: {company.website}")
    if company.industry_category:
        print(f"     Industry: {company.industry_category}")
    if company.revenue_range:
        print(f"     Revenue: {company.revenue_range}")
    if company.employee_count:
        print(f"     Employees: {company.employee_count}")
    if company.linkedin_url:
        print(f"     LinkedIn: {company.linkedin_url}")
    print(f"     Status: {investment.computed_status}")

# Enrichment statistics
print("\n📈 Enrichment Statistics:")

with_website = session.query(Company).join(CompanyPEInvestment).filter(
    CompanyPEInvestment.pe_firm_id == ga.id,
    Company.website.isnot(None)
).count()

with_industry = session.query(Company).join(CompanyPEInvestment).filter(
    CompanyPEInvestment.pe_firm_id == ga.id,
    Company.industry_category.isnot(None)
).count()

with_revenue = session.query(Company).join(CompanyPEInvestment).filter(
    CompanyPEInvestment.pe_firm_id == ga.id,
    Company.revenue_range.isnot(None)
).count()

with_employees = session.query(Company).join(CompanyPEInvestment).filter(
    CompanyPEInvestment.pe_firm_id == ga.id,
    Company.employee_count.isnot(None)
).count()

with_linkedin = session.query(Company).join(CompanyPEInvestment).filter(
    CompanyPEInvestment.pe_firm_id == ga.id,
    Company.linkedin_url.isnot(None)
).count()

print(f"   • Websites:   {with_website}/{total} ({with_website/total*100:.1f}%)")
print(f"   • Industry:   {with_industry}/{total} ({with_industry/total*100:.1f}%)")
print(f"   • Revenue:    {with_revenue}/{total} ({with_revenue/total*100:.1f}%)")
print(f"   • Employees:  {with_employees}/{total} ({with_employees/total*100:.1f}%)")
print(f"   • LinkedIn:   {with_linkedin}/{total} ({with_linkedin/total*100:.1f}%)")

print("\n" + "="*80)
if total == 386:
    print("✅ MIGRATION SUCCESSFUL - Ready to deploy!")
else:
    print(f"⚠️  Expected 386, got {total}")
print("="*80)

session.close()
