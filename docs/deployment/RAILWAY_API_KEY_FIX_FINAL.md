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

You have 6 Gemini API keys stored in `.env`:
1. `AIzaSyBlqE1F2G_L5l2Lg81gyt0UWcME_K3inFo`
2. `AIzaSyBaj9wvbB3n6ZjvI89fFACl4SQgUfTaC4s`
3. `AIzaSyAXr9YBivlfndzZ4azcm7g3yfgan4Xl_ls`
4. `AIzaSyBPeY_SCL9EdpmnDbmeYSI7r5wJ-JaT6Fc`
5. `AIzaSyD-xExhXC66P-eUuYzx5wwXifBvCwZYGMw`
6. `AIzaSyBcl-noOJDWb3tTXSQYibMsH6kOf9uQn0o`

**Use key #1** (or any that hasn't been leaked): `AIzaSyBlqE1F2G_L5l2Lg81gyt0UWcME_K3inFo`

### Step 2: Set in Railway

1. Go to Railway dashboard: https://railway.app
2. Select your project
3. Go to **Variables** tab
4. Click **+ New Variable**
5. Set:
   - **Name**: `GEMINI_API_KEY`
   - **Value**: `AIzaSyBlqE1F2G_L5l2Lg81gyt0UWcME_K3inFo`
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





