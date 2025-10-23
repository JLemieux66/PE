"""
FastAPI Backend for PE Portfolio Companies
REST API endpoints to access portfolio data
"""
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from pydantic import BaseModel
from database_models import get_session, PEFirm, PortfolioCompany
from sqlalchemy import func, or_

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
    description: Optional[str]
    exit_info: Optional[str]
    # Crunchbase enrichment fields
    revenue_range: Optional[str]
    employee_count: Optional[str]
    # Swarm enrichment fields
    swarm_industry: Optional[str]
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
    pe_firm: Optional[str] = Query(None, description="Filter by PE firm name"),
    status: Optional[str] = Query(None, description="Filter by status (current, former, past)"),
    sector: Optional[str] = Query(None, description="Filter by sector (partial match)"),
    search: Optional[str] = Query(None, description="Search in company name or description"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    """
    Get all companies with optional filters
    
    Example: /api/companies?pe_firm=Vista Equity Partners&status=current&limit=50
    """
    session = get_session()
    
    try:
        query = session.query(PortfolioCompany).join(PEFirm)
        
        # Apply filters
        if pe_firm:
            query = query.filter(PEFirm.name.ilike(f"%{pe_firm}%"))
        
        if status:
            query = query.filter(PortfolioCompany.status.ilike(f"%{status}%"))
        
        if sector:
            query = query.filter(PortfolioCompany.sector.ilike(f"%{sector}%"))
        
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
            
            result.append(CompanyResponse(
                id=company.id,
                name=company.name,
                pe_firm=company.pe_firm.name,
                sector=company.sector,
                status=company.status,
                investment_year=company.investment_year,
                headquarters=company.headquarters,
                website=company.website,
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
        
        return CompanyResponse(
            id=company.id,
            name=company.name,
            pe_firm=company.pe_firm.name,
            sector=company.sector,
            status=company.status,
            investment_year=company.investment_year,
            headquarters=company.headquarters,
            website=company.website,
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
    """Get all unique industries (from Swarm data)"""
    session = get_session()
    
    try:
        industries = session.query(PortfolioCompany.swarm_industry).distinct().filter(
            PortfolioCompany.swarm_industry != None,
            PortfolioCompany.swarm_industry != ""
        ).all()
        
        return {"industries": sorted([i[0] for i in industries if i[0]])}
    
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


# Run with: uvicorn api:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
