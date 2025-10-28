"""
Import Advent International portfolio from JSON to database
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import json
from src.models.database_models_v2 import (
    get_session, PEFirm, Company, CompanyPEInvestment
)
from src.utils.logger import log_info, log_success, log_error, log_header, log_warning

# Industry mapping for Advent sectors
INDUSTRY_MAPPING = {
    # Technology
    'technology': 'Technology & Software',
    'software': 'Technology & Software',
    'it services': 'Technology & Software',
    'digital': 'Technology & Software',
    
    # AI & Data
    'ai': 'Artificial Intelligence & Data',
    'artificial intelligence': 'Artificial Intelligence & Data',
    'data': 'Artificial Intelligence & Data',
    'analytics': 'Artificial Intelligence & Data',
    
    # Healthcare
    'healthcare': 'Healthcare & Life Sciences',
    'health': 'Healthcare & Life Sciences',
    'life sciences': 'Healthcare & Life Sciences',
    'pharmaceuticals': 'Healthcare & Life Sciences',
    'medical': 'Healthcare & Life Sciences',
    'biotech': 'Healthcare & Life Sciences',
    
    # Financial Services
    'financial services': 'Financial Services & Fintech',
    'fintech': 'Financial Services & Fintech',
    'banking': 'Financial Services & Fintech',
    'insurance': 'Financial Services & Fintech',
    'payments': 'Financial Services & Fintech',
    
    # Consumer & Retail
    'consumer': 'Consumer & Retail',
    'retail': 'Consumer & Retail',
    'e-commerce': 'Consumer & Retail',
    'ecommerce': 'Consumer & Retail',
    'food': 'Consumer & Retail',
    'beverage': 'Consumer & Retail',
    'restaurants': 'Consumer & Retail',
    
    # Business Services
    'business services': 'Business Services',
    'professional services': 'Business Services',
    'consulting': 'Business Services',
    
    # Industrial
    'industrial': 'Industrial & Manufacturing',
    'manufacturing': 'Industrial & Manufacturing',
    'chemicals': 'Industrial & Manufacturing',
    
    # Energy
    'energy': 'Energy & Utilities',
    'utilities': 'Energy & Utilities',
    'oil': 'Energy & Utilities',
    'gas': 'Energy & Utilities',
    
    # Media & Entertainment
    'media': 'Media & Entertainment',
    'entertainment': 'Media & Entertainment',
    'gaming': 'Media & Entertainment',
    
    # Education
    'education': 'Education',
    
    # Real Estate
    'real estate': 'Real Estate & Construction',
    'construction': 'Real Estate & Construction',
    
    # Transportation
    'transportation': 'Transportation & Logistics',
    'logistics': 'Transportation & Logistics',
}


def map_sectors_to_industry(sectors):
    """Map Advent sectors to normalized industry category"""
    if not sectors:
        return None
    
    # Try to find best match
    for sector in sectors:
        sector_lower = sector.lower()
        for key, category in INDUSTRY_MAPPING.items():
            if key in sector_lower:
                return category
    
    # Default to first sector if no match
    return None


def import_advent_portfolio():
    """Import Advent International portfolio from JSON"""
    json_file = Path("data/raw/json/advent_portfolio.json")
    
    if not json_file.exists():
        log_error(f"❌ JSON file not found: {json_file}")
        return
    
    log_header("IMPORTING ADVENT INTERNATIONAL PORTFOLIO")
    
    # Load JSON data
    with open(json_file, 'r', encoding='utf-8') as f:
        companies_data = json.load(f)
    
    log_info(f"📊 Loaded {len(companies_data)} companies from JSON")
    
    session = get_session()
    
    try:
        # Get or create PE firm
        pe_firm = session.query(PEFirm).filter_by(name='Advent International').first()
        if not pe_firm:
            log_info("Creating new PE firm: Advent International")
            pe_firm = PEFirm(
                name='Advent International',
                website='https://www.adventinternational.com',
                description='Global private equity firm'
            )
            session.add(pe_firm)
            session.commit()
            log_success("✅ Created PE firm")
        else:
            log_info(f"✅ Found existing PE firm: {pe_firm.name}")
        
        # Import companies
        new_companies = 0
        updated_companies = 0
        skipped_companies = 0
        
        for idx, company_data in enumerate(companies_data, 1):
            try:
                company_name = company_data.get('name')
                if not company_name:
                    log_warning(f"[{idx}] Skipping company with no name")
                    skipped_companies += 1
                    continue
                
                # Check if company exists
                company = session.query(Company).filter_by(name=company_name).first()
                
                # Map sectors to industry
                sectors = company_data.get('sectors')
                industry_category = map_sectors_to_industry(sectors)
                
                if company:
                    # Update existing company - ALWAYS update website if we have one
                    if company_data.get('website'):
                        company.website = company_data['website']
                        log_info(f"[{idx}] Updated website for {company_name}")
                    
                    if company_data.get('description') and not company.description:
                        company.description = company_data['description']
                    
                    if industry_category and not company.industry_category:
                        company.industry_category = industry_category
                    
                    updated_companies += 1
                else:
                    # Create new company
                    company = Company(
                        name=company_name,
                        website=company_data.get('website'),
                        description=company_data.get('description'),
                        industry_category=industry_category
                    )
                    session.add(company)
                    session.flush()  # Get the company ID
                    new_companies += 1
                    log_success(f"[{idx}] ✅ Created: {company_name}")
                
                # Check if investment relationship exists
                investment = session.query(CompanyPEInvestment).filter_by(
                    company_id=company.id,
                    pe_firm_id=pe_firm.id
                ).first()
                
                if not investment:
                    # Create investment relationship
                    investment = CompanyPEInvestment(
                        company_id=company.id,
                        pe_firm_id=pe_firm.id,
                        is_current=True  # Assume current unless specified
                    )
                    session.add(investment)
                
                # Commit every 50 companies
                if idx % 50 == 0:
                    session.commit()
                    log_info(f"💾 Saved batch (processed {idx}/{len(companies_data)})")
                
            except Exception as e:
                log_error(f"[{idx}] ✗ Error importing {company_data.get('name', 'unknown')}: {str(e)}")
                session.rollback()
                skipped_companies += 1
                continue
        
        # Final commit
        session.commit()
        
        # Summary
        log_header("IMPORT COMPLETE")
        log_success(f"✅ New companies created: {new_companies}")
        log_success(f"✅ Existing companies updated: {updated_companies}")
        if skipped_companies > 0:
            log_warning(f"⚠️  Companies skipped: {skipped_companies}")
        
        # Verify
        total_advent_companies = session.query(CompanyPEInvestment).filter_by(
            pe_firm_id=pe_firm.id
        ).count()
        log_info(f"\n📊 Total Advent International companies in database: {total_advent_companies}")
        
        # Check website coverage
        companies_with_websites = session.query(Company).join(CompanyPEInvestment).filter(
            CompanyPEInvestment.pe_firm_id == pe_firm.id,
            Company.website.isnot(None),
            Company.website != ''
        ).count()
        
        website_percentage = (companies_with_websites / total_advent_companies * 100) if total_advent_companies > 0 else 0
        log_info(f"🌐 Companies with websites: {companies_with_websites}/{total_advent_companies} ({website_percentage:.1f}%)")
        
    except Exception as e:
        log_error(f"❌ Import failed: {str(e)}")
        session.rollback()
        import traceback
        traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    import_advent_portfolio()
