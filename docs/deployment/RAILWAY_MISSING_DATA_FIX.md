# Railway 500 Error Fix - Missing Data Folder

## The Problem

The container was crashing because the `data/` folder (with ChromaDB collection and indices) is missing on Railway.

**What happened:**
- Server starts ✅
- Health check works ✅
- Query comes in → QueryEngine tries to connect to ChromaDB → **Collection doesn't exist** → Server crashes ❌

## The Fix

I've updated the code to handle missing data gracefully:

1. **QueryEngine initialization** - No longer crashes if collection is missing
   - Sets `self.collection = None` instead of raising exception
   - Server can start even without data

2. **Query method** - Checks if collection exists before processing
   - Returns helpful error message: "Database not initialized. Please run: python build_index.py"

3. **Server error handling** - Catches RuntimeError and returns 503 error
   - Server stays running
   - Returns helpful error message to user

## What You Need to Do

### Option 1: Upload Data Folder to Railway (Recommended)

1. **Build index locally** (if not already done):
   ```bash
   python build_index.py
   ```

2. **Upload `data/` folder to Railway**:
   - Use Railway CLI or web interface
   - Upload entire `data/` folder (includes `vectordb/` and `indices.json`)

3. **Verify**:
   - Check Railway logs for: `[OK] Connected to database (1,509 indexed chunks)`
   - Make a test query

### Option 2: Build Index on Railway

1. **SSH into Railway** (or use Railway terminal)
2. **Install build dependencies**:
   ```bash
   pip install -r requirements-full.txt
   ```
3. **Upload source documents** (if needed)
4. **Run build**:
   ```bash
   python build_index.py
   ```

## Testing

After uploading data, check Railway logs for:
- ✅ `[OK] Connected to database (1,509 indexed chunks)`
- ✅ `[OK] Collection ID: ...`

If you see:
- ❌ `[ERROR] Could not find collection` → Data folder not uploaded correctly
- ❌ `[WARNING] Server will start but queries will fail` → Server starts but queries return 503

## Current Status

- ✅ Server starts without crashing
- ✅ Health check works
- ✅ Queries return helpful error (503) instead of crashing
- ⏳ Waiting for `data/` folder to be uploaded

Once `data/` is uploaded, queries should work!





