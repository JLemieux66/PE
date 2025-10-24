"""
Add industry_category column to portfolio_companies table
"""
import sqlite3

def add_column():
    """Add industry_category column"""
    conn = sqlite3.connect('pe_portfolio.db')
    cursor = conn.cursor()
    
    try:
        print("Adding industry_category column...")
        cursor.execute("""
            ALTER TABLE portfolio_companies 
            ADD COLUMN industry_category VARCHAR(100)
        """)
        print("✅ industry_category column added")
        
        print("Creating index on industry_category...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_industry_category 
            ON portfolio_companies(industry_category)
        """)
        print("✅ Index created")
        
        conn.commit()
        print("\n✅ Migration complete!")
        
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("⚠️  Column already exists")
        else:
            print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    add_column()
