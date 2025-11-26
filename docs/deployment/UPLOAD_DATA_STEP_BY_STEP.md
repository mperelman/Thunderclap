# Upload Data to Railway - Step by Step (Windows)

You've created the volume. Now upload the files.

## Step 1: Install Railway CLI on Your Computer

**Open PowerShell** (Windows key → type "PowerShell" → press Enter)

**Run this command:**
```powershell
npm install -g @railway/cli
```

**Wait for it to finish** (may take 1-2 minutes)

**Verify it worked:**
```powershell
railway --version
```
(Should show a version number like "3.x.x")

## Step 2: Login to Railway

**In the same PowerShell window, run:**
```powershell
railway login
```

**This will:**
- Open your web browser
- Ask you to authorize Railway CLI
- Click "Authorize" in the browser
- Return to PowerShell when done

## Step 3: Link to Your Project

**Still in PowerShell, run:**
```powershell
railway link
```

**You'll see a list of projects. Select:**
- Type the number for "thunderclap" project
- Press Enter

## Step 4: Navigate to Your Project Folder

**In PowerShell, go to your project:**
```powershell
cd C:\Users\perel\OneDrive\Apps\thunderclap-ai
```

**Verify you're in the right place:**
```powershell
ls data
```
(Should show: indices.json, vectordb/, endnotes.json, etc.)

## Step 5: Upload indices.json

**Run this command:**
```powershell
Get-Content data\indices.json -Raw -Encoding UTF8 | railway run --service web sh -c "cat > /app/data/indices.json"
```

**Wait for it to finish** (may take 10-30 seconds)

**Verify it worked:**
```powershell
railway run --service web ls -la /app/data
```
(Should show indices.json)

## Step 6: Upload endnotes.json (if it exists)

**Check if it exists:**
```powershell
Test-Path data\endnotes.json
```

**If it returns "True", upload it:**
```powershell
Get-Content data\endnotes.json -Raw -Encoding UTF8 | railway run --service web sh -c "cat > /app/data/endnotes.json"
```

## Step 7: Upload vectordb Folder

**This is the big one. The vectordb folder has many subfolders.**

**First, check what's in vectordb:**
```powershell
ls data\vectordb
```

**You'll see many folders (like: 081babe1-1e5c-4172-ada6-8176aeadc0f5, etc.)**

**We need to copy the entire vectordb folder structure. This is complex, so let's use a different approach:**

### Option A: Copy via Railway Shell (Easier)

1. **Go to Railway website:**
   - https://railway.app
   - Click "thunderclap" project
   - Click "web" service
   - Click "Deployments" tab
   - Click on the latest deployment
   - Click "View Logs" → "Shell" button

2. **In the Railway shell, create the directory:**
   ```bash
   mkdir -p /app/data/vectordb
   ```

3. **Railway shell doesn't have direct file upload, so we need to use Railway CLI**

### Option B: Copy Entire vectordb via Railway CLI

**This will copy your entire local vectordb folder to Railway:**

```powershell
# Create a tar archive of vectordb
cd data
tar -czf vectordb.tar.gz vectordb/
cd ..

# Upload the tar file (this is complex - Railway CLI doesn't have direct file upload)
# Instead, we'll copy files one by one
```

**Actually, the easiest way is to use Railway's volume feature differently:**

## Alternative: Use Railway Volume Web Interface

Railway volumes persist data, but uploading files is tricky. 

**Easiest solution: Temporarily include data in Git (if repo is private):**

1. **Remove data/ from .gitignore temporarily:**
   - Open `.gitignore` in a text editor
   - Find the line `# data/` (around line 30)
   - Comment it out or delete it
   - Save the file

2. **Add data to Git:**
   ```powershell
   git add data/
   git commit -m "Temporarily include data for Railway deployment"
   git push
   ```

3. **Railway will rebuild with data included**

4. **After it works, remove data from Git again:**
   ```powershell
   git rm -r --cached data/
   git commit -m "Remove data from Git (use Railway Volume instead)"
   git push
   ```

**⚠️ Only do this if your GitHub repo is PRIVATE!**

## What I Recommend

**Since uploading vectordb via CLI is complex, try this:**

1. **Upload indices.json and endnotes.json via CLI** (Steps 1-6 above)
2. **For vectordb, use Railway Shell to check if volume is working:**
   - Railway → Shell
   - Run: `ls -la /app/data`
   - If you see the directory, the volume is mounted
3. **Then we can figure out how to copy vectordb files**

Let me know which step you're stuck on!




