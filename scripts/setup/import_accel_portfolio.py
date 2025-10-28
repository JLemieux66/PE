"""
Import Accel Portfolio to Database
Imports Accel portfolio companies from JSON and creates/updates records
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.models.database_models_v2 import Company, PEFirm, CompanyPEInvestment, get_session


def import_accel_portfolio(input_file: str = "data/raw/json/accel_portfolio.json"):
    """
    Import Accel portfolio companies to database
    
    Args:
        input_file: Path to Accel portfolio JSON
    """
    print("📥 Importing Accel Portfolio to Database")
    print("=" * 60)
    
    # Load data
    with open(input_file, 'r', encoding='utf-8') as f:
        companies_data = json.load(f)
    
    print(f"📂 Loaded {len(companies_data)} companies from {input_file}\n")
    
    # Get database session
    session = get_session()
    
    try:
        # Get or create Accel PE Firm
        accel_firm = session.query(PEFirm).filter_by(name="Accel").first()
        if not accel_firm:
            print("🏢 Creating Accel PE Firm entry...")
            accel_firm = PEFirm(name="Accel")
            session.add(accel_firm)
            session.commit()
            print(f"   ✓ Created Accel (ID: {accel_firm.id})\n")
        else:
            print(f"✓ Found existing Accel PE Firm (ID: {accel_firm.id})\n")
        
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
                    
                    # Always update website if we have one from scraper
                    if company_data.get('website'):
                        existing_company.website = company_data['website']
                        print(f"      → Updated website: {company_data['website']}")
                    
                    if company_data.get('description') and not existing_company.description:
                        existing_company.description = company_data['description']
                    
                    existing_company.updated_at = datetime.utcnow()
                    company = existing_company
                    updated_count += 1
                else:
                    # Create new company
                    print(f"   ✓ Adding new company")
                    
                    company = Company(
                        name=company_name,
                        website=company_data.get('website'),
                        description=company_data.get('description'),
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    session.add(company)
                    session.flush()  # Get the ID
                    added_count += 1
                
                # Create or update investment relationship
                existing_investment = session.query(CompanyPEInvestment).filter_by(
                    company_id=company.id,
                    pe_firm_id=accel_firm.id
                ).first()
                
                if not existing_investment:
                    investment = CompanyPEInvestment(
                        company_id=company.id,
                        pe_firm_id=accel_firm.id,
                        raw_status='Current',
                        computed_status='Active',
                        source_url='https://www.accel.com/relationships'
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
        total_investments = session.query(CompanyPEInvestment).filter_by(pe_firm_id=accel_firm.id).count()
        
        print(f"\n📊 Database Stats:")
        print(f"   Total companies: {total_companies}")
        print(f"   Total Accel investments: {total_investments}")
        
        # Check how many have real websites
        accel_companies = session.query(Company).join(CompanyPEInvestment).filter(
            CompanyPEInvestment.pe_firm_id == accel_firm.id
        ).all()
        
        real_websites = sum(1 for c in accel_companies if c.website and 'accel.com' not in c.website)
        accel_urls = sum(1 for c in accel_companies if c.website and 'accel.com' in c.website)
        no_website = sum(1 for c in accel_companies if not c.website)
        
        print(f"\n📈 Website Status:")
        print(f"   ✅ Real websites: {real_websites}")
        print(f"   ⚠️  Accel.com URLs: {accel_urls}")
        print(f"   ❌ No website: {no_website}")
        
    except Exception as e:
        print(f"\n❌ Critical error: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
        raise
    
    finally:
        session.close()
    
    print("\n✨ Import complete!")


if __name__ == "__main__":
    import sys
    
    input_file = sys.argv[1] if len(sys.argv) > 1 else "data/raw/json/accel_portfolio.json"
    
    import_accel_portfolio(input_file)
