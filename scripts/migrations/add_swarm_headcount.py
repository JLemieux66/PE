"""
Add swarm_headcount column to companies table

This migration adds a new integer column to store actual employee headcount
from The Swarm API, separate from the employee_count range field.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import create_engine, text
from src.models.database_models_v2 import get_database_url


def add_swarm_headcount_column():
    """Add swarm_headcount column to companies table"""
    db_url = get_database_url()
    engine = create_engine(db_url)
    
    print("🔧 Adding swarm_headcount column to companies table...")
    
    try:
        with engine.connect() as conn:
            # Check if we're using PostgreSQL or SQLite
            if 'postgresql' in db_url:
                # PostgreSQL: Check if column already exists
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='companies' AND column_name='swarm_headcount'
                """))
                
                if result.fetchone():
                    print("✅ Column swarm_headcount already exists")
                    return
                
                # Add the column
                conn.execute(text("""
                    ALTER TABLE companies 
                    ADD COLUMN swarm_headcount INTEGER
                """))
                
                # Add index for performance
                conn.execute(text("""
                    CREATE INDEX idx_companies_swarm_headcount 
                    ON companies(swarm_headcount)
                """))
            else:
                # SQLite: Use PRAGMA to check columns
                result = conn.execute(text("PRAGMA table_info(companies)"))
                columns = [row[1] for row in result.fetchall()]
                
                if 'swarm_headcount' in columns:
                    print("✅ Column swarm_headcount already exists")
                    return
                
                # Add the column (SQLite doesn't support adding indexes in ALTER TABLE)
                conn.execute(text("""
                    ALTER TABLE companies 
                    ADD COLUMN swarm_headcount INTEGER
                """))
                
                # Add index separately
                conn.execute(text("""
                    CREATE INDEX idx_companies_swarm_headcount 
                    ON companies(swarm_headcount)
                """))
            
            conn.commit()
            
            print("✅ Successfully added swarm_headcount column with index")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        raise
    finally:
        engine.dispose()


if __name__ == "__main__":
    add_swarm_headcount_column()
