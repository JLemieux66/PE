"""
Add initial tags to companies based on existing data
"""
from database_models import get_session, PortfolioCompany, CompanyTag

# Technology keywords for tagging
TECH_KEYWORDS = {
    'SaaS': ['saas', 'software as a service', 'cloud software', 'subscription software'],
    'AI/ML': ['artificial intelligence', 'ai', 'machine learning', 'ml', 'deep learning', 'neural network'],
    'Mobile': ['mobile app', 'mobile application', 'ios', 'android', 'mobile platform'],
    'Cloud': ['cloud computing', 'cloud platform', 'cloud infrastructure', 'aws', 'azure', 'gcp'],
    'Blockchain': ['blockchain', 'cryptocurrency', 'crypto', 'web3', 'defi', 'nft'],
    'IoT': ['iot', 'internet of things', 'connected devices', 'smart devices'],
    'Cybersecurity': ['cybersecurity', 'security', 'infosec', 'data protection', 'encryption'],
    'DevOps': ['devops', 'ci/cd', 'continuous integration', 'infrastructure as code'],
}

BUSINESS_MODEL_KEYWORDS = {
    'B2B': ['b2b', 'business to business', 'enterprise software', 'business software'],
    'B2C': ['b2c', 'business to consumer', 'consumer', 'direct to consumer', 'd2c'],
    'Marketplace': ['marketplace', 'platform', 'two-sided', 'peer-to-peer', 'p2p'],
    'Subscription': ['subscription', 'recurring revenue', 'saas'],
    'E-commerce': ['ecommerce', 'e-commerce', 'online retail', 'online shopping'],
}

MARKET_FOCUS_KEYWORDS = {
    'Enterprise': ['enterprise', 'large business', 'fortune 500'],
    'SMB': ['smb', 'small business', 'small and medium'],
    'Developer Tools': ['developer', 'api', 'sdk', 'development platform', 'coding'],
    'Healthcare': ['healthcare', 'health', 'medical', 'hospital', 'patient'],
    'Financial Services': ['fintech', 'financial', 'banking', 'payments', 'insurance'],
}

def extract_tags(company):
    """Extract tags from company data"""
    tags = []
    
    # Combine searchable text
    search_text = ' '.join([
        company.name or '',
        company.description or '',
        company.summary or '',
        company.swarm_industry or '',
        company.industry_category or '',
        company.sector or ''
    ]).lower()
    
    # Technology tags
    for tag_value, keywords in TECH_KEYWORDS.items():
        if any(keyword in search_text for keyword in keywords):
            tags.append(('technology', tag_value))
    
    # Business model tags
    for tag_value, keywords in BUSINESS_MODEL_KEYWORDS.items():
        if any(keyword in search_text for keyword in keywords):
            tags.append(('business_model', tag_value))
    
    # Market focus tags
    for tag_value, keywords in MARKET_FOCUS_KEYWORDS.items():
        if any(keyword in search_text for keyword in keywords):
            tags.append(('market_focus', tag_value))
    
    # Stage tags based on data
    if company.is_public:
        tags.append(('stage', 'Public'))
    
    if company.revenue_tier == 'Unicorn':
        tags.append(('stage', 'Unicorn'))
    
    if company.ipo_date and not company.is_public:
        tags.append(('stage', 'IPO Ready'))
    
    # Remove duplicates
    return list(set(tags))

def setup_initial_tags():
    """Add initial tags to all companies"""
    print("🏷️  Adding initial tags to companies...")
    
    session = get_session()
    
    try:
        # Clear existing tags
        session.query(CompanyTag).delete()
        session.commit()
        print("  Cleared existing tags")
        
        companies = session.query(PortfolioCompany).all()
        
        print(f"📊 Processing {len(companies)} companies...")
        
        total_tags = 0
        companies_with_tags = 0
        
        for i, company in enumerate(companies, 1):
            tags = extract_tags(company)
            
            if tags:
                companies_with_tags += 1
                for tag_category, tag_value in tags:
                    tag = CompanyTag(
                        company_id=company.id,
                        tag_category=tag_category,
                        tag_value=tag_value
                    )
                    session.add(tag)
                    total_tags += 1
            
            if i % 100 == 0:
                session.commit()
                print(f"  Processed {i}/{len(companies)} companies, added {total_tags} tags...")
        
        session.commit()
        
        print(f"\n✅ Tagging complete!")
        print(f"  Companies tagged: {companies_with_tags}/{len(companies)}")
        print(f"  Total tags added: {total_tags}")
        print(f"  Average tags per company: {total_tags/companies_with_tags:.1f}")
        
        # Show tag distribution
        from sqlalchemy import func
        
        print("\n📊 Technology Tags:")
        tech_tags = session.query(
            CompanyTag.tag_value,
            func.count(CompanyTag.id)
        ).filter(
            CompanyTag.tag_category == 'technology'
        ).group_by(CompanyTag.tag_value).order_by(
            func.count(CompanyTag.id).desc()
        ).all()
        
        for tag, count in tech_tags:
            print(f"  {tag:20} {count:4} companies")
        
        print("\n📊 Business Model Tags:")
        biz_tags = session.query(
            CompanyTag.tag_value,
            func.count(CompanyTag.id)
        ).filter(
            CompanyTag.tag_category == 'business_model'
        ).group_by(CompanyTag.tag_value).order_by(
            func.count(CompanyTag.id).desc()
        ).all()
        
        for tag, count in biz_tags:
            print(f"  {tag:20} {count:4} companies")
        
        print("\n📊 Market Focus Tags:")
        market_tags = session.query(
            CompanyTag.tag_value,
            func.count(CompanyTag.id)
        ).filter(
            CompanyTag.tag_category == 'market_focus'
        ).group_by(CompanyTag.tag_value).order_by(
            func.count(CompanyTag.id).desc()
        ).all()
        
        for tag, count in market_tags:
            print(f"  {tag:20} {count:4} companies")
        
        print("\n📊 Stage Tags:")
        stage_tags = session.query(
            CompanyTag.tag_value,
            func.count(CompanyTag.id)
        ).filter(
            CompanyTag.tag_category == 'stage'
        ).group_by(CompanyTag.tag_value).order_by(
            func.count(CompanyTag.id).desc()
        ).all()
        
        for tag, count in stage_tags:
            print(f"  {tag:20} {count:4} companies")
        
    finally:
        session.close()

if __name__ == "__main__":
    setup_initial_tags()
