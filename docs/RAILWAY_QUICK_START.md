# Railway Deployment - Quick Start

## Your Railway URL
Your frontend is already configured to use:
```
https://web-production-c4223.up.railway.app/query
```

## Deploy to Railway (If Not Already Deployed)

### Step 1: Deploy from GitHub
1. Go to: https://railway.app
2. Sign up/login with GitHub
3. Click **"New Project"**
4. Select **"Deploy from GitHub repo"**
5. Choose: `mperelman/Thunderclap`
6. Railway auto-detects Python and starts deploying

### Step 2: Set Environment Variable
1. Click on your project in Railway
2. Go to **Variables** tab
3. Add:
   - **Key**: `GEMINI_API_KEY`
   - **Value**: `AIzaSyBaj9wvbB3n6ZjvI89fFACl4SQgUfTaC4s` (or one of your 6 keys)
4. Click **Save** - Railway will redeploy automatically

### Step 3: Get/Verify Your Railway URL
1. Click on your service
2. Go to **Settings** → **Networking**
3. If no domain exists, click **"Generate Domain"**
4. Copy your Railway URL (should be like `https://web-production-c4223.up.railway.app`)

### Step 4: Upload Data Folder (IMPORTANT)
Railway needs your `data/` folder with the database and indices.

**Option A: Rebuild on Railway (Easiest)**
1. In Railway, go to your service
2. Click **"Deployments"** → **"View Logs"** → **"Shell"** button
3. Run:
   ```bash
   python build_index.py
   ```
4. This rebuilds the index from `source_documents/`

**Option B: Upload via Railway CLI**
1. Install Railway CLI: `npm install -g @railway/cli`
2. Login: `railway login`
3. Link project: `railway link` (select your Thunderclap project)
4. Upload data folder (see `docs/deployment/RAILWAY_DATA_UPLOAD_STEPS.md`)

### Step 5: Test
1. Visit: `https://web-production-c4223.up.railway.app/health`
   - Should return: `{"status":"ok"}`
2. Visit: `https://mperelman.github.io/Thunderclap/`
   - Should automatically use the Railway backend
3. Try a query - it should work!

## Troubleshooting

**If Railway returns 502/500:**
- Check Railway logs for errors
- Verify `GEMINI_API_KEY` is set in Variables
- Check if `data/` folder exists (rebuild index if needed)

**If queries fail:**
- Check Railway logs: Railway dashboard → Service → View Logs
- Look for API key errors or database errors
- Verify the API key is valid and has quota remaining

## Your Public Link
Once deployed, your public link is:
```
https://mperelman.github.io/Thunderclap/
```

The frontend automatically uses the Railway backend when accessed from GitHub Pages.
