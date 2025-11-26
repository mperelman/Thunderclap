# Quick Fix: Upload Data to Railway

## Check if Your Repo is Private

1. Go to: https://github.com/mperelman/Thunderclap
2. Look at the top right - does it say "Private" or "Public"?

## If REPO IS PRIVATE: Use This Method (Fastest)

**Run these commands in PowerShell:**

```powershell
cd C:\Users\perel\OneDrive\Apps\thunderclap-ai

# Force add data folder (overrides .gitignore)
git add -f data/

# Commit
git commit -m "Temporarily include data for Railway deployment"

# Push
git push
```

**Railway will automatically rebuild** with data included (2-3 minutes).

**After it works, remove data from Git:**
```powershell
git rm -r --cached data/
git commit -m "Remove data from Git"
git push
```

## If REPO IS PUBLIC: Install Node.js First

**Don't commit data to a public repo!** Instead:

1. **Install Node.js:**
   - Go to: https://nodejs.org/
   - Download LTS version
   - Install it
   - Restart PowerShell

2. **Then install Railway CLI:**
   ```powershell
   npm install -g @railway/cli
   railway login
   railway link
   ```

3. **Upload files:**
   ```powershell
   cd C:\Users\perel\OneDrive\Apps\thunderclap-ai
   Get-Content data\indices.json -Raw -Encoding UTF8 | railway run --service web sh -c "cat > /app/data/indices.json"
   ```

## Which Method Should You Use?

- **Private repo?** → Temporarily commit data (fastest, 2 minutes)
- **Public repo?** → Install Node.js and use Railway CLI (safer, 10 minutes)

Let me know which one applies to your repo!




