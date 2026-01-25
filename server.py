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

from fastapi import FastAPI, HTTPException, Request, Response, BackgroundTasks, UploadFile, File, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict
from collections import defaultdict, deque
import time
import uuid
import json
import shutil

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

# Decompress index if compressed version exists (in scripts/ or data/)
from lib.config import INDICES_FILE
compressed_paths = [
    os.path.join('scripts', 'indices.json.gz'),  # From git
    INDICES_FILE + '.gz'  # Direct upload
]
for compressed_path in compressed_paths:
    if os.path.exists(compressed_path) and not os.path.exists(INDICES_FILE):
        print(f"[STARTUP] Found compressed index at {compressed_path} - decompressing...")
        try:
            import gzip
            with gzip.open(compressed_path, 'rb') as f_in:
                with open(INDICES_FILE, 'wb') as f_out:
                    f_out.write(f_in.read())
            print(f"[STARTUP] ✅ Decompressed index ({os.path.getsize(INDICES_FILE) / 1024 / 1024:.2f} MB)")
            break
        except Exception as e:
            print(f"[STARTUP] ⚠️ Failed to decompress index: {e}")

# Check if ChromaDB collection exists, rebuild if missing
from lib.config import VECTORDB_DIR, COLLECTION_NAME
chromadb_exists_on_startup = False
try:
    import chromadb
    chroma_client_startup = chromadb.PersistentClient(path=VECTORDB_DIR)
    try:
        collection = chroma_client_startup.get_collection(name=COLLECTION_NAME)
        chromadb_exists_on_startup = True
        print(f"[STARTUP] ✅ ChromaDB collection exists ({collection.count():,} chunks)")
    except Exception:
        chromadb_exists_on_startup = False
        print(f"[STARTUP] ⚠️ ChromaDB collection '{COLLECTION_NAME}' not found")
        print(f"[STARTUP] Will rebuild ChromaDB in background (this may take a few minutes)...")
        # Will be handled by background_rebuild below
    finally:
        # CRITICAL: Delete the client to close any open file handles
        # This prevents "readonly database" errors during rebuild
        del chroma_client_startup
        import gc
        gc.collect()  # Force garbage collection to close file handles
except Exception as e:
    chromadb_exists_on_startup = False
    print(f"[STARTUP] ⚠️ Could not check ChromaDB: {e}")

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
        
        # Check if ChromaDB collection is missing (even if index JSON exists)
        from lib.config import VECTORDB_DIR, COLLECTION_NAME
        try:
            import chromadb
            chroma_client = chromadb.PersistentClient(path=VECTORDB_DIR)
            try:
                chroma_client.get_collection(name=COLLECTION_NAME)
                chromadb_exists = True
            except Exception:
                chromadb_exists = False
        except Exception:
            chromadb_exists = False
        
        # Quick check: if index doesn't exist, we need to build
        from lib.config import INDICES_FILE, VECTORDB_DIR
        if not os.path.exists(INDICES_FILE) or not chromadb_exists:
            # Check if we're on Railway - if so, can't rebuild ChromaDB
            is_railway = os.getenv('RAILWAY_ENVIRONMENT') is not None or os.getenv('RAILWAY_PROJECT_ID') is not None
            
            if is_railway and not chromadb_exists:
                print(f"\n[STARTUP] ⚠️ ChromaDB collection missing on Railway")
                print(f"[STARTUP] ⚠️ Railway volumes cannot create ChromaDB databases (SQLite write limitation)")
                print(f"[STARTUP] ⚠️ You must build the database locally and upload it:")
                print(f"[STARTUP]    1. Run 'python build_index.py' locally")
                print(f"[STARTUP]    2. Upload data/vectordb/ directory to Railway volume at /app/data/vectordb/")
                print(f"[STARTUP]    3. Restart Railway service")
                print(f"[STARTUP] ⚠️ Skipping rebuild to avoid error")
                rebuild_in_progress = False
            elif not os.path.exists(INDICES_FILE):
                print("\n[STARTUP] No index found - starting background rebuild...")
                rebuild_in_progress = True
                print(f"[STARTUP] Rebuild started at {time.strftime('%Y-%m-%d %H:%M:%S')}")
                success = rebuild_index()
                rebuild_in_progress = False
                if success:
                    print(f"[STARTUP] ✅ Background rebuild completed successfully at {time.strftime('%Y-%m-%d %H:%M:%S')}!")
                else:
                    print(f"[STARTUP] ⚠️ Background rebuild failed at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                print(f"\n[STARTUP] ChromaDB collection missing - starting background rebuild...")
                print(f"[STARTUP] VECTORDB_DIR: {VECTORDB_DIR}")
                print(f"[STARTUP] VECTORDB_DIR exists: {os.path.exists(VECTORDB_DIR)}")
                rebuild_in_progress = True
                print(f"[STARTUP] Rebuild started at {time.strftime('%Y-%m-%d %H:%M:%S')}")
                success = rebuild_index()
                rebuild_in_progress = False
                if success:
                    print(f"[STARTUP] ✅ Background rebuild completed successfully at {time.strftime('%Y-%m-%d %H:%M:%S')}!")
                    # Verify ChromaDB was created
                    try:
                        chroma_client = chromadb.PersistentClient(path=VECTORDB_DIR)
                        collection = chroma_client.get_collection(name=COLLECTION_NAME)
                        print(f"[STARTUP] ✅ Verified: ChromaDB collection exists with {collection.count()} chunks")
                    except Exception as e:
                        print(f"[STARTUP] ⚠️ WARNING: Rebuild reported success but ChromaDB still missing: {e}")
                else:
                    print(f"[STARTUP] ⚠️ Background rebuild failed at {time.strftime('%Y-%m-%d %H:%M:%S')}")
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
        import traceback
        traceback.print_exc()
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
        
        # Check if ChromaDB exists before creating QueryEngine
        from lib.config import VECTORDB_DIR, COLLECTION_NAME
        try:
            import chromadb
            chroma_client = chromadb.PersistentClient(path=VECTORDB_DIR)
            try:
                chroma_client.get_collection(name=COLLECTION_NAME)
                chromadb_exists = True
            except Exception:
                chromadb_exists = False
        except Exception:
            chromadb_exists = False
        
        if not chromadb_exists:
            if rebuild_in_progress:
                raise RuntimeError("Database is being rebuilt. Please wait a few minutes and try again. Check Railway logs for progress.")
            else:
                # Check if we're on Railway
                is_railway = os.getenv('RAILWAY_ENVIRONMENT') is not None or os.getenv('RAILWAY_PROJECT_ID') is not None
                if is_railway:
                    raise RuntimeError("Database not initialized. Railway volumes cannot create ChromaDB databases. Please build the database locally (python build_index.py) and upload data/vectordb/ to Railway volume at /app/data/vectordb/, then restart the service.")
                else:
                    raise RuntimeError("Database not initialized. The rebuild should start automatically. Please wait a few minutes and try again, or check Railway logs.")
        
        from lib.query_engine import QueryEngine
        
        # Wrap query in timeout to prevent runaway queries
        qe = None
        def run_query():
            nonlocal qe
            qe = QueryEngine(gemini_api_key=current_key, use_async=True)
            max_chunks_override = None
            normalized = question.lower().strip()
            if normalized.startswith("tell me about "):
                subject = normalized.replace("tell me about ", "", 1).strip()
                if subject and len(subject.split()) <= 2:
                    max_chunks_override = 40
            if max_chunks_override:
                print(f"[JOB {job_id}] Using max_chunks={max_chunks_override} for short subject query")
            try:
                if max_chunks_override:
                    return qe.query(question, max_chunks=max_chunks_override, use_llm=True)
                return qe.query(question, use_llm=True)
            except Exception as e:
                error_msg = str(e).lower()
                if any(token in error_msg for token in ("429", "quota", "rate limit")):
                    print(f"[JOB {job_id}] LLM rate limit/quota hit - falling back to raw search results")
                    return qe.query(question, use_llm=False)
                raise
        
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
        
        # Store chunk count and diagnostics for time estimation (if available)
        if qe and hasattr(qe, 'last_chunk_count'):
            JOB_STORE[job_id]["chunk_count"] = qe.last_chunk_count
        if qe and hasattr(qe, 'query_diagnostics'):
            JOB_STORE[job_id]["diagnostics"] = qe.query_diagnostics
            # Also add trace events for key diagnostic info
            try:
                from server import trace_event
                trace_event(job_id, "chunk_retrieval", **qe.query_diagnostics)
            except:
                pass
        
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
    
@app.get("/debug/rebuild-status")
def get_rebuild_status():
    """Get ChromaDB and rebuild status for debugging."""
    from lib.config import VECTORDB_DIR, COLLECTION_NAME, INDICES_FILE
    
    status = {
        "rebuild_in_progress": rebuild_in_progress,
        "index_json_exists": os.path.exists(INDICES_FILE),
        "vectordb_dir_exists": os.path.exists(VECTORDB_DIR),
        "chromadb_exists": False,
        "chromadb_error": None,
    }
    
    # Check ChromaDB
    try:
        import chromadb
        chroma_client = chromadb.PersistentClient(path=VECTORDB_DIR)
        try:
            collection = chroma_client.get_collection(name=COLLECTION_NAME)
            status["chromadb_exists"] = True
            status["chromadb_chunk_count"] = collection.count()
        except Exception as e:
            status["chromadb_error"] = str(e)
    except Exception as e:
        status["chromadb_error"] = f"Failed to connect: {str(e)}"
    
    return status

@app.post("/debug/trigger-rebuild")
@app.get("/debug/trigger-rebuild")  # Also allow GET for easier access
def trigger_rebuild():
    """Manually trigger a rebuild of ChromaDB."""
    global rebuild_in_progress
    
    if rebuild_in_progress:
        return {"status": "error", "message": "Rebuild already in progress"}
    
    # Run rebuild in background thread
    def run_rebuild():
        global rebuild_in_progress
        try:
            rebuild_in_progress = True
            from scripts.auto_rebuild_on_startup import rebuild_index
            print(f"[MANUAL REBUILD] Starting at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            success = rebuild_index()
            rebuild_in_progress = False
            if success:
                print(f"[MANUAL REBUILD] ✅ Completed successfully at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                print(f"[MANUAL REBUILD] ⚠️ Failed at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            rebuild_in_progress = False
            print(f"[MANUAL REBUILD] ❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    import threading
    thread = threading.Thread(target=run_rebuild, daemon=True)
    thread.start()
    
    return {"status": "started", "message": "Rebuild triggered in background. Check logs for progress."}

@app.get("/terms")
def get_indexed_terms():
    """Get list of indexed terms for hyperlinking in responses.
    CRITICAL: Always filter generic terms here - this is the single point of filtering.
    Hyperlinking is based on what this endpoint returns, so filtering here is simpler than
    filtering at multiple stages during indexing."""
    from lib.config import INDICES_FILE, DATA_DIR
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
        # Prefer data/filtered_terms.json (uploaded via API) over lib/filtered_terms.json (from git)
        filtered_file = None
        # Check DATA_DIR first (absolute path)
        data_filtered = os.path.join(DATA_DIR, 'filtered_terms.json')
        print(f"[TERMS] Checking for filtered_terms.json: DATA_DIR={DATA_DIR}, path={data_filtered}, exists={os.path.exists(data_filtered)}")
        if os.path.exists(data_filtered):
            filtered_file = data_filtered
        else:
            # Check lib/ directory (relative to current working directory)
            lib_filtered = os.path.join('lib', 'filtered_terms.json')
            print(f"[TERMS] Checking lib/: {lib_filtered}, exists={os.path.exists(lib_filtered)}")
            if os.path.exists(lib_filtered):
                filtered_file = lib_filtered
            else:
                # Fallback to relative data/ path
                rel_data_filtered = 'data/filtered_terms.json'
                print(f"[TERMS] Checking relative data/: {rel_data_filtered}, exists={os.path.exists(rel_data_filtered)}")
                if os.path.exists(rel_data_filtered):
                    filtered_file = rel_data_filtered
        
        if filtered_file and os.path.exists(filtered_file):
            try:
                print(f"[TERMS] Attempting to load from {filtered_file}")
                with open(filtered_file, 'r', encoding='utf-8') as f:
                    terms = json.load(f)
                if not isinstance(terms, list):
                    print(f"[TERMS] ERROR: {filtered_file} is not a list, got {type(terms)}")
                    terms = []
                else:
                    print(f"[TERMS] Successfully loaded {len(terms)} terms from {filtered_file}")
            except json.JSONDecodeError as e:
                print(f"[TERMS] JSON decode error loading {filtered_file}: {e}")
                filtered_file = None  # Fall through to indices loading
                terms = []
            except Exception as e:
                print(f"[TERMS] Error loading {filtered_file}: {e}")
                import traceback
                traceback.print_exc()
                filtered_file = None  # Fall through to indices loading
                terms = []
        
        if not filtered_file or not terms:
            print(f"[TERMS] No filtered_terms.json loaded, loading from indices. INDICES_FILE={INDICES_FILE}, exists={os.path.exists(INDICES_FILE)}")
            # Load from indices
            if os.path.exists(INDICES_FILE):
                try:
                    with open(INDICES_FILE, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    terms = list(data.get('term_to_chunks', {}).keys())
                    print(f"[TERMS] Loaded {len(terms)} terms from indices")
                except Exception as e:
                    print(f"[TERMS] Error loading indices: {e}")
                    import traceback
                    traceback.print_exc()
                    terms = []
            else:
                # No index file - use empty list
                terms = []
                print(f"[TERMS] No index file found at {INDICES_FILE} - using empty terms list")
        
        print(f"[TERMS] Final terms count before processing: {len(terms)}")
        
        # CRITICAL: Always filter generic terms here (single point of filtering)
        # This is simpler than filtering at multiple stages during indexing
        # Filter terms: ONLY include meaningful entities/proper nouns, exclude all common words
        
        # First, normalize terms: merge underscore/space variants, normalize apostrophes, merge case variants
        # This handles "Protected Jew" vs "Protected_Jew", "Farmers'" vs "Farmers'", "ROTHSCHILD" vs "Rothschild"
        normalized_terms_pre = {}
        for term in terms:
            # Normalize: replace underscores with spaces, normalize apostrophes, strip trailing apostrophes
            normalized = term.replace('_', ' ').replace("'", "'").replace("'", "'")
            # Strip trailing apostrophes (e.g., "Morgan Grenfell'" -> "Morgan Grenfell")
            normalized = normalized.rstrip("'").rstrip("'")
            
            # For proper nouns (single-word, all caps), normalize to proper case
            # "ROTHSCHILD" -> "Rothschild"
            # But preserve mixed-case distinctions (DuPont vs Dupont stay separate)
            if normalized.isupper() and len(normalized.split()) == 1 and len(normalized) > 2:
                normalized = normalized.capitalize()
            
            # For firm names, also normalize "Co" variants
            # "Farmers' Loan & Trust" and "Farmers' Loan & Trust Co" should merge
            if normalized.endswith(' Co') or normalized.endswith(' Company'):
                base = normalized.rsplit(' Co', 1)[0].rsplit(' Company', 1)[0].strip()
                if base:
                    normalized_terms_pre[base] = normalized_terms_pre.get(base, []) + [term]
                    continue
            
            # For single-word proper nouns, merge singular/plural variants
            # "Rothschild" and "Rothschilds" should merge (use singular as base)
            # But preserve case (DuPont vs Dupont stay separate)
            if len(normalized.split()) == 1 and normalized[0].isupper():
                base_key = normalized
                # If plural, use singular as base
                if normalized.lower().endswith('s') and not normalized.lower().endswith("'s") and len(normalized) > 3:
                    base_key = normalized[:-1]
                # Store with base key, but keep original term in variants
                if base_key not in normalized_terms_pre:
                    normalized_terms_pre[base_key] = []
                normalized_terms_pre[base_key].append(term)
            else:
                # Multi-word or lowercase - keep as is
                normalized_terms_pre[normalized] = normalized_terms_pre.get(normalized, []) + [term]
        
        # No offensive terms to filter - terms in TERM_GROUPS (like "jewless") will merge automatically
        filtered_terms_pre = {}
        for normalized, variants in normalized_terms_pre.items():
            # Filter out generic phrases like "National Women" (should just be "Women")
            if normalized.lower() in ['national women', 'national woman']:
                continue
            filtered_terms_pre[normalized] = variants
        
        # Now deduplicate case variants using TERM_GROUPS
        # This ensures "BLACK", "Black", "black", "Blacks", "blacks" all become one entry
        from lib.index_builder import TERM_GROUPS
        term_normalization_map = {}
        for main_term, variants in TERM_GROUPS.items():
            # Map all variants to the main term
            term_normalization_map[main_term] = main_term
            for variant in variants:
                term_normalization_map[variant] = main_term
                # Also map uppercase and capitalized versions
                term_normalization_map[variant.upper()] = main_term
                term_normalization_map[variant.capitalize()] = main_term
                # Also map Title Case for multi-word terms
                if ' ' in variant:
                    term_normalization_map[variant.title()] = main_term
                # Map all-caps single words (e.g., "JEWLESS" -> "jewish")
                if ' ' not in variant:
                    term_normalization_map[variant.upper()] = main_term
        
        # Normalize terms: use TERM_GROUPS main term if available, otherwise keep original
        # First pass: collect all variants for each normalized term
        term_variants = {}  # normalized -> list of all variants
        for normalized, variants in filtered_terms_pre.items():
            term_lower = normalized.lower().strip()
            # Check if this term (or its lowercase) is in TERM_GROUPS
            if term_lower in term_normalization_map:
                normalized_key = term_normalization_map[term_lower]
                if normalized_key not in term_variants:
                    term_variants[normalized_key] = []
                term_variants[normalized_key].extend(variants)
            else:
                # Not in TERM_GROUPS, keep original normalized form
                # (Singular/plural merging already done in first normalization pass)
                if normalized not in term_variants:
                    term_variants[normalized] = []
                term_variants[normalized].extend(variants)
        
        # Second pass: for each normalized term, pick the best display version
        # Prefer: capitalized plural > capitalized singular > space version (not underscore) > lowercase
        normalized_terms = {}
        for normalized, variants in term_variants.items():
            # Normalize all variants (replace underscores with spaces, normalize apostrophes, strip trailing apostrophes)
            normalized_variants = [v.replace('_', ' ').replace("'", "'").replace("'", "'").rstrip("'").rstrip("'") for v in variants]
            # Remove duplicates while preserving order
            seen = set()
            unique_variants = []
            for v in normalized_variants:
                if v not in seen:
                    seen.add(v)
                    unique_variants.append(v)
            
            # Find plural variants (capitalized preferred, no underscores)
            plural_capitalized = [v for v in unique_variants if v.lower().endswith('s') and not v.lower().endswith("'s") and v[0].isupper() and not v.isupper() and '_' not in v]
            plural_lowercase = [v for v in unique_variants if v.lower().endswith('s') and not v.lower().endswith("'s") and v.islower() and '_' not in v]
            # Find singular capitalized variants (no underscores)
            singular_capitalized = [v for v in unique_variants if not v.lower().endswith('s') and v[0].isupper() and not v.isupper() and '_' not in v]
            singular_lowercase = [v for v in unique_variants if not v.lower().endswith('s') and v.islower() and '_' not in v]
            # Find any variant without underscores (prefer spaces over underscores)
            no_underscore = [v for v in unique_variants if '_' not in v]
            
            # Determine if this is an identity term (should prefer plural) or a surname (should prefer singular)
            # Identity terms are in TERM_GROUPS, surnames are typically single capitalized words
            is_identity_term = term_lower in term_normalization_map
            is_likely_surname = len(normalized.split()) == 1 and normalized[0].isupper() and not is_identity_term
            
            # Pick best display version
            if is_likely_surname:
                # For surnames, prefer singular form
                if singular_capitalized:
                    normalized_terms[normalized] = singular_capitalized[0]  # "Seligman"
                elif singular_lowercase:
                    normalized_terms[normalized] = singular_lowercase[0].capitalize()  # "seligman" -> "Seligman"
                elif plural_capitalized:
                    # Fallback to plural if no singular exists
                    normalized_terms[normalized] = plural_capitalized[0]  # "Seligmans"
                elif plural_lowercase:
                    normalized_terms[normalized] = plural_lowercase[0].capitalize()  # "seligmans" -> "Seligmans"
                elif no_underscore:
                    normalized_terms[normalized] = no_underscore[0]
                else:
                    normalized_terms[normalized] = unique_variants[0] if unique_variants else normalized
            else:
                # For identity terms and other terms, prefer plural
                # BUT: For multi-word identity terms like "court jew", prefer singular form (not "court jews")
                # Check if this is a multi-word identity term that should use singular
                is_multi_word_identity = is_identity_term and ' ' in normalized
                
                # Filter out all-caps variants for identity terms (e.g., "JEWLESS" -> prefer "Jews" or "Jewish")
                # All-caps single words are likely indexing artifacts, not proper display terms
                filtered_variants = unique_variants
                if is_identity_term:
                    # Remove all-caps single-word variants (they're indexing artifacts)
                    filtered_variants = [v for v in unique_variants if not (v.isupper() and ' ' not in v)]
                    if not filtered_variants:
                        filtered_variants = unique_variants  # Fallback if all were filtered
                
                if is_multi_word_identity:
                    # For multi-word identity terms, prefer singular capitalized form
                    singular_capitalized_filtered = [v for v in filtered_variants if not v.lower().endswith('s') and v[0].isupper() and not v.isupper() and '_' not in v]
                    singular_lowercase_filtered = [v for v in filtered_variants if not v.lower().endswith('s') and v.islower() and '_' not in v]
                    if singular_capitalized_filtered:
                        normalized_terms[normalized] = singular_capitalized_filtered[0]  # "Court Jew" not "Court Jews"
                    elif singular_lowercase_filtered:
                        normalized_terms[normalized] = singular_lowercase_filtered[0].title()  # "court jew" -> "Court Jew"
                    elif plural_capitalized:
                        normalized_terms[normalized] = plural_capitalized[0]  # Fallback to plural
                    elif plural_lowercase:
                        normalized_terms[normalized] = plural_lowercase[0].title()  # "court jews" -> "Court Jews"
                    else:
                        normalized_terms[normalized] = unique_variants[0] if unique_variants else normalized
                elif plural_capitalized:
                    normalized_terms[normalized] = plural_capitalized[0]  # "Blacks"
                elif plural_lowercase:
                    # For multi-word terms, use title case; for single-word, capitalize first letter
                    if ' ' in plural_lowercase[0]:
                        normalized_terms[normalized] = plural_lowercase[0].title()  # "protected jews" -> "Protected Jews"
                    else:
                        normalized_terms[normalized] = plural_lowercase[0].capitalize()  # "blacks" -> "Blacks"
                elif singular_capitalized:
                    normalized_terms[normalized] = singular_capitalized[0]  # "Black", "Protected Jew"
                elif singular_lowercase:
                    # For multi-word terms, use title case; for single-word, capitalize first letter
                    if ' ' in singular_lowercase[0]:
                        normalized_terms[normalized] = singular_lowercase[0].title()  # "protected jew" -> "Protected Jew"
                    else:
                        normalized_terms[normalized] = singular_lowercase[0].capitalize()  # "black" -> "Black"
                elif no_underscore:
                    # Prefer space version over underscore version, and ensure proper capitalization
                    if ' ' in no_underscore[0] and no_underscore[0].islower():
                        normalized_terms[normalized] = no_underscore[0].title()  # "protected jew" -> "Protected Jew"
                    else:
                        normalized_terms[normalized] = no_underscore[0]
                else:
                    # Fallback: use first variant or normalized term, with proper capitalization
                    if unique_variants:
                        fallback = unique_variants[0]
                        if ' ' in fallback and fallback.islower():
                            normalized_terms[normalized] = fallback.title()  # "protected jew" -> "Protected Jew"
                        else:
                            normalized_terms[normalized] = fallback
                    else:
                        # Use normalized term with proper capitalization
                        if ' ' in normalized and normalized.islower():
                            normalized_terms[normalized] = normalized.title()  # "protected jew" -> "Protected Jew"
                        else:
                            normalized_terms[normalized] = normalized
        
        # Now filter the normalized terms
        # CRITICAL: Only include terms that have chunks associated with them
        # Load term_to_chunks to check chunk counts (reuse data if already loaded)
        term_to_chunks_for_filter = {}
        if os.path.exists(INDICES_FILE):
            with open(INDICES_FILE, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
                term_to_chunks_for_filter = index_data.get('term_to_chunks', {})
        
        filtered_terms = []
        seen_lower = set()  # Track lowercase to avoid duplicates
        for normalized_key, display_term in normalized_terms.items():
            # CRITICAL: Skip generic phrases that should only appear as part of longer firm names
            # "Central Bank" and "National Bank" should not be hyperlinked standalone
            if normalized_key.lower() in ['central bank', 'national bank']:
                # Only allow if there's a longer variant (e.g., "Central Bank of Chile")
                has_longer_variant = False
                for other_term in normalized_terms.keys():
                    if other_term.lower() != normalized_key.lower() and normalized_key.lower() in other_term.lower():
                        has_longer_variant = True
                        break
                if not has_longer_variant:
                    continue  # Skip standalone "Central Bank" or "National Bank"
            
            # CRITICAL: Skip terms with 0 chunks - they shouldn't appear in autofill
            # Check all variants of the normalized term to see if any have chunks
            has_chunks = False
            # Check normalized key first
            if normalized_key in term_to_chunks_for_filter and len(term_to_chunks_for_filter[normalized_key]) > 0:
                has_chunks = True
            else:
                # Check all original variants (before normalization)
                all_variants = term_variants.get(normalized_key, [normalized_key])
                for variant in all_variants:
                    # Check original variant
                    if variant in term_to_chunks_for_filter and len(term_to_chunks_for_filter[variant]) > 0:
                        has_chunks = True
                        break
                    # Also check normalized version of variant (underscore -> space)
                    variant_normalized = variant.replace('_', ' ').replace("'", "'").replace("'", "'")
                    if variant_normalized != variant and variant_normalized in term_to_chunks_for_filter and len(term_to_chunks_for_filter[variant_normalized]) > 0:
                        has_chunks = True
                        break
            
            if not has_chunks:
                continue  # Skip terms with no chunks
            
            # Skip if too short (but allow 2-3 char proper nouns like "Li", "Wu")
            # Only skip if it's a single lowercase word (likely not a proper noun)
            if len(display_term) < 2:
                continue
            # Skip 2-3 char terms that are all lowercase (likely not proper nouns)
            if len(display_term) < 4 and display_term.islower():
                continue
            # Skip generic words/phrases (comprehensive list)
            if should_exclude_term(display_term):
                continue
            term_lower = display_term.lower().strip()
            # Skip if we've already added this (case-insensitive)
            if term_lower in seen_lower:
                continue
            seen_lower.add(term_lower)
            # Skip if it's just a number
            if term_lower.isdigit():
                continue
            # Skip if it's a single character repeated
            if len(set(term_lower)) == 1:
                continue
            # Skip if it's a common verb form (ends in -ed, -ing, -s, etc.)
            if term_lower.endswith(('ed', 'ing', 'ly', 'er', 'est', 'tion', 'sion', 'ment', 'ness', 'ity', 'ies', 'ied')):
                # But allow if it's capitalized (might be a name)
                if not display_term[0].isupper():
                    continue
            # ONLY include terms that are clearly entities:
            # 1. Multi-word phrases (e.g., "Bank of Montreal", "David David")
            if ' ' in display_term:
                filtered_terms.append(display_term)
            # 2. Proper nouns (start with capital letter)
            elif display_term[0].isupper():
                filtered_terms.append(display_term)
            # 3. Acronyms (all caps, at least 2 chars)
            elif display_term.isupper() and len(display_term) >= 2:
                filtered_terms.append(display_term)
            # 4. Mixed case (e.g., "iPhone", "McDonald")
            elif any(c.isupper() for c in display_term[1:]):
                filtered_terms.append(display_term)
            # 5. Lowercase but long and not a common word (likely specific entity)
            elif len(display_term) >= 8 and not should_exclude_term(display_term):
                # Double-check it's not a common word we missed
                if not term_lower.endswith(('ing', 'ed', 'ly', 'er', 'est')):
                    filtered_terms.append(display_term)

        # Build identity cross-references for autofill
        # Load identity detection results to map surnames <-> identities
        identity_metadata = {}
        surname_to_identities = {}  # "parsons" -> ["black"]
        identity_to_surnames = {}   # "black" -> ["parsons", "mcguire", ...]
        
        from lib.config import DATA_DIR
        identity_file = os.path.join(DATA_DIR, 'identity_detection_v3.json')
        
        # Fallback to local data directory if DATA_DIR doesn't work (e.g. on some deployments)
        if not os.path.exists(identity_file):
            local_identity_file = os.path.join('data', 'identity_detection_v3.json')
            if os.path.exists(local_identity_file):
                identity_file = local_identity_file
            else:
                # Try relative to current working directory
                cwd_identity_file = os.path.join(os.getcwd(), 'data', 'identity_detection_v3.json')
                if os.path.exists(cwd_identity_file):
                    identity_file = cwd_identity_file
        
        print(f"[IDENTITY] Looking for identity file at: {identity_file}")
        print(f"[IDENTITY] File exists: {os.path.exists(identity_file)}")
        print(f"[IDENTITY] DATA_DIR: {DATA_DIR}")
        print(f"[IDENTITY] CWD: {os.getcwd()}")
        
        if os.path.exists(identity_file):
            try:
                with open(identity_file, 'r', encoding='utf-8') as f:
                    identity_data = json.load(f)
                
                print(f"[INFO] ✅ Loaded identity data from {identity_file}")
                print(f"[INFO] File size: {os.path.getsize(identity_file)} bytes")
                
                # Build surname -> identities mapping from surname_to_identity
                # Structure: {"parsons": ["black"], "mcguire": ["black", "irish"], ...}
                surname_to_identity_data = identity_data.get('surname_to_identity', {})
                for surname, identities_list in surname_to_identity_data.items():
                    surname_lower = surname.lower()
                    # Build surname -> identities mapping
                    if surname_lower not in surname_to_identities:
                        surname_to_identities[surname_lower] = []
                    for identity in identities_list:
                        identity_lower = identity.lower()
                        if identity_lower not in surname_to_identities[surname_lower]:
                            surname_to_identities[surname_lower].append(identity_lower)
                        
                        # Build identity -> surnames mapping (capitalize for display)
                        if identity_lower not in identity_to_surnames:
                            identity_to_surnames[identity_lower] = []
                        surname_display = surname.capitalize() if surname else surname
                        if surname_display not in identity_to_surnames[identity_lower]:
                            identity_to_surnames[identity_lower].append(surname_display)
            except Exception as e:
                print(f"[WARN] Failed to load identity metadata: {e}")
                import traceback
                traceback.print_exc()
        
        # Debug: Log what we loaded
        print(f"[IDENTITY] Loaded {len(surname_to_identities)} surnames, {len(identity_to_surnames)} identities")
        if surname_to_identities:
            sample_surname = list(surname_to_identities.keys())[0]
            print(f"[IDENTITY] Sample: '{sample_surname}' -> {surname_to_identities[sample_surname]}")
        
        # Add identity metadata to terms
        # First, build a normalization map from TERM_GROUPS to check identity terms
        from lib.index_builder import TERM_GROUPS
        identity_normalization_map = {}
        for main_term, variants in TERM_GROUPS.items():
            identity_normalization_map[main_term] = main_term
            for variant in variants:
                identity_normalization_map[variant.lower()] = main_term
        
        # Debug: Check if "blacks" normalizes correctly
        if 'blacks' in identity_normalization_map:
            print(f"[IDENTITY] 'blacks' normalizes to: {identity_normalization_map['blacks']}")
        if 'black' in identity_to_surnames:
            print(f"[IDENTITY] 'black' has {len(identity_to_surnames['black'])} related surnames")
            print(f"[IDENTITY] Sample: {identity_to_surnames['black'][:5]}")
        
        metadata_count = 0
        for term in filtered_terms:
            term_lower = term.lower()
            metadata = {}
            
            # If term is a surname, add its identities
            if term_lower in surname_to_identities:
                identities = surname_to_identities[term_lower]
                metadata['identities'] = identities
                
                # Detect if this surname likely represents multiple unrelated families
                # by checking for contradictory identity combinations
                if len(identities) > 5:  # High identity count suggests fusion
                    # Check for contradictory religious groups
                    major_religions = {'jewish', 'ashkenazi', 'sephardi', 'muslim', 'islam', 'hindu', 'christian', 'catholic', 'protestant', 'puritan', 'quaker', 'huguenot'}
                    found_religions = {id.lower() for id in identities if id.lower() in major_religions}
                    
                    # Contradictory combinations that suggest different families:
                    # - Jewish + Hindu (e.g., Ashkenazi + Brahmin if Hindu)
                    # - Jewish + Muslim
                    # - Hindu + Muslim
                    # - Multiple Jewish subgroups from different regions (Ashkenazi + Sephardi could be same family, but rare)
                    has_jewish = any('jew' in id.lower() or id.lower() in {'ashkenazi', 'sephardi'} for id in identities)
                    has_hindu = any(id.lower() in {'hindu', 'brahmin', 'bania'} for id in identities)
                    has_muslim = any('muslim' in id.lower() or id.lower() in {'islam', 'sunni', 'shia'} for id in identities)
                    
                    # If we have multiple major religions, likely fusion
                    religion_count = sum([has_jewish, has_hindu, has_muslim])
                    if religion_count >= 2:
                        metadata['_likely_fusion'] = True
                        metadata['_fusion_reason'] = f"Multiple major religions detected ({religion_count}): {', '.join(found_religions)}"
                
                metadata_count += 1
            
            # If term is an identity, add related surnames (filter to only surnames in index, limit to 20 for autofill)
            # Check both the exact term and its normalized form (e.g., "blacks" -> "black")
            identity_key = identity_normalization_map.get(term_lower, term_lower)
            if identity_key in identity_to_surnames:
                # Filter to only surnames that actually exist in filtered_terms (indexed)
                all_related = identity_to_surnames[identity_key]
                filtered_related = [s for s in all_related if s in filtered_terms or s.lower() in [t.lower() for t in filtered_terms]]
                metadata['related_surnames'] = filtered_related[:30]  # Increased limit to include more surnames
                metadata_count += 1
            elif term_lower in identity_to_surnames:
                # Fallback: check exact match
                all_related = identity_to_surnames[term_lower]
                filtered_related = [s for s in all_related if s in filtered_terms or s.lower() in [t.lower() for t in filtered_terms]]
                metadata['related_surnames'] = filtered_related[:30]  # Increased limit to include more surnames
                metadata_count += 1
            
            if metadata:
                identity_metadata[term] = metadata
        
        print(f"[IDENTITY] Attached metadata to {metadata_count} terms, {len(identity_metadata)} total entries")
        
        # Debug: Log some metadata examples
        if identity_metadata:
            sample_terms = [t for t in list(identity_metadata.keys())[:5] if identity_metadata[t].get('identities')]
            if sample_terms:
                print(f"[DEBUG] Sample terms with identity metadata: {sample_terms}")
            sample_identities = [t for t in list(identity_metadata.keys())[:5] if identity_metadata[t].get('related_surnames')]
            if sample_identities:
                print(f"[DEBUG] Sample identity terms with related surnames: {sample_identities}")
        
        if filtered_terms:
            return {
                "terms": filtered_terms,
                "identity_metadata": identity_metadata
            }
        return {"terms": [], "identity_metadata": {}}
    except Exception as e:
        print(f"[ERROR] Failed to load indexed terms: {e}")
        import traceback
        traceback.print_exc()
        return {"terms": [], "identity_metadata": {}}

@app.get("/debug/identity-status")
def debug_identity_status():
    """Debug endpoint to check identity metadata loading status."""
    from lib.config import DATA_DIR
    import os
    
    identity_file = os.path.join(DATA_DIR, 'identity_detection_v3.json')
    if not os.path.exists(identity_file):
        local_identity_file = os.path.join('data', 'identity_detection_v3.json')
        if os.path.exists(local_identity_file):
            identity_file = local_identity_file
        else:
            cwd_identity_file = os.path.join(os.getcwd(), 'data', 'identity_detection_v3.json')
            if os.path.exists(cwd_identity_file):
                identity_file = cwd_identity_file
    
    # List files in data directory
    data_files = []
    if os.path.exists(DATA_DIR):
        try:
            data_files = os.listdir(DATA_DIR)
        except:
            pass
    
    result = {
        "identity_file_path": identity_file,
        "file_exists": os.path.exists(identity_file),
        "data_dir": DATA_DIR,
        "cwd": os.getcwd(),
        "data_dir_exists": os.path.exists(DATA_DIR),
        "data_dir_files": sorted(data_files)[:20],  # First 20 files
    }
    
    if os.path.exists(identity_file):
        try:
            with open(identity_file, 'r', encoding='utf-8') as f:
                identity_data = json.load(f)
            result["file_size"] = os.path.getsize(identity_file)
            result["has_surname_to_identity"] = 'surname_to_identity' in identity_data
            result["surname_count"] = len(identity_data.get('surname_to_identity', {}))
            result["parsons_in_file"] = 'parsons' in identity_data.get('surname_to_identity', {})
            if 'parsons' in identity_data.get('surname_to_identity', {}):
                result["parsons_identities"] = identity_data['surname_to_identity']['parsons']
        except Exception as e:
            result["error"] = str(e)
            import traceback
            result["traceback"] = traceback.format_exc()
    
    # Also check what get_indexed_terms returns
    try:
        terms_result = get_indexed_terms()
        result["terms_count"] = len(terms_result.get('terms', []))
        result["metadata_count"] = len(terms_result.get('identity_metadata', {}))
        result["parsons_in_metadata"] = 'Parsons' in terms_result.get('identity_metadata', {})
        result["parsons_in_terms"] = 'Parsons' in terms_result.get('terms', [])
    except Exception as e:
        result["terms_error"] = str(e)
    
    return result

@app.post("/admin/upload-database")
async def upload_database(file: UploadFile = File(...), content_encoding: Optional[str] = Header(None)):
    """Upload ChromaDB database file (chroma.sqlite3) via HTTP."""
    from lib.config import VECTORDB_DIR
    
    try:
        # Read file content
        content = await file.read()
        
        # Handle gzip compression if present
        if content_encoding == "gzip":
            import gzip
            content = gzip.decompress(content)
        elif len(content) >= 2 and content[0] == 0x1f and content[1] == 0x8b:
            # Auto-detect gzip by magic bytes
            import gzip
            content = gzip.decompress(content)
        
        # Ensure vectordb directory exists
        os.makedirs(VECTORDB_DIR, exist_ok=True)
        
        # Write database file
        db_path = os.path.join(VECTORDB_DIR, "chroma.sqlite3")
        with open(db_path, "wb") as f:
            f.write(content)
        
        file_size_mb = len(content) / 1024 / 1024
        
        print(f"[UPLOAD] Successfully uploaded database ({file_size_mb:.2f} MB)")
        
        return {
            "status": "success",
            "message": f"Database uploaded successfully ({file_size_mb:.2f} MB)",
            "path": db_path,
            "size_bytes": len(content)
        }
    except Exception as e:
        print(f"[UPLOAD ERROR] Database upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/admin/upload-index")
async def upload_index(file: UploadFile = File(...)):
    """
    Upload a new indices.json file to replace the existing one.
    This endpoint allows updating the index without redeploying.
    """
    from lib.config import INDICES_FILE, DATA_DIR
    
    # Ensure data directory exists
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Validate filename (accept both .json and .json.gz)
    if file.filename not in ["indices.json", "indices.json.gz"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Expected filename 'indices.json' or 'indices.json.gz', got '{file.filename}'"
        )
    
    # Read and validate JSON
    try:
        content = await file.read()
        
        # Check if file is gzip-compressed (magic bytes: 1f 8b)
        import gzip
        if len(content) >= 2 and content[0] == 0x1f and content[1] == 0x8b:
            # Decompress gzip
            content = gzip.decompress(content)
        
        data = json.loads(content)
        
        # Basic validation - check for required keys
        if not isinstance(data, dict):
            raise ValueError("Root must be a dictionary")
        if 'term_to_chunks' not in data:
            raise ValueError("Missing 'term_to_chunks' key")
        if 'entity_associations' not in data:
            raise ValueError("Missing 'entity_associations' key")
        
        # Write to temporary file first, then rename (atomic operation)
        temp_path = INDICES_FILE + ".tmp"
        with open(temp_path, 'wb') as f:
            f.write(content)
        
        # Atomic rename
        if os.path.exists(INDICES_FILE):
            os.replace(temp_path, INDICES_FILE)
        else:
            os.rename(temp_path, INDICES_FILE)
        
        term_count = len(data.get('term_to_chunks', {}))
        print(f"[UPLOAD] Successfully uploaded indices.json with {term_count} terms")
        
        return {
            "status": "success",
            "message": f"Index uploaded successfully with {term_count} terms",
            "term_count": term_count
        }
        
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid index format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/admin/upload-endnotes")
async def upload_endnotes(file: UploadFile = File(...), content_encoding: Optional[str] = Header(None)):
    """Upload endnotes.json via HTTP."""
    from lib.config import DATA_DIR
    os.makedirs(DATA_DIR, exist_ok=True)

    if file.filename not in ["endnotes.json", "endnotes.json.gz"]:
        raise HTTPException(
            status_code=400,
            detail=f"Expected filename 'endnotes.json' or 'endnotes.json.gz', got '{file.filename}'"
        )

    try:
        content = await file.read()

        # Handle gzip compression if present
        if content_encoding == "gzip":
            import gzip
            content = gzip.decompress(content)
        elif len(content) >= 2 and content[0] == 0x1f and content[1] == 0x8b:
            import gzip
            content = gzip.decompress(content)

        # Validate JSON
        data = json.loads(content)
        if not isinstance(data, dict):
            raise ValueError("Root must be a dictionary")

        target_path = os.path.join(DATA_DIR, "endnotes.json")
        with open(target_path, 'wb') as f:
            f.write(content)

        return {
            "status": "success",
            "message": f"Endnotes uploaded successfully ({len(data):,} entries)",
            "path": target_path,
            "size_bytes": len(content)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/admin/upload-identity")
async def upload_identity(file: UploadFile = File(...), content_encoding: Optional[str] = Header(None)):
    """Upload identity_detection_v3.json via HTTP."""
    from lib.config import DATA_DIR
    os.makedirs(DATA_DIR, exist_ok=True)

    if file.filename not in ["identity_detection_v3.json"]:
        raise HTTPException(status_code=400, detail="File must be named 'identity_detection_v3.json'")
    
    try:
        # Read file content
        content = await file.read()
        
        # Handle gzip compression if needed
        if content_encoding == "gzip" or (file.filename and file.filename.endswith(".gz")):
            import gzip
            content = gzip.decompress(content)
        
        # Write to data directory
        identity_path = os.path.join(DATA_DIR, "identity_detection_v3.json")
        with open(identity_path, 'wb') as f:
            f.write(content)
        
        file_size_mb = len(content) / (1024 * 1024)
        print(f"[UPLOAD] Successfully uploaded identity file ({file_size_mb:.2f} MB)")
        
        # Verify it's valid JSON
        import json
        try:
            with open(identity_path, 'r', encoding='utf-8') as f:
                identity_data = json.load(f)
            surname_count = len(identity_data.get('surname_to_identity', {}))
            print(f"[UPLOAD] Identity file validated: {surname_count} surnames")
        except json.JSONDecodeError as e:
            print(f"[UPLOAD WARN] Identity file uploaded but JSON validation failed: {e}")
        
        return {
            "status": "success",
            "message": f"Identity file uploaded successfully ({file_size_mb:.2f} MB)",
            "path": identity_path,
            "size_bytes": len(content),
            "surname_count": surname_count if 'surname_count' in locals() else None
        }
    except Exception as e:
        print(f"[UPLOAD ERROR] Identity file upload failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/admin/upload-filtered-terms")
async def upload_filtered_terms(file: UploadFile = File(...)):
    """Upload filtered_terms.json via HTTP."""
    from lib.config import DATA_DIR
    import os
    
    os.makedirs(DATA_DIR, exist_ok=True)
    
    if file.filename not in ["filtered_terms.json"]:
        raise HTTPException(status_code=400, detail="File must be named 'filtered_terms.json'")
    
    try:
        content = await file.read()
        
        # Validate it's a JSON array
        import json
        terms = json.loads(content)
        if not isinstance(terms, list):
            raise ValueError("filtered_terms.json must be a JSON array")
        
        # Write to lib directory (server prefers lib/filtered_terms.json over data/filtered_terms.json)
        from lib.config import LIB_DIR
        lib_filtered_terms_path = os.path.join(LIB_DIR, "filtered_terms.json")
        with open(lib_filtered_terms_path, 'wb') as f:
            f.write(content)
        
        # Also write to data directory as backup
        data_filtered_terms_path = os.path.join(DATA_DIR, "filtered_terms.json")
        with open(data_filtered_terms_path, 'wb') as f:
            f.write(content)
        
        print(f"[UPLOAD] Successfully uploaded filtered_terms.json with {len(terms)} terms (to both lib/ and data/)")
        
        return {
            "status": "success",
            "message": f"Filtered terms uploaded successfully ({len(terms)} terms)",
            "path": lib_filtered_terms_path,
            "backup_path": data_filtered_terms_path,
            "term_count": len(terms)
        }
    except Exception as e:
        print(f"[UPLOAD ERROR] Filtered terms upload failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/admin/upload-chunk-to-endnotes")
async def upload_chunk_to_endnotes(file: UploadFile = File(...), content_encoding: Optional[str] = Header(None)):
    """Upload chunk_to_endnotes.json via HTTP."""
    from lib.config import DATA_DIR
    os.makedirs(DATA_DIR, exist_ok=True)

    if file.filename not in ["chunk_to_endnotes.json", "chunk_to_endnotes.json.gz"]:
        raise HTTPException(
            status_code=400,
            detail=f"Expected filename 'chunk_to_endnotes.json' or 'chunk_to_endnotes.json.gz', got '{file.filename}'"
        )

    try:
        content = await file.read()

        # Handle gzip compression if present
        if content_encoding == "gzip":
            import gzip
            content = gzip.decompress(content)
        elif len(content) >= 2 and content[0] == 0x1f and content[1] == 0x8b:
            import gzip
            content = gzip.decompress(content)

        # Validate JSON
        data = json.loads(content)
        if not isinstance(data, dict):
            raise ValueError("Root must be a dictionary")

        target_path = os.path.join(DATA_DIR, "chunk_to_endnotes.json")
        with open(target_path, 'wb') as f:
            f.write(content)

        return {
            "status": "success",
            "message": f"Chunk-to-endnotes uploaded successfully ({len(data):,} chunks)",
            "path": target_path,
            "size_bytes": len(content)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.get("/admin/build-info")
async def build_info():
    """Return runtime build + data diagnostics for debugging deployments."""
    from lib.config import INDICES_FILE, DATA_DIR, VECTORDB_DIR, COLLECTION_NAME
    info = {
        "build_id": os.getenv("BUILD_ID"),
        "indices_path": INDICES_FILE,
        "indices_exists": os.path.exists(INDICES_FILE),
        "endnotes_path": os.path.join(DATA_DIR, "endnotes.json"),
        "endnotes_exists": os.path.exists(os.path.join(DATA_DIR, "endnotes.json")),
        "chunk_to_endnotes_path": os.path.join(DATA_DIR, "chunk_to_endnotes.json"),
        "chunk_to_endnotes_exists": os.path.exists(os.path.join(DATA_DIR, "chunk_to_endnotes.json")),
        "vectordb_path": VECTORDB_DIR,
        "vectordb_exists": os.path.exists(VECTORDB_DIR),
        "collection_name": COLLECTION_NAME,
    }
    try:
        if os.path.exists(INDICES_FILE):
            with open(INDICES_FILE, "r", encoding="utf-8") as f:
                indices = json.load(f)
            term_to_chunks = indices.get("term_to_chunks", {})
            info["term_count"] = len(term_to_chunks)
            info["cullman_chunks"] = term_to_chunks.get("Cullman") or term_to_chunks.get("cullman") or []
            info["cullman_chunk_count"] = len(info["cullman_chunks"])
    except Exception as e:
        info["indices_error"] = str(e)
    try:
        if os.path.exists(os.path.join(DATA_DIR, "endnotes.json")):
            with open(os.path.join(DATA_DIR, "endnotes.json"), "r", encoding="utf-8") as f:
                endnotes = json.load(f)
            info["endnotes_count"] = len(endnotes)
        if os.path.exists(os.path.join(DATA_DIR, "chunk_to_endnotes.json")):
            with open(os.path.join(DATA_DIR, "chunk_to_endnotes.json"), "r", encoding="utf-8") as f:
                chunk_map = json.load(f)
            info["chunk_to_endnotes_count"] = len(chunk_map)
    except Exception as e:
        info["endnotes_error"] = str(e)
    try:
        import chromadb
        client = chromadb.PersistentClient(path=VECTORDB_DIR)
        coll = client.get_collection(name=COLLECTION_NAME)
        info["collection_count"] = coll.count()
    except Exception as e:
        info["collection_error"] = str(e)
    return info


@app.get("/admin/chunks")
async def admin_chunks(term: str, limit: int = 3):
    """Return sample chunks for a term to verify retrieval content."""
    from lib.config import INDICES_FILE, VECTORDB_DIR, COLLECTION_NAME
    term = term.strip()
    if not term:
        raise HTTPException(status_code=400, detail="term is required")
    if not os.path.exists(INDICES_FILE):
        raise HTTPException(status_code=500, detail="indices.json not found")
    with open(INDICES_FILE, "r", encoding="utf-8") as f:
        indices = json.load(f)
    term_to_chunks = indices.get("term_to_chunks", {})
    chunk_ids = term_to_chunks.get(term) or term_to_chunks.get(term.lower()) or term_to_chunks.get(term.capitalize()) or []
    if not chunk_ids:
        return {"term": term, "chunks": [], "chunk_count": 0}
    # Fetch from chroma
    import chromadb
    client = chromadb.PersistentClient(path=VECTORDB_DIR)
    coll = client.get_collection(name=COLLECTION_NAME)
    data = coll.get(ids=chunk_ids[:max(1, limit)])
    chunks = []
    for text, meta in zip(data.get("documents", []), data.get("metadatas", [])):
        chunks.append({
            "filename": meta.get("filename"),
            "text": text[:2000]
        })
    return {"term": term, "chunk_count": len(chunk_ids), "chunks": chunks}

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
