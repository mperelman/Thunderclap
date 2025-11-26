# How GitHub Pages Works

## Two Separate Parts

### 1. Frontend (GitHub Pages) ✅
- **What**: Static HTML/JavaScript file (`index.html`)
- **Where**: GitHub Pages hosts it
- **URL**: `https://mperelman.github.io/Thunderclap/`
- **What it does**: Shows the UI, takes user input, makes API calls
- **Limitation**: Can only host static files (HTML, CSS, JS) - **cannot run Python code**

### 2. Backend (Railway/Render) ⚠️ NEEDS DEPLOYMENT
- **What**: Python server (`server.py`) that processes queries
- **Where**: Must be deployed separately (Railway, Render, etc.)
- **What it does**: Receives API calls from frontend, processes queries, returns answers
- **Why separate**: GitHub Pages cannot run Python/backend code

## How They Work Together

```
User Browser
    ↓
GitHub Pages (index.html)
    ↓ (makes API call)
Railway/Render (server.py)
    ↓ (processes query)
Returns answer
    ↓
GitHub Pages (displays answer)
```

## Current Status

✅ **Frontend**: Ready for GitHub Pages (will be hosted at `mperelman.github.io`)
⏳ **Backend**: Needs deployment to Railway/Render (not deployed yet)

## To Make It Work

1. **Enable GitHub Pages** (if not done):
   - Go to: https://github.com/mperelman/Thunderclap/settings/pages
   - Source: "GitHub Actions"
   - Save

2. **Deploy Backend**:
   - Railway: https://railway.app → Deploy from GitHub
   - Get backend URL: `https://your-app.up.railway.app`

3. **Share Link**:
   ```
   https://mperelman.github.io/Thunderclap/?api=https://your-app.up.railway.app/query
   ```

## Summary

- **GitHub Pages** = Hosts the UI (index.html) ✅
- **Railway/Render** = Runs the backend (server.py) ⏳
- **Together** = Working application

The frontend is just a webpage that calls your backend API. GitHub Pages hosts the webpage, but the backend must run elsewhere.

