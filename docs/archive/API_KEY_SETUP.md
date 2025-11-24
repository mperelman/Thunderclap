# API Key Setup - Preventing "No Narrative Generated" Issue

## Problem

When you run `ask("question", use_llm=True)` and get back raw search results instead of a narrative, it's because **API keys are not set**.

## Solution: Create a `.env` File (Permanent Fix)

### Step 1: Install python-dotenv

```bash
pip install python-dotenv
```

Or reinstall all requirements:
```bash
pip install -r requirements.txt
```

### Step 2: Create `.env` File

Create a file named `.env` in the project root directory:

```bash
# Windows PowerShell
New-Item -Path .env -ItemType File

# Or manually create it in your text editor
```

### Step 3: Add Your API Key to `.env`

Edit the `.env` file and add:

```env
# Gemini API Key (primary - for narrative generation)
GEMINI_API_KEY=AIzaSyBlqE1F2G_L5l2Lg81gyt0UWcME_K3inFo

# OpenAI API Key (fallback - optional)
# OPENAI_API_KEY=your_openai_api_key_here
```

**Important:** `.env` is already in `.gitignore` - it won't be committed to git!

### Step 4: Verify It Works

```bash
python query.py "tell me about black bankers"
```

Or in Python:
```python
from query import ask

# Will now generate a full narrative (not just search results)
answer = ask("tell me about black bankers", use_llm=True)
print(answer)
```

## Alternative: Set Environment Variable Per Session

If you don't want to use `.env`, set it manually each session:

### PowerShell (Windows)
```powershell
$env:GEMINI_API_KEY='AIzaSyBlqE1F2G_L5l2Lg81gyt0UWcME_K3inFo'
python query.py "tell me about black bankers"
```

### Bash (Linux/Mac)
```bash
export GEMINI_API_KEY='AIzaSyBlqE1F2G_L5l2Lg81gyt0UWcME_K3inFo'
python query.py "tell me about black bankers"
```

**Downside:** You have to set it every time you open a new terminal.

## How It Works

1. **`query.py` auto-loads `.env`** - When you import `query`, it automatically calls `load_dotenv()`
2. **Environment variables are set** - `GEMINI_API_KEY` becomes available to the code
3. **LLM initializes** - `QueryEngine` sees the key and initializes the LLM
4. **Narratives generate** - When `use_llm=True`, actual narratives are generated

## Troubleshooting

### Still Getting Search Results Instead of Narrative?

**Check 1: Is .env file created?**
```bash
# Windows PowerShell
Test-Path .env

# Linux/Mac
ls -la | grep .env
```

**Check 2: Does .env contain the key?**
```bash
# Windows PowerShell
Get-Content .env

# Linux/Mac  
cat .env
```

**Check 3: Is python-dotenv installed?**
```bash
pip list | grep python-dotenv
```

**Check 4: Is the key being loaded?**
```python
import os
from dotenv import load_dotenv
load_dotenv()
print("Key loaded:", "YES" if os.getenv('GEMINI_API_KEY') else "NO")
```

### API Key Not Working?

Try the backup keys (from memory):
```env
# Key 1 (current)
GEMINI_API_KEY=AIzaSyBlqE1F2G_L5l2Lg81gyt0UWcME_K3inFo

# Key 2 (backup)
# GEMINI_API_KEY=AIzaSyD-xExhXC66P-eUuYzx5wwXifBvCwZYGMw

# Key 3 (backup)
# GEMINI_API_KEY=AIzaSyBPeY_SCL9EdpmnDbmeYSI7r5wJ-JaT6Fc
```

## Summary

**Best Practice (Recommended):**
1. Create `.env` file in project root
2. Add `GEMINI_API_KEY=your_key_here`  
3. Run `pip install python-dotenv` (already in requirements.txt)
4. API key loads automatically every time ✓

**Why This Prevents the Issue:**
- ✅ API key persists across terminal sessions
- ✅ No need to remember to set it manually
- ✅ Works consistently for all tools (query.py, notebooks, etc.)
- ✅ Secure (`.env` is in `.gitignore`, won't be committed)
- ✅ Standard practice in Python projects

**Now you'll get proper narratives every time!**


