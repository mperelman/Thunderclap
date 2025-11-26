# ⚠️ Backend Not Accessible Error

## The Problem

Your GitHub Pages frontend is trying to call:
```
http://localhost:8000/query
```

But `localhost:8000` is **not accessible** from GitHub Pages because:
- GitHub Pages is served from GitHub's servers
- `localhost` refers to YOUR computer, not GitHub's servers
- The backend server (`server.py`) isn't running or isn't publicly accessible

## Solutions

### Option 1: Deploy Backend to Railway (Recommended - Permanent)

**Steps:**
1. Go to: https://railway.app
2. Sign up with GitHub
3. New Project → Deploy from GitHub
4. Select: `mperelman/Thunderclap`
5. Add environment variable: `GEMINI_API_KEY=your_key`
6. Railway will auto-detect Python and deploy
7. Get your Railway URL: `https://your-app.up.railway.app`

**Then update your GitHub Pages link:**
```
https://mperelman.github.io/Thunderclap/?api=https://your-app.up.railway.app/query
```

### Option 2: Use ngrok (Temporary - For Testing)

**Steps:**
1. Install ngrok: https://ngrok.com/download
2. Start your backend locally:
   ```bash
   python server.py
   ```
3. In another terminal, expose it:
   ```bash
   ngrok http 8000
   ```
4. Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)

**Then use:**
```
https://mperelman.github.io/Thunderclap/?api=https://abc123.ngrok.io/query
```

**Note:** ngrok URLs expire after a few hours (free tier)

### Option 3: Run Backend Locally (For Development Only)

**Steps:**
1. Start backend: `python server.py`
2. Open GitHub Pages frontend with localhost API:
   ```
   https://mperelman.github.io/Thunderclap/?api=http://localhost:8000/query
   ```

**Note:** This only works if you're accessing from YOUR computer. Others can't use it.

## Quick Fix Right Now

**If you have Railway/Render backend URL:**
Add `?api=YOUR_BACKEND_URL/query` to your GitHub Pages URL:
```
https://mperelman.github.io/Thunderclap/?api=https://your-backend.up.railway.app/query
```

**If you want to test locally:**
1. Start: `python server.py`
2. Visit: `https://mperelman.github.io/Thunderclap/?api=http://localhost:8000/query`

## Additional Issue: API Key Errors

I also see in your server trace:
```
"403 Your API key was reported as leaked. Please use another API key."
```

**Fix:**
1. Check your `.env` file
2. Make sure `GEMINI_API_KEY` is set correctly
3. If a key is leaked, generate a new one at: https://makersuite.google.com/app/apikey
4. Update your `.env` file

## Summary

- ✅ Frontend is working (GitHub Pages)
- ❌ Backend needs to be deployed (Railway/Render) or exposed (ngrok)
- ⚠️ Some API keys might be invalid (check `.env`)

**Next step:** Deploy backend to Railway or use ngrok for testing.





