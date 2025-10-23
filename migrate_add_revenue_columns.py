"""
Add revenue_range and employee_count columns to existing database
"""
import sqlite3

def add_columns():
    """Add new columns to portfolio_companies table"""
    conn = sqlite3.connect('pe_portfolio.db')
    cursor = conn.cursor()
    
    try:
        # Add revenue_range column
        print("Adding revenue_range column...")
        cursor.execute("""
            ALTER TABLE portfolio_companies 
            ADD COLUMN revenue_range VARCHAR(50)
        """)
        print("✅ revenue_range added")
        
        # Add employee_count column
        print("Adding employee_count column...")
        cursor.execute("""
            ALTER TABLE portfolio_companies 
            ADD COLUMN employee_count VARCHAR(50)
        """)
        print("✅ employee_count added")
        
        # Create index on revenue_range
        print("Creating index on revenue_range...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_revenue_range 
            ON portfolio_companies(revenue_range)
        """)
        print("✅ Index created")
        
        conn.commit()
        print("\n✅ All columns added successfully!")
        
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("⚠️  Columns already exist")
        else:
            print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    add_columns()
