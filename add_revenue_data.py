"""
Add revenue and employee count data from Crunchbase to all companies
"""
from database_models import get_session, PortfolioCompany
from crunchbase_helpers import search_company_crunchbase, get_company_details_crunchbase
import time

def add_revenue_employee_data():
    """Add revenue and employee data to all companies"""
    session = get_session()
    
    try:
        # Get all companies
        companies = session.query(PortfolioCompany).all()
        total = len(companies)
        
        print(f"\n🔄 Adding revenue/employee data to {total} companies...\n")
        
        updated_count = 0
        skipped_count = 0
        
        for i, company in enumerate(companies, 1):
            print(f"[{i}/{total}] {company.name}...", end=" ")
            
            # Search Crunchbase
            results = search_company_crunchbase(company.name)
            
            if not results:
                print("❌ Not found in Crunchbase")
                skipped_count += 1
                continue
            
            entity_id = results[0]
            
            # Get details including revenue and employees
            details = get_company_details_crunchbase(entity_id)
            
            if details:
                revenue_range = details.get("revenue_range", "")
                employee_count = details.get("employee_count", "")
                
                if revenue_range or employee_count:
                    company.revenue_range = revenue_range
                    company.employee_count = employee_count
                    updated_count += 1
                    print(f"✅ Revenue: {revenue_range or 'N/A'}, Employees: {employee_count or 'N/A'}")
                else:
                    print("⚠️  No revenue/employee data available")
                    skipped_count += 1
            else:
                print("❌ Failed to get details")
                skipped_count += 1
            
            # Commit every 10 companies
            if i % 10 == 0:
                session.commit()
                print(f"\n💾 Progress saved ({i}/{total})\n")
            
            # Rate limiting
            time.sleep(0.3)
        
        # Final commit
        session.commit()
        
        print(f"\n✅ Complete!")
        print(f"   Updated: {updated_count}")
        print(f"   Skipped: {skipped_count}")
        print(f"   Total: {total}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    add_revenue_employee_data()
