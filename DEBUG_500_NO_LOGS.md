# Debug 500 Error - No Query Logs Appearing

## The Issue

- Health checks work ✅
- Queries return 500 error ❌
- **But no query logs appear** - queries aren't reaching the server or server crashes before logging

## Most Likely Cause: Missing Data Folder

The server crashes when trying to load `data/indices.json` or connect to ChromaDB.

**Check Railway logs for:**
- `[ERROR] Could not find collection 'historical_documents'`
- `[ERROR] Loading indices`
- `Indices not found: data/indices.json`
- Python traceback/crash

## How to Debug

### Step 1: Check Browser Console

1. Open frontend: `https://mperelman.github.io/Thunderclap/?api=https://web-production-c4223.up.railway.app/query`
2. Press **F12** (Developer Tools)
3. Go to **Console** tab
4. Make a query
5. **Share any errors** you see

### Step 2: Check Browser Network Tab

1. In Developer Tools, go to **Network** tab
2. Make a query
3. **Look for `/query` request**:
   - Does it appear? ✅/❌
   - Status code? (500?)
   - Response body?

### Step 3: Check Railway Logs After Query

1. Go to Railway → View Logs
2. **Make a query** from frontend
3. **Immediately refresh** Railway logs
4. **Look for**:
   - `[SERVER] Request ... started`
   - `[ERROR] Could not find collection`
   - `[ERROR] Loading indices`
   - Python tracebacks

## Quick Fix: Create Minimal Data Folder

If `data/` folder is missing, create it:

1. **SSH into Railway** (or use Railway terminal)
2. **Create directories**:
   ```bash
   mkdir -p data/vectordb
   ```
3. **Create minimal `data/indices.json`**:
   ```json
   {"version":"1.0","term_to_chunks":{},"term_index":{},"entity_associations":{}}
   ```
4. **This lets server start** (but queries won't work until full index is built)

## What to Share

1. **Browser Console** - Any JavaScript errors?
2. **Network Tab** - Does `/query` request appear? What's the response?
3. **Railway Logs** - Any error messages after making a query?

The missing `data/` folder is the most likely cause - the server crashes when trying to load it.

