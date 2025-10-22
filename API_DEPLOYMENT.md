# Deployment Guide: FastAPI Backend

## 🚀 Quick Start - Test Locally

```bash
# Run the API locally
pipenv run uvicorn api:app --reload

# Access at: http://localhost:8000
# API docs at: http://localhost:8000/docs (interactive Swagger UI)
```

## 📡 API Endpoints

### Base URL (local): `http://localhost:8000`

#### 1. **Get All Companies** (with filters)
```
GET /api/companies
GET /api/companies?pe_firm=Vista
GET /api/companies?status=current
GET /api/companies?sector=healthcare
GET /api/companies?search=software&limit=50
```

#### 2. **Get Specific Company**
```
GET /api/companies/{id}
```

#### 3. **Get All PE Firms**
```
GET /api/firms
```

#### 4. **Get Companies by PE Firm**
```
GET /api/firms/Vista/companies
GET /api/firms/TA Associates/companies
```

#### 5. **Get All Sectors**
```
GET /api/sectors
```

#### 6. **Get All Statuses**
```
GET /api/statuses
```

#### 7. **Get Statistics**
```
GET /api/stats
```

## 🌐 Deploy to Railway (Free)

### Prerequisites
1. GitHub account
2. Railway account: https://railway.app (free $5/month credit)

### Steps:

1. **Push to GitHub**
```bash
git add .
git commit -m "Add FastAPI backend"
git push origin main
```

2. **Deploy on Railway**
- Go to https://railway.app
- Click "New Project" → "Deploy from GitHub repo"
- Select your repository
- Railway will auto-detect Python and deploy

3. **Add Database (Optional - for PostgreSQL)**
- In Railway project, click "New" → "Database" → "PostgreSQL"
- Railway auto-creates `DATABASE_URL` environment variable
- Your app will use it automatically!

4. **Get Your API URL**
- Railway gives you: `https://your-app.railway.app`
- Test: `https://your-app.railway.app/api/companies`

## 🔄 Alternative: Deploy to Render (Free)

1. Go to https://render.com
2. Click "New" → "Web Service"
3. Connect GitHub repo
4. Settings:
   - **Build Command**: `pip install -r requirements.txt` (generate from Pipfile)
   - **Start Command**: `uvicorn api:app --host 0.0.0.0 --port $PORT`
5. Click "Create Web Service"

## 📦 Generate requirements.txt for Deployment

```bash
pipenv requirements > requirements.txt
```

## 🗄️ Database Options (All Free Tiers)

### Option 1: Keep SQLite (Simplest)
- SQLite file included in deployment
- Works for read-heavy workloads
- No extra setup needed

### Option 2: PostgreSQL on Railway
- Free PostgreSQL database included
- Automatic `DATABASE_URL` setup
- Better for production

### Option 3: Supabase (Free PostgreSQL)
- Go to https://supabase.com
- Create free project
- Get connection string
- Set as `DATABASE_URL` in Railway/Render

### Option 4: Neon (Free Serverless PostgreSQL)
- Go to https://neon.tech
- Create free project
- Copy connection string
- Set as `DATABASE_URL`

## 🧪 Test Your Deployed API

```bash
# Replace with your Railway/Render URL
curl https://your-app.railway.app/api/companies

# Or in browser:
https://your-app.railway.app/docs  # Interactive API documentation
```

## 📊 Example API Calls

### Python
```python
import requests

# Get all current Vista companies
response = requests.get(
    "https://your-app.railway.app/api/companies",
    params={"pe_firm": "Vista", "status": "current"}
)
companies = response.json()
```

### JavaScript
```javascript
// Get all companies in healthcare sector
fetch('https://your-app.railway.app/api/companies?sector=healthcare')
  .then(response => response.json())
  .then(data => console.log(data));
```

### cURL
```bash
# Get portfolio statistics
curl https://your-app.railway.app/api/stats
```

## 🔐 Environment Variables

If using PostgreSQL, set in Railway/Render:
```
DATABASE_URL=postgresql://user:password@host:port/database
```

## 📈 Cost Breakdown (FREE!)

- **Railway**: $5/month free credit (enough for small API)
- **Render**: 750 hours/month free
- **Database**: 
  - SQLite: Free (included)
  - Railway PostgreSQL: Free tier included
  - Supabase: 500MB free
  - Neon: 3GB free

## 🔄 Auto-Deploy

Both Railway and Render support auto-deploy:
- Push to GitHub → Automatic deployment
- No manual steps needed

## 🎯 Next Steps

1. Test locally: `pipenv run uvicorn api:app --reload`
2. Visit http://localhost:8000/docs for interactive API testing
3. Generate requirements.txt: `pipenv requirements > requirements.txt`
4. Push to GitHub
5. Deploy to Railway or Render
6. Share your API URL!

## 🛠️ Troubleshooting

**Port Issues**: Railway/Render use `$PORT` environment variable
**Database Connection**: Check `DATABASE_URL` is set correctly
**CORS Errors**: Frontend domain needs to be added to `allow_origins`

## 📚 API Documentation

Once deployed, visit:
- **Swagger UI**: `https://your-app.railway.app/docs`
- **ReDoc**: `https://your-app.railway.app/redoc`
