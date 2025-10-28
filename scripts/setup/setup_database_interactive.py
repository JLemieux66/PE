"""
Interactive database setup - creates database and imports data
"""
import sys
from pathlib import Path
# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


import os
import sys
from getpass import getpass
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError


def test_connection(db_url):
    """Test if database connection works"""
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        return False


def create_database(admin_url, db_name):
    """Create database using admin connection"""
    try:
        # Connect to postgres database to create new database
        engine = create_engine(admin_url)
        with engine.connect() as conn:
            # Need to be outside transaction to create database
            conn.execution_options(isolation_level="AUTOCOMMIT")
            conn.execute(text(f"CREATE DATABASE {db_name}"))
        return True
    except ProgrammingError as e:
        if "already exists" in str(e):
            print(f"✓ Database '{db_name}' already exists")
            return True
        raise
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False


def main():
    print("=" * 80)
    print("POSTGRESQL DATABASE SETUP")
    print("=" * 80)
    
    # Get credentials
    print("\nEnter your PostgreSQL credentials:")
    print("(Press Enter to use default values shown in brackets)")
    
    host = input("Host [localhost]: ").strip() or "localhost"
    port = input("Port [5432]: ").strip() or "5432"
    username = input("Username [postgres]: ").strip() or "postgres"
    password = getpass("Password: ")
    
    # Test connection to default postgres database
    admin_url = f"postgresql://{username}:{password}@{host}:{port}/postgres"
    
    print("\n🔌 Testing connection...")
    if not test_connection(admin_url):
        print("❌ Connection failed. Please check your credentials.")
        sys.exit(1)
    
    print("✓ Connection successful!")
    
    # Create pe_portfolio database
    print("\n📦 Creating 'pe_portfolio' database...")
    if not create_database(admin_url, "pe_portfolio"):
        sys.exit(1)
    
    print("✓ Database created!")
    
    # Save to .env file
    db_url = f"postgresql://{username}:{password}@{host}:{port}/pe_portfolio"
    
    print("\n💾 Saving connection string to .env file...")
    with open(".env", "w") as f:
        f.write(f"DATABASE_URL={db_url}\n")
    
    print("✓ Saved to .env")
    
    # Now run the import
    print("\n" + "=" * 80)
    print("IMPORTING DATA")
    print("=" * 80)
    
    os.environ["DATABASE_URL"] = db_url
    
    # Import the import script
    from import_to_database import import_all_json_files, show_database_stats
    from src.models.database_models import init_database
    
    print("\n🔧 Initializing database tables...")
    init_database()
    
    print("\n📥 Importing JSON files...")
    import_all_json_files()
    
    print("\n📊 Database statistics:")
    show_database_stats()
    
    print("\n" + "=" * 80)
    print("✅ SETUP COMPLETE!")
    print("=" * 80)
    print(f"\nDatabase URL saved to .env file")
    print(f"You can now query data with: pipenv run python query_database.py")


if __name__ == "__main__":
    main()
