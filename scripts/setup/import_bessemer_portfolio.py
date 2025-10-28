"""
Import Bessemer Venture Partners portfolio from JSON to database
Updates existing companies with real websites from scraped data
"""
import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.models.database_models_v2 import (
    get_session, PEFirm, Company, CompanyPEInvestment
)

INPUT_FILE = "data/raw/json/bessemer_portfolio.json"


def import_bessemer_portfolio():
    """Import Bessemer portfolio from JSON to database"""
    
    # Load JSON data
    print(f"📂 Loading {INPUT_FILE}...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        companies_data = json.load(f)
    
    print(f"✓ Loaded {len(companies_data)} companies from JSON\n")
    
    session = get_session()
    
    try:
        # Get or create Bessemer PE firm
        pe_firm = session.query(PEFirm).filter_by(name="Bessemer Venture Partners").first()
        if not pe_firm:
            pe_firm = PEFirm(
                name="Bessemer Venture Partners",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(pe_firm)
            session.commit()
            print(f"✅ Created PE firm: Bessemer Venture Partners\n")
        else:
            print(f"✓ Found existing PE firm: Bessemer Venture Partners\n")
        
        # Counters
        added_count = 0
        updated_count = 0
        skipped_count = 0
        websites_added = 0
        
        # Process each company
        for idx, company_data in enumerate(companies_data, 1):
            company_name = company_data.get('name')
            website = company_data.get('website')
            
            if not company_name:
                continue
            
            print(f"{idx}/{len(companies_data)}: {company_name}")
            
            # Find existing company by name
            existing_company = session.query(Company).filter_by(name=company_name).first()
            
            if existing_company:
                # Update existing company
                print(f"   ↻ Updating existing company (ID: {existing_company.id})")
                
                # Always update website if we have one from scraper
                if website:
                    existing_company.website = website
                    websites_added += 1
                    print(f"      → Updated website: {website}")
                
                existing_company.updated_at = datetime.utcnow()
                company = existing_company
                updated_count += 1
            else:
                # Create new company
                print(f"   ✓ Adding new company")
                company = Company(
                    name=company_name,
                    website=website,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                session.add(company)
                session.flush()  # Get the ID
                added_count += 1
                if website:
                    websites_added += 1
            
            # Check if investment relationship exists
            existing_investment = session.query(CompanyPEInvestment).filter_by(
                company_id=company.id,
                pe_firm_id=pe_firm.id
            ).first()
            
            if not existing_investment:
                # Create investment relationship
                # Parse last_scraped if it's a string
                last_scraped_value = company_data.get('last_scraped')
                if isinstance(last_scraped_value, str):
                    last_scraped_value = datetime.fromisoformat(last_scraped_value.replace('Z', '+00:00'))
                
                investment = CompanyPEInvestment(
                    company_id=company.id,
                    pe_firm_id=pe_firm.id,
                    raw_status=company_data.get('raw_status', 'Current'),
                    source_url=company_data.get('source_url'),
                    last_scraped=last_scraped_value,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                # Set computed_status based on raw_status
                if investment.raw_status in ['Current', 'Active']:
                    investment.computed_status = 'Active'
                elif investment.raw_status in ['Exit', 'Exited', 'Acquired', 'IPO']:
                    investment.computed_status = 'Exited'
                else:
                    investment.computed_status = 'Active'  # Default
                
                session.add(investment)
                print(f"   ✓ Created investment relationship")
            else:
                # Update existing investment
                if company_data.get('raw_status'):
                    existing_investment.raw_status = company_data['raw_status']
                if company_data.get('source_url'):
                    existing_investment.source_url = company_data['source_url']
                # Parse last_scraped if it's a string
                if company_data.get('last_scraped'):
                    last_scraped_str = company_data['last_scraped']
                    if isinstance(last_scraped_str, str):
                        existing_investment.last_scraped = datetime.fromisoformat(last_scraped_str.replace('Z', '+00:00'))
                    else:
                        existing_investment.last_scraped = last_scraped_str
                existing_investment.updated_at = datetime.utcnow()
                skipped_count += 1
                print(f"   ↻ Investment relationship already exists")
            
            # Commit after each company
            session.commit()
        
        # Final statistics
        print(f"\n{'='*60}")
        print(f"📊 Import Summary:")
        print(f"   ✅ Added new companies: {added_count}")
        print(f"   ↻  Updated existing: {updated_count}")
        print(f"   ⚠️  Skipped/Failed: {skipped_count}")
        print(f"   📈 Total processed: {len(companies_data)}")
        print(f"{'='*60}")
        
        # Database stats
        total_companies = session.query(Company).count()
        total_bessemer_investments = session.query(CompanyPEInvestment).filter_by(
            pe_firm_id=pe_firm.id
        ).count()
        
        print(f"\n📊 Database Stats:")
        print(f"   Total companies: {total_companies}")
        print(f"   Total Bessemer investments: {total_bessemer_investments}")
        
        # Website statistics
        bessemer_companies_with_websites = session.query(Company).join(
            CompanyPEInvestment
        ).filter(
            CompanyPEInvestment.pe_firm_id == pe_firm.id,
            Company.website.isnot(None),
            ~Company.website.contains('bvp.com')
        ).count()
        
        bessemer_companies_no_website = session.query(Company).join(
            CompanyPEInvestment
        ).filter(
            CompanyPEInvestment.pe_firm_id == pe_firm.id,
            Company.website.is_(None)
        ).count()
        
        print(f"\n📈 Website Status:")
        print(f"   ✅ Real websites: {bessemer_companies_with_websites}")
        print(f"   ❌ No website: {bessemer_companies_no_website}")
        
        success_rate = (bessemer_companies_with_websites / total_bessemer_investments * 100) if total_bessemer_investments > 0 else 0
        print(f"   📊 Success rate: {success_rate:.1f}%")
        
        print(f"\n✨ Import complete!")
        
    except Exception as e:
        print(f"\n❌ Error during import: {str(e)}")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    import_bessemer_portfolio()
