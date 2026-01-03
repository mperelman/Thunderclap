"""
Thunderclap AI - Web API Server
Run this file to start the server: python server.py
"""
import sys
import os

# Ensure lib is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Request, Response, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict
from collections import defaultdict, deque
import time
import uuid
import json

# Import query engine
from lib.query_engine import QueryEngine
from lib.config import MAX_ANSWER_LENGTH

app = FastAPI(title="Thunderclap AI")

# CORS - Allow requests from GitHub Pages and localhost
# Note: When allow_credentials=True, you cannot use allow_origins=["*"]
# Must specify origins explicitly
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://mperelman.github.io",
        "http://localhost:8000",
        "http://localhost:3000",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],  # expose X-Request-ID to browser
)

# Store API key for creating QueryEngine instances (from env var or .env file)
gemini_key = os.getenv('GEMINI_API_KEY')
if not gemini_key:
    print("ERROR: GEMINI_API_KEY environment variable not set!")
    print("  Set it with: $env:GEMINI_API_KEY='your-key' (PowerShell)")
    print("  Or add it to .env file: GEMINI_API_KEY=your-key")
    sys.exit(1)

print(f"API Key loaded: {gemini_key[:20]}... (length: {len(gemini_key)})")

print("Initializing Thunderclap AI...")

# Auto-rebuild index if source documents changed (in background to avoid blocking startup)
# Only rebuilds when source documents actually change, not on every startup
# This is efficient because:
# 1. Quick file mtime check (~milliseconds) - only checks if index exists
# 2. Server starts immediately, rebuild happens in background only if needed
# 3. Rebuild happens once when documents change, not on every restart
import threading
rebuild_in_progress = False

def background_rebuild():
    """Run rebuild check in background thread (non-blocking). Only rebuilds if source docs changed."""
    global rebuild_in_progress
    try:
        from scripts.auto_rebuild_on_startup import needs_rebuild, rebuild_index
        
        # Quick check: if index doesn't exist, we need to build
        from lib.config import INDICES_FILE
        if not os.path.exists(INDICES_FILE):
            print("\n[STARTUP] No index found - starting background rebuild...")
            rebuild_in_progress = True
            success = rebuild_index()
            rebuild_in_progress = False
            if success:
                print("[STARTUP] ✅ Background rebuild completed successfully!")
            else:
                print("[STARTUP] ⚠️ Background rebuild failed")
            return
        
        # Index exists - check if source documents changed
        print("\n[STARTUP] Checking if source documents changed...")
        if needs_rebuild():
            rebuild_in_progress = True
            print("[STARTUP] Source documents changed - starting background rebuild...")
            success = rebuild_index()
            rebuild_in_progress = False
            if success:
                print("[STARTUP] ✅ Background rebuild completed successfully!")
            else:
                print("[STARTUP] ⚠️ Background rebuild failed, using existing index")
        else:
            # No changes - skip rebuild entirely (most common case)
            print("[STARTUP] ✅ No changes - using existing index")
    except Exception as e:
        rebuild_in_progress = False
        print(f"[STARTUP] ⚠️ Could not check/rebuild index: {e}")
        print("[STARTUP] Continuing with existing index (if available)")

# Start rebuild check in background (non-blocking)
# Only rebuilds if source documents actually changed
rebuild_thread = threading.Thread(target=background_rebuild, daemon=True)
rebuild_thread.start()

print("Server ready! (QueryEngine created per-request)")
print("Note: Index will only rebuild if source documents changed\n")

print("Server ready! (QueryEngine created per-request)\n")

class QueryRequest(BaseModel):
    question: str
    max_length: int = MAX_ANSWER_LENGTH  # Maximum answer length in characters

class QueryJobResponse(BaseModel):
    job_id: str
    status: str
    message: str

class QueryStatusResponse(BaseModel):
    job_id: str
    status: str  # "pending", "processing", "complete", "error"
    answer: Optional[str] = None
    error: Optional[str] = None
    elapsed: Optional[float] = None
    chunk_count: Optional[int] = None  # Number of chunks being processed

# Rate limiting (per-IP, highly relaxed to avoid local dev throttling)
request_counts = defaultdict(list)
RATE_LIMIT = 10000  # requests per hour

def check_rate_limit(ip: str):
    now = time.time()
    hour_ago = now - 3600
    request_counts[ip] = [t for t in request_counts[ip] if t > hour_ago]
    if len(request_counts[ip]) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    request_counts[ip].append(now)

TRACE_BUFFER = deque(maxlen=200)
JOB_STORE: Dict[str, Dict] = {}  # Store job status and results

def trace_event(request_id: str, event: str, **fields):
    entry = {
        "ts": time.time(),
        "request_id": request_id,
        "event": event,
        **fields,
    }
    TRACE_BUFFER.append(entry)
    print("[TRACE]", json.dumps(entry))

@app.get("/")
async def root():
    """Serve the frontend HTML file."""
    import os
    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(html_path):
        from fastapi.responses import FileResponse
        return FileResponse(html_path, media_type="text/html")
    return {
        "service": "Thunderclap AI",
        "version": "2.0",
        "endpoints": {
            "POST /query": "Ask a question",
            "GET /health": "Health check"
        }
    }

@app.get("/health")
async def health():
    return {"status": "ok"}

async def process_query_job(job_id: str, question: str, max_length: int):
    """Background task to process query with timeout protection."""
    import sys
    import asyncio
    from lib.config import QUERY_TIMEOUT_SECONDS
    
    JOB_STORE[job_id]["status"] = "processing"
    JOB_STORE[job_id]["start_time"] = time.time()
    
    try:
        print(f"[JOB {job_id}] Starting query processing (timeout: {QUERY_TIMEOUT_SECONDS}s)...")
        sys.stdout.flush()
        
        # Reload .env file to pick up API key changes
        from dotenv import load_dotenv
        load_dotenv(override=True)  # override=True forces reload
        current_key = os.getenv('GEMINI_API_KEY') or gemini_key
        print(f"[JOB {job_id}] Using API key: {current_key[:20]}... (from .env: {os.getenv('GEMINI_API_KEY') is not None})")
        
        # Force reload modules to pick up code changes without server restart
        # BUT: Don't reload google.generativeai - it will reset its configuration
        # The genai module should be configured fresh in each request anyway
        import importlib
        if 'lib.query_engine' in sys.modules:
            importlib.reload(sys.modules['lib.query_engine'])
        if 'lib.llm' in sys.modules:
            importlib.reload(sys.modules['lib.llm'])
        if 'lib.llm_config' in sys.modules:
            importlib.reload(sys.modules['lib.llm_config'])
        # DO NOT reload google.generativeai - it resets configuration
        # The configure() call in llm.py will set it fresh for each request
        
        from lib.query_engine import QueryEngine
        
        # Wrap query in timeout to prevent runaway queries
        qe = None
        def run_query():
            nonlocal qe
            qe = QueryEngine(gemini_api_key=current_key, use_async=False)
            return qe.query(question, use_llm=True)
        
        # Run query in executor with timeout
        loop = asyncio.get_event_loop()
        try:
            answer = await asyncio.wait_for(
                loop.run_in_executor(None, run_query),
                timeout=QUERY_TIMEOUT_SECONDS - 10  # Leave 10s buffer for cleanup
            )
        except asyncio.TimeoutError:
            elapsed = time.time() - JOB_STORE[job_id]["start_time"]
            error_msg = f"Query timed out after {elapsed:.1f}s (limit: {QUERY_TIMEOUT_SECONDS}s). Query was too complex or retrieved too many chunks. Please simplify your question or break it into smaller parts."
            print(f"[JOB {job_id}] {error_msg}")
            sys.stdout.flush()
            JOB_STORE[job_id]["status"] = "error"
            JOB_STORE[job_id]["error"] = error_msg
            JOB_STORE[job_id]["elapsed"] = elapsed
            return
        
        # Store chunk count for time estimation (if available)
        if qe and hasattr(qe, 'last_chunk_count'):
            JOB_STORE[job_id]["chunk_count"] = qe.last_chunk_count
        
        if len(answer) > max_length:
            answer = answer[:max_length] + "\n\n[Truncated]"
        
        elapsed = time.time() - JOB_STORE[job_id]["start_time"]
        JOB_STORE[job_id]["status"] = "complete"
        JOB_STORE[job_id]["answer"] = answer
        JOB_STORE[job_id]["elapsed"] = elapsed
        
        print(f"[JOB {job_id}] Completed in {elapsed:.1f}s")
        sys.stdout.flush()
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        elapsed = time.time() - JOB_STORE[job_id].get("start_time", time.time())
        
        JOB_STORE[job_id]["status"] = "error"
        JOB_STORE[job_id]["error"] = f"{error_type}: {error_msg}"
        JOB_STORE[job_id]["elapsed"] = elapsed
        
        print(f"[JOB {job_id}] Error: {error_type}: {error_msg}")
        import traceback
        traceback.print_exc()
        sys.stdout.flush()

@app.get("/query/{job_id}", response_model=QueryStatusResponse)
async def get_query_status(job_id: str):
    """Get query job status and result."""
    if job_id not in JOB_STORE:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    job = JOB_STORE[job_id]
    elapsed = None
    if "start_time" in job:
        elapsed = time.time() - job["start_time"]
    
    return QueryStatusResponse(
        job_id=job_id,
        status=job.get("status", "pending"),
        answer=job.get("answer"),
        error=job.get("error"),
        elapsed=elapsed,
        chunk_count=job.get("chunk_count")
    )

@app.post("/query", response_model=QueryJobResponse)
async def query(req: QueryRequest, http_req: Request, background_tasks: BackgroundTasks):
    """Start query processing as background job - returns immediately to avoid Railway timeout."""
    client_ip = http_req.client.host if http_req and http_req.client else "unknown"
    job_id = str(uuid.uuid4())
    
    # Validate input
    if len(req.question) < 3:
        raise HTTPException(status_code=400, detail="Question too short")
    
    # Rate limiting
    try:
        check_rate_limit(client_ip)
    except HTTPException as rl_ex:
        raise
    
    # Create job entry
    JOB_STORE[job_id] = {
        "status": "pending",
        "question": req.question,
        "max_length": req.max_length,
        "created_at": time.time()
    }
    
    # Start background task
    background_tasks.add_task(process_query_job, job_id, req.question, req.max_length)
    
    trace_event(job_id, "job_created", question=req.question[:100])
    print(f"[SERVER] Job {job_id} created for: {req.question[:60]}...")
    import sys
    sys.stdout.flush()
    
    return QueryJobResponse(
        job_id=job_id,
        status="pending",
        message="Query processing started. Poll /query/{job_id} for status."
    )

@app.get("/debug/last")
def debug_last(n: int = 50):
    n = max(1, min(200, n))
    return list(TRACE_BUFFER)[-n:]

@app.get("/debug/job/{job_id}")
def debug_job(job_id: str):
    """Get diagnostic information for a specific job."""
    # Get job info
    job_info = JOB_STORE.get(job_id, {})
    
    # Get traces for this job
    job_traces = [t for t in TRACE_BUFFER if t.get("request_id") == job_id]
    
    return {
        "job_id": job_id,
        "job_info": {
            "status": job_info.get("status"),
            "question": job_info.get("question"),
            "elapsed": job_info.get("elapsed"),
            "chunk_count": job_info.get("chunk_count"),
            "error": job_info.get("error"),
        },
        "traces": job_traces,
        "trace_count": len(job_traces)
    }

@app.get("/status")
def get_status():
    """Get current server status and last query progress."""
    return {
        "status": "running",
        "last_traces": list(TRACE_BUFFER)[-20:],
        "trace_count": len(TRACE_BUFFER)
    }

@app.get("/terms")
def get_indexed_terms():
    """Get list of indexed terms for hyperlinking in responses.
    CRITICAL: Always filter generic terms here - this is the single point of filtering.
    Hyperlinking is based on what this endpoint returns, so filtering here is simpler than
    filtering at multiple stages during indexing."""
    from lib.config import INDICES_FILE
    from lib.constants import GENERIC_WORDS_TO_EXCLUDE, GENERIC_PHRASES_TO_EXCLUDE
    
    def should_exclude_term(term):
        """Check if term should be excluded (word or phrase)."""
        term_lower = term.lower().strip()
        if term_lower in GENERIC_WORDS_TO_EXCLUDE:
            return True
        if term_lower in GENERIC_PHRASES_TO_EXCLUDE:
            return True
        return False
    
    # Load terms from index (or filtered_terms.json if it exists)
    terms = []
    try:
        # Try to load pre-filtered terms first (LLM-filtered list)
        filtered_file = 'lib/filtered_terms.json'
        if not os.path.exists(filtered_file):
            filtered_file = 'data/filtered_terms.json'
        
        if os.path.exists(filtered_file):
            with open(filtered_file, 'r', encoding='utf-8') as f:
                terms = json.load(f)
            print(f"[TERMS] Loaded {len(terms)} terms from {filtered_file}")
        else:
            # Load from indices
            if os.path.exists(INDICES_FILE):
                with open(INDICES_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                terms = list(data.get('term_to_chunks', {}).keys())
                print(f"[TERMS] Loaded {len(terms)} terms from indices")
        
        # CRITICAL: Always filter generic terms here (single point of filtering)
        # This is simpler than filtering at multiple stages during indexing
            # Filter terms: ONLY include meaningful entities/proper nouns, exclude all common words
            filtered_terms = []
            for term in terms:
                # Skip if too short
                if len(term) < 4:
                    continue
            # Skip generic words/phrases (comprehensive list)
            if should_exclude_term(term):
                    continue
            term_lower = term.lower().strip()
                # Skip if it's just a number
                if term_lower.isdigit():
                    continue
                # Skip if it's a single character repeated
                if len(set(term_lower)) == 1:
                    continue
                # Skip if it's a common verb form (ends in -ed, -ing, -s, etc.)
                if term_lower.endswith(('ed', 'ing', 'ly', 'er', 'est', 'tion', 'sion', 'ment', 'ness', 'ity', 'ies', 'ied')):
                    # But allow if it's capitalized (might be a name)
                    if not term[0].isupper():
                        continue
                # ONLY include terms that are clearly entities:
                # 1. Multi-word phrases (e.g., "Bank of Montreal", "David David")
                if ' ' in term:
                    filtered_terms.append(term)
                # 2. Proper nouns (start with capital letter)
                elif term[0].isupper():
                    filtered_terms.append(term)
                # 3. Acronyms (all caps, at least 2 chars)
                elif term.isupper() and len(term) >= 2:
                    filtered_terms.append(term)
                # 4. Mixed case (e.g., "iPhone", "McDonald")
                elif any(c.isupper() for c in term[1:]):
                    filtered_terms.append(term)
                # 5. Lowercase but long and not a common word (likely specific entity)
            elif len(term) >= 8 and not should_exclude_term(term):
                    # Double-check it's not a common word we missed
                    if not term_lower.endswith(('ing', 'ed', 'ly', 'er', 'est')):
                        filtered_terms.append(term)
            
            return {"terms": filtered_terms}
        else:
            return {"terms": []}
    except Exception as e:
        print(f"[ERROR] Failed to load indexed terms: {e}")
        return {"terms": []}

if __name__ == "__main__":
    import uvicorn
    print("="*60)
    print("Starting Thunderclap AI Server")
    print("="*60)
    print("Server: http://localhost:8000")
    print("Press Ctrl+C to stop")
    print("="*60)
    # Railway uses PORT environment variable, default to 8000
    port = int(os.getenv('PORT', 8000))
    # Increase timeout for long-running queries (8 minutes to exceed frontend timeout of 7 minutes)
    # timeout_keep_alive must exceed QUERY_TIMEOUT_SECONDS (420s = 7min) to prevent connection drops
    uvicorn.run(app, host="0.0.0.0", port=port, timeout_keep_alive=480)
