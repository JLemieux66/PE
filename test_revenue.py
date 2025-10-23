"""Test revenue and employee data fetching"""
from crunchbase_helpers import (
    search_company_crunchbase,
    get_company_details_crunchbase,
    decode_revenue_range,
    decode_employee_count
)

# Test with a few companies
test_companies = ["Airbnb", "Stripe", "SpaceX"]

for company_name in test_companies:
    print(f"\n{'='*50}")
    print(f"Testing: {company_name}")
    print('='*50)
    
    results = search_company_crunchbase(company_name)
    
    if not results:
        print("❌ Not found in Crunchbase")
        continue
    
    entity_id = results[0]
    details = get_company_details_crunchbase(entity_id)
    
    if details:
        revenue_code = details.get("revenue_range", "")
        employee_code = details.get("employee_count", "")
        
        print(f"Revenue Range Code: {revenue_code}")
        print(f"Revenue Range: {decode_revenue_range(revenue_code)}")
        print(f"Employee Count Code: {employee_code}")
        print(f"Employee Count: {decode_employee_count(employee_code)}")
        print(f"Headquarters: {details.get('headquarters')}")
        print(f"Founded: {details.get('founded_year')}")
    else:
        print("❌ Failed to get details")
