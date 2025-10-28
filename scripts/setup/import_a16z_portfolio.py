"""
Import Andreessen Horowitz (a16z) Portfolio to Database
Reads from JSON file and updates database_models_v2
"""
import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.models.database_models_v2 import PEFirm, Company, CompanyPEInvestment, get_session

# Input file
INPUT_FILE = "data/raw/json/a16z_portfolio.json"


def import_a16z_portfolio():
    """Import a16z portfolio from JSON to database"""
    
    print("=" * 80)
    print("IMPORTING ANDREESSEN HOROWITZ (a16z) PORTFOLIO")
    print("=" * 80)
    
    # Load JSON data
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    companies_data = data["companies"]
    print(f"\n📊 Loaded {len(companies_data)} companies from {INPUT_FILE}")
    
    # Connect to database
    session = get_session()
    
    try:
        # Get or create PE firm
        pe_firm = session.query(PEFirm).filter_by(name="Andreessen Horowitz").first()
        
        if not pe_firm:
            print(f"\n✨ Creating PE firm: Andreessen Horowitz")
            pe_firm = PEFirm(
                name="Andreessen Horowitz",
                website="https://a16z.com",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(pe_firm)
            session.commit()
        else:
            print(f"\n✅ Found existing PE firm: {pe_firm.name}")
        
        # Statistics
        companies_added = 0
        companies_updated = 0
        investments_created = 0
        investments_skipped = 0
        websites_added = 0
        linkedin_added = 0
        
        # Process each company
        for i, company_data in enumerate(companies_data, 1):
            company_name = company_data["name"]
            website = company_data.get("website", "").strip()
            linkedin_url = company_data.get("linkedin_url", "").strip()
            sector = company_data.get("sector", "")
            status = company_data.get("status", "Active")
            stage = company_data.get("stage", "")
            exit_details = company_data.get("exit_details", "")
            
            print(f"\n[{i}/{len(companies_data)}] Processing: {company_name}")
            
            # Check if company exists
            existing_company = session.query(Company).filter_by(name=company_name).first()
            
            if existing_company:
                print(f"  ✅ Found existing company (ID: {existing_company.id})")
                
                # Always update website if we have one
                if website:
                    existing_company.website = website
                    websites_added += 1
                    print(f"    📝 Updated website: {website}")
                
                # Update LinkedIn if we have one
                if linkedin_url and not existing_company.linkedin_url:
                    existing_company.linkedin_url = linkedin_url
                    linkedin_added += 1
                    print(f"    📝 Updated LinkedIn: {linkedin_url}")
                
                existing_company.updated_at = datetime.utcnow()
                companies_updated += 1
                company = existing_company
                
            else:
                print(f"  ✨ Creating new company")
                company = Company(
                    name=company_name,
                    website=website,
                    linkedin_url=linkedin_url,
                    industry=sector if sector else None,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                session.add(company)
                session.flush()  # Get the ID
                companies_added += 1
                
                if website:
                    websites_added += 1
                    print(f"    📝 Website: {website}")
                if linkedin_url:
                    linkedin_added += 1
                    print(f"    📝 LinkedIn: {linkedin_url}")
            
            # Check if investment relationship exists
            existing_investment = session.query(CompanyPEInvestment).filter_by(
                company_id=company.id,
                pe_firm_id=pe_firm.id
            ).first()
            
            if not existing_investment:
                # Determine status
                investment_status = "Exit" if status == "Exit" else "Active"
                
                investment = CompanyPEInvestment(
                    company_id=company.id,
                    pe_firm_id=pe_firm.id,
                    investment_date=None,
                    exit_date=None,
                    status=investment_status,
                    notes=exit_details if exit_details else None,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                session.add(investment)
                investments_created += 1
                print(f"    ✅ Created investment relationship ({investment_status})")
            else:
                investments_skipped += 1
                print(f"    ⏭️  Investment relationship already exists")
            
            # Commit every 10 companies
            if i % 10 == 0:
                session.commit()
                print(f"\n💾 Committed batch {i//10} (companies 1-{i})")
        
        # Final commit
        session.commit()
        print("\n" + "=" * 80)
        print("IMPORT SUMMARY")
        print("=" * 80)
        print(f"Companies added (new): {companies_added}")
        print(f"Companies updated (existing): {companies_updated}")
        print(f"Investments created: {investments_created}")
        print(f"Investments skipped (already exist): {investments_skipped}")
        print(f"Total companies processed: {len(companies_data)}")
        print(f"\nWebsite Status:")
        print(f"  Real websites added: {websites_added}")
        print(f"  LinkedIn URLs added: {linkedin_added}")
        print(f"  Companies without website: {len(companies_data) - websites_added}")
        
        # Get total counts
        total_companies = session.query(Company).count()
        total_a16z_investments = session.query(CompanyPEInvestment).filter_by(
            pe_firm_id=pe_firm.id
        ).count()
        
        print(f"\nDatabase Totals:")
        print(f"  Total companies in database: {total_companies}")
        print(f"  Total a16z investments: {total_a16z_investments}")
        
        print("\n✅ Import completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during import: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    import_a16z_portfolio()
