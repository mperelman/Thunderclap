# Backend Deployment Files Added ✅

## Files Created

1. **`Procfile`** - For Railway/Heroku deployment
2. **`railway.json`** - Railway-specific configuration
3. **`render.yaml`** - Render.com configuration
4. **`nixpacks.toml`** - Nixpacks build configuration
5. **`runtime.txt`** - Python version specification
6. **`DEPLOY_BACKEND.md`** - Step-by-step deployment guide

## Updated Files

- **`requirements.txt`** - Added `fastapi`, `uvicorn`, `pydantic`
- **`server.py`** - Now reads `PORT` environment variable

## Ready to Deploy!

### Railway (Recommended)
1. Go to: https://railway.app
2. New Project → Deploy from GitHub
3. Select: `mperelman/Thunderclap`
4. Add env var: `GEMINI_API_KEY=your_key`
5. Deploy!

### Render
1. Go to: https://render.com
2. New Web Service → Connect GitHub
3. Select: `mperelman/Thunderclap`
4. Render auto-detects `render.yaml`
5. Add env var: `GEMINI_API_KEY=your_key`
6. Deploy!

## After Deployment

You'll get a backend URL like:
- Railway: `https://thunderclap-production.up.railway.app`
- Render: `https://thunderclap.onrender.com`

**Share this link:**
```
https://mperelman.github.io/Thunderclap/?api=https://YOUR-BACKEND-URL/query
```

## Important Notes

⚠️ **Data Files**: Your `data/` folder (indices, documents) needs to be uploaded separately to the deployed server, or the backend won't have access to the indexed content.

**Options:**
1. Upload `data/` folder to Railway/Render via their file system
2. Or rebuild index on the server after deployment
3. Or use a persistent volume/storage service

