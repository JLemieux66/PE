"""
Sync local database updates to production PostgreSQL database
This script copies company websites from local SQLite to production PostgreSQL
"""
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.database_models_v2 import Company, PEFirm, CompanyPEInvestment

# Local SQLite database
sqlite_engine = create_engine('sqlite:///pe_portfolio_v2.db')
SqliteSession = sessionmaker(bind=sqlite_engine)

# Production PostgreSQL database
postgres_url = os.getenv('DATABASE_URL')
if not postgres_url:
    print("❌ ERROR: DATABASE_URL environment variable not set")
    print("   Run with: railway run pipenv run python scripts/setup/sync_to_production.py")
    exit(1)

# Fix Railway's postgres:// to postgresql://
if postgres_url.startswith('postgres://'):
    postgres_url = postgres_url.replace('postgres://', 'postgresql://', 1)

postgres_engine = create_engine(postgres_url)
PostgresSession = sessionmaker(bind=postgres_engine)

print("\n" + "="*80)
print("🔄 SYNCING LOCAL DATABASE TO PRODUCTION")
print("="*80 + "\n")

# Get sessions
local_session = SqliteSession()
prod_session = PostgresSession()

try:
    # Get all companies with websites from local database
    local_companies = local_session.query(Company).filter(
        Company.website.isnot(None),
        Company.website != ''
    ).all()
    
    print(f"📊 Found {len(local_companies)} companies with websites in local database\n")
    
    websites_updated = 0
    websites_added = 0
    not_found = 0
    
    for i, local_company in enumerate(local_companies, 1):
        # Find matching company in production
        prod_company = prod_session.query(Company).filter_by(
            name=local_company.name
        ).first()
        
        if prod_company:
            # Update website if different
            if prod_company.website != local_company.website:
                old_website = prod_company.website or '(none)'
                print(f"[{i}] {local_company.name}: {old_website} → {local_company.website}")
                prod_company.website = local_company.website
                
                if old_website == '(none)':
                    websites_added += 1
                else:
                    websites_updated += 1
        else:
            not_found += 1
        
        # Commit in batches
        if i % 50 == 0:
            prod_session.commit()
            print(f"\n💾 Saved batch ({i}/{len(local_companies)} processed)\n")
    
    # Final commit
    prod_session.commit()
    
    print("\n" + "="*80)
    print("✅ SYNC COMPLETE")
    print("="*80 + "\n")
    
    print(f"🌐 Websites added: {websites_added}")
    print(f"✏️  Websites updated: {websites_updated}")
    print(f"ℹ️  Not found in production: {not_found}")
    
    # Summary by PE firm
    print("\n📊 Production Database Summary by PE Firm:")
    pe_firms = prod_session.query(PEFirm).all()
    
    for firm in pe_firms:
        total = prod_session.query(CompanyPEInvestment).filter_by(
            pe_firm_id=firm.id
        ).count()
        
        with_websites = prod_session.query(Company).join(CompanyPEInvestment).filter(
            CompanyPEInvestment.pe_firm_id == firm.id,
            Company.website.isnot(None),
            Company.website != ''
        ).count()
        
        percentage = (with_websites / total * 100) if total > 0 else 0
        status = "✅" if percentage > 90 else "⚠️" if percentage > 50 else "❌"
        print(f"  {status} {firm.name}: {with_websites}/{total} ({percentage:.1f}%)")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    prod_session.rollback()
    raise
finally:
    local_session.close()
    prod_session.close()
