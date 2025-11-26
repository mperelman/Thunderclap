# Railway 502 Error - Application Not Responding

## The Issue

Backend returns: `{"status":"error","code":502,"message":"Application failed to respond"}`

This means Railway deployed the image, but the server isn't starting or crashed.

## Common Causes

1. **Missing Environment Variables**
   - `GEMINI_API_KEY` not set
   - Server crashes on startup

2. **Missing Data Folder**
   - `data/indices.json` doesn't exist
   - Server crashes when trying to load indices

3. **Server Crash on Startup**
   - Import errors
   - Missing dependencies
   - Port binding issues

## How to Fix

### Step 1: Check Railway Logs

1. Go to Railway dashboard
2. Open your Thunderclap service
3. Click **"View Logs"** or **"Deployments"** → **"View Logs"**
4. Look for error messages

**Common errors you might see:**
- `GEMINI_API_KEY environment variable not set!`
- `Could not find collection 'historical_documents'`
- `Indices not found: data/indices.json`
- Import errors or missing modules

### Step 2: Set Environment Variables

1. In Railway dashboard, go to **Variables** tab
2. Add:
   - **Key:** `GEMINI_API_KEY`
   - **Value:** Your API key (from `.env` file)
3. Save - Railway will redeploy automatically

### Step 3: Check Data Folder

The server needs `data/indices.json` to start. Since we excluded `data/` from Docker:

**Option A: Rebuild on Railway**
1. Open Railway terminal/SSH
2. Upload `source_documents/` folder (or use existing)
3. Run: `python build_index.py`

**Option B: Upload Data Folder**
1. Create Railway volume
2. Upload your local `data/` folder
3. Mount it in your service

**Option C: Quick Test - Create Minimal Data**
1. SSH into Railway
2. Create `data/` directory
3. Create minimal `data/indices.json`:
   ```json
   {
     "version": "1.0",
     "term_to_chunks": {},
     "term_index": {},
     "entity_associations": {}
   }
   ```
4. This lets server start (but queries won't work until full index is built)

### Step 4: Check Server Code

Make sure `server.py` handles missing data gracefully:
- Should show helpful error messages
- Should not crash on startup

## Quick Debugging Steps

1. **Check Logs** - See what error Railway shows
2. **Set GEMINI_API_KEY** - Most common issue
3. **Create data/ folder** - Server needs this to start
4. **Redeploy** - After fixing, Railway auto-redeploys

## After Fixing

Once server starts:
- Health check should return: `{"status": "ok"}`
- Frontend link: `https://mperelman.github.io/Thunderclap/?api=https://web-production-c4223.up.railway.app/query`

## Share the Logs

If you can share the Railway logs, I can help identify the exact issue!





