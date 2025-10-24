"""
Migration script to add linkedin_url column to portfolio_companies table
"""
from sqlalchemy import create_engine, text
from database_models import get_database_url
import sys


def add_linkedin_url_column():
    """Add linkedin_url column to portfolio_companies table"""
    
    database_url = get_database_url()
    engine = create_engine(database_url, echo=True)
    
    print("\n🔄 Adding linkedin_url column to portfolio_companies table...")
    
    try:
        with engine.connect() as conn:
            # Add linkedin_url column
            conn.execute(text("""
                ALTER TABLE portfolio_companies 
                ADD COLUMN linkedin_url VARCHAR(500)
            """))
            conn.commit()
            
        print("✅ Successfully added linkedin_url column!")
        return True
        
    except Exception as e:
        error_msg = str(e)
        if "duplicate column" in error_msg.lower() or "already exists" in error_msg.lower():
            print("ℹ️  Column linkedin_url already exists, skipping...")
            return True
        else:
            print(f"❌ Error adding linkedin_url column: {e}")
            return False


if __name__ == "__main__":
    print("=" * 60)
    print("LinkedIn URL Column Migration")
    print("=" * 60)
    
    success = add_linkedin_url_column()
    
    if success:
        print("\n✅ Migration completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)
