# ⚠️ CRITICAL: Enable GitHub Pages First!

## The Error You're Seeing

```
Get Pages site failed. Please verify that the repository has Pages enabled 
and configured to build using GitHub Actions
```

This means **GitHub Pages is not enabled** in your repository settings.

## Quick Fix (2 minutes)

### Step 1: Enable GitHub Pages

1. Go to: **https://github.com/mperelman/Thunderclap/settings/pages**
2. Under **"Source"**, select: **"GitHub Actions"**
3. Click **"Save"**

### Step 2: Verify Workflow Permissions

1. Go to: **https://github.com/mperelman/Thunderclap/settings/actions**
2. Scroll to **"Workflow permissions"**
3. Select: **"Read and write permissions"**
4. Check: **"Allow GitHub Actions to create and approve pull requests"**
5. Click **"Save"**

### Step 3: Re-run the Workflow

1. Go to: **https://github.com/mperelman/Thunderclap/actions**
2. Find the **"Deploy to GitHub Pages"** workflow
3. Click **"Re-run all jobs"** (or wait for next push)

### Step 4: Wait 2-3 Minutes

The workflow will:
- Build your site
- Deploy to GitHub Pages
- Show your site URL

## After Enabling

Your site will be live at:
**https://mperelman.github.io/Thunderclap/**

## Still Not Working?

Check:
- ✅ Pages is enabled (Settings → Pages → Source: "GitHub Actions")
- ✅ Workflow permissions are "Read and write"
- ✅ The workflow ran successfully (green checkmark in Actions)
- ✅ No errors in the workflow logs

## Need Help?

If Pages is enabled but still failing:
1. Check the Actions tab for error messages
2. Look at the "Deploy to GitHub Pages" step logs
3. Verify `index.html` exists in your repository root

