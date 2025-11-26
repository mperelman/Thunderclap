# SIMPLE: Upload Data to Railway

## The Problem
Railway needs your `data/` folder but it's not in GitHub (gitignored for security).

## Solution: Railway Volumes (5 Steps)

### Step 1: Create Volume in Railway Web UI

1. Go to: https://railway.app
2. Click **"thunderclap"** project
3. Click **"web"** service  
4. Click **"Volumes"** tab (left sidebar)
5. Click **"+ New Volume"**
6. Name: `data`
7. Mount path: `/app/data`
8. Click **"Create"**

**Wait 1-2 minutes for Railway to redeploy**

### Step 2: Install Railway CLI

Open PowerShell and run:
```powershell
npm install -g @railway/cli
```

### Step 3: Login and Link

```powershell
railway login
railway link
```
(Select "thunderclap" when prompted)

### Step 4: Upload Files

**From your project directory** (`C:\Users\perel\OneDrive\Apps\thunderclap-ai`):

```powershell
# Upload indices.json
$content = Get-Content data\indices.json -Raw
$content | railway run --service web sh -c "cat > /app/data/indices.json"

# Upload endnotes.json (if exists)
if (Test-Path data\endnotes.json) {
    $content = Get-Content data\endnotes.json -Raw
    $content | railway run --service web sh -c "cat > /app/data/endnotes.json"
}

# Upload chunk_to_endnotes.json (if exists)
if (Test-Path data\chunk_to_endnotes.json) {
    $content = Get-Content data\chunk_to_endnotes.json -Raw
    $content | railway run --service web sh -c "cat > /app/data/chunk_to_endnotes.json"
}
```

### Step 5: Upload vectordb Folder

**This is the tricky part - vectordb has many subfolders.**

**Option A: Use Railway Shell (Easier)**

1. Railway dashboard → "thunderclap" → "web" → "Deployments"
2. Click latest deployment → "View Logs" → "Shell"
3. In shell:
   ```bash
   mkdir -p /app/data/vectordb
   ```
4. Then you'll need to copy files. Railway doesn't have direct file upload in web UI.

**Option B: Copy Entire vectordb via Railway CLI**

You'll need to copy each subfolder. This is complex. 

**EASIEST: Use a script to copy the entire folder structure.**

### Step 6: Verify

```powershell
railway logs
```

Look for:
```
[OK] Connected to database (X indexed chunks)
```

## If This Is Too Complex

**Alternative: Temporarily include data in Git (ONLY if repo is private):**

1. Remove `data/` from `.gitignore` temporarily
2. `git add data/`
3. `git commit -m "Temporarily include data for Railway"`
4. `git push`
5. Railway will rebuild with data included
6. Then remove data from Git again

**⚠️ Only do this if your GitHub repo is PRIVATE!**




