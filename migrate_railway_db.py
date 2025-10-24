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
        'industry_category': 'VARCHAR(100)',
        'country': 'VARCHAR(100)',
        'state_region': 'VARCHAR(100)',
        'city': 'VARCHAR(200)',
        'company_size_category': 'VARCHAR(50)',
        'revenue_tier': 'VARCHAR(50)',
        'investment_stage': 'VARCHAR(50)'
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
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_revenue_range ON portfolio_companies(revenue_range)")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_industry_category ON portfolio_companies(industry_category)")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_country ON portfolio_companies(country)")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_state_region ON portfolio_companies(state_region)")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_city ON portfolio_companies(city)")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_company_size_category ON portfolio_companies(company_size_category)")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_revenue_tier ON portfolio_companies(revenue_tier)")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_investment_stage ON portfolio_companies(investment_stage)")
        print("✅ Indexes created")
    except Exception as e:
        print(f"⚠️  Could not create indexes: {e}")
    
    # Create company_tags table if it doesn't exist
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS company_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER NOT NULL,
                tag_category VARCHAR(100) NOT NULL,
                tag_value VARCHAR(200) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES portfolio_companies (id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_company_id_tags ON company_tags(company_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tag_category ON company_tags(tag_category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tag_value ON company_tags(tag_value)")
        print("✅ company_tags table ready")
    except Exception as e:
        print(f"⚠️  Could not create company_tags table: {e}")
    
    conn.commit()
    conn.close()
    print("✅ Migration complete")

if __name__ == "__main__":
    migrate_database()
