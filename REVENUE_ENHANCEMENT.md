# Revenue & Employee Data Enhancement

## Summary

Added Crunchbase revenue range and employee count data to the PE Portfolio system.

## Changes Made

### 1. Database Schema
**File:** `database_models.py`
- Added `revenue_range` column (VARCHAR 50, indexed)
- Added `employee_count` column (VARCHAR 50)

### 2. Crunchbase API Helper
**File:** `crunchbase_helpers.py`
- Updated `get_company_details_crunchbase()` to fetch revenue_range and num_employees_enum
- Added `decode_revenue_range()` function to convert codes to readable strings
- Added `decode_employee_count()` function to convert codes to readable strings

**Revenue Range Mappings:**
- `r_00000000` → Less than $1M
- `r_00001000` → $1M - $10M
- `r_00010000` → $10M - $50M
- `r_00050000` → $50M - $100M
- `r_00100000` → $100M - $500M
- `r_00500000` → $500M - $1B
- `r_01000000` → $1B - $10B
- `r_10000000` → $10B+

**Employee Count Mappings:**
- `c_00001_00010` → 1-10
- `c_00011_00050` → 11-50
- `c_00051_00100` → 51-100
- `c_00101_00250` → 101-250
- `c_00251_00500` → 251-500
- `c_00501_01000` → 501-1,000
- `c_01001_05000` → 1,001-5,000
- `c_05001_10000` → 5,001-10,000
- `c_10001_max` → 10,001+

### 3. API Enhancement
**File:** `api.py`
- Added `revenue_range` and `employee_count` to CompanyResponse model
- Now available in all API endpoints

### 4. Dashboard Enhancement
**File:** `portfolio_app.py`
- Added revenue and employee data to `load_all_companies()` function
- Updated Company Profile section to display decoded revenue ranges and employee counts
- Shows readable format (e.g., "$10M - $50M" instead of "r_00010000")

### 5. Migration Scripts
**Created:**
- `migrate_add_revenue_columns.py` - Adds columns to existing database
- `add_revenue_data.py` - Enriches all 1,223 companies with revenue/employee data from Crunchbase
- `test_revenue.py` - Tests revenue/employee data fetching

## API Usage

### Get companies with revenue data:
```bash
curl "https://web-production-2de8b.up.railway.app/api/companies?limit=10"
```

Response now includes:
```json
{
  "id": 1,
  "name": "Accelya",
  "revenue_range": "r_00050000",
  "employee_count": "c_01001_05000",
  ...
}
```

### Filter by PE firm and get revenue data:
```bash
curl "https://web-production-2de8b.up.railway.app/api/companies?pe_firm=Vista%20Equity%20Partners&status=Active&limit=100"
```

## Dashboard Features

### Company Profile Page
Now displays:
- **Revenue Range:** Decoded human-readable format (e.g., "$50M - $100M")
- **Employee Count:** Decoded human-readable format (e.g., "1,001-5,000")
- Located in "Company Size & Revenue" section

## Data Quality

Based on enrichment progress (first 57 companies):
- ✅ High coverage - Most companies have revenue data
- ✅ High coverage - Most companies have employee count data
- ⚠️  Some companies return "N/A" when data not available in Crunchbase

## Next Steps

1. ✅ Database migration complete
2. 🔄 Data enrichment in progress (57/1,223 companies completed)
3. ⏳ Once complete, commit changes to GitHub
4. ⏳ Deploy to Railway (API will auto-deploy)
5. ⏳ Update Streamlit dashboard

## Files Modified
- `database_models.py`
- `crunchbase_helpers.py`
- `api.py`
- `portfolio_app.py`

## Files Created
- `migrate_add_revenue_columns.py`
- `add_revenue_data.py`
- `test_revenue.py`

## Testing

Run tests:
```bash
pipenv run python test_revenue.py
```

Expected output:
```
Testing: Airbnb
Revenue Range: $10B+
Employee Count: 5,001-10,000
```
