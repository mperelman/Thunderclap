# How to Share a Working Link

## Quick Option: Use ngrok (Temporary, for Testing)

1. **Install ngrok**: https://ngrok.com/download

2. **Start your backend locally**:
   ```bash
   python server.py
   ```

3. **In another terminal, expose it**:
   ```bash
   ngrok http 8000
   ```

4. **You'll get a URL like**: `https://abc123.ngrok.io`

5. **Share this link**:
   ```
   https://mperelman.github.io/Thunderclap/?api=https://abc123.ngrok.io/query
   ```

**Note**: ngrok URLs expire after a few hours (free tier) or stay active (paid tier)

---

## Permanent Option: Deploy Backend to Railway/Render

### Railway (Recommended - Easiest)

1. **Sign up**: https://railway.app
2. **Create new project** → Deploy from GitHub
3. **Connect your repo**: `mperelman/Thunderclap`
4. **Set environment variables**:
   - `GEMINI_API_KEY` = your API key
5. **Deploy** → Railway gives you a URL like: `https://thunderclap-production.up.railway.app`

6. **Share with Railway URL**:
   ```
   https://mperelman.github.io/Thunderclap/?api=https://thunderclap-production.up.railway.app/query
   ```

### Render (Alternative)

1. **Sign up**: https://render.com
2. **New Web Service** → Connect GitHub repo
3. **Settings**:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn server:app --host 0.0.0.0 --port $PORT`
   - Environment: `GEMINI_API_KEY`
4. **Deploy** → Get URL like: `https://thunderclap.onrender.com`

---

## Simplest: Pre-configure Frontend

I can update `index.html` to automatically use a deployed backend URL when accessed from GitHub Pages. Just tell me your backend URL and I'll update it!

---

## Current Status

✅ Frontend: Ready for GitHub Pages  
⏳ Backend: Needs deployment or tunnel  
✅ CORS: Already configured to allow GitHub Pages origin

