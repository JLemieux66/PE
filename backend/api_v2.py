"""
FastAPI Backend for PE Portfolio Companies V2
REST API endpoints using v2 database schema
"""
from fastapi import FastAPI, Query, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from pydantic import BaseModel
from src.models.database_models_v2 import get_session, PEFirm, Company, CompanyPEInvestment
from src.enrichment.crunchbase_helpers import decode_revenue_range, decode_employee_count
import os

# Reverse mappings for filtering (both full ranges and partial values)
REVENUE_RANGE_CODES = {
    "Less than $1M": "r_00000000",
    "$1M - $10M": "r_00001000",
    "$10M - $50M": "r_00010000",
    "$50M - $100M": "r_00050000",
    "$100M - $500M": "r_00100000",
    "$500M - $1B": "r_00500000",
    "$1B - $10B": "r_01000000",
    "$10B+": "r_10000000",
    # Partial matches for convenience
    "$1M": "r_00001000",
    "$10M": "r_00010000",
    "$50M": "r_00050000",
    "$100M": "r_00100000",
    "$500M": "r_00500000",
    "$1B": "r_01000000",
    "$10B": "r_10000000"
}

EMPLOYEE_COUNT_CODES = {
    # Exact decoded values (what users see in the API)
    "1-10": "c_00001_00010",
    "11-50": "c_00011_00050",
    "51-100": "c_00051_00100",
    "101-250": "c_00101_00250",
    "251-500": "c_00251_00500",
    "501-1,000": "c_00501_01000",
    "1,001-5,000": "c_01001_05000",
    "5,001-10,000": "c_05001_10000",
    "10,001+": "c_10001_max"
}
from sqlalchemy import func, or_, desc
from sqlalchemy.orm import joinedload

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
    crunchbase_url: Optional[str] = None
    description: Optional[str] = None
    # Enrichment data
    revenue_range: Optional[str] = None
    employee_count: Optional[str] = None
    industry_category: Optional[str] = None
    total_funding_usd: Optional[int] = None
    # predicted_revenue: Optional[float] = None  # ML-predicted revenue (disabled)
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
    # predicted_revenue: Optional[float] = None  # ML-predicted revenue (disabled)
    headquarters: Optional[str] = None
    website: Optional[str] = None
    linkedin_url: Optional[str] = None
    crunchbase_url: Optional[str] = None
    
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
    pe_firm: Optional[str] = Query(None, description="Filter by PE firm name(s), comma-separated for multiple"),
    status: Optional[str] = Query(None, description="Filter by status (Active/Exit)"),
    exit_type: Optional[str] = Query(None, description="Filter by exit type (IPO/Acquisition)"),
    industry: Optional[str] = Query(None, description="Filter by industry category(ies), comma-separated for multiple"),
    search: Optional[str] = Query(None, description="Search company names"),
    limit: int = Query(10000, ge=1, le=10000, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip")
):
    """Get all investments with filters (supports multi-select with comma-separated values)"""
    session = get_session()
    
    try:
        query = session.query(CompanyPEInvestment).join(Company).join(PEFirm)
        
        # Apply filters with multi-select support
        if pe_firm:
            pe_firms = [f.strip() for f in pe_firm.split(',')]
            firm_conditions = [PEFirm.name.ilike(f"%{firm}%") for firm in pe_firms]
            query = query.filter(or_(*firm_conditions))
        
        if status:
            query = query.filter(CompanyPEInvestment.computed_status.ilike(f"%{status}%"))
        
        if exit_type:
            query = query.filter(CompanyPEInvestment.exit_type.ilike(f"%{exit_type}%"))
        
        if industry:
            industries = [i.strip() for i in industry.split(',')]
            industry_conditions = [Company.industry_category.ilike(f"%{ind}%") for ind in industries]
            query = query.filter(or_(*industry_conditions))
        
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
    pe_firm: Optional[str] = Query(None, description="Filter by PE firm name(s), comma-separated for multiple"),
    industry: Optional[str] = Query(None, description="Filter by industry category(ies), comma-separated for multiple"),
    revenue_range: Optional[str] = Query(None, description="Filter by revenue range(s), comma-separated for multiple"),
    employee_count: Optional[str] = Query(None, description="Filter by employee count range(s), comma-separated for multiple"),
    is_public: Optional[bool] = Query(None, description="Filter by public status"),
    limit: int = Query(10000, ge=1, le=10000, description="Number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    """Get companies (deduplicated across PE firms)"""
    session = get_session()
    
    try:
        # Start with base query - always join to get PE firm data
        query = session.query(Company).join(Company.investments).join(CompanyPEInvestment.pe_firm)
        
        # Apply all filters
        if search:
            query = query.filter(Company.name.ilike(f"%{search}%"))
        
        if industry:
            industries = [i.strip() for i in industry.split(',')]
            industry_conditions = [Company.industry_category.ilike(f"%{ind}%") for ind in industries]
            query = query.filter(or_(*industry_conditions))
        
        if revenue_range:
            revenue_ranges = [r.strip() for r in revenue_range.split(',')]
            revenue_conditions = []
            for rr in revenue_ranges:
                # First check for exact match in our mapping
                if rr in REVENUE_RANGE_CODES:
                    revenue_conditions.append(Company.revenue_range == REVENUE_RANGE_CODES[rr])
                else:
                    # Fallback to fuzzy matching for partial values
                    revenue_conditions.append(Company.revenue_range.ilike(f"%{rr}%"))
                    # Also check if this partial value matches any key
                    for readable, code in REVENUE_RANGE_CODES.items():
                        if rr in readable:
                            revenue_conditions.append(Company.revenue_range == code)
            query = query.filter(or_(*revenue_conditions))
        
        if employee_count:
            # Smart split: check for exact matches with commas first, then split
            employee_conditions = []
            remaining = employee_count
            matched_values = []
            
            # First, extract exact matches that contain commas (like "501-1,000")
            for key in EMPLOYEE_COUNT_CODES.keys():
                if ',' in key and key in remaining:
                    matched_values.append(key)
                    remaining = remaining.replace(key, '')
            
            # Now split the remaining by comma and add them
            if remaining.strip(','):
                for ec in remaining.split(','):
                    ec = ec.strip()
                    if ec:
                        matched_values.append(ec)
            
            # Build conditions for all matched values
            for ec in matched_values:
                # First check for exact match in our mapping
                if ec in EMPLOYEE_COUNT_CODES:
                    employee_conditions.append(Company.employee_count == EMPLOYEE_COUNT_CODES[ec])
                else:
                    # Fallback to fuzzy matching
                    employee_conditions.append(Company.employee_count.ilike(f"%{ec}%"))
                    # Also check if this partial value matches any key
                    for readable, code in EMPLOYEE_COUNT_CODES.items():
                        if ec in readable:
                            employee_conditions.append(Company.employee_count == code)
            
            if employee_conditions:
                query = query.filter(or_(*employee_conditions))
        
        if is_public is not None:
            query = query.filter(Company.is_public == is_public)
        
        if pe_firm:
            pe_firms = [f.strip() for f in pe_firm.split(',')]
            firm_conditions = [PEFirm.name.ilike(f"%{firm}%") for firm in pe_firms]
            query = query.filter(or_(*firm_conditions))
        
        # Use distinct to avoid duplicates from the join, then add eager loading
        query = query.distinct().options(
            joinedload(Company.investments).joinedload(CompanyPEInvestment.pe_firm)
        )
        
        # Order by name
        query = query.order_by(Company.name)
        
        # Apply pagination
        companies = query.offset(offset).limit(limit).all()
        
        # Format response with PE firms list
        result = []
        for company in companies:
            pe_firms = [inv.pe_firm.name for inv in company.investments]
            status = company.investments[0].computed_status if company.investments else 'Unknown'
            exit_type = company.investments[0].exit_type if company.investments else None
            investment_year = company.investments[0].investment_year if company.investments else None
            
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
        company = session.query(Company).options(
            joinedload(Company.investments).joinedload(CompanyPEInvestment.pe_firm)
        ).filter_by(id=company_id).first()
        
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        pe_firms = [inv.pe_firm.name for inv in company.investments]
        status = company.investments[0].computed_status if company.investments else 'Unknown'
        exit_type = company.investments[0].exit_type if company.investments else None
        investment_year = company.investments[0].investment_year if company.investments else None
        
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
            is_public=company.is_public,
            stock_exchange=company.ipo_exchange
        )
    finally:
        session.close()


# Admin authentication
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "your-secret-admin-key-here")

def verify_admin(x_admin_key: Optional[str] = Header(None)):
    """Verify admin API key"""
    if not x_admin_key or x_admin_key != ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Admin access required")
    return True


# Pydantic models for updates
class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    website: Optional[str] = None
    linkedin_url: Optional[str] = None
    crunchbase_url: Optional[str] = None
    description: Optional[str] = None
    city: Optional[str] = None
    state_region: Optional[str] = None
    country: Optional[str] = None
    industry_category: Optional[str] = None
    revenue_range: Optional[str] = None  # Crunchbase code
    employee_count: Optional[str] = None  # Crunchbase code
    is_public: Optional[bool] = None
    ipo_exchange: Optional[str] = None
    ipo_date: Optional[str] = None


@app.put("/api/companies/{company_id}", dependencies=[Depends(verify_admin)])
async def update_company(company_id: int, company_update: CompanyUpdate):
    """
    Update company details (Admin only)
    Requires X-Admin-Key header for authentication
    """
    session = get_session()
    try:
        company = session.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Update fields that were provided
        update_data = company_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(company, field):
                setattr(company, field, value)
        
        session.commit()
        session.refresh(company)
        
        return {
            "message": "Company updated successfully",
            "company_id": company_id,
            "updated_fields": list(update_data.keys())
        }
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating company: {str(e)}")
    finally:
        session.close()


@app.delete("/api/companies/{company_id}", dependencies=[Depends(verify_admin)])
async def delete_company(company_id: int):
    """
    Delete a company (Admin only)
    Requires X-Admin-Key header for authentication
    """
    session = get_session()
    try:
        company = session.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        company_name = company.name
        session.delete(company)
        session.commit()
        
        return {
            "message": f"Company '{company_name}' deleted successfully",
            "company_id": company_id
        }
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting company: {str(e)}")
    finally:
        session.close()


@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "PE Portfolio API V2",
        "version": "2.0.0",
        "endpoints": {
            "companies": "/api/companies",
            "investments": "/api/investments",
            "pe_firms": "/api/pe-firms",
            "stats": "/api/stats"
        },
        "admin_endpoints": {
            "update_company": "PUT /api/companies/{id} (requires X-Admin-Key header)",
            "delete_company": "DELETE /api/companies/{id} (requires X-Admin-Key header)"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
