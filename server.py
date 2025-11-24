"""
Thunderclap AI - Web API Server
Run this file to start the server: python server.py
"""
import sys
import os

# Ensure lib is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from collections import defaultdict, deque
import time
import uuid
import json

# Import query engine
from lib.query_engine import QueryEngine
from lib.config import MAX_ANSWER_LENGTH

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

# Store API key for creating QueryEngine instances
gemini_key_raw = os.getenv('GEMINI_API_KEY')
gemini_key = gemini_key_raw.strip() if gemini_key_raw else None
if not gemini_key:
    print("="*60)
    print("ERROR: GEMINI_API_KEY environment variable not set!")
    print("="*60)
    print("To fix:")
    print("1. Go to Railway → Variables tab")
    print("2. Add variable: GEMINI_API_KEY")
    print("3. Value: Your Gemini API key (no quotes, no spaces)")
elif len(gemini_key) != 39 or not gemini_key.startswith('AIza'):
    print("="*60)
    print(f"WARNING: GEMINI_API_KEY format looks incorrect!")
    print(f"  Length: {len(gemini_key)} (expected 39)")
    print(f"  Starts with: {gemini_key[:10]}... (expected 'AIza...')")
    print("="*60)
    print("4. Railway will auto-redeploy")
    print("="*60)
    sys.exit(1)

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
    """Test endpoint to verify server is working."""
    try:
        print("[TEST] Test endpoint called")
        sys.stdout.flush()
        return {
            "status": "ok",
            "message": "Server is working",
            "api_key_present": bool(gemini_key),
            "api_key_length": len(gemini_key) if gemini_key else 0
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
        print(f"[SERVER] Request ID: {request_id}")
        print(f"[SERVER] API Key present: {bool(gemini_key)}")
        trace_event(request_id, "query_start", question=req.question[:100])
        sys.stdout.flush()
        
        # Create query engine with async disabled for FastAPI compatibility
        print(f"[SERVER] Creating QueryEngine...")
        sys.stdout.flush()
        from lib.query_engine import QueryEngine
        from lib.config import QUERY_TIMEOUT_SECONDS
        try:
            qe = QueryEngine(gemini_api_key=gemini_key, use_async=False)
            print(f"[SERVER] QueryEngine created successfully")
            sys.stdout.flush()
        except Exception as init_error:
            print(f"[SERVER] FAILED to create QueryEngine: {type(init_error).__name__}: {init_error}")
            import traceback
            traceback.print_exc()
            sys.stdout.flush()
            raise
        init_time = time.time() - init_start
        print(f"[SERVER] QueryEngine initialization took {init_time:.1f}s")
        trace_event(request_id, "engine_init", duration=init_time)
        sys.stdout.flush()
        
        # CRITICAL FIX: Send immediate response headers to prevent connection timeout
        # Then process query and stream progress updates
        import asyncio
        loop = asyncio.get_event_loop()
        query_start = time.time()
        
        async def stream_query_progress():
            """Stream query progress with keepalive to prevent timeouts."""
            # Send immediate acknowledgment
            yield f"data: {json.dumps({'status': 'started', 'request_id': request_id})}\n\n"
            
            # Start processing in executor
            query_task = loop.run_in_executor(None, lambda: qe.query(req.question, use_llm=True))
            
            # Send keepalive every 15 seconds while processing
            last_update = time.time()
            while not query_task.done():
                await asyncio.sleep(2)  # Check every 2 seconds
                elapsed = time.time() - last_update
                if elapsed >= 15.0:  # Send keepalive every 15 seconds
                    total_elapsed = int(time.time() - query_start)
                    yield f"data: {json.dumps({'status': 'processing', 'elapsed': total_elapsed, 'request_id': request_id})}\n\n"
                    last_update = time.time()
            
            # Get result
            try:
                answer = await query_task
            except RuntimeError as e:
                error_msg = str(e)
                print(f"[SERVER] Database error: {error_msg}")
                trace_event(request_id, "error", type="RuntimeError", message=error_msg)
                yield f"data: {json.dumps({'status': 'error', 'detail': f'Database not initialized. {error_msg}', 'request_id': request_id})}\n\n"
                return
            
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
            
            # Send final result
            yield f"data: {json.dumps({'status': 'complete', 'answer': answer, 'request_id': request_id})}\n\n"
        
        return StreamingResponse(
            stream_query_progress(),
            media_type="text/event-stream",
            headers={
                "X-Request-ID": request_id,
                "Cache-Control": "no-cache",
                "Connection": "keep-alive"
            }
        )
    
    except Exception as e:
        duration = time.time() - query_start_time if 'query_start_time' in locals() else 0
        error_type = type(e).__name__
        error_msg = str(e)
        trace_event(request_id, "error", type=error_type, message=error_msg, duration=duration)
        print(f"[SERVER] ERROR processing query {request_id}: {error_type}: {error_msg}")
        import traceback
        print(f"[SERVER] FULL TRACEBACK:")
        traceback.print_exc()
        sys.stdout.flush()
        # Include Request ID in error detail so it's visible even on timeout
        error_detail = f"Query failed: {str(e)} (Request ID: {request_id})"
        print(f"[SERVER] Raising HTTPException: {error_detail}")
        sys.stdout.flush()
        raise HTTPException(status_code=500, detail=error_detail)

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
    # Increase timeout for long-running queries (8 minutes to exceed frontend timeout of 7 minutes)
    # timeout_keep_alive must exceed QUERY_TIMEOUT_SECONDS (420s = 7min) to prevent connection drops
    uvicorn.run(app, host="0.0.0.0", port=port, timeout_keep_alive=480)

