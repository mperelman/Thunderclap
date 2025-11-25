# Update Railway with New API Key

## Get Your API Key

1. Go to: https://aistudio.google.com/apikey
2. Create a new API key
3. Copy it (starts with `AIza...`, 39 characters)

## Steps to Update Railway

1. **Go to Railway**: https://railway.app
2. **Open your Thunderclap service**
3. **Go to Variables tab**
4. **Find `GEMINI_API_KEY`** (or add it if it doesn't exist)
5. **Set the value to**: Your API key from step above
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
GEMINI_API_KEY=YOUR_API_KEY_HERE
```

**IMPORTANT**: Never commit `.env` to Git! It's already in `.gitignore`.

## After Update

✅ Railway will restart automatically  
✅ Queries should work  
✅ No more "403 Your API key was reported as leaked" errors




