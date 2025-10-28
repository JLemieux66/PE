"""
Reorganize project structure
Moves files from flat root directory to organized folder structure
"""
import os
import shutil
from pathlib import Path

# Base directory
BASE_DIR = Path(r"c:\Users\josep\documentation-helper")

# Define the new structure and file mappings
REORGANIZATION = {
    # Source code
    "src/scrapers": [
        "accel_scraper_v2.py",  # rename to accel_scraper.py
        "ta_complete_scraper.py",  # rename to ta_scraper.py
        "vista_table_scraper.py",  # rename to vista_scraper.py
    ],
    "src/scrapers/a16z": [
        "a16z_scraper_enhanced.py",  # Keep the latest, rename to a16z_scraper.py
    ],
    "src/enrichment": [
        "enrich_pipeline.py",
        "crunchbase_helpers.py",
        "ai_classify_industries.py",
    ],
    "src/models": [
        "database_models.py",
    ],
    "src/utils": [
        "logger.py",
        "consts.py",
    ],
    "src/config": [
        "pe_firms_config.py",
    ],
    
    # Scripts
    "scripts/migrations": [
        "migrate_recreate_database.py",
        "migrate_remove_investors.py",
        "migrate_cleanup_fields.py",
        "migrate_add_industry_category.py",
        "migrate_add_investments.py",
        "migrate_add_linkedin_url.py",
        "migrate_add_organization_fields.py",
        "migrate_add_revenue_columns.py",
        "migrate_create_tags_table.py",
        "migrate_railway_db.py",
    ],
    "scripts/analysis": [
        "analyze_database.py",
        "analyze_industry_coverage.py",
        "analyze_locations.py",
        "analyze_missing_industries.py",
        "check_database.py",
        "check_other_category.py",
        "check_unknown_status.py",
        "CLEANUP_SUMMARY.py",
    ],
    "scripts/setup": [
        "setup_database_interactive.py",
        "setup_initial_tags.py",
        "setup_pe_index.py",
        "setup_endpoints.py",
    ],
    "scripts/testing": [
        "test_api.py",
        "test_api_filters.py",
        "test_crunchbase.py",
        "test_crunchbase_endpoints.py",
        "test_crunchbase_fields.py",
        "test_crunchbase_param.py",
        "test_industry_enrichment.py",
        "test_missing_categories.py",
        "test_rate_limits.py",
        "test_revenue.py",
        "test_swarm_api.py",
        "test_swarm_enrichment.py",
        "test_swarm_search.py",
        "test_tavily_crawl.py",
        "test_vista_page.py",
        "debug_a16z_scraper.py",
        "debug_crunchbase_categories.py",
        "debug_fiverr.py",
        "debug_portfolio_page.py",
        "debug_vista_data.py",
        "check_a16z_data.py",
        "check_portfolio_content.py",
        "check_portfolio_page.py",
        "check_saved_industries.py",
        "check_ta_company_page.py",
        "check_ta_portfolio.py",
        "inspect_structure.py",
        "inspect_ta_sector.py",
        "inspect_ta_structure.py",
        "inspect_vista_modal.py",
    ],
    
    # Data
    "data/raw/json": [
        "a16z_portfolio.json",
        "a16z_portfolio_complete.json",
        "a16z_portfolio_enhanced.json",
        "a16z_portfolio_full_enriched.json",
        "ta_portfolio.json",
        "ta_portfolio_complete.json",
        "ta_portfolio_full_enriched.json",
        "vista_companies_from_websites.json",
        "vista_complete_details.json",
        "vista_complete_details_final.json",
        "vista_complete_final.json",
        "vista_portfolio_cleaned.json",
        "vista_portfolio_detailed_from_pinecone.json",
        "vista_portfolio_detailed_sample.json",
        "vista_portfolio_enhanced.json",
        "vista_portfolio_final.json",
        "vista_portfolio_full_enriched.json",
        "vista_portfolio_playwright.json",
        "vista_portfolio_with_status.json",
        "portfolio_companies_output.json",
        "portfolio_companies_output_v2.json",
        "portfolio_companies_output_v3_aggressive.json",
    ],
    "data/raw/csv": [
        "vista_companies_from_websites.csv",
        "vista_complete_details.csv",
        "vista_portfolio_companies.csv",
        "vista_portfolio_detailed.csv",
    ],
    "data/backups": [
        "pe_portfolio_backup_20251025_140103.db",
        "pe_portfolio_backup_20251025_140231.db",
    ],
    
    # Documentation
    "docs": [
        "API_DEPLOYMENT.md",
        "API_EXAMPLES.md",
        "COMPLETE_SYSTEM_GUIDE.md",
        "DATABASE_SETUP.md",
        "DASHBOARD_FEATURES.md",
        "DEPLOYMENT_READY.md",
        "EXTRACTION_IMPROVEMENTS.md",
        "FINAL_SOLUTION_SUMMARY.md",
        "FINAL_SUMMARY.md",
        "PLAYWRIGHT_SOLUTION_COMPLETE.md",
        "README_API.md",
        "README_PE_PORTFOLIO.md",
        "REVENUE_ENHANCEMENT.md",
        "SOLUTION_JAVASCRIPT_PROBLEM.md",
        "SUCCESS_FINAL_RESULTS.md",
        "SUMMARY_FOR_USER.md",
        "PROJECT_REORGANIZATION_PLAN.md",
    ],
    
    # Frontend
    "frontend": [
        "portfolio_app.py",
        "portfolio_app_improved.py",
    ],
    
    # Archive - old scrapers
    ".archive/old_scrapers": [
        "a16z_scraper.py",
        "a16z_crunchbase_scraper.py",
        "a16z_swarm_scraper.py",
        "accel_scraper.py",  # v1
        "ta_scraper.py",
        "playwright_scraper.py",
        "playwright_scraper_enhanced.py",
        "playwright_scraper_enhanced_details.py",
        "playwright_scraper_final.py",
        "playwright_full_solution.py",
        "playwright_company_website_scraper.py",
        "playwright_network_inspector.py",
        "playwright_vista_complete.py",
        "playwright_vista_final.py",
        "playwright_vista_pages.py",
        "parse_vista_portfolio.py",
        "linkedin_spider.py",
    ],
    ".archive/old_enrichment": [
        "enrich_vista.py",
        "enrich_ta.py",
        "enrich_with_swarm.py",
        "find_linkedin_urls.py",
        "find_linkedin_urls_direct.py",
        "find_linkedin_urls_firecrawl.py",
        "find_linkedin_urls_serper.py",
        "add_revenue_data.py",
        "swarm_investment_harvester.py",
    ],
    ".archive/old_scripts": [
        "ingestion.py",
        "ingestion_pe_portfolio.py",
        "ingestion_pe_portfolio_test.py",
        "import_linkedin_from_json.py",
        "import_to_database.py",
        "populate_categorization_fields.py",
        "populate_geographic_fields.py",
        "query_database.py",
        "query_portfolio_companies.py",
        "query_portfolio_companies_v2.py",
        "query_portfolio_companies_v3_aggressive.py",
        "standardize_industries.py",
        "standardize_statuses.py",
        "update_unknown_to_active.py",
        "verify_enrichment.py",
        "verify_statuses.py",
        "find_all_companies.py",
        "clean_company_names.py",
        "clear_index.py",
        "clear_swarm_investors.py",
        "extract_company_details_from_pinecone.py",
        "sample_index.py",
    ],
    ".archive/old_data": [
        "a16z_portfolio_snapshot.html",
        "ta_portfolio_snapshot.html",
        "accel_page_screenshot.png",
        "accel_page_source.html",
        "vista_portfolio_playwright_raw.txt",
        "pe_crawl_summary_test.json",
    ],
}

# Files to delete (can be regenerated or are empty)
FILES_TO_DELETE = [
    # "nul",  # Skip - Windows reserved name
]

# Renames during move
RENAMES = {
    "accel_scraper_v2.py": "accel_scraper.py",
    "ta_complete_scraper.py": "ta_scraper.py",
    "vista_table_scraper.py": "vista_scraper.py",
    "a16z_scraper_enhanced.py": "a16z_scraper.py",
    "ai_classify_industries.py": "ai_classifier.py",
}

def create_init_files(directory):
    """Create __init__.py in Python package directories"""
    init_file = directory / "__init__.py"
    if not init_file.exists():
        init_file.write_text("# Auto-generated __init__.py\n")
        print(f"   ✅ Created {init_file.relative_to(BASE_DIR)}")

def move_file(src_file, dest_dir, rename=None):
    """Move a file to destination directory"""
    src_path = BASE_DIR / src_file
    
    if not src_path.exists():
        print(f"   ⚠️  Skip: {src_file} (not found)")
        return False
    
    # Create destination directory
    dest_path = BASE_DIR / dest_dir
    dest_path.mkdir(parents=True, exist_ok=True)
    
    # Determine final filename
    final_name = rename if rename else src_path.name
    dest_file = dest_path / final_name
    
    # Move file
    shutil.move(str(src_path), str(dest_file))
    print(f"   ✅ {src_file} → {dest_dir}/{final_name}")
    return True

def reorganize_project():
    """Execute the reorganization"""
    print("=" * 80)
    print("PROJECT REORGANIZATION")
    print("=" * 80)
    print(f"\nBase directory: {BASE_DIR}\n")
    
    moved_count = 0
    skipped_count = 0
    
    # 1. Delete unnecessary files
    if FILES_TO_DELETE:
        print("\n📋 DELETING UNNECESSARY FILES")
        print("-" * 80)
        for file in FILES_TO_DELETE:
            file_path = BASE_DIR / file
            if file_path.exists():
                file_path.unlink()
                print(f"   ✅ Deleted: {file}")
            else:
                print(f"   ⚠️  Not found: {file}")
    
    # 2. Move files to new structure
    for dest_dir, files in REORGANIZATION.items():
        print(f"\n📁 {dest_dir.upper()}")
        print("-" * 80)
        
        for file in files:
            rename = RENAMES.get(file)
            if move_file(file, dest_dir, rename):
                moved_count += 1
            else:
                skipped_count += 1
    
    # 3. Create __init__.py files in src/ directories
    print("\n📋 CREATING __init__.py FILES")
    print("-" * 80)
    python_dirs = [
        "src",
        "src/scrapers",
        "src/scrapers/a16z",
        "src/enrichment",
        "src/models",
        "src/utils",
        "src/config",
    ]
    for dir_path in python_dirs:
        create_init_files(BASE_DIR / dir_path)
    
    # 4. Move static directory if exists
    static_dir = BASE_DIR / "static"
    if static_dir.exists():
        print("\n📁 MOVING STATIC DIRECTORY")
        print("-" * 80)
        dest = BASE_DIR / "frontend" / "static"
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(static_dir), str(dest))
        print(f"   ✅ static/ → frontend/static/")
    
    # 5. Move .streamlit directory if exists
    streamlit_dir = BASE_DIR / ".streamlit"
    if streamlit_dir.exists():
        print("\n📁 MOVING .STREAMLIT DIRECTORY")
        print("-" * 80)
        dest = BASE_DIR / "frontend" / ".streamlit"
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(streamlit_dir), str(dest))
        print(f"   ✅ .streamlit/ → frontend/.streamlit/")
    
    # Summary
    print("\n" + "=" * 80)
    print("REORGANIZATION COMPLETE!")
    print("=" * 80)
    print(f"✅ Files moved: {moved_count}")
    print(f"⚠️  Files skipped: {skipped_count}")
    print(f"\n💡 Next steps:")
    print(f"   1. Update imports in moved files")
    print(f"   2. Test that everything still works")
    print(f"   3. Delete remaining unnecessary files from root")
    print(f"   4. Commit changes to git")
    print("=" * 80)

if __name__ == "__main__":
    response = input("⚠️  This will reorganize your project structure. Continue? (yes/no): ")
    if response.lower() in ['yes', 'y']:
        reorganize_project()
    else:
        print("❌ Reorganization cancelled")
