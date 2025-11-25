"""
Thunderclap AI - Web API Server
Run this file to start the server: python server.py
"""
import sys
import os

# Ensure lib is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, Request, Response, BackgroundTasks
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from collections import defaultdict, deque
import time
import uuid
import json
import asyncio
from typing import Optional, Dict

# Import query engine
from lib.query_engine import QueryEngine
from lib.config import MAX_ANSWER_LENGTH, QUERY_TIMEOUT_SECONDS

app = FastAPI(title="Thunderclap AI")

# Add global exception handler to catch ALL errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    error_type = type(exc).__name__
    error_msg = str(exc)
    print(f"[GLOBAL ERROR HANDLER] {error_type}: {error_msg}")
    print(f"[GLOBAL ERROR HANDLER] Full traceback:")
    traceback.print_exc()
    import sys
    sys.stdout.flush()
    
    # Try to get request ID from headers
    request_id = request.headers.get("X-Request-ID", "unknown")
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": f"Server error: {error_msg}",
            "error_type": error_type,
            "request_id": request_id
        }
    )

# Add validation error handler to see what's wrong
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"[DEBUG] Validation error: {exc.errors()}")
    try:
        body = await request.body()
        print(f"[DEBUG] Request body: {body}")
    except:
        print(f"[DEBUG] Could not read request body")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],  # expose X-Request-ID to browser
)

# Add middleware to send keepalive headers and prevent proxy timeouts
@app.middleware("http")
async def add_timeout_headers(request: Request, call_next):
    """Add headers to prevent proxy timeouts during long requests."""
    response = await call_next(request)
    # Add headers to prevent Railway proxy timeout
    response.headers["X-Accel-Buffering"] = "no"  # Disable nginx buffering
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Connection"] = "keep-alive"
    response.headers["Keep-Alive"] = "timeout=600"  # 10 minutes
    return response

# Store API key for creating QueryEngine instances
gemini_key_raw = os.getenv('GEMINI_API_KEY')
print("="*60)
print("[STARTUP] Checking GEMINI_API_KEY environment variable...")
print(f"[STARTUP] Raw value from os.getenv: {bool(gemini_key_raw)}")
if gemini_key_raw:
    print(f"[STARTUP] Raw value length: {len(gemini_key_raw)}")
    print(f"[STARTUP] Raw value starts with: {gemini_key_raw[:10]}...")
    print(f"[STARTUP] Raw value (first 20 chars): {gemini_key_raw[:20]}...")
gemini_key = gemini_key_raw.strip() if gemini_key_raw else None
if not gemini_key:
    print("="*60)
    print("ERROR: GEMINI_API_KEY environment variable not set!")
    print("="*60)
    print("To fix:")
    print("1. Go to Railway → Variables tab")
    print("2. Add variable: GEMINI_API_KEY")
    print("3. Value: Your Gemini API key (no quotes, no spaces)")
    print("4. Railway will auto-redeploy")
    print("="*60)
elif len(gemini_key) != 39 or not gemini_key.startswith('AIza'):
    print("="*60)
    print(f"WARNING: GEMINI_API_KEY format looks incorrect!")
    print(f"  Length: {len(gemini_key)} (expected 39)")
    print(f"  Starts with: {gemini_key[:10]}... (expected 'AIza...')")
    print("="*60)
    print("Check Railway Variables → GEMINI_API_KEY")
    print("="*60)
    # Don't exit - let it try anyway, might still work
else:
    print(f"[STARTUP] ✓ GEMINI_API_KEY found and looks valid (length: {len(gemini_key)})")
    print("="*60)

print("="*60)
print("Initializing Thunderclap AI Server")
print("="*60)
print(f"API Key present: {bool(gemini_key)}")
print(f"API Key length: {len(gemini_key) if gemini_key else 0}")
print(f"API Key starts with: {gemini_key[:10] if gemini_key else 'N/A'}...")
print("Server ready! (QueryEngine created per-request)")
print("="*60)

from lib.config import MAX_ANSWER_LENGTH

class QueryRequest(BaseModel):
    question: str
    max_length: int = MAX_ANSWER_LENGTH  # Maximum answer length in characters

class QueryResponse(BaseModel):
    answer: str

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

# In-memory job store (simple dict - for production use Redis or database)
JOB_STORE: Dict[str, Dict] = {}

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

@app.get("/test")
async def test():
    """Test endpoint to verify server is working and check data files."""
    try:
        print("[TEST] Test endpoint called")
        sys.stdout.flush()
        
        # Check data folder status
        data_status = {}
        chroma_path = "data/vectordb/chroma.sqlite3"
        if os.path.exists(chroma_path):
            size = os.path.getsize(chroma_path)
            data_status["chroma_exists"] = True
            data_status["chroma_size"] = size
            data_status["chroma_size_mb"] = round(size / (1024 * 1024), 2)
            data_status["is_pointer"] = size < 1000000
        else:
            data_status["chroma_exists"] = False
        
        indices_path = "data/indices.json"
        data_status["indices_exists"] = os.path.exists(indices_path)
        if os.path.exists(indices_path):
            data_status["indices_size"] = os.path.getsize(indices_path)
        
        vectordb_dir = "data/vectordb"
        if os.path.exists(vectordb_dir):
            files = os.listdir(vectordb_dir)
            data_status["vectordb_files"] = files[:10]  # First 10 files
        
        return {
            "status": "ok",
            "message": "Server is working",
            "api_key_present": bool(gemini_key),
            "api_key_length": len(gemini_key) if gemini_key else 0,
            "data_status": data_status
        }
    except Exception as e:
        print(f"[TEST] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.stdout.flush()
        return {"status": "error", "error": str(e)}

@app.get("/query")
async def query_get():
    """Handle GET requests to /query with helpful error message."""
    return JSONResponse(
        status_code=405,
        content={
            "error": "Method Not Allowed",
            "message": "The /query endpoint requires a POST request with JSON body.",
            "example": {
                "method": "POST",
                "url": "/query",
                "headers": {"Content-Type": "application/json"},
                "body": {"question": "Tell me about Rothschild", "max_length": 15000}
            }
        }
    )

async def process_query_job(job_id: str, question: str, max_length: int):
    """Background task to process query."""
    import sys
    JOB_STORE[job_id]["status"] = "processing"
    JOB_STORE[job_id]["start_time"] = time.time()
    
    try:
        print(f"[JOB {job_id}] Starting query processing...")
        sys.stdout.flush()
        
        from lib.query_engine import QueryEngine
        from lib.config import QUERY_TIMEOUT_SECONDS
        
        qe = QueryEngine(gemini_api_key=gemini_key, use_async=False)
        
        loop = asyncio.get_event_loop()
        answer = await asyncio.wait_for(
            loop.run_in_executor(None, lambda: qe.query(question, use_llm=True)),
            timeout=QUERY_TIMEOUT_SECONDS - 10
        )
        
        # Truncate if needed
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
        status=job["status"],
        answer=job.get("answer"),
        error=job.get("error"),
        elapsed=elapsed
    )

@app.get("/debug/last")
def debug_last(n: int = 50):
    n = max(1, min(200, n))
    return list(TRACE_BUFFER)[-n:]

@app.get("/status")
def get_status():
    """Get current server status and last query progress."""
    return {
        "status": "running",
        "last_traces": list(TRACE_BUFFER)[-20:],
        "trace_count": len(TRACE_BUFFER),
        "query_timeout_seconds": QUERY_TIMEOUT_SECONDS
    }

@app.get("/test-timeout")
async def test_timeout():
    """Test endpoint to check Railway's proxy timeout."""
    import asyncio
    await asyncio.sleep(65)  # Sleep for 65 seconds to test if Railway times out
    return {"message": "Timeout test passed - server is still alive after 65 seconds"}
if __name__ == "__main__":
    import uvicorn
    # Read PORT from environment (Railway/Render set this) or default to 8000
    port = int(os.getenv("PORT", 8000))
    print("="*60)
    print("Starting Thunderclap AI Server")
    print("="*60)
    print(f"Server: http://0.0.0.0:{port}")
    print("Press Ctrl+C to stop")
    print("="*60)
    # CRITICAL: Set very high timeout to prevent Railway proxy from timing out
    # Railway proxy timeout is likely 60s, but we set uvicorn to 600s (10 min) to be safe
    # This ensures the connection stays alive during long queries
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port, 
        timeout_keep_alive=600,  # 10 minutes - exceeds Railway's likely 60s proxy timeout
        timeout_graceful_shutdown=30,
        log_level="info"
    )

