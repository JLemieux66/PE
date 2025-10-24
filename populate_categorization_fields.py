"""
Calculate and populate company_size_category, revenue_tier, and investment_stage fields
"""
from database_models import get_session, PortfolioCompany
from crunchbase_helpers import REVENUE_RANGES, EMPLOYEE_RANGES
from sqlalchemy import func

def categorize_company_size(employee_code):
    """Convert employee count code to size category"""
    if not employee_code:
        return None
    
    size_map = {
        "c_00001_00010": "Startup",      # 1-10
        "c_00011_00050": "Startup",      # 11-50
        "c_00051_00100": "Small",        # 51-100
        "c_00101_00250": "Small",        # 101-250
        "c_00251_00500": "Medium",       # 251-500
        "c_00501_01000": "Medium",       # 501-1,000
        "c_01001_05000": "Large",        # 1,001-5,000
        "c_05001_10000": "Enterprise",   # 5,001-10,000
        "c_10001_max": "Enterprise"      # 10,001+
    }
    
    return size_map.get(employee_code)

def categorize_revenue_tier(revenue_code):
    """Convert revenue code to tier"""
    if not revenue_code:
        return None
    
    tier_map = {
        "r_00000000": "Pre-Revenue",     # Less than $1M
        "r_00001000": "Early Stage",     # $1M - $10M
        "r_00010000": "Growth Stage",    # $10M - $50M
        "r_00050000": "Growth Stage",    # $50M - $100M
        "r_00100000": "Scale-up",        # $100M - $500M
        "r_00500000": "Scale-up",        # $500M - $1B
        "r_01000000": "Unicorn",         # $1B - $10B
        "r_10000000": "Unicorn"          # $10B+
    }
    
    return tier_map.get(revenue_code)

def categorize_investment_stage(investment_year):
    """Convert investment year to stage"""
    if not investment_year or investment_year.strip() == '':
        return None
    
    try:
        year = int(investment_year)
        if year >= 2020:
            return "Recent"
        elif year >= 2015:
            return "Mature"
        else:
            return "Legacy"
    except (ValueError, TypeError):
        return None

def populate_categorization_fields():
    """Calculate and populate all categorization fields"""
    print("🔄 Calculating categorization fields...")
    
    session = get_session()
    
    try:
        companies = session.query(PortfolioCompany).all()
        
        print(f"📊 Processing {len(companies)} companies...")
        
        size_count = 0
        revenue_count = 0
        stage_count = 0
        
        for i, company in enumerate(companies, 1):
            # Company size category
            if company.employee_count:
                company.company_size_category = categorize_company_size(company.employee_count)
                if company.company_size_category:
                    size_count += 1
            
            # Revenue tier
            if company.revenue_range:
                company.revenue_tier = categorize_revenue_tier(company.revenue_range)
                if company.revenue_tier:
                    revenue_count += 1
            
            # Investment stage
            if company.investment_year:
                company.investment_stage = categorize_investment_stage(company.investment_year)
                if company.investment_stage:
                    stage_count += 1
            
            if i % 100 == 0:
                session.commit()
                print(f"  Processed {i}/{len(companies)} companies...")
        
        session.commit()
        
        print(f"\n✅ Categorization complete!")
        print(f"  Company sizes: {size_count}/{len(companies)}")
        print(f"  Revenue tiers: {revenue_count}/{len(companies)}")
        print(f"  Investment stages: {stage_count}/{len(companies)}")
        
        # Show distribution statistics
        print("\n📊 Company Size Distribution:")
        size_dist = session.query(
            PortfolioCompany.company_size_category,
            func.count(PortfolioCompany.id)
        ).filter(
            PortfolioCompany.company_size_category != None
        ).group_by(PortfolioCompany.company_size_category).all()
        
        for category, count in sorted(size_dist, key=lambda x: x[1], reverse=True):
            print(f"  {category:20} {count:4} companies")
        
        print("\n📊 Revenue Tier Distribution:")
        revenue_dist = session.query(
            PortfolioCompany.revenue_tier,
            func.count(PortfolioCompany.id)
        ).filter(
            PortfolioCompany.revenue_tier != None
        ).group_by(PortfolioCompany.revenue_tier).all()
        
        # Sort by tier order
        tier_order = ["Pre-Revenue", "Early Stage", "Growth Stage", "Scale-up", "Unicorn"]
        revenue_dist_sorted = sorted(revenue_dist, key=lambda x: tier_order.index(x[0]) if x[0] in tier_order else 999)
        
        for tier, count in revenue_dist_sorted:
            print(f"  {tier:20} {count:4} companies")
        
        print("\n📊 Investment Stage Distribution:")
        stage_dist = session.query(
            PortfolioCompany.investment_stage,
            func.count(PortfolioCompany.id)
        ).filter(
            PortfolioCompany.investment_stage != None
        ).group_by(PortfolioCompany.investment_stage).all()
        
        stage_order = ["Recent", "Mature", "Legacy"]
        stage_dist_sorted = sorted(stage_dist, key=lambda x: stage_order.index(x[0]) if x[0] in stage_order else 999)
        
        for stage, count in stage_dist_sorted:
            print(f"  {stage:20} {count:4} companies")
        
    finally:
        session.close()

if __name__ == "__main__":
    populate_categorization_fields()
