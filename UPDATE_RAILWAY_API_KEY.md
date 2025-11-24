# Update Railway with New API Key

## Your New API Key
```
AIzaSyDLV5J4etz6jDNIAYFqTa06ljXd7y6TO_w
```

## Steps to Update Railway

1. **Go to Railway**: https://railway.app
2. **Open your Thunderclap service**
3. **Go to Variables tab**
4. **Find `GEMINI_API_KEY`** (or add it if it doesn't exist)
5. **Set the value to**: `AIzaSyDLV5J4etz6jDNIAYFqTa06ljXd7y6TO_w`
6. **Save** - Railway will automatically restart

## Verify It Works

After Railway restarts (1-2 minutes):

1. **Test health endpoint:**
   ```
   https://web-production-c4223.up.railway.app/health
   ```
   Should return: `{"status": "ok"}`

2. **Test a query from frontend:**
   ```
   https://mperelman.github.io/Thunderclap/?api=https://web-production-c4223.up.railway.app/query
   ```

3. **Try asking**: "Tell me about Lehman"

## Optional: Update Local .env File

If you want to use this key locally too, update your `.env` file:

```env
GEMINI_API_KEY=AIzaSyDLV5J4etz6jDNIAYFqTa06ljXd7y6TO_w
```

Or add it as one of your rotation keys:
```env
GEMINI_API_KEY_5=AIzaSyDLV5J4etz6jDNIAYFqTa06ljXd7y6TO_w
```

## After Update

✅ Railway will restart automatically  
✅ Queries should work  
✅ No more "403 Your API key was reported as leaked" errors

