"""
Query and analyze PE portfolio data from PostgreSQL database
"""
from database_models import PEFirm, PortfolioCompany, get_session
from sqlalchemy import func, or_, and_


class PortfolioQuery:
    """Helper class for querying portfolio data"""
    
    def __init__(self):
        self.session = get_session()
    
    def close(self):
        """Close database session"""
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def get_all_pe_firms(self):
        """Get all PE firms"""
        return self.session.query(PEFirm).all()
    
    def get_pe_firm_by_name(self, name: str):
        """Get PE firm by name"""
        return self.session.query(PEFirm).filter_by(name=name).first()
    
    def get_companies_by_pe_firm(self, pe_firm_name: str):
        """Get all companies for a PE firm"""
        pe_firm = self.get_pe_firm_by_name(pe_firm_name)
        if pe_firm:
            return self.session.query(PortfolioCompany).filter_by(pe_firm_id=pe_firm.id).all()
        return []
    
    def get_current_portfolio(self, pe_firm_name: str):
        """Get current portfolio companies for a PE firm"""
        pe_firm = self.get_pe_firm_by_name(pe_firm_name)
        if pe_firm:
            return (
                self.session.query(PortfolioCompany)
                .filter_by(pe_firm_id=pe_firm.id)
                .filter(PortfolioCompany.status == "current")
                .all()
            )
        return []
    
    def get_exited_portfolio(self, pe_firm_name: str):
        """Get exited portfolio companies for a PE firm"""
        pe_firm = self.get_pe_firm_by_name(pe_firm_name)
        if pe_firm:
            return (
                self.session.query(PortfolioCompany)
                .filter_by(pe_firm_id=pe_firm.id)
                .filter(
                    or_(
                        PortfolioCompany.status == "former",
                        PortfolioCompany.status.like("past%")
                    )
                )
                .all()
            )
        return []
    
    def search_companies(self, search_term: str):
        """Search companies by name"""
        return (
            self.session.query(PortfolioCompany)
            .filter(PortfolioCompany.name.ilike(f"%{search_term}%"))
            .all()
        )
    
    def get_companies_by_sector(self, sector: str):
        """Get companies by sector"""
        return (
            self.session.query(PortfolioCompany)
            .filter(PortfolioCompany.sector.ilike(f"%{sector}%"))
            .all()
        )
    
    def get_companies_by_year(self, year: str):
        """Get companies by investment year"""
        return (
            self.session.query(PortfolioCompany)
            .filter(PortfolioCompany.investment_year == year)
            .all()
        )
    
    def get_sector_distribution(self, pe_firm_name: str = None):
        """Get distribution of companies by sector"""
        query = self.session.query(
            PortfolioCompany.sector,
            func.count(PortfolioCompany.id).label("count")
        )
        
        if pe_firm_name:
            pe_firm = self.get_pe_firm_by_name(pe_firm_name)
            if pe_firm:
                query = query.filter(PortfolioCompany.pe_firm_id == pe_firm.id)
        
        return query.group_by(PortfolioCompany.sector).order_by(func.count(PortfolioCompany.id).desc()).all()
    
    def get_investment_timeline(self, pe_firm_name: str = None):
        """Get investment timeline (companies by year)"""
        query = self.session.query(
            PortfolioCompany.investment_year,
            func.count(PortfolioCompany.id).label("count")
        )
        
        if pe_firm_name:
            pe_firm = self.get_pe_firm_by_name(pe_firm_name)
            if pe_firm:
                query = query.filter(PortfolioCompany.pe_firm_id == pe_firm.id)
        
        return (
            query.filter(PortfolioCompany.investment_year != "")
            .group_by(PortfolioCompany.investment_year)
            .order_by(PortfolioCompany.investment_year)
            .all()
        )
    
    def get_status_breakdown(self, pe_firm_name: str = None):
        """Get status breakdown"""
        query = self.session.query(
            PortfolioCompany.status,
            func.count(PortfolioCompany.id).label("count")
        )
        
        if pe_firm_name:
            pe_firm = self.get_pe_firm_by_name(pe_firm_name)
            if pe_firm:
                query = query.filter(PortfolioCompany.pe_firm_id == pe_firm.id)
        
        return query.group_by(PortfolioCompany.status).order_by(func.count(PortfolioCompany.id).desc()).all()


def demo_queries():
    """Demo various queries"""
    with PortfolioQuery() as pq:
        print("=" * 80)
        print("PORTFOLIO DATABASE QUERIES - DEMO")
        print("=" * 80)
        
        # 1. All PE Firms
        print("\n📊 All PE Firms:")
        firms = pq.get_all_pe_firms()
        for firm in firms:
            print(f"  • {firm.name}: {firm.total_companies} companies (Current: {firm.current_portfolio_count}, Exited: {firm.exited_portfolio_count})")
        
        # 2. Vista Equity Partners - Current Portfolio
        print("\n📊 Vista Equity Partners - Current Portfolio (first 10):")
        vista_current = pq.get_current_portfolio("Vista Equity Partners")
        for company in vista_current[:10]:
            print(f"  • {company.name} | {company.sector} | {company.investment_year}")
        print(f"  ... ({len(vista_current)} total current companies)")
        
        # 3. TA Associates - Status Breakdown
        print("\n📊 TA Associates - Status Breakdown:")
        ta_status = pq.get_status_breakdown("TA Associates")
        for status, count in ta_status[:10]:
            status_display = status[:60] + "..." if len(status) > 60 else status
            print(f"  • {status_display}: {count}")
        
        # 4. Search by name
        print("\n🔍 Search for companies with 'health' in name:")
        health_companies = pq.search_companies("health")
        for company in health_companies[:5]:
            print(f"  • {company.name} | {company.pe_firm.name} | {company.status}")
        print(f"  ... ({len(health_companies)} total matches)")
        
        # 5. Technology sector companies
        print("\n💻 Technology Sector Companies (first 10):")
        tech_companies = pq.get_companies_by_sector("Technology")
        for company in tech_companies[:10]:
            print(f"  • {company.name} | {company.pe_firm.name} | {company.investment_year}")
        print(f"  ... ({len(tech_companies)} total tech companies)")
        
        # 6. Investment Timeline for TA Associates
        print("\n📅 TA Associates - Investment Timeline (Recent Years):")
        ta_timeline = pq.get_investment_timeline("TA Associates")
        for year, count in ta_timeline[-10:]:  # Last 10 years
            print(f"  • {year}: {count} companies")
        
        print("\n" + "=" * 80)


if __name__ == "__main__":
    demo_queries()
