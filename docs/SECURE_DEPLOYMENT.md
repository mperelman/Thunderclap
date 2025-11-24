# Secure Deployment Guide

## Security Goals

✅ **1. No Document Downloads** - Users cannot access original documents or chunks  
✅ **2. No Raw Data Access** - Users cannot see unprocessed text, indices, or database  
✅ **3. No Code Access** - Users cannot view or modify source code  
✅ **4. No Code Changes** - Server-side deployment prevents tampering  

---

## What Gets Protected

### Server-Side (Hidden from users):
- ✅ `data/cache/*.json` - Original document cache
- ✅ `data/indices.json` - All searchable terms and chunk mappings
- ✅ `data/endnotes.json` - 14,094 endnotes
- ✅ `data/vectordb/` - ChromaDB database (1,517 chunks)
- ✅ `lib/*.py` - All source code
- ✅ `.env` - API keys
- ✅ Prompt templates and rules

### Exposed to Users (By Design):
- Generated narratives only
- Suggested follow-up questions
- "Powered by Thunderclap AI" attribution

---

## Protection Methods

### 1. API-Only Architecture

**How it works:**
```
User → Frontend UI → API Request → Your Server → Processes Query → Returns Narrative
```

**User NEVER gets:**
- Raw document text
- Chunk content
- Source code
- Database access

### 2. Files Protected by .gitignore

Current `.gitignore` protects:
- `data/` - All documents and indices
- `.env` - API keys
- `temp/` - Temporary files
- `*.json` - All JSON data files

**Never commit to GitHub:**
- Original documents
- Processed data
- API keys
- .env files

### 3. Deployment Best Practices

**For Private GitHub Repo:**
```bash
# If repo is private, data/ is safe on your machine
# Deploy ONLY the code to cloud
# Upload data/ separately to server (not via Git)
```

**For Public GitHub Repo:**
- `.gitignore` already blocks `data/` from being committed
- Verify: `git status` should NOT show `data/` folder
- Data lives ONLY on your server, never in Git

### 4. Rate Limiting

Prevents abuse:
- 10 requests/hour per user (configurable)
- 50 requests/day per user (configurable)
- Blocks scraping attempts

---

## Deployment Options

### Option A: Streamlit (Simplest)
**Security**: ⭐⭐⭐⭐
- Data stays on server
- Users only see UI
- No code exposed
- **Issue**: Data uploaded to Streamlit Cloud (they can see it)

**Use if**: You trust Streamlit Cloud with your data

### Option B: FastAPI on Railway/Render (Recommended)
**Security**: ⭐⭐⭐⭐⭐
- Full control
- Data on YOUR server only
- API endpoints you control
- Rate limiting
- Access logs

**Use if**: You want maximum control

### Option C: Self-Hosted (Most Secure)
**Security**: ⭐⭐⭐⭐⭐
- Your own server (AWS, DigitalOcean, etc.)
- Complete data isolation
- Custom security rules
- **Cost**: $5-20/month

**Use if**: Handling sensitive/proprietary data

---

## What Cannot Be Protected

### ⚠️ Generated Narratives Are Visible
Users can:
- Copy/paste narratives you generate
- Screenshot results
- Save to their computer

**Mitigation**: Add watermark/attribution to every response

### ⚠️ Reverse Engineering Risk (Low)
If someone makes 1,000+ queries, they could potentially:
- Map out what topics you have
- Reconstruct partial knowledge

**Mitigation**: Rate limiting + monitoring

### ⚠️ Streamlit Cloud Access
If using Streamlit Cloud:
- Your data uploads to their servers
- They theoretically could access it (per their ToS)

**Mitigation**: Use Railway/Render instead

---

## Pre-Deployment Checklist

- [ ] Verify `.gitignore` blocks `data/` folder
- [ ] Check `git status` - ensure no data files staged
- [ ] Copy `env.example` to `.env` with real API keys
- [ ] Test `secure_api.py` locally
- [ ] Set rate limits appropriate for your use case
- [ ] Add frontend domain to CORS whitelist
- [ ] Deploy data separately from code
- [ ] Test that raw endpoints return 404 (not exposed)
- [ ] Monitor initial usage for abuse

---

## Testing Security Locally

```bash
# Start secure API
uvicorn secure_api:app --reload

# Try to access protected endpoints (should fail):
curl http://localhost:8000/docs        # Should return 404
curl http://localhost:8000/chunks      # Should return 404
curl http://localhost:8000/raw-data    # Should return 404

# Valid endpoint (should work):
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "tell me about Lehman"}'
```

---

## Cost Estimate

**Free Tier (Railway/Render):**
- Hosting: FREE
- Storage (335MB): FREE
- API calls: FREE (using your Gemini keys)
- **Total**: $0/month for <500 hours runtime

**If Traffic Grows:**
- Paid Railway: ~$5/month
- More API keys: FREE (Gemini free tier)
- **Total**: <$10/month for moderate use

---

## Questions?

**Q: Can users reconstruct my documents?**  
A: No. They only see LLM-generated narratives, not raw text.

**Q: Can someone hack my server and steal data?**  
A: Use HTTPS, keep packages updated, use strong passwords. Standard web security applies.

**Q: Should I make my GitHub repo private?**  
A: Not necessary if `.gitignore` is correct (data/ is blocked). But private is safer.

**Q: What if Streamlit/Railway goes down?**  
A: Keep local backup of `data/` folder. Redeploy elsewhere.

**Q: Can I add authentication (login)?**  
A: Yes - add JWT auth to `secure_api.py` (requires user accounts).




