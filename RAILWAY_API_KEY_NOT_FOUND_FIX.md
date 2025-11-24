# Railway API Key "Not Found" Error

## The Error

```
"400 API Key not found. Please pass a valid API key."
```

This means:
- The API key might not be set in Railway
- Or the key format is incorrect
- Or the key hasn't been activated yet

## How to Fix

### Step 1: Verify Key is Set in Railway

1. Go to Railway: https://railway.app
2. Open your Thunderclap service
3. Go to **Variables** tab
4. **Check if `GEMINI_API_KEY` exists** and has the value:
   ```
   AIzaSyDLV5J4etz6jDNIAYFqTa06ljXd7y6TO_w
   ```

### Step 2: Check Railway Logs

1. In Railway dashboard, click **"View Logs"**
2. Look for startup messages
3. Check if you see:
   - `[OK] Gemini API configured` ✅
   - OR `[ERROR] Gemini setup failed` ❌
   - OR `[WARNING] No Gemini API key found` ❌

### Step 3: Verify Key Format

The key should:
- Start with `AIza`
- Be exactly 39 characters long
- Have no spaces or extra characters

Your key: `AIzaSyDLV5J4etz6jDNIAYFqTa06ljXd7y6TO_w` (39 chars) ✅

### Step 4: Check if Key is Activated

1. Go to: https://makersuite.google.com/app/apikey
2. Verify the key exists and is active
3. Make sure it has permissions for Gemini API

### Step 5: Restart Railway Service

After setting/updating the key:
1. Railway should auto-restart
2. If not, manually restart:
   - Go to **Settings** → **Restart**

## Common Issues

**Issue 1: Key not set**
- Solution: Add `GEMINI_API_KEY` variable in Railway

**Issue 2: Key has extra spaces**
- Solution: Copy-paste the key exactly, no spaces

**Issue 3: Key not activated**
- Solution: Verify key exists at https://makersuite.google.com/app/apikey

**Issue 4: Wrong variable name**
- Solution: Must be exactly `GEMINI_API_KEY` (case-sensitive)

## After Fixing

1. Check Railway logs for: `[OK] Gemini API configured`
2. Test: `https://web-production-c4223.up.railway.app/health`
3. Should return: `{"status": "ok"}`
4. Try a query from frontend

## Debug Steps

**Check Railway logs for:**
```
[ERROR] Gemini setup failed: ...
```
or
```
[WARNING] No Gemini API key found
```

These will tell you exactly what's wrong.

