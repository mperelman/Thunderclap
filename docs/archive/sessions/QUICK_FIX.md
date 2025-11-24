# Quick Fix - Enable Narrative Generation

## Problem
Running `ask("question", use_llm=True)` returns search results instead of a narrative.

## One-Time Fix (30 seconds)

**Step 1: Install python-dotenv**
```bash
pip install python-dotenv
```

**Step 2: Create .env file** (already done for you!)
```
✓ .env file created with your GEMINI_API_KEY
```

**Step 3: Test it works**
```bash
python query.py "tell me about black bankers"
```

## Done!

From now on, **every time** you run:
```python
from query import ask
answer = ask("tell me about black bankers", use_llm=True)
```

You'll get a **full narrative**, not just search results.

## What Changed?

1. **Added to `requirements.txt`**: `python-dotenv>=1.0.0`
2. **Updated `query.py`**: Auto-loads `.env` file on import
3. **Created `.env`**: Contains your GEMINI_API_KEY (already in .gitignore)

## How It Works

```
query.py imports
    ↓
load_dotenv() runs automatically  
    ↓
Reads .env file
    ↓
Sets GEMINI_API_KEY environment variable
    ↓
QueryEngine initializes LLM
    ↓
Narratives generate! ✓
```

## Why This Won't Happen Again

**Before:**
- Had to manually set `$env:GEMINI_API_KEY` every terminal session ❌
- Easy to forget ❌
- Lost on terminal restart ❌

**After:**
- API key in `.env` file ✓
- Loads automatically every time ✓
- Persists across sessions ✓
- Standard Python practice ✓

See `docs/API_KEY_SETUP.md` for detailed troubleshooting.

