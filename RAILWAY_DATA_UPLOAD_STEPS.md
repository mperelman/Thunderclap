# Upload Data Folder to Railway - Step by Step

## The Problem
Railway needs the `data/` folder (ChromaDB + indices) but it's excluded from Docker builds for security.

## Solution: Railway Volumes

### Step 1: Create a Volume in Railway

1. Go to: https://railway.app
2. Click on your **Thunderclap** project
3. Click on your **web** service
4. Click the **"Volumes"** tab (in the left sidebar)
5. Click **"+ New Volume"**
6. Name it: `data-volume`
7. Mount path: `/app/data`
8. Click **"Create"**

### Step 2: Upload Files via Railway CLI

**Install Railway CLI:**
```bash
npm install -g @railway/cli
```

**Login:**
```bash
railway login
```

**Link to your project:**
```bash
railway link
```
(Select your Thunderclap project when prompted)

**Upload the data folder:**
```bash
# From your project root directory
railway run --service web sh -c "mkdir -p /app/data/vectordb && echo 'Volume ready'"
```

Then copy files:
```bash
# Copy indices.json
railway run --service web sh -c "cat > /app/data/indices.json" < data/indices.json

# Copy endnotes.json (if exists)
railway run --service web sh -c "cat > /app/data/endnotes.json" < data/endnotes.json

# Copy vectordb folder (this is trickier - may need to zip first)
```

### Alternative: Use Railway's Web Terminal

1. In Railway dashboard → Your service → **"Deployments"** tab
2. Click on the latest deployment
3. Click **"View Logs"** → **"Shell"** button
4. In the terminal:
   ```bash
   mkdir -p /app/data/vectordb
   ```
5. Use Railway's file upload feature (if available) or continue with CLI method

### Step 3: Verify

After uploading, check Railway logs:
```bash
railway logs
```

Look for:
```
[OK] Connected to database (X indexed chunks)
```

If you see this, it's working!

## What Files to Upload

From your local `data/` folder, upload:
- ✅ `data/indices.json` (required)
- ✅ `data/vectordb/` (entire folder - required)
- ✅ `data/endnotes.json` (if exists)
- ✅ `data/chunk_to_endnotes.json` (if exists)

## Quick Test

After uploading, try a query from the frontend. If you still get "Database not initialized", check Railway logs to see what's missing.

