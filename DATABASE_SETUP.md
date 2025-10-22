# PostgreSQL Database Setup for PE Portfolio Companies

## Overview
This setup allows you to store and query portfolio company data from Vista Equity Partners and TA Associates in a PostgreSQL database.

## Prerequisites
1. PostgreSQL installed and running
2. Python packages installed: `psycopg2-binary`, `sqlalchemy` (already installed via Pipfile)

## Database Setup

### Option 1: Local PostgreSQL Setup

1. **Install PostgreSQL** (if not already installed):
   - Download from: https://www.postgresql.org/download/
   - Or use Docker: `docker run --name pe-postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres`

2. **Create Database**:
   ```bash
   # Connect to PostgreSQL
   psql -U postgres
   
   # Create database
   CREATE DATABASE pe_portfolio;
   
   # Exit
   \q
   ```

3. **Set Database URL** in `.env` file:
   ```
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/pe_portfolio
   ```
   Format: `postgresql://username:password@host:port/database_name`

### Option 2: Cloud PostgreSQL (Heroku, AWS RDS, etc.)

Set the `DATABASE_URL` in your `.env` file with your cloud provider's connection string.

## File Structure

```
📁 documentation-helper/
├── database_models.py          # SQLAlchemy models (PEFirm, PortfolioCompany)
├── import_to_database.py       # Import JSON data to PostgreSQL
├── query_database.py           # Query helper functions
├── vista_portfolio_with_status.json   # Vista data
├── ta_portfolio_complete.json         # TA Associates data
└── .env                        # Database credentials
```

## Database Schema

### Tables

#### `pe_firms`
- `id` (Primary Key)
- `name` (Unique, Indexed)
- `total_companies`
- `current_portfolio_count`
- `exited_portfolio_count`
- `last_scraped`
- `extraction_time_minutes`

#### `portfolio_companies`
- `id` (Primary Key)
- `pe_firm_id` (Foreign Key → pe_firms)
- `name` (Indexed)
- `description`
- `website`
- `sector` (Indexed)
- `headquarters`
- `status` (Indexed) - 'current', 'former', 'past', etc.
- `investment_year` (Indexed)
- `exit_info`
- `source_url`
- `sector_page`
- `data_area` (Vista specific)
- `data_fund` (Vista specific)
- `created_at`
- `updated_at`

### Indexes
- `idx_pe_firm_status` - Query by PE firm and status
- `idx_sector_status` - Query by sector and status
- `idx_investment_year` - Query by investment year

## Usage

### 1. Initialize Database and Import Data

```bash
pipenv run python import_to_database.py
```

This will:
- Create database tables
- Import Vista Equity Partners data (145 companies)
- Import TA Associates data (366 companies)
- Display statistics

### 2. Query Data

```bash
pipenv run python query_database.py
```

Example queries included:
- All PE firms
- Current portfolio companies
- Exited companies
- Search by name
- Filter by sector
- Investment timeline
- Status breakdown

### 3. Use Programmatically

```python
from query_database import PortfolioQuery

# Create query helper
with PortfolioQuery() as pq:
    # Get all Vista current companies
    vista_current = pq.get_current_portfolio("Vista Equity Partners")
    
    # Search for healthcare companies
    healthcare = pq.get_companies_by_sector("Healthcare")
    
    # Get companies invested in 2020
    companies_2020 = pq.get_companies_by_year("2020")
    
    # Search by name
    results = pq.search_companies("software")
```

## Common Queries

### Get all current portfolio companies for Vista
```python
from query_database import PortfolioQuery

with PortfolioQuery() as pq:
    companies = pq.get_current_portfolio("Vista Equity Partners")
    for company in companies:
        print(f"{company.name} | {company.sector} | {company.investment_year}")
```

### Get sector distribution
```python
with PortfolioQuery() as pq:
    sectors = pq.get_sector_distribution("TA Associates")
    for sector, count in sectors:
        print(f"{sector}: {count} companies")
```

### Advanced SQL queries
```python
from database_models import get_session, PortfolioCompany, PEFirm

session = get_session()

# Get all healthcare companies invested after 2020
companies = session.query(PortfolioCompany).filter(
    PortfolioCompany.sector.ilike('%healthcare%'),
    PortfolioCompany.investment_year >= '2020'
).all()
```

## Maintenance

### Re-import/Update Data
Simply run the import script again. It will update existing companies and add new ones:
```bash
pipenv run python import_to_database.py
```

### Backup Database
```bash
pg_dump -U postgres pe_portfolio > backup.sql
```

### Restore Database
```bash
psql -U postgres pe_portfolio < backup.sql
```

## Troubleshooting

### Connection Error
- Check PostgreSQL is running: `pg_isready`
- Verify DATABASE_URL in `.env` file
- Check firewall/port 5432 access

### Import Fails
- Check JSON files exist
- Verify database exists: `psql -U postgres -l`
- Check logs for specific error messages

### Performance Issues
- Indexes are already created for common queries
- For large datasets, consider adding more indexes
- Use `EXPLAIN ANALYZE` to optimize specific queries

## Next Steps

1. Create database: `CREATE DATABASE pe_portfolio;`
2. Set DATABASE_URL in `.env`
3. Run: `pipenv run python import_to_database.py`
4. Query: `pipenv run python query_database.py`
