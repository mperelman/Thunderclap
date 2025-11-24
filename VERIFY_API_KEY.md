# Verify API Key Format

## Your API Key
```
AIzaSyDLV5J4etz6jDNIAYFqTa06ljXd7y6TO_w
```

## Format Check ✅

- **Length**: 39 characters ✅
- **Starts with**: `AIza` ✅
- **Format**: Looks correct ✅

## Verify in Railway

1. **Go to Railway**: https://railway.app
2. **Open your Thunderclap service**
3. **Go to Variables tab**
4. **Check `GEMINI_API_KEY`**:
   - Value should be **exactly**: `AIzaSyDLV5J4etz6jDNIAYFqTa06ljXd7y6TO_w`
   - **No spaces** before/after
   - **No quotes** around it
   - **Exact match**

## Verify at Google

1. **Go to**: https://makersuite.google.com/app/apikey
2. **Check if this key exists**
3. **Make sure it's active**
4. **Verify Gemini API is enabled** for this key

## Common Issues

**If key format is correct but still getting errors:**

1. **Key not activated** - Check at Google API console
2. **Key has restrictions** - Make sure it allows requests from Railway's IPs
3. **Key not set correctly** - Double-check Railway Variables (no spaces, exact match)
4. **Railway cache** - Try restarting the service manually

## Test

After verifying:
1. Make a query from frontend
2. Check Railway logs for:
   - `[OK] Gemini API configured` ✅
   - OR `[ERROR] Gemini setup failed: ...` ❌

