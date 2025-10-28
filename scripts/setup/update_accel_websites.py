"""
Update Accel portfolio companies with real websites scraped by accel_scraper.py
Reads from the scraper's saved data and updates the database
"""

import json
import sys
from pathlib import Path
from sqlalchemy.orm import Session

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.models.database_models_v2 import Company, PEFirm, CompanyPEInvestment, get_session


def load_scraped_data():
    """Load the most recent Accel scraper data from the database or create mapping"""
    # Since the scraper saved to old database_models, we need to re-scrape or
    # use the scraper's output. For now, let's run the scraper again to get fresh data
    # but this time save to JSON
    print("⚠️  Need to re-run scraper to get JSON output...")
    print("    The scraper currently saves to old database_models.py")
    print("    We need to update it to save JSON instead")
    return None


def update_accel_websites():
    """Update Accel companies in database with real websites"""
    print("📥 Updating Accel Portfolio Websites in Database")
    print("=" * 60)
    
    # For now, let's just verify what we have
    session = get_session()
    
    try:
        # Get Accel PE Firm
        accel_firm = session.query(PEFirm).filter_by(name="Accel").first()
        if not accel_firm:
            print("❌ Accel PE Firm not found in database")
            return
        
        print(f"✓ Found Accel PE Firm (ID: {accel_firm.id})")
        
        # Get all Accel investments
        investments = session.query(CompanyPEInvestment).filter_by(
            pe_firm_id=accel_firm.id
        ).all()
        
        print(f"📊 Total Accel investments: {len(investments)}")
        
        # Check how many have accel.com websites
        accel_urls = 0
        real_urls = 0
        no_urls = 0
        
        for inv in investments:
            company = inv.company
            if not company.website:
                no_urls += 1
            elif 'accel.com' in company.website:
                accel_urls += 1
            else:
                real_urls += 1
        
        print(f"\n📈 Website Status:")
        print(f"   ✅ Real websites: {real_urls}")
        print(f"   ⚠️  Accel.com URLs: {accel_urls}")
        print(f"   ❌ No website: {no_urls}")
        
        if accel_urls > 0:
            print(f"\n⚠️  {accel_urls} companies still have accel.com URLs")
            print("   Need to re-run scraper with JSON output to update these")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    update_accel_websites()
