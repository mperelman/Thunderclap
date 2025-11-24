# Railway API Key Debugging

## Current Error

```
"400 API Key not found. Please pass a valid API key."
```

This means the API key is either:
1. **Not set** in Railway environment variables
2. **Set incorrectly** (has spaces, wrong format)
3. **Not being read** by the server

## How to Fix

### Step 1: Verify API Key in Railway

1. Go to Railway: https://railway.app
2. Open your Thunderclap service
3. Go to **Variables** tab
4. **Check if `GEMINI_API_KEY` exists**
5. **Value should be exactly**: `AIzaSyDLV5J4etz6jDNIAYFqTa06ljXd7y6TO_w`
   - No spaces before/after
   - No quotes around it
   - No extra characters
   - Exact match

### Step 2: Add Debug Logging

The server should print the API key status. Check Railway logs for:
- `[OK] Gemini API configured` ✅
- `[ERROR] Gemini setup failed: ...` ❌
- `[WARNING] No Gemini API key found` ❌

### Step 3: Test API Key Format

Your key: `AIzaSyDLV5J4etz6jDNIAYFqTa06ljXd7y6TO_w`
- Length: 39 characters ✅
- Starts with: `AIza` ✅
- Format looks correct ✅

### Step 4: Verify Key is Active

1. Go to: https://makersuite.google.com/app/apikey
2. Check if the key exists
3. Make sure it's **active** and has **Gemini API** enabled

### Step 5: Restart Railway Service

After updating the key:
1. Railway should auto-restart
2. If not, manually restart: **Settings** → **Restart**

## Common Issues

**Issue 1: Variable name wrong**
- Must be exactly: `GEMINI_API_KEY` (case-sensitive)
- Not: `gemini_api_key` or `GEMINI-API-KEY`

**Issue 2: Key has spaces**
- Copy-paste exactly: `AIzaSyDLV5J4etz6jDNIAYFqTa06ljXd7y6TO_w`
- No spaces before/after

**Issue 3: Key not activated**
- Check at https://makersuite.google.com/app/apikey
- Make sure Gemini API is enabled for this key

**Issue 4: Railway cache**
- Try deleting and re-adding the variable
- Or restart the service manually

## What to Check

1. **Railway Variables tab** - Is `GEMINI_API_KEY` set?
2. **Railway Logs** - What does it say about API key?
3. **Google API Console** - Is the key active?

## Next Steps

1. **Double-check Railway Variables** - Make sure `GEMINI_API_KEY` is set correctly
2. **Check Railway logs** - Look for API key related messages
3. **Share what you see** - Especially any `[ERROR]` or `[WARNING]` messages

