"""
Clean up non-company entities from the database
Removes entries like [untitled], holding companies, funds, etc.
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker
from src.models.database_models_v2 import Company, CompanyPEInvestment, get_database_url

# Patterns that indicate non-companies
NON_COMPANY_PATTERNS = [
    'A leading infrastructure provider',  # Description text, not company name
    'firm in china',
    'holding company',
    'venture capital',
    'investment group',
    'capital partners',
    'private equity',
    'asset management',
    '[redacted]',
    '[confidential]',
    'n/a',
    'tbd',
    'various',
    'portfolio',
    'group investments',
]

def cleanup_non_companies(dry_run=True):
    """Remove non-company entities from database"""
    
    # Connect to database
    engine = create_engine(get_database_url())
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        print("🔍 Scanning for non-company entities...\n")
        
        # Build query with all patterns
        conditions = []
        for pattern in NON_COMPANY_PATTERNS:
            conditions.append(Company.name.ilike(f'%{pattern}%'))
        
        # Also check for very short names (likely not real companies)
        suspicious_companies = session.query(Company).filter(
            or_(*conditions)
        ).all()
        
        print(f"Found {len(suspicious_companies)} suspicious entries:\n")
        
        if not suspicious_companies:
            print("✅ No suspicious entries found!")
            return
        
        # Group by pattern for reporting
        for company in suspicious_companies:
            # Count investments
            investment_count = session.query(CompanyPEInvestment).filter_by(
                company_id=company.id
            ).count()
            
            matched_pattern = "unknown"
            for pattern in NON_COMPANY_PATTERNS:
                if pattern.lower() in company.name.lower():
                    matched_pattern = pattern
                    break
            
            print(f"  • {company.name}")
            print(f"    ID: {company.id}")
            print(f"    Pattern: {matched_pattern}")
            print(f"    Investments: {investment_count}")
            print(f"    Industry: {company.industry_category or 'N/A'}")
            print()
        
        if dry_run:
            print("\n⚠️  DRY RUN - No changes made")
            print("Run with --execute to delete these entries")
        else:
            print("\n🗑️  Deleting entries...")
            deleted_count = 0
            
            for company in suspicious_companies:
                # Delete investments first (foreign key constraint)
                session.query(CompanyPEInvestment).filter_by(
                    company_id=company.id
                ).delete()
                
                # Delete company
                session.delete(company)
                deleted_count += 1
            
            session.commit()
            print(f"✅ Deleted {deleted_count} suspicious entries")
    
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Clean up non-company entities')
    parser.add_argument('--execute', action='store_true', 
                       help='Actually delete entries (default is dry run)')
    
    args = parser.parse_args()
    
    cleanup_non_companies(dry_run=not args.execute)
