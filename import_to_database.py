"""
Import PE portfolio data from JSON files into PostgreSQL database
"""
import json
from datetime import datetime
from pathlib import Path
from database_models import PEFirm, PortfolioCompany, init_database, get_session
from sqlalchemy.exc import IntegrityError


def import_json_to_db(json_file_path: str):
    """
    Import portfolio data from JSON file to database
    
    Args:
        json_file_path: Path to JSON file (vista_portfolio_with_status.json or ta_portfolio_complete.json)
    """
    # Load JSON data
    with open(json_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Get database session
    session = get_session()
    
    try:
        # Calculate current/exited counts from company data
        companies = data["companies"]
        current_count = sum(1 for c in companies if c.get("status", "").lower() in ["active", "current"])
        exited_count = sum(1 for c in companies if c.get("status", "").lower() in ["exit", "former", "past"] or "exit" in c.get("status", "").lower())
        
        # Create or update PE Firm
        pe_firm_name = data["pe_firm"]
        pe_firm = session.query(PEFirm).filter_by(name=pe_firm_name).first()
        
        if pe_firm:
            print(f"⚠️  PE Firm '{pe_firm_name}' already exists. Updating...")
            # Update existing firm
            pe_firm.total_companies = data["total_companies"]
            pe_firm.current_portfolio_count = data.get("current_portfolio", current_count)
            pe_firm.exited_portfolio_count = data.get("exited_portfolio", exited_count)
            pe_firm.last_scraped = datetime.fromisoformat(data["extraction_date"])
            pe_firm.extraction_time_minutes = data.get("extraction_time_minutes")
        else:
            print(f"✅ Creating new PE Firm: {pe_firm_name}")
            pe_firm = PEFirm(
                name=pe_firm_name,
                total_companies=data["total_companies"],
                current_portfolio_count=data.get("current_portfolio", current_count),
                exited_portfolio_count=data.get("exited_portfolio", exited_count),
                last_scraped=datetime.fromisoformat(data["extraction_date"]),
                extraction_time_minutes=data.get("extraction_time_minutes"),
            )
            session.add(pe_firm)
            session.flush()  # Get the ID
        
        # Import companies
        companies_added = 0
        companies_updated = 0
        companies_skipped = 0
        
        for company_data in data["companies"]:
            # Check if company already exists for this PE firm
            existing_company = (
                session.query(PortfolioCompany)
                .filter_by(
                    pe_firm_id=pe_firm.id,
                    name=company_data["name"]
                )
                .first()
            )
            
            if existing_company:
                # Update existing company
                existing_company.description = company_data.get("description", "")
                existing_company.website = company_data.get("website", "")
                # Vista uses 'industry', TA uses 'sector', a16z uses 'sector'
                existing_company.sector = company_data.get("sector", company_data.get("industry", ""))
                existing_company.headquarters = company_data.get("hq", company_data.get("headquarters", ""))
                existing_company.status = company_data.get("status", "")
                existing_company.investment_year = company_data.get("investment_year", "")
                # a16z uses 'exit_details', TA uses 'exit_info'
                existing_company.exit_info = company_data.get("exit_info", company_data.get("exit_details", ""))
                existing_company.source_url = company_data.get("url", "")
                existing_company.sector_page = company_data.get("sector_page", "")
                existing_company.data_area = company_data.get("area", "")
                existing_company.data_fund = company_data.get("fund", "")
                existing_company.updated_at = datetime.utcnow()
                companies_updated += 1
            else:
                # Create new company
                company = PortfolioCompany(
                    pe_firm_id=pe_firm.id,
                    name=company_data["name"],
                    description=company_data.get("description", ""),
                    website=company_data.get("website", ""),
                    # Vista uses 'industry', TA uses 'sector', a16z uses 'sector'
                    sector=company_data.get("sector", company_data.get("industry", "")),
                    headquarters=company_data.get("hq", company_data.get("headquarters", "")),
                    status=company_data.get("status", ""),
                    investment_year=company_data.get("investment_year", ""),
                    # a16z uses 'exit_details', TA uses 'exit_info'
                    exit_info=company_data.get("exit_info", company_data.get("exit_details", "")),
                    source_url=company_data.get("url", ""),
                    sector_page=company_data.get("sector_page", ""),
                    data_area=company_data.get("area", ""),
                    data_fund=company_data.get("fund", ""),
                )
                session.add(company)
                companies_added += 1
        
        # Commit all changes
        session.commit()
        
        print("\n" + "=" * 80)
        print(f"✅ Successfully imported data from {Path(json_file_path).name}")
        print("=" * 80)
        print(f"PE Firm: {pe_firm_name}")
        print(f"Companies Added: {companies_added}")
        print(f"Companies Updated: {companies_updated}")
        print(f"Total Companies in DB: {companies_added + companies_updated}")
        print("=" * 80)
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error importing data: {e}")
        raise
    finally:
        session.close()


def import_all_json_files():
    """Import all JSON files in the current directory"""
    json_files = [
        "vista_portfolio_with_status.json",
        "ta_portfolio_complete.json",
        "a16z_portfolio_complete.json"
    ]
    
    for json_file in json_files:
        if Path(json_file).exists():
            print(f"\n📂 Processing {json_file}...")
            import_json_to_db(json_file)
        else:
            print(f"⚠️  File not found: {json_file}")


def show_database_stats():
    """Display statistics about the database"""
    session = get_session()
    
    try:
        print("\n" + "=" * 80)
        print("DATABASE STATISTICS")
        print("=" * 80)
        
        # PE Firms
        pe_firms = session.query(PEFirm).all()
        print(f"\n📊 PE Firms: {len(pe_firms)}")
        for firm in pe_firms:
            print(f"  • {firm.name}: {firm.total_companies} companies")
        
        # Total companies
        total_companies = session.query(PortfolioCompany).count()
        print(f"\n📈 Total Portfolio Companies: {total_companies}")
        
        # By status
        print("\n📊 By Status:")
        from sqlalchemy import func
        status_counts = (
            session.query(
                PortfolioCompany.status,
                func.count(PortfolioCompany.id)
            )
            .group_by(PortfolioCompany.status)
            .order_by(func.count(PortfolioCompany.id).desc())
            .all()
        )
        for status, count in status_counts[:10]:  # Top 10
            print(f"  • {status}: {count}")
        
        # By sector
        print("\n📊 Top Sectors:")
        sector_counts = (
            session.query(
                PortfolioCompany.sector,
                func.count(PortfolioCompany.id)
            )
            .group_by(PortfolioCompany.sector)
            .order_by(func.count(PortfolioCompany.id).desc())
            .limit(10)
            .all()
        )
        for sector, count in sector_counts:
            print(f"  • {sector}: {count}")
        
        print("=" * 80)
        
    finally:
        session.close()


if __name__ == "__main__":
    print("=" * 80)
    print("PE PORTFOLIO DATABASE IMPORT")
    print("=" * 80)
    
    # Initialize database (create tables if they don't exist)
    print("\n🔧 Initializing database...")
    init_database()
    
    # Import all JSON files
    print("\n📥 Importing JSON files...")
    import_all_json_files()
    
    # Show statistics
    show_database_stats()
