"""
FastAPI Backend for PE Portfolio Companies V2
REST API endpoints using v2 database schema
"""
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import Optional, List
from pydantic import BaseModel
from pathlib import Path
from src.models.database_models_v2 import get_session, PEFirm, Company, CompanyPEInvestment
from src.enrichment.crunchbase_helpers import decode_revenue_range, decode_employee_count
from sqlalchemy import func, or_, desc

# Initialize FastAPI
app = FastAPI(
    title="PE Portfolio API V2",
    description="REST API for Private Equity Portfolio Companies",
    version="2.0.0"
)

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve React build files
frontend_dist = Path(__file__).parent.parent / "frontend-react" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

# Response Models
class CompanyResponse(BaseModel):
    id: int
    name: str
    pe_firms: List[str]  # Can have multiple PE firms
    status: str
    exit_type: Optional[str] = None
    investment_year: Optional[str] = None
    headquarters: Optional[str] = None
    website: Optional[str] = None
    linkedin_url: Optional[str] = None
    description: Optional[str] = None
    # Enrichment data
    revenue_range: Optional[str] = None
    employee_count: Optional[str] = None
    industry_category: Optional[str] = None
    total_funding_usd: Optional[int] = None
    predicted_revenue: Optional[float] = None  # ML-predicted revenue
    is_public: Optional[bool] = False
    stock_exchange: Optional[str] = None
    
    class Config:
        from_attributes = True


class InvestmentResponse(BaseModel):
    company_id: int
    company_name: str
    pe_firm_name: str
    status: str
    raw_status: Optional[str] = None
    exit_type: Optional[str] = None
    exit_info: Optional[str] = None
    investment_year: Optional[str] = None
    sector: Optional[str] = None
    # Company enrichment data
    revenue_range: Optional[str] = None
    employee_count: Optional[str] = None
    industry_category: Optional[str] = None
    predicted_revenue: Optional[float] = None  # ML-predicted revenue
    headquarters: Optional[str] = None
    website: Optional[str] = None
    linkedin_url: Optional[str] = None
    
    class Config:
        from_attributes = True


class PEFirmResponse(BaseModel):
    id: int
    name: str
    total_investments: int
    active_count: int
    exit_count: int
    
    class Config:
        from_attributes = True


class StatsResponse(BaseModel):
    total_companies: int
    total_investments: int
    total_pe_firms: int
    active_investments: int
    exited_investments: int
    co_investments: int
    enrichment_rate: float


@app.get("/")
def read_root():
    """API root endpoint"""
    return {
        "message": "PE Portfolio API V2",
        "version": "2.0.0",
        "endpoints": {
            "companies": "/api/companies",
            "investments": "/api/investments",
            "pe_firms": "/api/pe-firms",
            "stats": "/api/stats"
        }
    }


@app.get("/api/stats", response_model=StatsResponse)
def get_stats():
    """Get overall portfolio statistics"""
    session = get_session()
    
    try:
        total_companies = session.query(Company).count()
        total_investments = session.query(CompanyPEInvestment).count()
        total_pe_firms = session.query(PEFirm).count()
        
        active_investments = session.query(CompanyPEInvestment).filter_by(computed_status='Active').count()
        exit_investments = session.query(CompanyPEInvestment).filter_by(computed_status='Exit').count()
        
        # Co-investments: companies with multiple PE firms
        co_investments = session.query(Company.id).join(CompanyPEInvestment).group_by(Company.id).having(
            func.count(CompanyPEInvestment.pe_firm_id) > 1
        ).count()
        
        # Enrichment rate: companies with LinkedIn URLs
        enriched = session.query(Company).filter(Company.linkedin_url != None).count()
        enrichment_rate = (enriched / total_companies * 100) if total_companies > 0 else 0
        
        return StatsResponse(
            total_companies=total_companies,
            total_investments=total_investments,
            total_pe_firms=total_pe_firms,
            active_investments=active_investments,
            exited_investments=exit_investments,
            co_investments=co_investments,
            enrichment_rate=round(enrichment_rate, 1)
        )
    finally:
        session.close()


@app.get("/api/pe-firms", response_model=List[PEFirmResponse])
def get_pe_firms():
    """Get all PE firms with statistics"""
    session = get_session()
    
    try:
        firms = session.query(PEFirm).all()
        
        result = []
        for firm in firms:
            total = session.query(CompanyPEInvestment).filter_by(pe_firm_id=firm.id).count()
            active = session.query(CompanyPEInvestment).filter_by(pe_firm_id=firm.id, computed_status='Active').count()
            exited = session.query(CompanyPEInvestment).filter_by(pe_firm_id=firm.id, computed_status='Exit').count()
            
            result.append(PEFirmResponse(
                id=firm.id,
                name=firm.name,
                total_investments=total,
                active_count=active,
                exit_count=exited
            ))
        
        return result
    finally:
        session.close()


@app.get("/api/investments", response_model=List[InvestmentResponse])
def get_investments(
    pe_firm: Optional[str] = Query(None, description="Filter by PE firm name"),
    status: Optional[str] = Query(None, description="Filter by status (Active/Exit)"),
    exit_type: Optional[str] = Query(None, description="Filter by exit type (IPO/Acquisition)"),
    industry: Optional[str] = Query(None, description="Filter by industry category"),
    search: Optional[str] = Query(None, description="Search company names"),
    limit: int = Query(100, ge=1, le=1000, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip")
):
    """Get all investments with filters"""
    session = get_session()
    
    try:
        query = session.query(CompanyPEInvestment).join(Company).join(PEFirm)
        
        # Apply filters
        if pe_firm:
            query = query.filter(PEFirm.name.ilike(f"%{pe_firm}%"))
        
        if status:
            query = query.filter(CompanyPEInvestment.computed_status.ilike(f"%{status}%"))
        
        if exit_type:
            query = query.filter(CompanyPEInvestment.exit_type.ilike(f"%{exit_type}%"))
        
        if industry:
            query = query.filter(Company.industry_category.ilike(f"%{industry}%"))
        
        if search:
            query = query.filter(Company.name.ilike(f"%{search}%"))
        
        # Order by company name
        query = query.order_by(Company.name)
        
        # Apply pagination
        investments = query.offset(offset).limit(limit).all()
        
        # Format response
        result = []
        for inv in investments:
            # Build headquarters from geographic fields
            hq_parts = []
            if inv.company.city:
                hq_parts.append(inv.company.city)
            if inv.company.state_region:
                hq_parts.append(inv.company.state_region)
            if inv.company.country:
                hq_parts.append(inv.company.country)
            headquarters = ", ".join(hq_parts) if hq_parts else None
            
            result.append(InvestmentResponse(
                company_id=inv.company.id,
                company_name=inv.company.name,
                pe_firm_name=inv.pe_firm.name,
                status=inv.computed_status or 'Unknown',
                raw_status=inv.raw_status,
                exit_type=inv.exit_type,
                exit_info=inv.exit_info,
                investment_year=inv.investment_year,
                sector=inv.sector_page,
                revenue_range=decode_revenue_range(inv.company.revenue_range),
                employee_count=decode_employee_count(inv.company.employee_count),
                industry_category=inv.company.industry_category,
                predicted_revenue=inv.company.predicted_revenue,
                headquarters=headquarters,
                website=inv.company.website,
                linkedin_url=inv.company.linkedin_url
            ))
        
        return result
    finally:
        session.close()


@app.get("/api/companies", response_model=List[CompanyResponse])
def get_companies(
    search: Optional[str] = Query(None, description="Search company names"),
    industry: Optional[str] = Query(None, description="Filter by industry category"),
    is_public: Optional[bool] = Query(None, description="Filter by public status"),
    limit: int = Query(100, ge=1, le=1000, description="Number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    """Get companies (deduplicated across PE firms)"""
    session = get_session()
    
    try:
        query = session.query(Company)
        
        # Apply filters
        if search:
            query = query.filter(Company.name.ilike(f"%{search}%"))
        
        if industry:
            query = query.filter(Company.industry_category.ilike(f"%{industry}%"))
        
        if is_public is not None:
            query = query.filter(Company.is_public == is_public)
        
        # Order by name
        query = query.order_by(Company.name)
        
        # Apply pagination
        companies = query.offset(offset).limit(limit).all()
        
        # Format response with PE firms list
        result = []
        for company in companies:
            pe_firms = [inv.pe_firm.name for inv in company.pe_investments]
            status = company.pe_investments[0].computed_status if company.pe_investments else 'Unknown'
            exit_type = company.pe_investments[0].exit_type if company.pe_investments else None
            investment_year = company.pe_investments[0].investment_year if company.pe_investments else None
            
            # Build headquarters from geographic fields
            hq_parts = []
            if company.city:
                hq_parts.append(company.city)
            if company.state_region:
                hq_parts.append(company.state_region)
            if company.country:
                hq_parts.append(company.country)
            headquarters = ", ".join(hq_parts) if hq_parts else None
            
            result.append(CompanyResponse(
                id=company.id,
                name=company.name,
                pe_firms=pe_firms,
                status=status,
                exit_type=exit_type,
                investment_year=investment_year,
                headquarters=headquarters,
                website=company.website,
                linkedin_url=company.linkedin_url,
                description=company.description,
                revenue_range=decode_revenue_range(company.revenue_range),
                employee_count=decode_employee_count(company.employee_count),
                industry_category=company.industry_category,
                total_funding_usd=None,  # Not in v2 schema
                predicted_revenue=company.predicted_revenue,
                is_public=company.is_public,
                stock_exchange=company.ipo_exchange
            ))
        
        return result
    finally:
        session.close()


@app.get("/api/companies/{company_id}", response_model=CompanyResponse)
def get_company(company_id: int):
    """Get a specific company by ID"""
    session = get_session()
    
    try:
        company = session.query(Company).filter_by(id=company_id).first()
        
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        pe_firms = [inv.pe_firm.name for inv in company.pe_investments]
        status = company.pe_investments[0].computed_status if company.pe_investments else 'Unknown'
        exit_type = company.pe_investments[0].exit_type if company.pe_investments else None
        investment_year = company.pe_investments[0].investment_year if company.pe_investments else None
        
        # Build headquarters from geographic fields
        hq_parts = []
        if company.city:
            hq_parts.append(company.city)
        if company.state_region:
            hq_parts.append(company.state_region)
        if company.country:
            hq_parts.append(company.country)
        headquarters = ", ".join(hq_parts) if hq_parts else None
        
        return CompanyResponse(
            id=company.id,
            name=company.name,
            pe_firms=pe_firms,
            status=status,
            exit_type=exit_type,
            investment_year=investment_year,
            headquarters=headquarters,
            website=company.website,
            linkedin_url=company.linkedin_url,
            description=company.description,
            revenue_range=decode_revenue_range(company.revenue_range),
            employee_count=decode_employee_count(company.employee_count),
            industry_category=company.industry_category,
            total_funding_usd=None,  # Not in v2 schema
            predicted_revenue=company.predicted_revenue,
            is_public=company.is_public,
            stock_exchange=company.ipo_exchange
        )
    finally:
        session.close()


# Serve React frontend at root
@app.get("/")
async def serve_frontend():
    """Serve the React frontend"""
    index_file = frontend_dist / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "PE Portfolio API V2", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
