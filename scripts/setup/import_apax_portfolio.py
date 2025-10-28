"""
Import Apax Partners portfolio companies from JSON to database
"""
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.models.database_models_v2 import (
    get_session, PEFirm, Company, CompanyPEInvestment
)

def import_apax_portfolio():
    """Import Apax Partners companies from JSON"""
    
    print("\n" + "="*80)
    print("📥 IMPORTING APAX PARTNERS PORTFOLIO")
    print("="*80 + "\n")
    
    # Load JSON data
    json_file = 'data/raw/json/apax_portfolio.json'
    with open(json_file, 'r', encoding='utf-8') as f:
        companies_data = json.load(f)
    
    print(f"📊 Loaded {len(companies_data)} companies from JSON\n")
    
    session = get_session()
    
    try:
        # Get Apax Partners PE firm
        pe_firm = session.query(PEFirm).filter_by(name='Apax Partners').first()
        
        if not pe_firm:
            print("❌ Apax Partners not found in database!")
            return
        
        print(f"✅ Found PE firm: {pe_firm.name}\n")
        
        # Track statistics
        websites_updated = 0
        websites_skipped = 0
        not_found = 0
        batch_size = 50
        
        for i, company_data in enumerate(companies_data, 1):
            company_name = company_data.get('name')
            website = company_data.get('website')
            
            if not company_name:
                continue
            
            # Find company in database (it should exist from old scraper)
            # Try exact match first, then fuzzy match
            company = session.query(Company).filter(
                Company.name.ilike(company_name)
            ).first()
            
            # If not found, try without special characters
            if not company:
                clean_name = company_name.replace('&', 'and').strip()
                company = session.query(Company).filter(
                    Company.name.ilike(f"%{clean_name}%")
                ).first()
            
            if company:
                # Check if this company is linked to Apax
                investment = session.query(CompanyPEInvestment).filter_by(
                    company_id=company.id,
                    pe_firm_id=pe_firm.id
                ).first()
                
                if investment:
                    # Update website if we have one and it's different
                    if website and company.website != website:
                        old_website = company.website or '(none)'
                        print(f"[{i}] Updated {company_name}: {old_website} → {website}")
                        company.website = website
                        websites_updated += 1
                    else:
                        websites_skipped += 1
                else:
                    # Company exists but not linked to Apax - skip
                    not_found += 1
            else:
                not_found += 1
            
            # Commit in batches
            if i % batch_size == 0:
                session.commit()
                print(f"💾 Saved batch (processed {i}/{len(companies_data)})")
        
        # Final commit
        session.commit()
        
        # Summary
        print("\n" + "="*80)
        print("IMPORT COMPLETE")
        print("="*80 + "\n")
        
        print(f"✅ Websites updated: {websites_updated}")
        print(f"ℹ️  Skipped (no change): {websites_skipped}")
        print(f"ℹ️  Not found in database: {not_found}")
        
        # Check final statistics
        total_investments = session.query(CompanyPEInvestment).filter_by(
            pe_firm_id=pe_firm.id
        ).count()
        
        companies_with_websites = session.query(Company).join(CompanyPEInvestment).filter(
            CompanyPEInvestment.pe_firm_id == pe_firm.id,
            Company.website.isnot(None),
            Company.website != ''
        ).count()
        
        print(f"\n📊 Total Apax Partners companies in database: {total_investments}")
        print(f"🌐 Companies with websites: {companies_with_websites}/{total_investments} ({companies_with_websites/total_investments*100:.1f}%)")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == '__main__':
    import_apax_portfolio()
