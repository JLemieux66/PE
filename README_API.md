# PE Portfolio API

REST API for accessing Private Equity portfolio company data.

## Quick Deploy to Railway (Free)

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template)

1. Click "Deploy on Railway" or go to [railway.app](https://railway.app)
2. Connect your GitHub repository
3. Railway auto-detects and deploys
4. Get your API URL: `https://your-app.railway.app`

## API Documentation

Once deployed, visit:
- Interactive docs: `https://your-app.railway.app/docs`
- API reference: `https://your-app.railway.app/redoc`

## Endpoints

- `GET /api/companies` - Get all companies (with filters)
- `GET /api/companies/{id}` - Get specific company
- `GET /api/firms` - Get all PE firms
- `GET /api/firms/{name}/companies` - Companies by PE firm
- `GET /api/sectors` - All sectors
- `GET /api/statuses` - All statuses
- `GET /api/stats` - Portfolio statistics

## Local Development

```bash
# Install dependencies
pipenv install

# Run API
pipenv run uvicorn api:app --reload

# Visit http://localhost:8000/docs
```

## Database

Currently uses SQLite (pe_portfolio.db). To upgrade to PostgreSQL:

1. Add PostgreSQL database in Railway
2. Railway auto-sets `DATABASE_URL`
3. Re-run import: `pipenv run python import_to_database.py`
