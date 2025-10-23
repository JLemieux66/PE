"""
Crunchbase API helper functions
"""
import requests

CRUNCHBASE_API_KEY = "7631ec690653f0055ea43a1169f12787"
CRUNCHBASE_BASE_URL = "https://api.crunchbase.com/v4/data"

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
            "field_ids": "location_identifiers,founded_on,short_description"
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
            "description": properties.get("short_description", "")
        }
    except:
        return {}
