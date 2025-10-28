"""
Setup endpoints to populate data on Railway without manual database upload
"""
import sys
from pathlib import Path
# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


from fastapi import APIRouter, BackgroundTasks, HTTPException
from src.models.database_models import get_session, PortfolioCompany, CompanyTag
from populate_geographic_fields import parse_location, populate_geographic_fields
from populate_categorization_fields import categorize_company_size, categorize_revenue_tier, categorize_investment_stage
from setup_initial_tags import extract_tags
from sqlalchemy import func

router = APIRouter()

# Track setup status
setup_status = {
    "geographic": {"completed": False, "count": 0},
    "categorization": {"completed": False, "count": 0},
    "tags": {"completed": False, "count": 0}
}

@router.get("/api/setup/status")
def get_setup_status():
    """Check what data has been populated"""
    session = get_session()
    
    try:
        # Check if data exists
        geo_count = session.query(PortfolioCompany).filter(PortfolioCompany.country != None).count()
        cat_count = session.query(PortfolioCompany).filter(PortfolioCompany.company_size_category != None).count()
        tag_count = session.query(CompanyTag).count()
        
        return {
            "geographic_data": {"populated": geo_count > 0, "count": geo_count},
            "categorization_data": {"populated": cat_count > 0, "count": cat_count},
            "tags": {"populated": tag_count > 0, "count": tag_count},
            "ready_to_use": geo_count > 0 and cat_count > 0 and tag_count > 0
        }
    finally:
        session.close()


@router.post("/api/setup/populate-all")
def populate_all_data(background_tasks: BackgroundTasks):
    """
    Populate all enhancement data: geographic fields, categorizations, and tags.
    This runs in the background and can take 30-60 seconds.
    Call GET /api/setup/status to check progress.
    """
    session = get_session()
    
    try:
        # Check if already populated
        geo_count = session.query(PortfolioCompany).filter(PortfolioCompany.country != None).count()
        tag_count = session.query(CompanyTag).count()
        
        if geo_count > 1000 and tag_count > 2000:
            return {
                "status": "already_populated",
                "message": "Data already exists. Use force=true to repopulate.",
                "geographic_count": geo_count,
                "tag_count": tag_count
            }
        
        # Run population in background
        background_tasks.add_task(run_full_population)
        
        return {
            "status": "started",
            "message": "Data population started in background. Check /api/setup/status for progress.",
            "estimated_time": "30-60 seconds"
        }
        
    finally:
        session.close()


def run_full_population():
    """Run all population scripts"""
    session = get_session()
    
    try:
        print("🔄 Starting full data population...")
        
        # 1. Populate geographic fields
        print("📍 Populating geographic data...")
        companies = session.query(PortfolioCompany).filter(
            PortfolioCompany.headquarters != None,
            PortfolioCompany.headquarters != ''
        ).all()
        
        for company in companies:
            city, state_region, country = parse_location(company.headquarters)
            company.city = city
            company.state_region = state_region
            company.country = country
        
        session.commit()
        print(f"✅ Geographic data: {len(companies)} companies")
        
        # 2. Populate categorization fields
        print("📊 Populating categorization data...")
        all_companies = session.query(PortfolioCompany).all()
        
        for company in all_companies:
            if company.employee_count:
                company.company_size_category = categorize_company_size(company.employee_count)
            
            if company.revenue_range:
                company.revenue_tier = categorize_revenue_tier(company.revenue_range)
            
            if company.investment_year:
                company.investment_stage = categorize_investment_stage(company.investment_year)
        
        session.commit()
        print(f"✅ Categorization: {len(all_companies)} companies")
        
        # 3. Populate tags
        print("🏷️  Populating tags...")
        # Clear existing tags
        session.query(CompanyTag).delete()
        session.commit()
        
        total_tags = 0
        for company in all_companies:
            tags = extract_tags(company)
            
            if tags:
                for tag_category, tag_value in tags:
                    tag = CompanyTag(
                        company_id=company.id,
                        tag_category=tag_category,
                        tag_value=tag_value
                    )
                    session.add(tag)
                    total_tags += 1
        
        session.commit()
        print(f"✅ Tags: {total_tags} tags added")
        
        print("🎉 Full population complete!")
        
    except Exception as e:
        print(f"❌ Error during population: {e}")
        session.rollback()
    finally:
        session.close()


@router.post("/api/setup/populate-geographic")
def populate_geographic_only():
    """Populate only geographic fields (country, state, city)"""
    session = get_session()
    
    try:
        companies = session.query(PortfolioCompany).filter(
            PortfolioCompany.headquarters != None,
            PortfolioCompany.headquarters != ''
        ).all()
        
        for company in companies:
            city, state_region, country = parse_location(company.headquarters)
            company.city = city
            company.state_region = state_region
            company.country = country
        
        session.commit()
        
        return {
            "status": "completed",
            "message": "Geographic data populated successfully",
            "count": len(companies)
        }
        
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@router.post("/api/setup/populate-categories")
def populate_categories_only():
    """Populate only categorization fields (size, revenue tier, investment stage)"""
    session = get_session()
    
    try:
        companies = session.query(PortfolioCompany).all()
        
        for company in companies:
            if company.employee_count:
                company.company_size_category = categorize_company_size(company.employee_count)
            
            if company.revenue_range:
                company.revenue_tier = categorize_revenue_tier(company.revenue_range)
            
            if company.investment_year:
                company.investment_stage = categorize_investment_stage(company.investment_year)
        
        session.commit()
        
        return {
            "status": "completed",
            "message": "Categorization data populated successfully",
            "count": len(companies)
        }
        
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@router.post("/api/setup/populate-tags")
def populate_tags_only():
    """Populate only tags"""
    session = get_session()
    
    try:
        # Clear existing tags
        session.query(CompanyTag).delete()
        session.commit()
        
        companies = session.query(PortfolioCompany).all()
        
        total_tags = 0
        for company in companies:
            tags = extract_tags(company)
            
            if tags:
                for tag_category, tag_value in tags:
                    tag = CompanyTag(
                        company_id=company.id,
                        tag_category=tag_category,
                        tag_value=tag_value
                    )
                    session.add(tag)
                    total_tags += 1
        
        session.commit()
        
        return {
            "status": "completed",
            "message": "Tags populated successfully",
            "total_tags": total_tags
        }
        
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()
