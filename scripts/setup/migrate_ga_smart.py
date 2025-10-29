"""
Smart Migration: Only migrate General Atlantic companies that don't already exist by name
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.database_models_v2 import Base, Company, PEFirm, CompanyPEInvestment
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable must be set")

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

def normalize_status(raw_status):
    """Normalize status from portfolio_companies table"""
    if not raw_status:
        return "Active"
    
    status_lower = raw_status.lower()
    if any(word in status_lower for word in ['active', 'current', 'ongoing']):
        return "Active"
    elif any(word in status_lower for word in ['exit', 'exited', 'sold', 'acquired']):
        return "Exit"
    else:
        return "Active"

def smart_migrate():
    """Only migrate unique General Atlantic companies + create all investment relationships"""
    
    print("=" * 80)
    print("SMART MIGRATION: General Atlantic (Deduplicated)")
    print("=" * 80)
    
    # Get General Atlantic PE firm
    pe_firm = session.query(PEFirm).filter_by(name="General Atlantic").first()
    if not pe_firm:
        print("❌ General Atlantic PE firm not found")
        return
    
    print(f"✅ Found General Atlantic (ID: {pe_firm.id})")
    
    # Get all existing company names in v2 schema
    existing_names = set()
    for company in session.query(Company.name).all():
        existing_names.add(company.name.lower())
    
    print(f"📊 Found {len(existing_names)} existing companies in v2 schema")
    
    # Connect to PostgreSQL
    conn = psycopg2.connect(DATABASE_URL)
    raw_cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get all General Atlantic companies from portfolio_companies table
    raw_cursor.execute("""
        SELECT 
            name, website, description, status,
            country, state_region, city,
            industry_category, revenue_range, employee_count, linkedin_url
        FROM portfolio_companies
        WHERE pe_firm_id = %s
        ORDER BY name
    """, (pe_firm.id,))
    
    portfolio_companies = raw_cursor.fetchall()
    print(f"📦 Found {len(portfolio_companies)} General Atlantic companies\n")
    
    # Separate into new vs existing
    new_companies = []
    existing_companies = []
    
    for row in portfolio_companies:
        if row['name'].lower() in existing_names:
            existing_companies.append(row)
        else:
            new_companies.append(row)
    
    print(f"🆕 New companies (will create):     {len(new_companies)}")
    print(f"🔄 Existing companies (link only):  {len(existing_companies)}")
    print()
    
    companies_created = 0
    investments_created = 0
    investments_existing = 0
    errors = 0
    
    # Process NEW companies (create company + investment)
    print("Creating new companies...")
    for idx, row in enumerate(new_companies, 1):
        try:
            name = row['name']
            website = row['website']
            status = normalize_status(row['status'])
            
            # Create company
            company = Company(
                name=name,
                website=website,
                description=row['description'],
                industry_category=row['industry_category'],
                revenue_range=row['revenue_range'],
                employee_count=row['employee_count'],
                linkedin_url=row['linkedin_url'],
                country=row['country'],
                state_region=row['state_region'],
                city=row['city']
            )
            session.add(company)
            session.flush()
            companies_created += 1
            
            # Create investment
            investment = CompanyPEInvestment(
                company_id=company.id,
                pe_firm_id=pe_firm.id,
                raw_status=row['status'],
                computed_status=status
            )
            session.add(investment)
            investments_created += 1
            
            if idx % 25 == 0:
                session.commit()
                print(f"  ✅ [{idx}/{len(new_companies)}] Created {companies_created} companies, {investments_created} investments")
        
        except Exception as e:
            session.rollback()
            errors += 1
            print(f"  ❌ [{idx}] Error with {row.get('name', 'unknown')}: {str(e)[:80]}")
            continue
    
    # Commit new companies
    try:
        session.commit()
        print(f"  💾 Committed {companies_created} new companies\n")
    except Exception as e:
        session.rollback()
        print(f"  ❌ Commit error: {e}\n")
    
    # Process EXISTING companies (create investment only)
    print("Linking existing companies...")
    for idx, row in enumerate(existing_companies, 1):
        try:
            name = row['name']
            status = normalize_status(row['status'])
            
            # Find existing company
            company = session.query(Company).filter_by(name=name).first()
            if not company:
                print(f"  ⚠️  [{idx}] Company '{name}' not found (should exist)")
                continue
            
            # Check if investment already exists
            existing_inv = session.query(CompanyPEInvestment).filter_by(
                company_id=company.id,
                pe_firm_id=pe_firm.id
            ).first()
            
            if existing_inv:
                investments_existing += 1
                continue
            
            # Create investment
            investment = CompanyPEInvestment(
                company_id=company.id,
                pe_firm_id=pe_firm.id,
                raw_status=row['status'],
                computed_status=status
            )
            session.add(investment)
            investments_created += 1
            
            if idx % 50 == 0:
                session.commit()
                print(f"  ✅ [{idx}/{len(existing_companies)}] Created {investments_created} investment relationships")
        
        except Exception as e:
            session.rollback()
            errors += 1
            print(f"  ❌ [{idx}] Error with {row.get('name', 'unknown')}: {str(e)[:80]}")
            continue
    
    # Final commit
    try:
        session.commit()
        print(f"  💾 Final commit complete\n")
    except Exception as e:
        session.rollback()
        print(f"  ❌ Final commit error: {e}\n")
    
    # Verify
    total = session.query(CompanyPEInvestment).filter_by(pe_firm_id=pe_firm.id).count()
    
    print("=" * 80)
    print("📈 MIGRATION SUMMARY")
    print("=" * 80)
    print(f"🆕 New companies created:           {companies_created}")
    print(f"✅ Investment relationships created: {investments_created}")
    print(f"⏭️  Investment relationships existed: {investments_existing}")
    print(f"❌ Errors:                          {errors}")
    print("=" * 80)
    print(f"\n📊 Total General Atlantic investments in v2 schema: {total}")
    
    # Show sample
    sample = session.query(Company).join(CompanyPEInvestment).filter(
        CompanyPEInvestment.pe_firm_id == pe_firm.id
    ).limit(5).all()
    
    print(f"\n📋 Sample General Atlantic companies:")
    for company in sample:
        print(f"   - {company.name}")
        if company.industry_category:
            print(f"     Industry: {company.industry_category}")
        if company.revenue_range:
            print(f"     Revenue: {company.revenue_range}")
    
    raw_cursor.close()
    conn.close()
    session.close()
    
    print("\n✅ Smart migration complete!")
    return total

if __name__ == "__main__":
    result = smart_migrate()
    print(f"\n🎉 Result: {result} General Atlantic investments in v2 schema")
