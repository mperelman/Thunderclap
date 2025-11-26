# Upload Data Folder to Railway - SIMPLE STEPS

## Step 1: Create Railway Volume

1. Go to: https://railway.app
2. Click your **"thunderclap"** project
3. Click **"web"** service
4. Click **"Volumes"** tab (left sidebar)
5. Click **"+ New Volume"**
6. Name: `data-volume`
7. Mount path: `/app/data`
8. Click **"Create"**

**Wait for Railway to redeploy** (1-2 minutes)

## Step 2: Upload Files Using Railway Shell

1. In Railway dashboard → **"thunderclap"** → **"web"** service
2. Click **"Deployments"** tab
3. Click on the **latest deployment**
4. Click **"View Logs"** → **"Shell"** button (opens terminal)

In the Railway shell, run:

```bash
# Create directories
mkdir -p /app/data/vectordb

# Check if volume is mounted
ls -la /app/data
```

## Step 3: Upload Files from Your Computer

**You need to upload these files from your local `data/` folder:**

From your computer (`C:\Users\perel\OneDrive\Apps\thunderclap-ai\data\`):

### Option A: Use Railway CLI (Easier)

**Install Railway CLI:**
```powershell
npm install -g @railway/cli
```

**Login and link:**
```powershell
railway login
railway link
```
(Select "thunderclap" project)

**Upload files:**
```powershell
# Upload indices.json
Get-Content data\indices.json | railway run --service web sh -c "cat > /app/data/indices.json"

# Upload endnotes.json (if exists)
if (Test-Path data\endnotes.json) {
    Get-Content data\endnotes.json | railway run --service web sh -c "cat > /app/data/endnotes.json"
}

# Upload chunk_to_endnotes.json (if exists)
if (Test-Path data\chunk_to_endnotes.json) {
    Get-Content data\chunk_to_endnotes.json | railway run --service web sh -c "cat > /app/data/chunk_to_endnotes.json"
}
```

### Option B: Copy vectordb Folder (The Big One)

The `vectordb/` folder is complex. **Easiest method:**

1. **Zip your local vectordb folder:**
   ```powershell
   Compress-Archive -Path data\vectordb\* -DestinationPath vectordb.zip
   ```

2. **Upload zip via Railway:**
   - Railway doesn't have direct file upload in web UI
   - You'll need to use Railway CLI or a workaround

3. **Or use Railway CLI to copy entire folder:**
   ```powershell
   # This is complex - vectordb has many subfolders
   # You may need to copy each subfolder individually
   ```

## Step 4: Verify

After uploading, check Railway logs:
```powershell
railway logs
```

Look for:
```
[OK] Connected to database (X indexed chunks)
```

## Alternative: Include Data in Docker Build (Temporary)

If uploading is too difficult, we can temporarily include data in the Docker image:

1. Remove `data/` from `.dockerignore` (temporarily)
2. Commit data folder to Git (temporarily - remove after)
3. Railway will rebuild with data included
4. Then remove data from Git again

**⚠️ WARNING:** This exposes your data in Git history. Only do this if the repo is private.

## What Files Are Required

Minimum required:
- ✅ `data/indices.json` - Term indices (REQUIRED)
- ✅ `data/vectordb/` - ChromaDB database (REQUIRED - entire folder)

Optional but helpful:
- `data/endnotes.json`
- `data/chunk_to_endnotes.json`




