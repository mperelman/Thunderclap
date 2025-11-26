"""
Thunderclap AI - Web API Server
Run this file to start the server: python server.py
"""
import sys
import os

# Ensure lib is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from collections import defaultdict, deque
import time
import uuid
import json

# Import query engine
from lib.query_engine import QueryEngine
from lib.config import MAX_ANSWER_LENGTH

app = FastAPI(title="Thunderclap AI")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],  # expose X-Request-ID to browser
)

# Store API key for creating QueryEngine instances
gemini_key = os.getenv('GEMINI_API_KEY')
if not gemini_key:
    print("ERROR: GEMINI_API_KEY environment variable not set!")
    sys.exit(1)

print("Initializing Thunderclap AI...")
print("Server ready! (QueryEngine created per-request)\n")

from lib.config import MAX_ANSWER_LENGTH

class QueryRequest(BaseModel):
    question: str
    max_length: int = MAX_ANSWER_LENGTH  # Maximum answer length in characters

class QueryResponse(BaseModel):
    answer: str
    request_id: str

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

@app.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest, http_req: Request, resp: Response):
    """Handle query requests - matches archived working_api.py pattern exactly."""
    client_ip = http_req.client.host if http_req and http_req.client else "unknown"
    request_id = str(uuid.uuid4())
    resp.headers["X-Request-ID"] = request_id
    
    # Log request start IMMEDIATELY
    trace_event(request_id, "request_start", ip=client_ip, question=req.question[:100])
    print(f"[SERVER] Request {request_id} started: {req.question[:60]}...")
    import sys
    sys.stdout.flush()
    
    # Rate limiting
    try:
        check_rate_limit(client_ip)
    except HTTPException as rl_ex:
        trace_event(request_id, "rate_limit", detail=rl_ex.detail)
        from fastapi.responses import JSONResponse
        return JSONResponse(
            content={"detail": rl_ex.detail, "request_id": request_id},
            status_code=rl_ex.status_code,
            headers={"X-Request-ID": request_id},
        )
    
    # Validate input
    if len(req.question) < 3:
        trace_event(request_id, "validation_error", detail="Question too short")
        raise HTTPException(status_code=400, detail="Question too short")
    
    query_start_time = time.time()
    init_start = time.time()
    try:
        # Generate answer (matches archived working_api.py pattern)
        print(f"[SERVER] Processing query: {req.question}")
        trace_event(request_id, "query_start", question=req.question[:100])
        sys.stdout.flush()
        
        # Create query engine with async disabled for FastAPI compatibility
        from lib.query_engine import QueryEngine
        from lib.config import QUERY_TIMEOUT_SECONDS
        qe = QueryEngine(gemini_api_key=gemini_key, use_async=False)
        init_time = time.time() - init_start
        print(f"[SERVER] QueryEngine initialization took {init_time:.1f}s")
        trace_event(request_id, "engine_init", duration=init_time)
        sys.stdout.flush()
        
        # Process query (uses sequential processing to avoid event loop conflicts)
        # Run blocking query in executor to avoid blocking async event loop
        # Add timeout wrapper to ensure we don't exceed QUERY_TIMEOUT_SECONDS
        import asyncio
        loop = asyncio.get_event_loop()
        query_start = time.time()
        
        # Wrap query in timeout to prevent exceeding server timeout
        try:
            answer = await asyncio.wait_for(
                loop.run_in_executor(None, lambda: qe.query(req.question, use_llm=True)),
                timeout=QUERY_TIMEOUT_SECONDS - 10  # Leave 10s buffer for cleanup
            )
        except asyncio.TimeoutError:
            query_time = time.time() - query_start
            trace_event(request_id, "query_timeout", duration=query_time)
            raise HTTPException(
                status_code=504,
                detail=f"Query timed out after {query_time:.1f}s (limit: {QUERY_TIMEOUT_SECONDS}s). Request ID: {request_id}"
            )
        
        query_time = time.time() - query_start
        print(f"[SERVER] Query processing took {query_time:.1f}s")
        trace_event(request_id, "query_processing", duration=query_time)
        sys.stdout.flush()
        
        # Truncate if needed
        if len(answer) > req.max_length:
            answer = answer[:req.max_length] + "\n\n[Truncated]"
        
        duration = time.time() - query_start_time
        trace_event(request_id, "query_complete", duration=duration, answer_length=len(answer))
        print(f"[SERVER] Request {request_id} completed in {duration:.1f}s")
        sys.stdout.flush()
        
        return QueryResponse(answer=answer, request_id=request_id)
    
    except Exception as e:
        duration = time.time() - query_start_time if 'query_start_time' in locals() else 0
        trace_event(request_id, "error", type=type(e).__name__, message=str(e), duration=duration)
        print(f"[SERVER] Error processing query {request_id}: {e}")
        import traceback
        traceback.print_exc()
        sys.stdout.flush()
        # Include Request ID in error detail so it's visible even on timeout
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)} (Request ID: {request_id})")

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
        "trace_count": len(TRACE_BUFFER)
    }

@app.get("/query/{request_id}")
async def get_query_status(request_id: str):
    """Get status of a query by request ID. Handles frontend polling."""
    # Handle undefined gracefully - return complete to stop infinite polling
    if request_id == "undefined" or not request_id:
        return {
            "status": "complete",
            "request_id": request_id or "undefined",
            "message": "Query completed (request ID not available)"
        }
    
    # Check if we have traces for this request
    matching_traces = [t for t in TRACE_BUFFER if t.get("request_id") == request_id]
    
    if not matching_traces:
        return {
            "status": "not_found",
            "request_id": request_id,
            "message": "Request ID not found in trace buffer"
        }
    
    # Find the latest event for this request
    latest_trace = matching_traces[-1]
    event = latest_trace.get("event", "unknown")
    
    # Determine status based on event
    if event == "query_complete":
        return {
            "status": "complete",
            "request_id": request_id,
            "event": event
        }
    elif event in ["query_timeout", "error"]:
        return {
            "status": "error",
            "request_id": request_id,
            "event": event
        }
    else:
        return {
            "status": "processing",
            "request_id": request_id,
            "event": event
        }
if __name__ == "__main__":
    import uvicorn
    print("="*60)
    print("Starting Thunderclap AI Server")
    print("="*60)
    print("Server: http://localhost:8000")
    print("Press Ctrl+C to stop")
    print("="*60)
    # Increase timeout for long-running queries (8 minutes to exceed frontend timeout of 7 minutes)
    # timeout_keep_alive must exceed QUERY_TIMEOUT_SECONDS (420s = 7min) to prevent connection drops
    uvicorn.run(app, host="0.0.0.0", port=8000, timeout_keep_alive=480)

