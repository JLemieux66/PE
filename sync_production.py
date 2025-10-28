"""
Quick sync script to update production database from JSON files
Run this on Railway with: railway run python sync_production.py
"""
import os
import json
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.database_models_v2 import Company

# Get database URL
database_url = os.getenv('DATABASE_URL')
if not database_url:
    print("❌ ERROR: DATABASE_URL not set")
    exit(1)

# Fix Railway's postgres:// to postgresql://
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

print("\n" + "="*80)
print("🔄 SYNCING JSON FILES TO PRODUCTION DATABASE")
print("="*80 + "\n")

# Connect to database
engine = create_engine(database_url)
Session = sessionmaker(bind=engine)
session = Session()

# JSON files to sync
json_files = [
    'data/raw/json/ta_portfolio_complete.json',
    'data/raw/json/apax_portfolio.json',
    'data/raw/json/advent_portfolio.json',
    'data/raw/json/bessemer_portfolio.json',
    'data/raw/json/a16z_portfolio.json',
]

websites_updated = 0
websites_added = 0
not_found = 0
processed = 0

for json_file in json_files:
    file_path = Path(json_file)
    if not file_path.exists():
        print(f"⚠️  Skipping {json_file} (not found)")
        continue
    
    print(f"📁 Processing {json_file}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        companies_data = json.load(f)
    
    # Deduplicate by name
    seen_names = set()
    unique_companies = []
    for company_data in companies_data:
        name = company_data.get('name')
        if name and name not in seen_names:
            seen_names.add(name)
            unique_companies.append(company_data)
    
    for company_data in unique_companies:
        name = company_data.get('name')
        website = company_data.get('website')
        
        if not name or not website:
            continue
        
        # Find company in database
        company = session.query(Company).filter_by(name=name).first()
        
        if company:
            old_website = company.website
            if old_website != website:
                print(f"   ✏️  {name}: {old_website or '(none)'} → {website}")
                company.website = website
                if old_website:
                    websites_updated += 1
                else:
                    websites_added += 1
        else:
            not_found += 1
        
        processed += 1
        
        # Commit in batches
        if processed % 100 == 0:
            session.commit()
            print(f"   💾 Saved batch ({processed} processed)")

# Final commit
session.commit()

print("\n" + "="*80)
print("✅ SYNC COMPLETE")
print("="*80 + "\n")

print(f"🌐 Websites added: {websites_added}")
print(f"✏️  Websites updated: {websites_updated}")
print(f"ℹ️  Not found in database: {not_found}")
print(f"📊 Total processed: {processed}")

session.close()
