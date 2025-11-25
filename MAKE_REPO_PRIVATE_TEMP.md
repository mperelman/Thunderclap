# Temporarily Make Repo Private to Upload Data

## Step 1: Make Repo Private

1. Go to: https://github.com/mperelman/Thunderclap
2. Click **"Settings"** tab (top right)
3. Scroll down to **"Danger Zone"** section
4. Click **"Change visibility"**
5. Select **"Make private"**
6. Type repository name to confirm: `mperelman/Thunderclap`
7. Click **"I understand, change repository visibility"**

## Step 2: Temporarily Commit Data

**In PowerShell:**
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

## Step 3: Verify It Works

1. Wait 2-3 minutes for Railway to rebuild
2. Try a query from the frontend
3. If it works, proceed to Step 4

## Step 4: Remove Data from Git

**In PowerShell:**
```powershell
# Remove data from Git (but keep files locally)
git rm -r --cached data/

# Update .gitignore to ensure data/ is ignored
# (Edit .gitignore and uncomment the data/ line if needed)

git commit -m "Remove data from Git"
git push
```

## Step 5: Make Repo Public Again (Optional)

1. Go to: https://github.com/mperelman/Thunderclap/settings
2. Scroll to **"Danger Zone"**
3. Click **"Change visibility"**
4. Select **"Make public"**
5. Confirm

**Note:** Even after making it public again, the data will be in Git history. If you want to completely remove it from history, you'll need to use `git filter-branch` or `git filter-repo` (more complex).

## Recommendation

**If you want to share the code publicly:**
- Keep repo public
- Install Node.js and use Railway CLI (takes 10 minutes but keeps data secure)

**If you don't need to share:**
- Make repo private
- Commit data temporarily (takes 2 minutes)
- Keep it private

