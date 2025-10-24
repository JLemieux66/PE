"""
Ensure database has all required columns - run on Railway startup
"""
import sqlite3
import os

def migrate_database():
    """Add missing columns if they don't exist"""
    db_path = os.getenv('DATABASE_URL', 'sqlite:///pe_portfolio.db').replace('sqlite:///', '')
    
    print(f"Migrating database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check what columns exist
    cursor.execute("PRAGMA table_info(portfolio_companies)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    
    print(f"Existing columns: {existing_columns}")
    
    # Add missing columns
    columns_to_add = {
        'revenue_range': 'VARCHAR(50)',
        'employee_count': 'VARCHAR(50)',
        'industry_category': 'VARCHAR(100)'
    }
    
    for col_name, col_type in columns_to_add.items():
        if col_name not in existing_columns:
            try:
                print(f"Adding column: {col_name}")
                cursor.execute(f"ALTER TABLE portfolio_companies ADD COLUMN {col_name} {col_type}")
                print(f"✅ Added {col_name}")
            except Exception as e:
                print(f"⚠️  Could not add {col_name}: {e}")
    
    # Create indexes if they don't exist
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_revenue_range ON portfolio_companies(revenue_range)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_industry_category ON portfolio_companies(industry_category)")
        print("✅ Indexes created")
    except Exception as e:
        print(f"⚠️  Could not create indexes: {e}")
    
    conn.commit()
    conn.close()
    print("✅ Migration complete")

if __name__ == "__main__":
    migrate_database()
