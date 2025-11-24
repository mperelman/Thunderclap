# Test Railway Query to See Error

## Current Status

✅ Server is running
✅ Health check works
❓ Gemini API initialization happens per-request (not at startup)

## The Issue

The server creates QueryEngine per-request, so LLM initialization happens when you make a query. The "API Key not found" error happens during query processing.

## Test Query

Try making a query and check Railway logs:

1. **Make a query** from the frontend:
   ```
   https://mperelman.github.io/Thunderclap/?api=https://web-production-c4223.up.railway.app/query
   ```

2. **Immediately check Railway logs** (refresh the logs page)
3. **Look for**:
   - `Connecting to document database...`
   - `[OK] Connected to database`
   - `Initializing LLM...`
   - `[OK] Gemini API configured` ✅
   - OR `[ERROR] Gemini setup failed: ...` ❌
   - OR `[WARNING] No Gemini API key found` ❌

## Verify API Key

**Double-check Railway Variables:**
1. Go to Railway → Variables tab
2. Find `GEMINI_API_KEY`
3. Value should be: `AIzaSyDLV5J4etz6jDNIAYFqTa06ljXd7y6TO_w`
4. **Make sure**:
   - No spaces
   - No quotes
   - Exact match

## If Key is Set But Still Failing

**Possible issues:**
1. **Key not activated** - Check at https://makersuite.google.com/app/apikey
2. **Key format wrong** - Should be 39 characters, starts with `AIza`
3. **Railway cache** - Try restarting the service manually

## Next Steps

1. Make a test query
2. Check Railway logs immediately after
3. Share what you see in the logs (especially any `[ERROR]` or `[WARNING]` messages)

