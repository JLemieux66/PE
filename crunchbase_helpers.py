"""
Crunchbase API helper functions
"""
import requests

CRUNCHBASE_API_KEY = "7631ec690653f0055ea43a1169f12787"
CRUNCHBASE_BASE_URL = "https://api.crunchbase.com/v4/data"

# Revenue range mappings
REVENUE_RANGES = {
    "r_00000000": "Less than $1M",
    "r_00001000": "$1M - $10M",
    "r_00010000": "$10M - $50M",
    "r_00050000": "$50M - $100M",
    "r_00100000": "$100M - $500M",
    "r_00500000": "$500M - $1B",
    "r_01000000": "$1B - $10B",
    "r_10000000": "$10B+"
}

# Employee count mappings
EMPLOYEE_RANGES = {
    "c_00001_00010": "1-10",
    "c_00011_00050": "11-50",
    "c_00051_00100": "51-100",
    "c_00101_00250": "101-250",
    "c_00251_00500": "251-500",
    "c_00501_01000": "501-1,000",
    "c_01001_05000": "1,001-5,000",
    "c_05001_10000": "5,001-10,000",
    "c_10001_max": "10,001+"
}

def decode_revenue_range(code):
    """Convert Crunchbase revenue code to readable string"""
    return REVENUE_RANGES.get(code, code if code else "N/A")

def decode_employee_count(code):
    """Convert Crunchbase employee code to readable string"""
    return EMPLOYEE_RANGES.get(code, code if code else "N/A")

def search_company_crunchbase(company_name):
    """Search for company in Crunchbase"""
    try:
        url = f"{CRUNCHBASE_BASE_URL}/autocompletes"
        params = {
            "query": company_name,
            "collection_ids": "organizations",
            "user_key": CRUNCHBASE_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code != 200:
            return []
        
        data = response.json()
        entities = data.get("entities", [])
        
        if entities:
            return [entities[0].get("identifier", {}).get("permalink", "")]
        
        return []
    except:
        return []

def get_company_details_crunchbase(entity_id):
    """Get company details from Crunchbase"""
    try:
        url = f"{CRUNCHBASE_BASE_URL}/entities/organizations/{entity_id}"
        params = {
            "user_key": CRUNCHBASE_API_KEY,
            "field_ids": "location_identifiers,founded_on,short_description,revenue_range,num_employees_enum"
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code != 200:
            return {}
        
        data = response.json()
        properties = data.get("properties", {})
        
        # Extract headquarters
        hq = ""
        location_ids = properties.get("location_identifiers", [])
        if location_ids and len(location_ids) > 0:
            city = next((loc.get("value") for loc in location_ids if loc.get("location_type") == "city"), "")
            region = next((loc.get("value") for loc in location_ids if loc.get("location_type") == "region"), "")
            
            if city and region:
                hq = f"{city}, {region}"
            elif city:
                hq = city
            elif region:
                hq = region
        
        # Extract founded year
        founded_on = properties.get("founded_on", {})
        founded_year = ""
        if founded_on and isinstance(founded_on, dict):
            value = founded_on.get("value", "")
            if value and len(value) >= 4:
                founded_year = value[:4]
        
        return {
            "headquarters": hq,
            "founded_year": founded_year,
            "description": properties.get("short_description", ""),
            "revenue_range": properties.get("revenue_range", ""),
            "employee_count": properties.get("num_employees_enum", "")
        }
    except:
        return {}
