"""
Parse headquarters field and populate country, state_region, and city columns
"""
from database_models import get_session, PortfolioCompany
from sqlalchemy import func

# US states mapping
US_STATES = {
    'Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado', 'Connecticut',
    'Delaware', 'Florida', 'Georgia', 'Hawaii', 'Idaho', 'Illinois', 'Indiana', 'Iowa',
    'Kansas', 'Kentucky', 'Louisiana', 'Maine', 'Maryland', 'Massachusetts', 'Michigan',
    'Minnesota', 'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada', 'New Hampshire',
    'New Jersey', 'New Mexico', 'New York', 'North Carolina', 'North Dakota', 'Ohio',
    'Oklahoma', 'Oregon', 'Pennsylvania', 'Rhode Island', 'South Carolina', 'South Dakota',
    'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington', 'West Virginia',
    'Wisconsin', 'Wyoming', 'District of Columbia',
    # Abbreviations
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN',
    'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV',
    'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN',
    'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC'
}

CANADIAN_PROVINCES = {
    'Alberta', 'British Columbia', 'Manitoba', 'New Brunswick', 'Newfoundland and Labrador',
    'Northwest Territories', 'Nova Scotia', 'Nunavut', 'Ontario', 'Prince Edward Island',
    'Quebec', 'Saskatchewan', 'Yukon',
    'AB', 'BC', 'MB', 'NB', 'NL', 'NT', 'NS', 'NU', 'ON', 'PE', 'QC', 'SK', 'YT'
}

# Country aliases
UK_NAMES = {'England', 'Scotland', 'Wales', 'Northern Ireland', 'United Kingdom', 'UK'}

def parse_location(headquarters):
    """Parse headquarters string into city, state_region, country"""
    if not headquarters or headquarters.strip() == '':
        return None, None, None
    
    parts = [p.strip() for p in headquarters.split(',')]
    
    if len(parts) == 1:
        # Just city or country
        return parts[0], None, None
    
    elif len(parts) == 2:
        city, region = parts
        
        # Check if US state
        if region in US_STATES:
            return city, region, 'United States'
        
        # Check if Canadian province
        elif region in CANADIAN_PROVINCES:
            return city, region, 'Canada'
        
        # Check if UK
        elif region in UK_NAMES:
            return city, region, 'United Kingdom'
        
        # Otherwise, region is the country
        else:
            return city, None, region
    
    elif len(parts) >= 3:
        # Format: City, State, Country
        city = parts[0]
        state_region = parts[1] if len(parts) > 2 else None
        country_part = parts[-1]
        
        # Determine country
        if state_region and state_region in US_STATES:
            country = 'United States'
        elif state_region and state_region in CANADIAN_PROVINCES:
            country = 'Canada'
        elif country_part in UK_NAMES:
            country = 'United Kingdom'
            state_region = parts[1] if len(parts) > 2 else None
        else:
            country = country_part
            state_region = parts[1] if len(parts) > 2 else None
        
        return city, state_region, country
    
    return None, None, None

def populate_geographic_fields():
    """Parse all headquarters and populate geographic fields"""
    print("🔄 Parsing geographic data from headquarters field...")
    
    session = get_session()
    
    try:
        # Get all companies with headquarters
        companies = session.query(PortfolioCompany).filter(
            PortfolioCompany.headquarters != None,
            PortfolioCompany.headquarters != ''
        ).all()
        
        print(f"📍 Processing {len(companies)} companies...")
        
        updated = 0
        for i, company in enumerate(companies, 1):
            city, state_region, country = parse_location(company.headquarters)
            
            company.city = city
            company.state_region = state_region
            company.country = country
            
            if i % 100 == 0:
                session.commit()
                print(f"  Processed {i}/{len(companies)} companies...")
                updated = i
        
        session.commit()
        print(f"✅ Successfully parsed {len(companies)} locations!")
        
        # Show statistics
        print("\n📊 Statistics:")
        country_counts = session.query(
            PortfolioCompany.country,
            func.count(PortfolioCompany.id)
        ).filter(
            PortfolioCompany.country != None
        ).group_by(PortfolioCompany.country).order_by(
            func.count(PortfolioCompany.id).desc()
        ).limit(10).all()
        
        print("\nTop 10 Countries:")
        for country, count in country_counts:
            print(f"  {country:30} {count:4} companies")
        
        state_counts = session.query(
            PortfolioCompany.state_region,
            func.count(PortfolioCompany.id)
        ).filter(
            PortfolioCompany.state_region != None,
            PortfolioCompany.country == 'United States'
        ).group_by(PortfolioCompany.state_region).order_by(
            func.count(PortfolioCompany.id).desc()
        ).limit(10).all()
        
        print("\nTop 10 US States:")
        for state, count in state_counts:
            print(f"  {state:30} {count:4} companies")
        
    finally:
        session.close()

if __name__ == "__main__":
    populate_geographic_fields()
