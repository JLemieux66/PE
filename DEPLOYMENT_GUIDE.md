# PE Portfolio App - Deployment Guide

## 🎉 Your App is Ready to Deploy!

### What's Included
✅ **Backend API** (FastAPI) - `backend/api_v2.py`  
✅ **SQLite Database** - `pe_portfolio_v2.db` (3.4 MB, 3,303 companies)  
✅ **ML Revenue Model** - `scripts/sec_edgar/sec_revenue_model.pkl` (trained on 864 public companies)  
✅ **React Frontend** - `frontend-react/` (Vite + TypeScript + Tailwind)  
✅ **Deployment Config** - `Procfile` and `railway.json` configured

---

## 🚀 Option 1: Deploy to Railway (Recommended)

### Step 1: Install Railway CLI
```powershell
npm install -g @railway/cli
```

### Step 2: Login to Railway
```powershell
railway login
```

### Step 3: Initialize Railway Project
```powershell
railway init
```
- Choose "Empty Project"
- Name it: `pe-portfolio-app`

### Step 4: Link and Deploy
```powershell
# Link to the Railway project
railway link

# Deploy the app
railway up
```

### Step 5: Add Environment Variables (Optional)
```powershell
railway variables set PORT=8000
```

### Step 6: Get Your URL
```powershell
railway domain
```

Your app will be live at: `https://your-app-name.up.railway.app`

---

## 🌐 Option 2: Deploy to Render

### Step 1: Create New Web Service
1. Go to https://dashboard.render.com
2. Click "New +" → "Web Service"
3. Connect your GitHub repo: `jlemieux66/PE`

### Step 2: Configure Build Settings
- **Name**: `pe-portfolio-app`
- **Region**: Choose closest to you
- **Branch**: `main`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn backend.api_v2:app --host 0.0.0.0 --port $PORT`

### Step 3: Environment Variables
- `PYTHON_VERSION`: `3.11.0`
- `PORT`: `10000` (Render default)

### Step 4: Deploy
Click "Create Web Service" - your app will deploy automatically!

---

## 🔧 Option 3: Deploy to Heroku

### Step 1: Install Heroku CLI
Download from: https://devcenter.heroku.com/articles/heroku-cli

### Step 2: Login and Create App
```powershell
heroku login
heroku create pe-portfolio-app
```

### Step 3: Deploy
```powershell
git push heroku main
```

### Step 4: Open Your App
```powershell
heroku open
```

---

## 🖥️ Option 4: Test Locally First

### Backend Only
```powershell
pipenv run uvicorn backend.api_v2:app --reload --port 8000
```
Visit: http://localhost:8000/docs

### Frontend + Backend (Full Stack)
Terminal 1 - Backend:
```powershell
pipenv run uvicorn backend.api_v2:app --reload --port 8000
```

Terminal 2 - Frontend:
```powershell
cd frontend-react
npm install
npm run dev
```
Visit: http://localhost:3000

---

## 📊 What Your App Includes

### **3,303 Portfolio Companies**
- 2,600 with Crunchbase revenue data (78.7%)
- 703 with ML-predicted revenue
- All 3,303 have ML predictions

### **Revenue Predictions**
- **Model**: XGBoost with 21 features
- **Training Data**: 864 public companies (S&P 500 + Russell 2000)
- **Features**: Industry, location, company size, employee count
- **Accuracy**: 66% (industry-aware predictions)
- **Range**: $5.5M to $15B

### **API Endpoints**
- `GET /api/stats` - Dashboard statistics
- `GET /api/pe-firms` - List of PE firms
- `GET /api/investments` - Portfolio companies (filterable)
- `GET /api/companies/{id}` - Individual company details

### **Frontend Features**
- Company cards with dual revenue display:
  - **Revenue (CB)**: Crunchbase range
  - **Revenue (ML)**: Machine learning prediction (blue)
- Filters: PE firm, status, industry, search
- Real-time stats dashboard
- Responsive design (mobile-friendly)

---

## 🎯 Post-Deployment Checklist

### Test Your Deployed App
1. ✅ Visit `/api/docs` - Swagger API documentation should load
2. ✅ Visit `/api/stats` - Should return JSON with 3,303 companies
3. ✅ Check a company - Should have both `revenue_range` and `predicted_revenue`
4. ✅ Frontend loads without errors
5. ✅ Company cards display both CB and ML revenue values

### Expected Results
```json
{
  "id": 1,
  "name": "Applied Systems",
  "revenue_range": "$100M - $500M",
  "predicted_revenue": 5500000000,  // $5.5B in USD
  "employee_count": "5,001-10,000",
  "industry_category": "Technology & Software"
}
```

Frontend Display:
```
Applied Systems
--------------
Industry: Technology & Software
Employees: 5,001-10,000
Revenue (CB): $100M - $500M
Revenue (ML): $5.5B  ← Blue, ML prediction
```

---

## 🔥 Troubleshooting

### Backend won't start
- Check `requirements.txt` has all dependencies
- Verify Python 3.11+ is installed
- Check logs: `railway logs` or `heroku logs --tail`

### Database errors
- Database file `pe_portfolio_v2.db` must be in root directory
- Should be 3.4 MB (3,303 companies)
- Run locally first to test: `pipenv run python -c "from src.models.database_models_v2 import Company, create_database_engine; from sqlalchemy.orm import sessionmaker; engine = create_database_engine(); Session = sessionmaker(bind=engine); session = Session(); print(f'Companies: {session.query(Company).count()}')"`

### ML predictions not showing
- Check `scripts/sec_edgar/sec_revenue_model.pkl` exists (should be ~500KB)
- Verify `predicted_revenue` column in database
- Test: `pipenv run python -c "from src.models.database_models_v2 import Company, create_database_engine; from sqlalchemy.orm import sessionmaker; engine = create_database_engine(); Session = sessionmaker(bind=engine); session = Session(); c = session.query(Company).first(); print(f'{c.name}: ${c.predicted_revenue:,.0f}')"`

### Frontend shows codes instead of text
- Backend API should decode automatically
- Check `/api/investments` returns decoded values
- Verify `crunchbase_helpers.py` is imported correctly

---

## 📈 Next Steps

### Improve ML Model
```powershell
# Download more training data
pipenv run python scripts/sec_edgar/download_yahoo_finance.py --max 2000

# Retrain model
pipenv run python scripts/sec_edgar/train_sec_model.py yahoo_training_data.csv

# Regenerate predictions
pipenv run python run_predictions.py
```

### Update Database
```powershell
# Add more companies or refresh data
pipenv run python ingestion.py

# Update predictions after adding companies
pipenv run python run_predictions.py
```

---

## 🎉 Success!

Your PE portfolio app with ML revenue predictions is deployed and running!

**Features:**
- ✨ 3,303 companies with detailed data
- 🤖 ML-powered revenue predictions
- 📊 Interactive dashboard
- 🔍 Advanced filtering
- 📱 Mobile responsive

Built with: FastAPI + React + XGBoost + SQLite
