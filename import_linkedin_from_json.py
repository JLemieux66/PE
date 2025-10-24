"""
Import LinkedIn URLs from existing JSON files (a16z_portfolio_enhanced.json)
This will populate linkedin_url field for companies that were already scraped
"""
import json
from database_models import get_session, PortfolioCompany
from sqlalchemy import func


def import_linkedin_from_json(json_file='a16z_portfolio_enhanced.json'):
    """
    Import LinkedIn URLs from existing JSON file
    
    Args:
        json_file: Path to JSON file with company data including linkedin_url
    """
    session = get_session()
    
    try:
        # Load JSON file
        print(f"📂 Loading {json_file}...")
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        companies_data = data.get('companies', [])
        print(f"📊 Found {len(companies_data)} companies in JSON")
        
        updated_count = 0
        skipped_count = 0
        not_found_count = 0
        
        for company_data in companies_data:
            company_name = company_data.get('name')
            linkedin_url = company_data.get('linkedin_url', '').strip()
            
            if not company_name or not linkedin_url:
                continue
            
            # Find company in database by name
            company = session.query(PortfolioCompany).filter(
                PortfolioCompany.name.ilike(company_name)
            ).first()
            
            if company:
                # Check if already has LinkedIn URL
                if company.linkedin_url:
                    skipped_count += 1
                    print(f"  ⏭️  Skipped {company_name} (already has URL)")
                else:
                    # Update with LinkedIn URL
                    company.linkedin_url = linkedin_url
                    updated_count += 1
                    print(f"  ✅ Updated {company_name}")
            else:
                not_found_count += 1
                print(f"  ⚠️  Not found in DB: {company_name}")
        
        # Commit changes
        session.commit()
        
        print("\n" + "=" * 70)
        print("✅ Import completed!")
        print(f"📊 Updated: {updated_count}")
        print(f"⏭️  Skipped (already had URL): {skipped_count}")
        print(f"⚠️  Not found in database: {not_found_count}")
        print("=" * 70)
        
        # Show updated coverage
        total = session.query(func.count(PortfolioCompany.id)).scalar()
        with_linkedin = session.query(func.count(PortfolioCompany.id)).filter(
            (PortfolioCompany.linkedin_url != None) & 
            (PortfolioCompany.linkedin_url != '')
        ).scalar()
        
        coverage = (with_linkedin / total * 100) if total > 0 else 0
        print(f"\n📊 Total LinkedIn URL Coverage: {with_linkedin}/{total} ({coverage:.1f}%)")
        
    except FileNotFoundError:
        print(f"❌ File not found: {json_file}")
    except Exception as e:
        print(f"❌ Error: {e}")
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    import sys
    
    print("\n" + "=" * 70)
    print("📥 Import LinkedIn URLs from JSON")
    print("=" * 70)
    
    json_file = sys.argv[1] if len(sys.argv) > 1 else 'a16z_portfolio_enhanced.json'
    
    import_linkedin_from_json(json_file)
