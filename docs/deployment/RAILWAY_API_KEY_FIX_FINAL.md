# Railway API Key Fix - FINAL

## The Error

Railway logs show:
```
"event":"error","type":"InvalidArgument","message":"400 API Key not found. Please pass a valid API key."
```

## The Problem

The `GEMINI_API_KEY` environment variable is **not set** or **set incorrectly** in Railway.

## The Fix

### Step 1: Get Your API Key

**IMPORTANT:** Do NOT use keys from this documentation file - they may be exposed.

**Get your API key from:**
- Your Google Cloud Console: https://makersuite.google.com/app/apikey
- Your secure `.env` file (local only, never committed to git)
- Railway environment variables (already set)

**Never use keys from:**
- Documentation files (they may be exposed in git history)
- Test files
- Any file committed to git

### Step 2: Set in Railway

1. Go to Railway dashboard: https://railway.app
2. Select your project
3. Go to **Variables** tab
4. Click **+ New Variable**
5. Set:
   - **Name**: `GEMINI_API_KEY`
   - **Value**: `YOUR_API_KEY_HERE` (get from Google Cloud Console or your secure .env file)
   - **DO NOT** add quotes around the value
   - **DO NOT** add spaces
6. Click **Add**
7. Railway will automatically redeploy

### Step 3: Verify

1. Wait ~30 seconds for redeploy
2. Visit: `https://web-production-c4223.up.railway.app/test`
3. Should show: `"api_key_present": true`
4. Make a query - should work now!

## Important Notes

- **Variable name must be exactly**: `GEMINI_API_KEY` (case-sensitive)
- **No quotes** around the value
- **No spaces** before/after the value
- Railway will redeploy automatically when you add the variable

## If Still Not Working

Check Railway logs for:
- `[SERVER] API Key present: True` ✅
- `[SERVER] API Key length: 39` ✅ (should be 39 characters)

If you see `False` or `0`, the variable isn't set correctly.





