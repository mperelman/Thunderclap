# Railway 500 Error - No Query Logs

## The Problem

- Health checks work: `200 OK` ✅
- Queries return: `500 Internal Server Error` ❌
- **But no query logs appear** - queries aren't reaching the server

## Possible Causes

### 1. CORS Preflight Issue
The browser might be blocking the request before it reaches the server.

**Check:**
- Open browser Developer Tools (F12)
- Go to **Network** tab
- Make a query
- Look for the `/query` request
- Check if it shows:
  - **CORS error** ❌
  - **OPTIONS request failing** ❌
  - **Request blocked** ❌

### 2. Frontend Not Sending Request
The frontend might not be making the request correctly.

**Check:**
- Browser console (F12 → Console)
- Look for JavaScript errors
- Check if `fetch` is being called

### 3. Server Crashing on Request
The server might be crashing when it receives the request (before logging).

**Check Railway logs for:**
- Server restart messages
- Python errors/tracebacks
- Any crash messages

### 4. Data Folder Missing
The server might be crashing when trying to load `data/indices.json`.

**Check Railway logs for:**
- `[ERROR] Could not find collection`
- `[ERROR] Loading indices`
- `Indices not found: data/indices.json`

## How to Debug

### Step 1: Check Browser Console

1. Open frontend: `https://mperelman.github.io/Thunderclap/?api=https://web-production-c4223.up.railway.app/query`
2. Open Developer Tools (F12)
3. Go to **Console** tab
4. Make a query
5. **Look for errors** - share what you see

### Step 2: Check Browser Network Tab

1. In Developer Tools, go to **Network** tab
2. Make a query
3. **Look for `/query` request**:
   - Does it appear? ✅/❌
   - What's the status code?
   - What's the response?

### Step 3: Check Railway Logs

1. Go to Railway → View Logs
2. Make a query from frontend
3. **Immediately refresh Railway logs**
4. **Look for**:
   - `[SERVER] Request ... started`
   - `[DEBUG] Validation error`
   - `[ERROR]` messages
   - Python tracebacks

## Most Likely Issue

**Missing `data/` folder** - The server crashes when trying to load indices.

**Fix:**
1. SSH into Railway
2. Create `data/` directory
3. Create minimal `data/indices.json`:
   ```json
   {"version":"1.0","term_to_chunks":{},"term_index":{},"entity_associations":{}}
   ```
4. Or upload your full `data/` folder

## What to Share

1. **Browser Console errors** (F12 → Console)
2. **Network tab** - Does `/query` request appear?
3. **Railway logs** - Any error messages after making a query?





