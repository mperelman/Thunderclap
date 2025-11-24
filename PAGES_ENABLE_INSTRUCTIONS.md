# ⚠️ REQUIRED: Enable GitHub Pages Manually

## The Error

```
Error: Create Pages site failed
Error: HttpError: Resource not accessible by integration
```

**This means:** The workflow cannot automatically enable GitHub Pages. You must enable it manually in repository settings.

## Why?

GitHub requires **admin-level permissions** to enable Pages, which workflows don't have for security reasons. This is a GitHub security feature.

## Fix (2 minutes)

### Step 1: Enable GitHub Pages

1. **Go to**: https://github.com/mperelman/Thunderclap/settings/pages
2. **Under "Source"**, select: **"GitHub Actions"**
3. **Click "Save"**

### Step 2: Verify Workflow Permissions

1. **Go to**: https://github.com/mperelman/Thunderclap/settings/actions
2. **Scroll to "Workflow permissions"**
3. **Select**: **"Read and write permissions"**
4. **Check**: **"Allow GitHub Actions to create and approve pull requests"**
5. **Click "Save"**

### Step 3: Re-run the Workflow

1. **Go to**: https://github.com/mperelman/Thunderclap/actions
2. **Find**: "Deploy to GitHub Pages"
3. **Click**: **"Re-run all jobs"**

### Step 4: Wait 2-3 Minutes

The workflow will:
- ✅ Build your site (`index.html` + `public/` folder)
- ✅ Upload to GitHub Pages
- ✅ Deploy successfully

## After Enabling

Your site will be live at:
**https://mperelman.github.io/Thunderclap/**

## Verify It Worked

1. Check Actions tab: Green checkmark ✅
2. Check Settings → Pages: Should show "Your site is live at..."
3. Visit: https://mperelman.github.io/Thunderclap/

## Still Not Working?

**Check these:**
- ✅ Pages is enabled (Settings → Pages → Source: "GitHub Actions")
- ✅ Workflow permissions are "Read and write"
- ✅ The workflow ran successfully (green checkmark)
- ✅ `index.html` exists in repository root
- ✅ No errors in workflow logs

**If still failing:**
- Check the "Deploy to GitHub Pages" step logs
- Look for any error messages
- Verify repository is public (or you have GitHub Pro for private repos)

