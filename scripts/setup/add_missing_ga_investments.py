"""
Add the 5 missing General Atlantic investment relationships
The companies exist but with different capitalization
"""
import os
import sys
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.models.database_models_v2 import Company, PEFirm, CompanyPEInvestment

def normalize_status(raw_status):
    """Normalize raw status to standard categories"""
    if not raw_status:
        return 'unknown'
    
    status_lower = raw_status.lower().strip()
    
    if any(word in status_lower for word in ['current', 'active', 'portfolio']):
        return 'current'
    elif any(word in status_lower for word in ['exit', 'exited', 'former', 'acquired', 'ipo']):
        return 'exited'
    else:
        return 'unknown'

# Database connection
engine = create_engine(os.environ['DATABASE_URL'])
Session = sessionmaker(bind=engine)
session = Session()

print("\n" + "="*80)
print("ADDING MISSING GENERAL ATLANTIC INVESTMENTS")
print("="*80)

# Get General Atlantic
ga = session.query(PEFirm).filter(PEFirm.name == "General Atlantic").first()
if not ga:
    print("❌ General Atlantic not found!")
    sys.exit(1)

print(f"✅ Found General Atlantic (ID: {ga.id})")

# Companies to link (case-insensitive search)
missing_companies = [
    {'name': 'Buzzfeed', 'actual': 'BuzzFeed', 'status': 'Portfolio'},
    {'name': 'Citiustech', 'actual': 'CitiusTech', 'status': 'Portfolio'},
    {'name': 'Copilotiq', 'actual': 'CopilotIQ', 'status': 'Portfolio'},
    {'name': 'Crowdstrike', 'actual': 'CrowdStrike', 'status': 'Portfolio'},
    {'name': 'Nydig', 'actual': 'NYDIG', 'status': 'Portfolio'}
]

added = 0
already_exist = 0

for company_info in missing_companies:
    # Find company (case-insensitive)
    company = session.query(Company).filter(
        func.lower(Company.name) == company_info['name'].lower()
    ).first()
    
    if not company:
        print(f"❌ Company '{company_info['name']}' not found")
        continue
    
    # Check if investment already exists
    existing = session.query(CompanyPEInvestment).filter(
        CompanyPEInvestment.company_id == company.id,
        CompanyPEInvestment.pe_firm_id == ga.id
    ).first()
    
    if existing:
        print(f"⏭️  Investment already exists: {company.name} ↔ General Atlantic")
        already_exist += 1
        continue
    
    # Create investment
    investment = CompanyPEInvestment(
        company_id=company.id,
        pe_firm_id=ga.id,
        raw_status=company_info['status'],
        computed_status=normalize_status(company_info['status'])
    )
    session.add(investment)
    print(f"✅ Added: {company.name} (ID: {company.id}) ↔ General Atlantic")
    added += 1

# Commit
try:
    session.commit()
    print(f"\n💾 Committed {added} new investments")
except Exception as e:
    session.rollback()
    print(f"\n❌ Commit error: {e}")
    sys.exit(1)

# Final count
final_count = session.query(CompanyPEInvestment).filter(
    CompanyPEInvestment.pe_firm_id == ga.id
).count()

print("\n" + "="*80)
print("📈 SUMMARY")
print("="*80)
print(f"✅ Added:            {added}")
print(f"⏭️  Already existed:  {already_exist}")
print(f"📊 Total GA investments: {final_count}")
print("="*80)

if final_count == 386:
    print("\n🎉 SUCCESS! All 386 General Atlantic companies are now in v2 schema!")
else:
    print(f"\n⚠️  Expected 386, got {final_count}")

session.close()
