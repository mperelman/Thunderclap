# Deploy Backend to Share Online Link

## Quick Setup: Railway (Free, 5 minutes)

### Step 1: Sign Up & Deploy

1. **Go to**: https://railway.app
2. **Sign up** with GitHub
3. **Click**: "New Project"
4. **Select**: "Deploy from GitHub repo"
5. **Choose**: `mperelman/Thunderclap`
6. **Railway auto-detects** Python and starts deploying

### Step 2: Set Environment Variable

1. **Click** on your project
2. **Go to**: Variables tab
3. **Add**:
   - Key: `GEMINI_API_KEY`
   - Value: `your-api-key-here` (from your .env file)
4. **Save** - Railway will redeploy automatically

### Step 3: Get Your Backend URL

1. **Click**: Settings → Generate Domain
2. **Copy** the URL (e.g., `https://thunderclap-production.up.railway.app`)

### Step 4: Share the Link!

**Your shareable link**:
```
https://mperelman.github.io/Thunderclap/frontend.html?api=https://YOUR-RAILWAY-URL/query
```

Replace `YOUR-RAILWAY-URL` with your actual Railway domain.

**Example**:
```
https://mperelman.github.io/Thunderclap/frontend.html?api=https://thunderclap-production.up.railway.app/query
```

---

## Alternative: Render (Also Free)

1. **Go to**: https://render.com
2. **Sign up** → New Web Service
3. **Connect** GitHub repo: `mperelman/Thunderclap`
4. **Settings**:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn server:app --host 0.0.0.0 --port $PORT`
   - Environment: `GEMINI_API_KEY=your-key`
5. **Deploy** → Get URL like: `https://thunderclap.onrender.com`
6. **Share**: `https://mperelman.github.io/Thunderclap/frontend.html?api=https://thunderclap.onrender.com/query`

---

## Make It Permanent (Optional)

Once you have your backend URL, I can update `frontend.html` to use it automatically when accessed from GitHub Pages, so you can just share:
```
https://mperelman.github.io/Thunderclap/
```

Without the `?api=` parameter!

