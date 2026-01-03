# Railway API Key Error Fix

## The Problem

Railway logs show:
```
"403 Your API key was reported as leaked. Please use another API key."
```

The `GEMINI_API_KEY` environment variable on Railway is using a leaked/invalid key.

## Quick Fix

### Step 1: Update Railway Environment Variable

1. Go to Railway dashboard: https://railway.app
2. Open your Thunderclap service
3. Go to **Variables** tab
4. Find `GEMINI_API_KEY`
5. **Update it** with one of your valid API keys from your `.env` file:
   - `GEMINI_API_KEY_1` through `GEMINI_API_KEY_6`
   - Use a key that hasn't been leaked
6. **Save** - Railway will restart automatically

### Step 2: Verify It Works

1. Wait for Railway to restart (1-2 minutes)
2. Test: `https://web-production-c4223.up.railway.app/health`
3. Should return: `{"status": "ok"}`
4. Try a query from the frontend

## Your Available API Keys

**IMPORTANT:** Do NOT use keys from documentation files - they may be exposed in git history.

**Get your API key from:**
- Your Google Cloud Console: https://makersuite.google.com/app/apikey
- Your secure `.env` file (local only, never committed to git)
- Railway environment variables (already set)

**Never use keys from:**
- Documentation files (they may be exposed in git history)
- Test files
- Any file committed to git

## After Fixing

Once you update the API key:
- ✅ Server will restart automatically
- ✅ Queries should work
- ✅ Frontend link: `https://mperelman.github.io/Thunderclap/?api=https://web-production-c4223.up.railway.app/query`

## Optional: Add API Key Rotation

If you want automatic rotation (tries multiple keys if one fails), I can add that feature to the server. But for now, just updating the single key should fix it.





