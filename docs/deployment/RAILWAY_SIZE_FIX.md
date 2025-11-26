# Railway Deployment Size Issue (8GB+)

## The Problem

Railway is reporting 8GB+ image size. This is likely from:

1. **ML Models** - `sentence-transformers` downloads large models (500MB-2GB each)
2. **Python Dependencies** - ChromaDB, NumPy, etc. can be large
3. **Archive Files** - `docs/archive/` has 213 files that don't need to be deployed

## Solution: Use `.railwayignore`

I've created `.railwayignore` to exclude:
- ✅ `data/` folder (rebuild on server or upload separately)
- ✅ `docs/archive/` (213 files - not needed for runtime)
- ✅ `tests/`, `scripts/`, `temp/` (development files)
- ✅ Documentation files (except README.md)

## What Railway Actually Needs

**For runtime, Railway only needs:**
- `server.py` (main server)
- `lib/` (Python modules)
- `requirements.txt` (dependencies)
- `railway.json` (config)
- `Procfile` or start command

**NOT needed:**
- `data/` (rebuild index on server)
- `vectordb/` (rebuild on server)
- `docs/archive/` (213 files)
- `tests/`, `scripts/` (development only)

## Alternative: Reduce Model Size

If still too large, you can:

1. **Use smaller models** in `sentence-transformers`:
   ```python
   # In lib/query_engine.py or wherever models are loaded
   # Use smaller model: 'all-MiniLM-L6-v2' (80MB) instead of larger ones
   ```

2. **Rebuild index on Railway** instead of uploading:
   - Upload only `source_documents/` (or rebuild from scratch)
   - Run `python build_index.py` on Railway after deployment

3. **Use Railway's volume storage** for data:
   - Deploy code separately
   - Upload `data/` folder to Railway volume (persistent storage)

## Check Actual Size

After adding `.railwayignore`, Railway should deploy much smaller:
- Code: ~50-100MB
- Dependencies: ~500MB-1GB (with models)
- **Total: ~1-2GB** (not 8GB)

## Next Steps

1. ✅ `.railwayignore` created - excludes unnecessary files
2. Deploy again - should be much smaller
3. If still large, check Railway build logs for what's being included





