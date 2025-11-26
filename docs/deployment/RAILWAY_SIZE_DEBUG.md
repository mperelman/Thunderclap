# Railway Image Size Debugging

## Current Issue
Railway reports 8.2GB image size (exceeds 4GB free tier limit)

## What We've Done
1. ✅ Removed `sentence-transformers` (~1-2GB)
2. ✅ Removed `openai` (not used)
3. ✅ Removed `python-docx`, `tqdm` (indexing only)
4. ✅ Multi-stage Docker build
5. ✅ `.dockerignore` excludes data/, docs/, tests/

## Remaining Large Dependencies

**ChromaDB** might be pulling in:
- `onnxruntime` (~500MB-1GB) - ML runtime
- `sentence-transformers` dependencies (even if not directly installed)
- Other ML libraries

## Solutions

### Option 1: Check Railway Build Logs
Look at Railway build logs to see what's actually being included:
- Which packages are being installed?
- What's the size of each layer?
- Is ChromaDB pulling in onnxruntime?

### Option 2: Use ChromaDB Lite/Client-Only
If ChromaDB server isn't needed, use client-only mode:
```python
# In lib/query_engine.py
# Use HTTP client instead of embedded ChromaDB
```

### Option 3: Split Deployment
- Deploy API server (small, ~500MB)
- Use external ChromaDB (separate service)
- Or use Railway volumes for data

### Option 4: Upgrade Railway Plan
- Free tier: 4GB limit
- Hobby plan: Higher limit (but costs money)

## Next Steps

1. **Check Railway build logs** - see what's actually being installed
2. **Test locally**: Build Docker image locally to check size:
   ```bash
   docker build -t thunderclap-test .
   docker images thunderclap-test
   ```
3. **If ChromaDB is the issue**: Consider using ChromaDB cloud or external service
4. **Alternative**: Use simpler vector DB or pre-computed indices only

## Expected Sizes

- **Python base image**: ~150MB
- **FastAPI + dependencies**: ~50MB
- **ChromaDB**: Could be 500MB-2GB (if includes onnxruntime)
- **Numpy**: ~50MB
- **Total (without ChromaDB bloat)**: ~300-500MB
- **Total (with ChromaDB bloat)**: Could be 2-4GB+

The 8.2GB suggests ChromaDB or Railway is including something unexpected.





