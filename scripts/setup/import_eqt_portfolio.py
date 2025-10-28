"""
Import EQT Portfolio to Database
Imports enriched EQT portfolio companies and creates investment relationships
"""

import json
import sys
from pathlib import Path
from sqlalchemy.orm import Session
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.models.database_models_v2 import Company, PEFirm, CompanyPEInvestment, get_session

def import_eqt_portfolio(input_file: str = "data/raw/json/eqt_portfolio_enriched.json"):
    """
    Import EQT portfolio companies to database
    
    Args:
        input_file: Path to enriched portfolio JSON
    """
    print("📥 Importing EQT Portfolio to Database")
    print("=" * 60)
    
    # Load enriched data
    with open(input_file, 'r', encoding='utf-8') as f:
        companies_data = json.load(f)
    
    print(f"📂 Loaded {len(companies_data)} companies from {input_file}\n")
    
    # Get database session
    session = get_session()
    
    try:
        # Get or create EQT PE Firm
        eqt_firm = session.query(PEFirm).filter_by(name="EQT").first()
        if not eqt_firm:
            print("🏢 Creating EQT PE Firm entry...")
            eqt_firm = PEFirm(name="EQT")
            session.add(eqt_firm)
            session.commit()
            print(f"   ✓ Created EQT (ID: {eqt_firm.id})\n")
        else:
            print(f"✓ Found existing EQT PE Firm (ID: {eqt_firm.id})\n")
        
        # Import companies
        added_count = 0
        updated_count = 0
        skipped_count = 0
        
        for i, company_data in enumerate(companies_data, 1):
            company_name = company_data['name']
            print(f"{i}/{len(companies_data)}: {company_name}")
            
            try:
                # Check if company already exists
                existing_company = session.query(Company).filter_by(name=company_name).first()
                
                if existing_company:
                    # Update existing company with new data
                    print(f"   ↻ Updating existing company (ID: {existing_company.id})")
                    
                    # Update fields if we have new data
                    if company_data.get('website') and not existing_company.website:
                        existing_company.website = company_data['website']
                    if company_data.get('linkedin_url') and not existing_company.linkedin_url:
                        existing_company.linkedin_url = company_data['linkedin_url']
                    if company_data.get('description') and not existing_company.description:
                        existing_company.description = company_data['description']
                    if company_data.get('industry') and not existing_company.industry_category:
                        existing_company.industry_category = company_data['industry']
                    if company_data.get('country') and not existing_company.country:
                        existing_company.country = company_data['country']
                    if company_data.get('revenue_range') and not existing_company.revenue_range:
                        existing_company.revenue_range = company_data['revenue_range']
                    if company_data.get('employee_count') and not existing_company.employee_count:
                        existing_company.employee_count = company_data['employee_count']
                    
                    company = existing_company
                    updated_count += 1
                else:
                    # Create new company
                    print(f"   ✓ Adding new company")
                    
                    # Parse investment year
                    investment_year = None
                    if company_data.get('investment_year') and company_data['investment_year'] != '-':
                        try:
                            investment_year = int(company_data['investment_year'])
                        except:
                            pass
                    
                    company = Company(
                        name=company_name,
                        website=company_data.get('website'),
                        linkedin_url=company_data.get('linkedin_url'),
                        description=company_data.get('description'),
                        industry_category=company_data.get('industry'),
                        country=company_data.get('country'),
                        revenue_range=company_data.get('revenue_range'),
                        employee_count=company_data.get('employee_count'),
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    session.add(company)
                    session.flush()  # Get the ID
                    added_count += 1
                
                # Create or update investment relationship
                existing_investment = session.query(CompanyPEInvestment).filter_by(
                    company_id=company.id,
                    pe_firm_id=eqt_firm.id
                ).first()
                
                if not existing_investment:
                    # Parse investment year
                    investment_year = None
                    if company_data.get('investment_year') and company_data['investment_year'] != '-':
                        try:
                            investment_year = int(company_data['investment_year'])
                        except:
                            pass
                    
                    investment = CompanyPEInvestment(
                        company_id=company.id,
                        pe_firm_id=eqt_firm.id,
                        investment_year=str(investment_year) if investment_year else None,
                        raw_status='Current',
                        computed_status='Active',
                        source_url='https://eqtgroup.com/current-portfolio/'
                    )
                    session.add(investment)
                    print(f"   ✓ Created investment relationship")
                
                # Commit after each company
                session.commit()
                
            except Exception as e:
                print(f"   ❌ Error: {str(e)[:100]}")
                session.rollback()
                skipped_count += 1
                continue
        
        print(f"\n📊 Import Summary:")
        print(f"   ✅ Added new companies: {added_count}")
        print(f"   ↻  Updated existing: {updated_count}")
        print(f"   ⚠️  Skipped/Failed: {skipped_count}")
        print(f"   📈 Total processed: {len(companies_data)}")
        
        # Show some stats
        total_companies = session.query(Company).count()
        total_investments = session.query(CompanyPEInvestment).filter_by(pe_firm_id=eqt_firm.id).count()
        
        print(f"\n📊 Database Stats:")
        print(f"   Total companies: {total_companies}")
        print(f"   Total EQT investments: {total_investments}")
        
        # Show sample of imported companies
        print(f"\n📋 Sample imported companies:")
        recent_companies = session.query(Company).filter(
            Company.name.in_([c['name'] for c in companies_data[:5]])
        ).all()
        
        for company in recent_companies:
            print(f"   • {company.name}")
            if company.website:
                print(f"     🌐 {company.website}")
            if company.linkedin_url:
                print(f"     🔗 {company.linkedin_url}")
            if company.industry_category:
                print(f"     🏭 {company.industry_category}")
        
    except Exception as e:
        print(f"\n❌ Critical error: {e}")
        session.rollback()
        raise
    
    finally:
        session.close()
    
    print("\n✨ Import complete!")

if __name__ == "__main__":
    import sys
    
    input_file = sys.argv[1] if len(sys.argv) > 1 else "data/raw/json/eqt_portfolio_enriched.json"
    
    import_eqt_portfolio(input_file)
