# Simple Guide: Upload Data Folder to Railway

## The Problem
Railway needs your local `data/` folder but it's not in the Docker image.

## Solution: Use Railway CLI to Upload Files

### Step 1: Install Railway CLI

**Windows (PowerShell):**
```powershell
npm install -g @railway/cli
```

### Step 2: Login and Link

```powershell
railway login
railway link
```
(Select your "thunderclap" project when prompted)

### Step 3: Upload Files

**From your project directory** (`C:\Users\perel\OneDrive\Apps\thunderclap-ai`):

```powershell
# Create the data directory in Railway
railway run --service web mkdir -p /app/data

# Upload indices.json
Get-Content data\indices.json | railway run --service web sh -c "cat > /app/data/indices.json"

# Upload endnotes.json (if it exists)
if (Test-Path data\endnotes.json) {
    Get-Content data\endnotes.json | railway run --service web sh -c "cat > /app/data/endnotes.json"
}

# Upload chunk_to_endnotes.json (if it exists)
if (Test-Path data\chunk_to_endnotes.json) {
    Get-Content data\chunk_to_endnotes.json | railway run --service web sh -c "cat > /app/data/chunk_to_endnotes.json"
}
```

### Step 4: Upload vectordb Folder (This is the big one)

The `vectordb/` folder is large and complex. **Easiest method:**

1. **Create a Railway Volume:**
   - Go to Railway → Your project → web service
   - Click **"Volumes"** tab
   - Click **"+ New Volume"**
   - Name: `data-volume`
   - Mount path: `/app/data`
   - Click **"Create"**

2. **After volume is created, Railway will redeploy**

3. **Upload vectordb via Railway Shell:**
   - Go to Railway → Your project → web service → **"Deployments"** tab
   - Click latest deployment → **"View Logs"** → **"Shell"** button
   - In the shell:
     ```bash
     mkdir -p /app/data/vectordb
     ```
   - Then use Railway's file upload feature (if available) or continue with CLI

### Alternative: Zip and Upload

If Railway CLI file upload is difficult, try this:

```powershell
# Create a zip of the data folder
Compress-Archive -Path data\* -DestinationPath data.zip

# Upload zip to Railway (you may need to use Railway's web interface for this)
# Then in Railway shell, unzip it:
# unzip data.zip -d /app/data
```

### Step 5: Verify

Check Railway logs:
```powershell
railway logs
```

Look for:
```
[OK] Connected to database (X indexed chunks)
```

If you see this, it's working!

## Quick Test

After uploading, try a query. If you still get "Database not initialized", check:
1. Railway logs for errors
2. That files are in `/app/data/` (use Railway shell: `ls -la /app/data`)




