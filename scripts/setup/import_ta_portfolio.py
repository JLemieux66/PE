"""
Import TA Associates portfolio from JSON to update database with correct websites
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import json
from src.models.database_models_v2 import (
    get_session, PEFirm, Company, CompanyPEInvestment
)
from src.utils.logger import log_info, log_success, log_error, log_header, log_warning


def import_ta_portfolio():
    """Import TA Associates portfolio from JSON"""
    json_file = Path("ta_portfolio_complete.json")
    
    if not json_file.exists():
        log_error(f"❌ JSON file not found: {json_file}")
        return
    
    log_header("IMPORTING TA ASSOCIATES PORTFOLIO")
    
    # Load JSON data
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    companies_data = data.get('companies', [])
    log_info(f"📊 Loaded {len(companies_data)} companies from JSON")
    
    # Remove duplicates by keeping first occurrence of each company name
    seen_names = set()
    unique_companies = []
    duplicates_removed = 0
    
    for company in companies_data:
        name = company.get('name')
        if name and name not in seen_names:
            seen_names.add(name)
            unique_companies.append(company)
        else:
            duplicates_removed += 1
    
    log_info(f"📊 After removing duplicates: {len(unique_companies)} unique companies")
    log_info(f"🗑️  Duplicates removed: {duplicates_removed}")
    
    companies_data = unique_companies
    
    session = get_session()
    
    try:
        # Get PE firm
        pe_firm = session.query(PEFirm).filter_by(name='TA Associates').first()
        if not pe_firm:
            log_error("❌ TA Associates PE firm not found in database")
            return
        
        log_info(f"✅ Found PE firm: {pe_firm.name}")
        
        # Import companies
        updated_websites = 0
        skipped_no_website = 0
        not_found = 0
        
        for idx, company_data in enumerate(companies_data, 1):
            try:
                company_name = company_data.get('name')
                website = company_data.get('website')
                
                if not company_name:
                    continue
                
                # Check if company exists
                company = session.query(Company).filter_by(name=company_name).first()
                
                if not company:
                    # Company might not be in database (could be exited)
                    not_found += 1
                    continue
                
                # Update website if we have one
                if website:
                    old_website = company.website
                    company.website = website
                    
                    # Only log if we actually changed something
                    if old_website != website:
                        updated_websites += 1
                        if idx <= 10:  # Show first 10
                            log_info(f"[{idx}] Updated {company_name}: {old_website} → {website}")
                else:
                    skipped_no_website += 1
                
                # Commit every 50 companies
                if idx % 50 == 0:
                    session.commit()
                    log_info(f"💾 Saved batch (processed {idx}/{len(companies_data)})")
                
            except Exception as e:
                log_error(f"[{idx}] ✗ Error importing {company_data.get('name', 'unknown')}: {str(e)}")
                session.rollback()
                continue
        
        # Final commit
        session.commit()
        
        # Summary
        log_header("IMPORT COMPLETE")
        log_success(f"✅ Websites updated: {updated_websites}")
        log_info(f"ℹ️  Skipped (no website in JSON): {skipped_no_website}")
        log_info(f"ℹ️  Not found in database: {not_found}")
        
        # Verify
        total_ta_companies = session.query(CompanyPEInvestment).filter_by(
            pe_firm_id=pe_firm.id
        ).count()
        log_info(f"\n📊 Total TA Associates companies in database: {total_ta_companies}")
        
        # Check website coverage
        companies_with_websites = session.query(Company).join(CompanyPEInvestment).filter(
            CompanyPEInvestment.pe_firm_id == pe_firm.id,
            Company.website.isnot(None),
            Company.website != ''
        ).count()
        
        website_percentage = (companies_with_websites / total_ta_companies * 100) if total_ta_companies > 0 else 0
        log_success(f"🌐 Companies with websites: {companies_with_websites}/{total_ta_companies} ({website_percentage:.1f}%)")
        
    except Exception as e:
        log_error(f"❌ Import failed: {str(e)}")
        session.rollback()
        import traceback
        traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    import_ta_portfolio()
