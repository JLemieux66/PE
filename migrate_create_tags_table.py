"""
Create company_tags table for flexible tagging
"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "pe_portfolio.db")

def create_tags_table():
    """Create the company_tags table"""
    print("🔄 Creating company_tags table...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create company_tags table
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
    
    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_company_id ON company_tags(company_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tag_category ON company_tags(tag_category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tag_value ON company_tags(tag_value)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_company_category ON company_tags(company_id, tag_category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_category_value ON company_tags(tag_category, tag_value)")
    
    conn.commit()
    conn.close()
    
    print("✅ company_tags table created successfully!")
    print("\nTag categories to use:")
    print("  - technology: SaaS, AI/ML, Mobile, Cloud, Blockchain, IoT")
    print("  - business_model: B2B, B2C, B2B2C, Marketplace, Platform, Subscription")
    print("  - market_focus: Enterprise, SMB, Consumer, Developer Tools")
    print("  - stage: Unicorn, IPO Ready, High Growth, Turnaround")

if __name__ == "__main__":
    create_tags_table()
