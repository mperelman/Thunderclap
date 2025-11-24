# ✅ Railway Deployment Complete!

## Next Steps

### 1. Get Your Railway URL

1. Go to: https://railway.app
2. Open your Thunderclap project
3. Click on your service
4. Go to **Settings** → **Networking**
5. Click **Generate Domain** (if not already generated)
6. Copy your Railway URL (e.g., `https://thunderclap-production.up.railway.app`)

### 2. Update GitHub Pages Frontend

Once you have your Railway URL, update your GitHub Pages link:

```
https://mperelman.github.io/Thunderclap/?api=https://YOUR-RAILWAY-URL/query
```

Replace `YOUR-RAILWAY-URL` with your actual Railway domain.

**Example:**
```
https://mperelman.github.io/Thunderclap/?api=https://thunderclap-production.up.railway.app/query
```

### 3. Test the Connection

1. Visit your GitHub Pages URL with the `?api=` parameter
2. Try a test query: "Tell me about Lehman"
3. Check if it works!

### 4. Important: Data Folder

⚠️ **Your `data/` folder is NOT deployed** (excluded via `.dockerignore`)

**You need to either:**

**Option A: Rebuild Index on Railway**
1. Open Railway terminal/SSH
2. Run: `python build_index.py`
3. This rebuilds indices from `source_documents/`

**Option B: Upload Data Separately**
- Use Railway volumes to upload `data/` folder
- Or mount it as persistent storage

**Option C: Use Pre-built Data**
- If you have the `data/` folder ready, upload it to Railway volume

### 5. Verify Everything Works

✅ Frontend loads: `https://mperelman.github.io/Thunderclap/`
✅ Backend responds: `https://YOUR-RAILWAY-URL/health`
✅ Queries work: Try asking a question

## Troubleshooting

**If queries fail:**
- Check Railway logs for errors
- Verify `GEMINI_API_KEY` is set in Railway environment variables
- Check if `data/` folder exists (might need to rebuild index)

**If frontend can't connect:**
- Verify Railway URL is correct
- Check CORS settings (should be `allow_origins=["*"]` in server.py)
- Test backend directly: `curl https://YOUR-RAILWAY-URL/health`

## Share Your Link!

Once everything works, share this link:
```
https://mperelman.github.io/Thunderclap/?api=https://YOUR-RAILWAY-URL/query
```

