# Railway Backend URL Setup

## Your Railway URL
**Backend:** `https://web-production-c4223.up.railway.app`

## Test Your Backend

**Health Check:**
```
https://web-production-c4223.up.railway.app/health
```

Should return: `{"status": "ok"}`

## Connect Frontend to Backend

**Use this GitHub Pages link:**
```
https://mperelman.github.io/Thunderclap/?api=https://web-production-c4223.up.railway.app/query
```

## Test It

1. Visit: `https://mperelman.github.io/Thunderclap/?api=https://web-production-c4223.up.railway.app/query`
2. Try a query: "Tell me about Lehman"
3. Check if it works!

## Important: Data Folder Setup

⚠️ **Your `data/` folder is NOT in the Docker image** (excluded for size)

**You need to set up the data folder:**

### Option 1: Rebuild Index on Railway (Recommended)

1. Go to Railway dashboard
2. Open your service
3. Click **"View Logs"** or **"Open Terminal"**
4. Run:
   ```bash
   python build_index.py
   ```
5. This rebuilds indices from `source_documents/`

**Note:** You'll need to upload `source_documents/` folder first, or rebuild from scratch.

### Option 2: Upload Data Folder to Railway Volume

1. Create a Railway volume
2. Upload your local `data/` folder to the volume
3. Mount it in your service

### Option 3: Use Railway File System

1. SSH into Railway
2. Upload `data/` folder via Railway CLI or dashboard
3. Make sure it's in the correct path

## Verify Everything Works

✅ **Backend Health:** `https://web-production-c4223.up.railway.app/health`
✅ **Frontend:** `https://mperelman.github.io/Thunderclap/?api=https://web-production-c4223.up.railway.app/query`
✅ **Test Query:** Try asking a question

## Troubleshooting

**If queries fail:**
- Check Railway logs for errors
- Verify `GEMINI_API_KEY` is set in Railway environment variables
- Check if `data/` folder exists (might need to rebuild index)
- Verify `data/indices.json` exists

**If frontend can't connect:**
- Verify Railway URL is correct
- Check CORS settings (should be `allow_origins=["*"]` in server.py)
- Test backend directly: `curl https://web-production-c4223.up.railway.app/health`

## Share Your Link

Once everything works, share this link:
```
https://mperelman.github.io/Thunderclap/?api=https://web-production-c4223.up.railway.app/query
```





