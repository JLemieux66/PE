"""
FastAPI Backend for PE Portfolio Companies
REST API endpoints to access portfolio data
"""
from fastapi import FastAPI, Query, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from pydantic import BaseModel
from database_models import get_session, PEFirm, PortfolioCompany
from sqlalchemy import func, or_
from crunchbase_helpers import decode_revenue_range, decode_employee_count

# Run database migration on startup
try:
    from migrate_railway_db import migrate_database
    migrate_database()
except Exception as e:
    print(f"Migration warning: {e}")

# Import setup endpoints
try:
    from setup_endpoints import router as setup_router
except ImportError as e:
    print(f"Setup endpoints not available: {e}")
    setup_router = None

# Initialize FastAPI
app = FastAPI(
    title="PE Portfolio API",
    description="REST API for Private Equity Portfolio Companies",
    version="1.0.0"
)

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include setup endpoints if available
if setup_router:
    app.include_router(setup_router)

# Response Models
class CompanyResponse(BaseModel):
    id: int
    name: str
    pe_firm: str
    sector: Optional[str]
    status: str
    investment_year: Optional[str]
    headquarters: Optional[str]
    website: Optional[str]
    linkedin_url: Optional[str]
    description: Optional[str]
    exit_info: Optional[str]
    # Crunchbase enrichment fields
    revenue_range: Optional[str]
    employee_count: Optional[str]
    # Geographic fields
    country: Optional[str]
    state_region: Optional[str]
    city: Optional[str]
    # Categorization fields
    company_size_category: Optional[str]
    revenue_tier: Optional[str]
    investment_stage: Optional[str]
    # Swarm enrichment fields
    swarm_industry: Optional[str]
    industry_category: Optional[str]
    size_class: Optional[str]
    total_funding_usd: Optional[int]
    last_round_type: Optional[str]
    last_round_amount_usd: Optional[int]
    market_cap: Optional[int]
    ipo_date: Optional[str]
    ipo_year: Optional[int]
    ownership_status: Optional[str]
    ownership_status_detailed: Optional[str]
    is_public: Optional[bool]
    is_acquired: Optional[bool]
    is_exited_swarm: Optional[bool]
    customer_types: Optional[str]
    stock_exchange: Optional[str]
    summary: Optional[str]
    
    class Config:
        from_attributes = True


class PEFirmResponse(BaseModel):
    id: int
    name: str
    total_companies: int
    current_portfolio_count: int
    exited_portfolio_count: int
    last_scraped: str
    
    class Config:
        from_attributes = True


class StatsResponse(BaseModel):
    total_companies: int
    total_pe_firms: int
    current_companies: int
    exited_companies: int


# Root endpoint
@app.get("/")
def read_root():
    """API Health Check"""
    return {
        "message": "PE Portfolio API is running",
        "version": "1.0.0",
        "endpoints": {
            "GET /api/companies": "Get all companies with optional filters",
            "GET /api/companies/{id}": "Get specific company by ID",
            "GET /api/firms": "Get all PE firms",
            "GET /api/firms/{name}/companies": "Get companies for specific PE firm",
            "GET /api/sectors": "Get all sectors",
            "GET /api/statuses": "Get all statuses",
            "GET /api/stats": "Get portfolio statistics"
        }
    }


@app.get("/api/companies", response_model=List[CompanyResponse])
def get_companies(
    pe_firm: Optional[str] = Query(None, description="Filter by PE firm name (comma-separated for multiple)"),
    status: Optional[str] = Query(None, description="Filter by status (comma-separated: Active,Exited)"),
    sector: Optional[str] = Query(None, description="Filter by sector (comma-separated)"),
    industry_category: Optional[str] = Query(None, description="Filter by industry category (comma-separated)"),
    country: Optional[str] = Query(None, description="Filter by country (comma-separated)"),
    state_region: Optional[str] = Query(None, description="Filter by state/region (comma-separated)"),
    city: Optional[str] = Query(None, description="Filter by city (comma-separated)"),
    employee_count: Optional[str] = Query(None, description="Filter by employee count (comma-separated: 1-10,11-50,51-100,101-250,251-500,501-1,000,1,001-5,000,5,001-10,000,10,001+)"),
    revenue_range: Optional[str] = Query(None, description="Filter by revenue range (comma-separated: Less than $1M,$1M - $10M,$10M - $50M,$50M - $100M,$100M - $500M,$500M - $1B,$1B - $10B,$10B+)"),
    company_size_category: Optional[str] = Query(None, description="Filter by size (comma-separated: Startup,Small,Medium,Large,Enterprise)"),
    revenue_tier: Optional[str] = Query(None, description="Filter by revenue tier (comma-separated: Pre-Revenue,Early Stage,Growth Stage,Scale-up,Unicorn)"),
    investment_stage: Optional[str] = Query(None, description="Filter by investment stage (comma-separated: Recent,Mature,Legacy)"),
    is_public: Optional[bool] = Query(None, description="Filter by public status (true/false)"),
    search: Optional[str] = Query(None, description="Search in company name or description"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    """
    Get all companies with optional filters. Multiple values can be comma-separated.
    
    Examples:
    - /api/companies?pe_firm=Vista Equity Partners&status=Active&limit=50
    - /api/companies?country=United States,Canada&company_size_category=Large,Enterprise
    - /api/companies?industry_category=Technology & Software,AI&revenue_tier=Unicorn,Scale-up
    """
    session = get_session()
    
    try:
        query = session.query(PortfolioCompany).join(PEFirm)
        
        # Helper function to split comma-separated values
        def parse_filter(value):
            if not value:
                return None
            return [v.strip() for v in value.split(',') if v.strip()]
        
        # Apply filters with multiple value support
        if pe_firm:
            firms = parse_filter(pe_firm)
            if firms:
                query = query.filter(or_(*[PEFirm.name.ilike(f"%{f}%") for f in firms]))
        
        if status:
            statuses = parse_filter(status)
            if statuses:
                query = query.filter(or_(*[PortfolioCompany.status.ilike(f"%{s}%") for s in statuses]))
        
        if sector:
            sectors = parse_filter(sector)
            if sectors:
                query = query.filter(or_(*[PortfolioCompany.sector.ilike(f"%{s}%") for s in sectors]))
        
        if industry_category:
            categories = parse_filter(industry_category)
            if categories:
                query = query.filter(or_(*[PortfolioCompany.industry_category.ilike(f"%{c}%") for c in categories]))
        
        if country:
            countries = parse_filter(country)
            if countries:
                query = query.filter(or_(*[PortfolioCompany.country.ilike(f"%{c}%") for c in countries]))
        
        if state_region:
            states = parse_filter(state_region)
            if states:
                query = query.filter(or_(*[PortfolioCompany.state_region.ilike(f"%{s}%") for s in states]))
        
        if city:
            cities = parse_filter(city)
            if cities:
                query = query.filter(or_(*[PortfolioCompany.city.ilike(f"%{c}%") for c in cities]))
        
        if employee_count:
            # Need to convert human-readable format back to codes for filtering
            from crunchbase_helpers import EMPLOYEE_RANGES
            employee_ranges = parse_filter(employee_count)
            if employee_ranges:
                # Map human-readable to codes
                code_map = {v: k for k, v in EMPLOYEE_RANGES.items()}
                codes = [code_map.get(r) for r in employee_ranges if code_map.get(r)]
                if codes:
                    query = query.filter(PortfolioCompany.employee_count.in_(codes))
        
        if revenue_range:
            # Need to convert human-readable format back to codes for filtering
            from crunchbase_helpers import REVENUE_RANGES
            revenue_ranges = parse_filter(revenue_range)
            if revenue_ranges:
                # Map human-readable to codes
                code_map = {v: k for k, v in REVENUE_RANGES.items()}
                codes = [code_map.get(r) for r in revenue_ranges if code_map.get(r)]
                if codes:
                    query = query.filter(PortfolioCompany.revenue_range.in_(codes))
        
        if company_size_category:
            sizes = parse_filter(company_size_category)
            if sizes:
                query = query.filter(PortfolioCompany.company_size_category.in_(sizes))
        
        if revenue_tier:
            tiers = parse_filter(revenue_tier)
            if tiers:
                query = query.filter(PortfolioCompany.revenue_tier.in_(tiers))
        
        if investment_stage:
            stages = parse_filter(investment_stage)
            if stages:
                query = query.filter(PortfolioCompany.investment_stage.in_(stages))
        
        if is_public is not None:
            query = query.filter(PortfolioCompany.is_public == is_public)
        
        if search:
            query = query.filter(
                or_(
                    PortfolioCompany.name.ilike(f"%{search}%"),
                    PortfolioCompany.description.ilike(f"%{search}%")
                )
            )
        
        # Pagination
        companies = query.offset(offset).limit(limit).all()
        
        # Format response
        result = []
        for company in companies:
            # Handle empty string IPO year
            ipo_year = company.ipo_year
            if isinstance(ipo_year, str) and ipo_year.strip() == '':
                ipo_year = None
            
            # Decode Crunchbase codes to human-readable format
            revenue_code = getattr(company, 'revenue_range', None)
            employee_code = getattr(company, 'employee_count', None)
            
            result.append(CompanyResponse(
                id=company.id,
                name=company.name,
                pe_firm=company.pe_firm.name,
                sector=company.sector,
                status=company.status,
                investment_year=company.investment_year,
                headquarters=company.headquarters,
                website=company.website,
                linkedin_url=getattr(company, 'linkedin_url', None),
                description=company.description,
                exit_info=company.exit_info,
                revenue_range=decode_revenue_range(revenue_code) if revenue_code else None,
                employee_count=decode_employee_count(employee_code) if employee_code else None,
                country=getattr(company, 'country', None),
                state_region=getattr(company, 'state_region', None),
                city=getattr(company, 'city', None),
                company_size_category=getattr(company, 'company_size_category', None),
                revenue_tier=getattr(company, 'revenue_tier', None),
                investment_stage=getattr(company, 'investment_stage', None),
                swarm_industry=company.swarm_industry,
                industry_category=getattr(company, 'industry_category', None),
                size_class=company.size_class,
                total_funding_usd=company.total_funding_usd,
                last_round_type=company.last_round_type,
                last_round_amount_usd=company.last_round_amount_usd,
                market_cap=company.market_cap,
                ipo_date=company.ipo_date,
                ipo_year=ipo_year,
                ownership_status=company.ownership_status,
                ownership_status_detailed=company.ownership_status_detailed,
                is_public=company.is_public,
                is_acquired=company.is_acquired,
                is_exited_swarm=company.is_exited_swarm,
                customer_types=company.customer_types,
                stock_exchange=company.stock_exchange,
                summary=company.summary
            ))
        
        return result
    
    finally:
        session.close()


@app.get("/api/companies/{company_id}", response_model=CompanyResponse)
def get_company(company_id: int):
    """Get specific company by ID"""
    session = get_session()
    
    try:
        company = session.query(PortfolioCompany).filter_by(id=company_id).first()
        
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Handle empty string IPO year
        ipo_year = company.ipo_year
        if isinstance(ipo_year, str) and ipo_year.strip() == '':
            ipo_year = None
        
        # Decode Crunchbase codes to human-readable format
        revenue_code = getattr(company, 'revenue_range', None)
        employee_code = getattr(company, 'employee_count', None)
        
        return CompanyResponse(
            id=company.id,
            name=company.name,
            pe_firm=company.pe_firm.name,
            sector=company.sector,
            status=company.status,
            investment_year=company.investment_year,
            headquarters=company.headquarters,
            website=company.website,
            linkedin_url=getattr(company, 'linkedin_url', None),
            description=company.description,
            exit_info=company.exit_info,
            revenue_range=decode_revenue_range(revenue_code) if revenue_code else None,
            employee_count=decode_employee_count(employee_code) if employee_code else None,
            country=getattr(company, 'country', None),
            state_region=getattr(company, 'state_region', None),
            city=getattr(company, 'city', None),
            company_size_category=getattr(company, 'company_size_category', None),
            revenue_tier=getattr(company, 'revenue_tier', None),
            investment_stage=getattr(company, 'investment_stage', None),
            swarm_industry=company.swarm_industry,
            industry_category=getattr(company, 'industry_category', None),
            size_class=company.size_class,
            total_funding_usd=company.total_funding_usd,
            last_round_type=company.last_round_type,
            last_round_amount_usd=company.last_round_amount_usd,
            market_cap=company.market_cap,
            ipo_date=company.ipo_date,
            ipo_year=ipo_year,
            ownership_status=company.ownership_status,
            ownership_status_detailed=company.ownership_status_detailed,
            is_public=company.is_public,
            is_acquired=company.is_acquired,
            is_exited_swarm=company.is_exited_swarm,
            customer_types=company.customer_types,
            stock_exchange=company.stock_exchange,
            summary=company.summary
        )
    
    finally:
        session.close()


@app.get("/api/firms", response_model=List[PEFirmResponse])
def get_pe_firms():
    """Get all PE firms"""
    session = get_session()
    
    try:
        firms = session.query(PEFirm).all()
        
        result = []
        for firm in firms:
            result.append(PEFirmResponse(
                id=firm.id,
                name=firm.name,
                total_companies=firm.total_companies,
                current_portfolio_count=firm.current_portfolio_count,
                exited_portfolio_count=firm.exited_portfolio_count,
                last_scraped=str(firm.last_scraped)
            ))
        
        return result
    
    finally:
        session.close()


@app.get("/api/firms/{firm_name}/companies", response_model=List[CompanyResponse])
def get_firm_companies(
    firm_name: str,
    limit: int = Query(100, ge=1, le=1000)
):
    """Get all companies for a specific PE firm"""
    session = get_session()
    
    try:
        firm = session.query(PEFirm).filter(PEFirm.name.ilike(f"%{firm_name}%")).first()
        
        if not firm:
            raise HTTPException(status_code=404, detail="PE firm not found")
        
        companies = session.query(PortfolioCompany).filter_by(pe_firm_id=firm.id).limit(limit).all()
        
        result = []
        for company in companies:
            # Handle empty string IPO year
            ipo_year = company.ipo_year
            if isinstance(ipo_year, str) and ipo_year.strip() == '':
                ipo_year = None
                
            result.append(CompanyResponse(
                id=company.id,
                name=company.name,
                pe_firm=company.pe_firm.name,
                sector=company.sector,
                status=company.status,
                investment_year=company.investment_year,
                headquarters=company.headquarters,
                website=company.website,
                linkedin_url=getattr(company, 'linkedin_url', None),
                description=company.description,
                exit_info=company.exit_info,
                swarm_industry=company.swarm_industry,
                size_class=company.size_class,
                total_funding_usd=company.total_funding_usd,
                last_round_type=company.last_round_type,
                last_round_amount_usd=company.last_round_amount_usd,
                market_cap=company.market_cap,
                ipo_date=company.ipo_date,
                ipo_year=ipo_year,
                ownership_status=company.ownership_status,
                ownership_status_detailed=company.ownership_status_detailed,
                is_public=company.is_public,
                is_acquired=company.is_acquired,
                is_exited_swarm=company.is_exited_swarm,
                customer_types=company.customer_types,
                stock_exchange=company.stock_exchange,
                summary=company.summary
            ))
        
        return result
    
    finally:
        session.close()


@app.get("/api/industries")
def get_industries():
    """Get all unique industries (from Swarm data) - detailed view"""
    session = get_session()
    
    try:
        industries = session.query(PortfolioCompany.swarm_industry).distinct().filter(
            PortfolioCompany.swarm_industry != None,
            PortfolioCompany.swarm_industry != ""
        ).all()
        
        return {"industries": sorted([i[0] for i in industries if i[0]])}
    
    finally:
        session.close()


@app.get("/api/industry-categories")
def get_industry_categories():
    """Get standardized industry categories (20 broad categories)"""
    session = get_session()
    
    try:
        categories = session.query(
            PortfolioCompany.industry_category,
            func.count(PortfolioCompany.id).label('count')
        ).filter(
            PortfolioCompany.industry_category != None,
            PortfolioCompany.industry_category != ""
        ).group_by(PortfolioCompany.industry_category).all()
        
        return {
            "categories": sorted([
                {"name": cat[0], "count": cat[1]} 
                for cat in categories if cat[0]
            ], key=lambda x: x['count'], reverse=True)
        }
    
    finally:
        session.close()


@app.get("/api/sectors")
def get_sectors():
    """Get all unique sectors"""
    session = get_session()
    
    try:
        sectors = session.query(PortfolioCompany.sector).distinct().filter(
            PortfolioCompany.sector != ""
        ).all()
        
        return {"sectors": sorted([s[0] for s in sectors if s[0]])}
    
    finally:
        session.close()


@app.get("/api/statuses")
def get_statuses():
    """Get all unique statuses"""
    session = get_session()
    
    try:
        statuses = session.query(PortfolioCompany.status).distinct().all()
        
        return {"statuses": sorted([s[0] for s in statuses if s[0]])}
    
    finally:
        session.close()


@app.get("/api/stats", response_model=StatsResponse)
def get_stats():
    """Get overall portfolio statistics"""
    session = get_session()
    
    try:
        total_companies = session.query(PortfolioCompany).count()
        total_firms = session.query(PEFirm).count()
        current = session.query(PortfolioCompany).filter_by(status="current").count()
        exited = session.query(PortfolioCompany).filter(
            or_(
                PortfolioCompany.status == "former",
                PortfolioCompany.status.like("past%")
            )
        ).count()
        
        return StatsResponse(
            total_companies=total_companies,
            total_pe_firms=total_firms,
            current_companies=current,
            exited_companies=exited
        )
    
    finally:
        session.close()


@app.get("/api/filters")
def get_filter_options():
    """Get all available filter values for dropdown menus"""
    session = get_session()
    
    try:
        # Get all unique values for each filterable field
        countries = session.query(PortfolioCompany.country, func.count(PortfolioCompany.id))\
            .filter(PortfolioCompany.country != None)\
            .group_by(PortfolioCompany.country)\
            .order_by(func.count(PortfolioCompany.id).desc()).all()
        
        states = session.query(PortfolioCompany.state_region, func.count(PortfolioCompany.id))\
            .filter(PortfolioCompany.state_region != None)\
            .group_by(PortfolioCompany.state_region)\
            .order_by(func.count(PortfolioCompany.id).desc()).all()
        
        cities = session.query(PortfolioCompany.city, func.count(PortfolioCompany.id))\
            .filter(PortfolioCompany.city != None)\
            .group_by(PortfolioCompany.city)\
            .order_by(func.count(PortfolioCompany.id).desc()).limit(50).all()
        
        categories = session.query(PortfolioCompany.industry_category, func.count(PortfolioCompany.id))\
            .filter(PortfolioCompany.industry_category != None)\
            .group_by(PortfolioCompany.industry_category)\
            .order_by(func.count(PortfolioCompany.id).desc()).all()
        
        sizes = session.query(PortfolioCompany.company_size_category, func.count(PortfolioCompany.id))\
            .filter(PortfolioCompany.company_size_category != None)\
            .group_by(PortfolioCompany.company_size_category).all()
        
        tiers = session.query(PortfolioCompany.revenue_tier, func.count(PortfolioCompany.id))\
            .filter(PortfolioCompany.revenue_tier != None)\
            .group_by(PortfolioCompany.revenue_tier).all()
        
        stages = session.query(PortfolioCompany.investment_stage, func.count(PortfolioCompany.id))\
            .filter(PortfolioCompany.investment_stage != None)\
            .group_by(PortfolioCompany.investment_stage).all()
        
        return {
            "countries": [{"value": c[0], "count": c[1]} for c in countries],
            "states": [{"value": s[0], "count": s[1]} for s in states],
            "top_cities": [{"value": c[0], "count": c[1]} for c in cities],
            "industry_categories": [{"value": c[0], "count": c[1]} for c in categories],
            "company_sizes": [{"value": s[0], "count": s[1]} for s in sizes],
            "revenue_tiers": [{"value": t[0], "count": t[1]} for t in tiers],
            "investment_stages": [{"value": s[0], "count": s[1]} for s in stages]
        }
    
    finally:
        session.close()


@app.get("/api/companies/{company_id}/tags")
def get_company_tags(company_id: int):
    """Get all tags for a specific company"""
    from database_models import CompanyTag
    
    session = get_session()
    
    try:
        # Check if company exists
        company = session.query(PortfolioCompany).filter_by(id=company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        tags = session.query(CompanyTag).filter_by(company_id=company_id).all()
        
        # Group by category
        result = {}
        for tag in tags:
            if tag.tag_category not in result:
                result[tag.tag_category] = []
            result[tag.tag_category].append(tag.tag_value)
        
        return {
            "company_id": company_id,
            "company_name": company.name,
            "tags": result,
            "total_tags": len(tags)
        }
    
    finally:
        session.close()


@app.get("/api/tags/{tag_category}")
def get_companies_by_tag(
    tag_category: str,
    tag_value: Optional[str] = Query(None, description="Specific tag value (comma-separated for multiple)"),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get all companies with a specific tag category and optionally specific tag values"""
    from database_models import CompanyTag
    
    session = get_session()
    
    try:
        query = session.query(PortfolioCompany).join(
            CompanyTag, PortfolioCompany.id == CompanyTag.company_id
        ).filter(CompanyTag.tag_category == tag_category)
        
        if tag_value:
            values = [v.strip() for v in tag_value.split(',') if v.strip()]
            if values:
                query = query.filter(CompanyTag.tag_value.in_(values))
        
        companies = query.distinct().limit(limit).all()
        
        # Get unique tag values for this category
        tag_values = session.query(CompanyTag.tag_value, func.count(CompanyTag.id))\
            .filter(CompanyTag.tag_category == tag_category)\
            .group_by(CompanyTag.tag_value)\
            .order_by(func.count(CompanyTag.id).desc()).all()
        
        return {
            "tag_category": tag_category,
            "available_values": [{"value": v[0], "count": v[1]} for v in tag_values],
            "companies": [{"id": c.id, "name": c.name, "pe_firm": c.pe_firm.name} for c in companies],
            "total": len(companies)
        }
    
    finally:
        session.close()


# Run with: uvicorn api:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
