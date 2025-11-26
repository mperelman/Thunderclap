# Static vs Python: How Thunderclap Works

## What "Static" Means

**"Static"** = Files that don't need a server to run. Just HTML, CSS, and JavaScript files that your browser can display directly.

**GitHub Pages hosts STATIC files only:**
- ✅ `index.html` (your frontend UI)
- ✅ CSS styles
- ✅ JavaScript code
- ❌ **NO Python** - GitHub Pages cannot run Python code

## Your Application Has TWO Parts

### Part 1: Frontend (Static - on GitHub Pages)
**File:** `index.html`
**Location:** GitHub Pages (`mperelman.github.io`)
**What it does:**
- Shows the UI (search box, buttons)
- Takes user input
- Makes API calls to your Python backend
- Displays the results

**Code example from `index.html`:**
```javascript
// This JavaScript code runs in the user's browser
const API_URL = 'http://localhost:8000/query';  // Points to Python backend

// When user clicks "Ask Thunderclap":
fetch(API_URL, {
    method: 'POST',
    body: JSON.stringify({ question: "Tell me about Lehman" })
})
.then(response => response.json())
.then(data => {
    // Display the answer from Python backend
    document.getElementById('answer').innerHTML = data.answer;
});
```

### Part 2: Backend (Python - on Railway/Render)
**File:** `server.py`
**Location:** Railway or Render (separate hosting)
**What it does:**
- Receives API requests from the frontend
- Processes queries using Python
- Searches your indexed documents
- Uses LLM to generate answers
- Returns JSON response

**Code example from `server.py`:**
```python
# This Python code runs on Railway/Render server
@app.post("/query")
async def query(req: QueryRequest):
    # Process query using Python
    answer = qe.query(req.question, use_llm=True)
    return {"answer": answer}
```

## How They Work Together

```
┌─────────────────────────────────────────────────────────┐
│  User Types Question: "Tell me about Lehman"            │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  GitHub Pages (Static HTML/JS)                         │
│  - index.html loads in browser                          │
│  - JavaScript sends API request                        │
└─────────────────────────────────────────────────────────┘
                        ↓
              HTTP POST Request
              {question: "Tell me about Lehman"}
                        ↓
┌─────────────────────────────────────────────────────────┐
│  Railway/Render (Python Server)                        │
│  - server.py receives request                          │
│  - Searches indexed documents                          │
│  - Uses LLM to generate answer                        │
│  - Returns JSON: {answer: "Lehman was..."}            │
└─────────────────────────────────────────────────────────┘
                        ↓
              HTTP Response (JSON)
                        ↓
┌─────────────────────────────────────────────────────────┐
│  GitHub Pages (Static HTML/JS)                         │
│  - JavaScript receives answer                         │
│  - Displays answer on page                            │
└─────────────────────────────────────────────────────────┘
```

## Why Two Separate Hosts?

**GitHub Pages:**
- ✅ Free hosting for static files
- ✅ Fast CDN (content delivery network)
- ❌ Cannot run Python code
- ❌ Cannot run server-side code

**Railway/Render:**
- ✅ Can run Python code
- ✅ Can run server-side applications
- ✅ Can access your indexed documents
- ✅ Can call LLM APIs

## Current Setup

**✅ Frontend (Static):**
- `index.html` → GitHub Pages
- URL: `https://mperelman.github.io/Thunderclap/`
- Status: Ready to deploy

**⏳ Backend (Python):**
- `server.py` → Needs deployment to Railway/Render
- URL: `https://your-app.up.railway.app` (after deployment)
- Status: Not deployed yet

## To Make It Work

1. **GitHub Pages** hosts `index.html` (static frontend) ✅
2. **Railway/Render** hosts `server.py` (Python backend) ⏳
3. **Frontend calls backend** via API: `index.html` → `server.py`
4. **Backend returns answer** → Frontend displays it

## Summary

- **"Static"** = HTML/CSS/JS files (no server needed)
- **Python backend** = Runs separately on Railway/Render
- **GitHub Pages** = Only hosts the static frontend
- **Together** = Full working application

Think of it like a restaurant:
- **GitHub Pages** = The dining room (where customers sit)
- **Railway/Render** = The kitchen (where food is prepared)
- **API calls** = Waiters carrying orders between dining room and kitchen





