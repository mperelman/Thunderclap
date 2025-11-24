# ✅ Deployment Successful!

## Backend Status
✅ **Server is running** on Railway
✅ **Health check working**: `https://web-production-c4223.up.railway.app/health`
✅ **Port**: 8080 (Railway assigned)

## Connect Frontend to Backend

**Your working GitHub Pages link:**
```
https://mperelman.github.io/Thunderclap/?api=https://web-production-c4223.up.railway.app/query
```

## Test It Now

1. Visit: `https://mperelman.github.io/Thunderclap/?api=https://web-production-c4223.up.railway.app/query`
2. Try a query: "Tell me about Lehman"
3. Check if it works!

## Important: Still Need to Set Up

### 1. GEMINI_API_KEY Environment Variable

1. Go to Railway dashboard
2. Open your Thunderclap service
3. Go to **Variables** tab
4. Add:
   - **Key:** `GEMINI_API_KEY`
   - **Value:** Your API key (from `.env` file)
5. Save - Railway will restart automatically

### 2. Data Folder

⚠️ **Your `data/` folder is NOT deployed** (excluded for size)

**You need to:**

**Option A: Rebuild Index on Railway**
1. Open Railway terminal/SSH
2. Upload `source_documents/` folder (or use existing)
3. Run: `python build_index.py`
4. This rebuilds indices from `source_documents/`

**Option B: Upload Data Folder**
1. Create Railway volume
2. Upload your local `data/` folder
3. Mount it in your service

**Option C: Quick Test - Create Minimal Data**
1. SSH into Railway
2. Create `data/` directory
3. Create minimal `data/indices.json`:
   ```json
   {"version":"1.0","term_to_chunks":{},"term_index":{},"entity_associations":{}}
   ```
4. This lets server start (but queries won't work until full index is built)

## Current Status

✅ Backend deployed and running
✅ Health check working
⏳ Need to set `GEMINI_API_KEY`
⏳ Need to set up `data/` folder

## Share Your Link

Once `GEMINI_API_KEY` and `data/` are set up:
```
https://mperelman.github.io/Thunderclap/?api=https://web-production-c4223.up.railway.app/query
```

