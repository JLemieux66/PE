# PE Portfolio API - Usage Examples

Base URL: `http://127.0.0.1:8000` (local) or your deployed Railway URL

## API Documentation
Interactive docs: `http://127.0.0.1:8000/docs`

---

## 📋 All Available Endpoints

### 1. **Get All Companies** (with filters)
```bash
GET /api/companies
```

**Query Parameters:**
- `pe_firm` - Filter by PE firm name (partial match)
- `status` - Filter by status (Active, Exit)
- `sector` - Filter by sector (partial match)
- `search` - Search in company name or description
- `limit` - Max results (default: 100, max: 1000)
- `offset` - Pagination offset (default: 0)

**PowerShell Examples:**

```powershell
# Get all companies (first 100)
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/companies" | ConvertTo-Json -Depth 5

# Get Vista Equity Partners companies
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/companies?pe_firm=Vista&limit=50"

# Get only Active companies
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/companies?status=Active&limit=100"

# Search for specific company
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/companies?search=Airbnb"

# Combine filters
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/companies?pe_firm=Andreessen&status=Active&limit=200"

# Get with pagination
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/companies?limit=50&offset=0"  # First page
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/companies?limit=50&offset=50" # Second page
```

**Response Fields:**
```json
{
  "id": 442,
  "name": "Airbnb",
  "pe_firm": "Andreessen Horowitz",
  "sector": "Consumer",
  "status": "Exit",
  "investment_year": "2008",
  "headquarters": "San Francisco, California",
  "website": "",
  "description": "...",
  "exit_info": "IPO: ABNB",
  
  // Swarm enrichment fields:
  "swarm_industry": "Hospitality",
  "size_class": "10001+",
  "total_funding_usd": 6400000000,
  "last_round_type": "secondary market",
  "last_round_amount_usd": 0,
  "market_cap": 90234000000,
  "ipo_date": "2020-12-10T00:00:00Z",
  "ipo_year": 2020,
  "ownership_status": "active",
  "ownership_status_detailed": "Publicly Held",
  "is_public": true,
  "is_acquired": false,
  "is_exited_swarm": true,
  "customer_types": "B2C",
  "stock_exchange": "NAS",
  "summary": "Airbnb is a community based on connection and belonging."
}
```

---

### 2. **Get Specific Company by ID**
```bash
GET /api/companies/{company_id}
```

**PowerShell Example:**
```powershell
# Get company with ID 442
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/companies/442"
```

---

### 3. **Get All PE Firms**
```bash
GET /api/firms
```

**PowerShell Example:**
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/firms"
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "Vista Equity Partners",
    "total_companies": 145,
    "current_portfolio_count": 92,
    "exited_portfolio_count": 53,
    "last_scraped": "2024-10-23 10:30:00"
  },
  ...
]
```

---

### 4. **Get Companies for Specific PE Firm**
```bash
GET /api/firms/{firm_name}/companies
```

**PowerShell Examples:**
```powershell
# Get all Vista companies
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/firms/Vista/companies?limit=200"

# Get all TA Associates companies
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/firms/TA Associates/companies?limit=300"

# Get all a16z companies
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/firms/Andreessen/companies?limit=800"
```

---

### 5. **Get All Industries** (NEW!)
```bash
GET /api/industries
```

**PowerShell Example:**
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/industries"
```

**Response:**
```json
{
  "industries": [
    "Accounting",
    "Aerospace",
    "Agriculture",
    "Artificial Intelligence (AI)",
    "Automotive",
    ...
  ]
}
```

---

### 6. **Get All Sectors**
```bash
GET /api/sectors
```

**PowerShell Example:**
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/sectors"
```

---

### 7. **Get All Statuses**
```bash
GET /api/statuses
```

**PowerShell Example:**
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/statuses"
```

**Response:**
```json
{
  "statuses": ["Active", "Exit"]
}
```

---

### 8. **Get Portfolio Statistics**
```bash
GET /api/stats
```

**PowerShell Example:**
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/stats"
```

**Response:**
```json
{
  "total_companies": 1223,
  "total_pe_firms": 3,
  "current_companies": 855,
  "exited_companies": 368
}
```

---

## 🔍 Advanced Query Examples

### Find Public Companies Only
```powershell
# Get all companies from API, then filter by is_public
$companies = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/companies?limit=1000"
$public = $companies | Where-Object { $_.is_public -eq $true }
$public | Select-Object name, pe_firm, market_cap, stock_exchange | Format-Table
```

### Find Companies with High Market Cap
```powershell
$companies = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/companies?limit=1000"
$bigCap = $companies | Where-Object { $_.market_cap -gt 1000000000 } | Sort-Object market_cap -Descending
$bigCap | Select-Object name, market_cap, ipo_year | Format-Table
```

### Find Companies by Industry
```powershell
# Find all AI companies
$companies = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/companies?search=AI&limit=500"
$companies | Where-Object { $_.swarm_industry -like "*AI*" } | Select-Object name, swarm_industry, pe_firm
```

### Get IPO Companies
```powershell
$companies = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/companies?limit=1000"
$ipos = $companies | Where-Object { $_.ipo_year -ne $null } | Sort-Object ipo_year -Descending
$ipos | Select-Object name, ipo_year, stock_exchange, market_cap | Format-Table
```

### Export to CSV
```powershell
# Get all Vista companies and export to CSV
$companies = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/companies?pe_firm=Vista&limit=200"
$companies | Export-Csv -Path "vista_companies.csv" -NoTypeInformation
```

---

## 🌐 Using from Other Languages

### Python Example:
```python
import requests

# Get all companies
response = requests.get("http://127.0.0.1:8000/api/companies", params={
    "pe_firm": "Vista",
    "status": "Active",
    "limit": 100
})
companies = response.json()

for company in companies:
    print(f"{company['name']} - {company['swarm_industry']} - ${company['market_cap']:,}")
```

### JavaScript/Node.js Example:
```javascript
const axios = require('axios');

async function getCompanies() {
    const response = await axios.get('http://127.0.0.1:8000/api/companies', {
        params: {
            pe_firm: 'Andreessen',
            limit: 500
        }
    });
    
    console.log(response.data);
}
```

### cURL Example:
```bash
# Get all companies
curl "http://127.0.0.1:8000/api/companies?limit=100"

# Search for specific company
curl "http://127.0.0.1:8000/api/companies?search=Figma"

# Get company by ID
curl "http://127.0.0.1:8000/api/companies/442"
```

---

## 📊 Data Fields Reference

### Standard Fields:
- `id` - Unique company identifier
- `name` - Company name
- `pe_firm` - PE firm name
- `sector` - Company sector
- `status` - Active or Exit
- `investment_year` - Year founded/invested
- `headquarters` - HQ location
- `website` - Company website
- `description` - Company description
- `exit_info` - Exit details if applicable

### Swarm Enrichment Fields:
- `swarm_industry` - Industry category
- `size_class` - Employee size range
- `total_funding_usd` - Total funding raised (USD)
- `last_round_type` - Type of last funding round
- `last_round_amount_usd` - Amount of last round (USD)
- `market_cap` - Market capitalization (USD)
- `ipo_date` - IPO date
- `ipo_year` - IPO year
- `ownership_status` - Current ownership status
- `ownership_status_detailed` - Detailed ownership info
- `is_public` - Boolean: Is publicly traded
- `is_acquired` - Boolean: Has been acquired
- `is_exited_swarm` - Boolean: Has exited
- `customer_types` - B2B, B2C, etc.
- `stock_exchange` - Stock exchange ticker
- `summary` - Company summary

---

## 🚀 Rate Limits & Performance

- Default limit: 100 companies per request
- Maximum limit: 1000 companies per request
- No authentication required (local/development)
- Use pagination for large datasets (`limit` + `offset`)

---

## 🔗 Interactive API Documentation

Visit: `http://127.0.0.1:8000/docs`

This provides:
- Interactive API testing
- Full schema documentation
- Example requests/responses
- Try out all endpoints in your browser
