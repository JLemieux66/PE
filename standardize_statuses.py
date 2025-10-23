"""
Standardize company statuses across all PE firms
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_models import PortfolioCompany, Base
import re

# Database setup
DATABASE_URL = "sqlite:///pe_portfolio.db"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Status mapping rules
STATUS_MAPPING = {
    # Active variations
    "current": "Active",
    "active": "Active",
    
    # Exit variations
    "former": "Exit",
    "past": "Exit",
    "exit": "Exit",
    
    # Unknown/Other
    "unknown": "Unknown",
}

def standardize_status(status):
    """Standardize a status value"""
    if not status:
        return "Unknown"
    
    # Convert to lowercase for matching
    status_lower = status.lower().strip()
    
    # Check if it contains acquisition info (e.g., "past | acquired by...")
    if "acquired" in status_lower or "acquisition" in status_lower:
        # Extract acquisition info for the acquired_by field
        # Pattern: "past | acquired by X" or similar
        match = re.search(r'acquired by (.+)', status_lower)
        if match:
            acquirer = match.group(1).strip()
            return "Exit", acquirer
        return "Exit", "acquired"
    
    # Standard mapping
    for key, standardized in STATUS_MAPPING.items():
        if key in status_lower:
            return standardized, None
    
    # If no match, keep original but capitalize
    return status.capitalize(), None

print("=" * 80)
print("STANDARDIZING COMPANY STATUSES")
print("=" * 80)

# Get all companies
companies = session.query(PortfolioCompany).all()
print(f"\nTotal companies: {len(companies)}")

# Track changes
changes = []
status_counts_before = {}
status_counts_after = {}
acquired_companies = []

# First pass: count before
for company in companies:
    status = company.status or "Unknown"
    status_counts_before[status] = status_counts_before.get(status, 0) + 1

# Second pass: standardize
for company in companies:
    old_status = company.status or "Unknown"
    new_status, acquirer = standardize_status(old_status)
    
    if old_status != new_status:
        changes.append({
            "name": company.name,
            "pe_firm": company.pe_firm.name if company.pe_firm else "Unknown",
            "old": old_status,
            "new": new_status
        })
        company.status = new_status
        
        # If acquired, mark it in the company record
        if acquirer:
            acquired_companies.append({
                "name": company.name,
                "acquirer": acquirer
            })
            # We could add an acquired_by field, but for now just mark as Exit
            # and note it was acquired
            if not company.is_acquired:
                company.is_acquired = True

# Count after
for company in companies:
    status = company.status or "Unknown"
    status_counts_after[status] = status_counts_after.get(status, 0) + 1

print("\n" + "=" * 80)
print("STATUS DISTRIBUTION BEFORE")
print("=" * 80)
for status, count in sorted(status_counts_before.items(), key=lambda x: x[1], reverse=True):
    print(f"  {status:50} {count:5} companies")

print("\n" + "=" * 80)
print("STATUS DISTRIBUTION AFTER")
print("=" * 80)
for status, count in sorted(status_counts_after.items(), key=lambda x: x[1], reverse=True):
    print(f"  {status:50} {count:5} companies")

print("\n" + "=" * 80)
print(f"CHANGES MADE: {len(changes)}")
print("=" * 80)

if changes:
    print("\nSample changes (first 10):")
    for change in changes[:10]:
        print(f"  {change['name']:30} ({change['pe_firm']:20}) {change['old']:30} → {change['new']}")

if acquired_companies:
    print(f"\n" + "=" * 80)
    print(f"ACQUIRED COMPANIES: {len(acquired_companies)}")
    print("=" * 80)
    for company in acquired_companies:
        print(f"  {company['name']:40} acquired by {company['acquirer']}")

# Commit changes
print("\n" + "=" * 80)
print("Committing changes to database...")
session.commit()
print("✅ Changes committed successfully!")
print("=" * 80)

session.close()
