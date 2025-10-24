"""
Add organization and categorization fields to portfolio_companies table
"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "pe_portfolio.db")

def migrate_database():
    """Add new columns for geographic and categorization fields"""
    print("🔄 Starting database migration...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check existing columns
    cursor.execute("PRAGMA table_info(portfolio_companies)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    
    # Columns to add
    columns_to_add = {
        'country': 'VARCHAR(100)',
        'state_region': 'VARCHAR(100)',
        'city': 'VARCHAR(200)',
        'company_size_category': 'VARCHAR(50)',
        'revenue_tier': 'VARCHAR(50)',
        'investment_stage': 'VARCHAR(50)'
    }
    
    # Add missing columns
    for col_name, col_type in columns_to_add.items():
        if col_name not in existing_columns:
            print(f"  Adding column: {col_name}")
            cursor.execute(f"ALTER TABLE portfolio_companies ADD COLUMN {col_name} {col_type}")
        else:
            print(f"  ✓ Column already exists: {col_name}")
    
    # Create indexes
    indexes = [
        ("idx_country", "country"),
        ("idx_state_region", "state_region"),
        ("idx_city", "city"),
        ("idx_company_size_category", "company_size_category"),
        ("idx_revenue_tier", "revenue_tier"),
        ("idx_investment_stage", "investment_stage")
    ]
    
    for index_name, column_name in indexes:
        try:
            cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON portfolio_companies({column_name})")
            print(f"  ✓ Created index: {index_name}")
        except Exception as e:
            print(f"  ⚠️  Index {index_name} may already exist: {e}")
    
    conn.commit()
    conn.close()
    
    print("✅ Migration completed successfully!")
    print("\nNext steps:")
    print("  1. Run populate_geographic_fields.py to parse location data")
    print("  2. Run populate_categorization_fields.py to calculate size/tier categories")
    print("  3. Run setup_initial_tags.py to add initial tags")

if __name__ == "__main__":
    migrate_database()
