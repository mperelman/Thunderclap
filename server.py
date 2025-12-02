"""
Thunderclap AI - Web API Server
Run this file to start the server: python server.py
"""
import sys
import os

# Ensure lib is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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
    """Background task to process query."""
    import sys
    JOB_STORE[job_id]["status"] = "processing"
    JOB_STORE[job_id]["start_time"] = time.time()
    
    try:
        print(f"[JOB {job_id}] Starting query processing...")
        sys.stdout.flush()
        
        from lib.query_engine import QueryEngine
        qe = QueryEngine(gemini_api_key=gemini_key, use_async=False)
        answer = qe.query(question, use_llm=True)
        
        # Store chunk count for time estimation (if available)
        if hasattr(qe, 'last_chunk_count'):
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
    Updated: 2025-01-22 - Force redeploy."""
    from lib.config import INDICES_FILE
    try:
        if os.path.exists(INDICES_FILE):
            with open(INDICES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            terms = list(data.get('term_to_chunks', {}).keys())
            
            # Comprehensive list of common English words to exclude
            common_words = {
                # Articles, pronouns, prepositions
                'the', 'a', 'an', 'and', 'or', 'but', 'if', 'of', 'to', 'in', 'on', 'at', 'by', 'for', 'with', 'from', 'as', 'is', 'was', 'are', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their', 'mine', 'yours', 'hers', 'ours', 'theirs',
                # Common verbs
                'get', 'got', 'go', 'went', 'come', 'came', 'see', 'saw', 'know', 'knew', 'think', 'thought', 'take', 'took', 'give', 'gave', 'make', 'made', 'say', 'said', 'tell', 'told', 'ask', 'asked', 'find', 'found', 'work', 'worked', 'try', 'tried', 'use', 'used', 'call', 'called', 'want', 'wanted', 'need', 'needed', 'seem', 'seemed', 'help', 'helped', 'show', 'showed', 'play', 'played', 'move', 'moved', 'live', 'lived', 'believe', 'believed', 'bring', 'brought', 'happen', 'happened', 'write', 'wrote', 'sit', 'sat', 'stand', 'stood', 'lose', 'lost', 'pay', 'paid', 'meet', 'met', 'include', 'included', 'continue', 'continued', 'set', 'put', 'let', 'allow', 'allowed',
                # Common nouns (generic)
                'time', 'year', 'people', 'way', 'day', 'man', 'thing', 'woman', 'life', 'child', 'world', 'school', 'state', 'family', 'student', 'group', 'country', 'problem', 'hand', 'part', 'place', 'case', 'week', 'company', 'system', 'program', 'question', 'work', 'government', 'number', 'night', 'point', 'home', 'water', 'room', 'mother', 'area', 'money', 'story', 'fact', 'month', 'lot', 'right', 'study', 'book', 'eye', 'job', 'word', 'business', 'issue', 'side', 'kind', 'head', 'house', 'service', 'friend', 'father', 'power', 'hour', 'game', 'line', 'end', 'member', 'law', 'car', 'city', 'community', 'name', 'president', 'team', 'minute', 'idea', 'kid', 'body', 'information', 'back', 'parent', 'face', 'others', 'level', 'office', 'door', 'health', 'person', 'art', 'war', 'history', 'party', 'result', 'change', 'morning', 'reason', 'research', 'girl', 'guy', 'moment', 'air', 'teacher', 'force', 'education',
                # Common adjectives/adverbs
                'good', 'new', 'first', 'last', 'long', 'great', 'little', 'own', 'other', 'old', 'right', 'big', 'high', 'different', 'small', 'large', 'next', 'early', 'young', 'important', 'few', 'public', 'bad', 'same', 'able', 'human', 'local', 'late', 'hard', 'major', 'better', 'economic', 'strong', 'possible', 'whole', 'free', 'military', 'true', 'federal', 'international', 'full', 'special', 'sure', 'clear', 'recent', 'personal', 'private', 'past', 'foreign', 'available', 'popular', 'national', 'current', 'wrong', 'receive', 'receive', 'according', 'behind', 'during', 'through', 'throughout', 'within', 'without', 'above', 'below', 'across', 'after', 'before', 'between', 'among', 'around', 'along', 'against', 'toward', 'towards', 'upon', 'under', 'over', 'into', 'onto', 'out', 'off', 'up', 'down', 'away', 'back', 'here', 'there', 'where', 'when', 'why', 'how', 'what', 'which', 'who', 'whom', 'whose', 'very', 'much', 'more', 'most', 'less', 'least', 'many', 'some', 'any', 'all', 'each', 'every', 'both', 'either', 'neither', 'few', 'several', 'enough', 'too', 'also', 'only', 'just', 'even', 'still', 'yet', 'already', 'again', 'once', 'twice', 'always', 'never', 'often', 'sometimes', 'usually', 'really', 'quite', 'rather', 'pretty', 'almost', 'nearly', 'about', 'approximately', 'exactly', 'almost', 'nearly', 'quite', 'very', 'too', 'so', 'such', 'well', 'better', 'best', 'worse', 'worst', 'more', 'most', 'less', 'least',
                # Numbers and basic terms
                'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'first', 'second', 'third', 'fourth', 'fifth', 'last', 'next', 'previous', 'another', 'other', 'others', 'same', 'different', 'similar', 'various', 'several', 'many', 'few', 'most', 'least', 'more', 'less', 'much', 'little', 'enough', 'too', 'also', 'only', 'just', 'even', 'still', 'yet', 'already', 'again', 'once', 'twice', 'always', 'never', 'often', 'sometimes', 'usually', 'really', 'quite', 'rather', 'pretty', 'almost', 'nearly', 'about', 'approximately', 'exactly',
                # Time-related
                'year', 'years', 'month', 'months', 'week', 'weeks', 'day', 'days', 'hour', 'hours', 'minute', 'minutes', 'second', 'seconds', 'time', 'times', 'today', 'yesterday', 'tomorrow', 'now', 'then', 'when', 'while', 'during', 'before', 'after', 'since', 'until', 'ago', 'later', 'earlier', 'soon', 'recently', 'recent', 'past', 'present', 'future', 'early', 'late', 'long', 'short', 'quick', 'slow', 'fast',
                # Generic location terms
                'place', 'places', 'area', 'areas', 'region', 'regions', 'country', 'countries', 'state', 'states', 'city', 'cities', 'town', 'towns', 'village', 'villages', 'home', 'homes', 'house', 'houses', 'building', 'buildings', 'room', 'rooms', 'office', 'offices', 'school', 'schools', 'hospital', 'hospitals', 'store', 'stores', 'shop', 'shops', 'restaurant', 'restaurants', 'hotel', 'hotels', 'park', 'parks', 'street', 'streets', 'road', 'roads', 'way', 'ways', 'path', 'paths', 'direction', 'directions', 'north', 'south', 'east', 'west', 'left', 'right', 'up', 'down', 'here', 'there', 'where', 'everywhere', 'anywhere', 'somewhere', 'nowhere', 'away', 'back', 'out', 'in', 'inside', 'outside', 'above', 'below', 'over', 'under', 'across', 'through', 'around', 'along', 'beside', 'behind', 'beyond', 'near', 'far', 'close', 'distant',
            }
            
            # Filter terms: ONLY include meaningful entities/proper nouns, exclude all common words
            filtered_terms = []
            for term in terms:
                term_lower = term.lower().strip()
                # Skip if too short
                if len(term) < 4:
                    continue
                # Skip common words (comprehensive list)
                if term_lower in common_words:
                    continue
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
                elif len(term) >= 8 and term_lower not in common_words:
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
