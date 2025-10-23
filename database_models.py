"""
Database models for PE Portfolio Companies
"""
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Boolean,
    BigInteger,
    create_engine,
    Index,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime

Base = declarative_base()


class PEFirm(Base):
    """Private Equity Firm"""

    __tablename__ = "pe_firms"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    total_companies = Column(Integer)
    current_portfolio_count = Column(Integer)
    exited_portfolio_count = Column(Integer)
    last_scraped = Column(DateTime, default=datetime.utcnow)
    extraction_time_minutes = Column(Integer)

    # Relationship
    companies = relationship("PortfolioCompany", back_populates="pe_firm")

    def __repr__(self):
        return f"<PEFirm(name='{self.name}', total={self.total_companies})>"


class PortfolioCompany(Base):
    """Portfolio Company"""

    __tablename__ = "portfolio_companies"

    id = Column(Integer, primary_key=True)
    pe_firm_id = Column(Integer, ForeignKey("pe_firms.id"), nullable=False)
    name = Column(String(500), nullable=False, index=True)
    description = Column(Text)
    website = Column(String(500))
    sector = Column(String(500), index=True)
    headquarters = Column(String(500))
    status = Column(String(500), index=True)  # 'current', 'former', 'past', etc.
    investment_year = Column(String(50), index=True)
    exit_info = Column(Text)
    source_url = Column(String(500))
    sector_page = Column(String(255))
    data_area = Column(String(255))  # Vista specific
    data_fund = Column(String(255))  # Vista specific
    
    # Swarm API enrichment fields
    swarm_industry = Column(String(255), index=True)
    size_class = Column(String(50))
    total_funding_usd = Column(BigInteger)
    last_round_type = Column(String(100))
    last_round_amount_usd = Column(BigInteger)
    market_cap = Column(BigInteger)
    ipo_date = Column(String(50))
    ipo_year = Column(String(10), index=True)
    ownership_status = Column(String(100))
    ownership_status_detailed = Column(String(255))
    is_public = Column(Boolean, default=False, index=True)
    is_acquired = Column(Boolean, default=False)
    is_exited_swarm = Column(Boolean, default=False)
    customer_types = Column(String(100))
    stock_exchange = Column(String(50))
    summary = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    pe_firm = relationship("PEFirm", back_populates="companies")

    # Indexes for common queries
    __table_args__ = (
        Index("idx_pe_firm_status", "pe_firm_id", "status"),
        Index("idx_sector_status", "sector", "status"),
        Index("idx_investment_year", "investment_year"),
    )

    def __repr__(self):
        return f"<PortfolioCompany(name='{self.name}', sector='{self.sector}', status='{self.status}')>"


# Database connection function
def get_database_url():
    """
    Get database URL from environment or use default.
    Set DATABASE_URL environment variable for production.
    Format: postgresql://user:password@localhost:5432/pe_portfolio
    Or for SQLite: sqlite:///pe_portfolio.db
    """
    import os
    from dotenv import load_dotenv

    load_dotenv()

    # Default to SQLite if not set (no password needed)
    return os.getenv(
        "DATABASE_URL",
        "sqlite:///pe_portfolio.db"
    )


def create_database_engine():
    """Create and return database engine"""
    database_url = get_database_url()
    engine = create_engine(database_url, echo=False)
    return engine


def init_database():
    """Initialize database - create all tables"""
    engine = create_database_engine()
    Base.metadata.create_all(engine)
    print("✅ Database tables created successfully!")
    return engine


def get_session():
    """Get database session"""
    engine = create_database_engine()
    Session = sessionmaker(bind=engine)
    return Session()


if __name__ == "__main__":
    # Test database connection and create tables
    print("Creating database tables...")
    init_database()
