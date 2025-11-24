"""
Working Secure API for Thunderclap AI
"""
import sys
import os

# Add parent directory to path so we can import query
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from collections import defaultdict
import time

# Import after path is set
from query import ask

app = FastAPI(title="Thunderclap AI - Banking History")

# CORS - allow all origins for testing (restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific domain in production
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    question: str
    max_length: int = 3000

class QueryResponse(BaseModel):
    answer: str
    source: str = "Thunderclap AI"

# Simple rate limiting
request_counts = defaultdict(list)
RATE_LIMIT = 20  # requests per hour

def check_rate_limit(ip: str):
    """Simple rate limiting"""
    now = time.time()
    hour_ago = now - 3600
    
    # Clean old requests
    request_counts[ip] = [t for t in request_counts[ip] if t > hour_ago]
    
    if len(request_counts[ip]) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again in an hour.")
    
    request_counts[ip].append(now)

@app.get("/")
async def root():
    return {
        "service": "Thunderclap AI",
        "description": "Historical banking research through sociological and cultural lenses",
        "version": "2.0 (Async-optimized - 5x faster)",
        "database": {
            "chunks": "1,517 indexed document chunks",
            "terms": "19,330 searchable terms",
            "endnotes": "14,094 genealogical records",
            "panics": "31 financial crises indexed",
            "coverage": "Medieval period through 21st century"
        },
        "search_categories": {
            "families": ["Rothschild", "Lehman", "Morgan", "Baring", "Hope", "Sassoon", "Kadoorie", "Goldsmid", "Cohen-Barent", "Hambro", "Warburg", "Schiff"],
            "panics": ["Panic of 1763", "Panic of 1825", "Panic of 1873", "Panic of 1893", "Panic of 1907", "Panic of 1914", "Panic of 1929", "Panic of 2008"],
            "identities": ["Jewish", "Sephardi", "Ashkenazi", "Quaker", "Huguenot", "Puritan", "Greek Orthodox", "Armenian", "Hindu", "Parsee", "Bania", "Dalit"],
            "geographies": ["London", "New York", "Paris", "Frankfurt", "Amsterdam", "Bombay", "Shanghai", "Hong Kong"]
        },
        "endpoints": {
            "POST /query": "Submit a question about banking history",
            "GET /health": "Check service health",
            "GET /": "This information page"
        },
        "examples": [
            "Tell me about the Rothschild family",
            "What happened during the Panic of 1907?",
            "Tell me about Quaker bankers",
            "Tell me about Cohen-Barent",
            "Tell me about Hindu bankers in Bombay"
        ],
        "rate_limit": "20 requests per hour",
        "response_format": {
            "answer": "Generated narrative (max 3000 chars)",
            "source": "Thunderclap AI"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "thunderclap-ai"}

@app.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest):
    """
    Main query endpoint - ONLY returns generated narratives.
    No access to raw chunks, documents, or code.
    """
    
    # Rate limiting
    client_ip = "demo_user"  # In production: extract from Request object
    check_rate_limit(client_ip)
    
    # Validate input
    if not request.question or len(request.question) < 3:
        raise HTTPException(status_code=400, detail="Question too short (minimum 3 characters)")
    
    if len(request.question) > 500:
        raise HTTPException(status_code=400, detail="Question too long (maximum 500 characters)")
    
    try:
        # Generate answer (all data access happens server-side)
        print(f"Processing query: {request.question}")
        
        # Import here to avoid circular dependency
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        from lib.query_engine import QueryEngine
        from lib.identity_hierarchy import expand_search_terms
        
        # Create query engine with async disabled for FastAPI compatibility
        gemini_key = os.getenv('GEMINI_API_KEY')
        qe = QueryEngine(gemini_api_key=gemini_key, use_async=False)
        
        # Process query (uses sequential processing to avoid event loop conflicts)
        answer = qe.query(request.question, use_llm=True)
        
        # Truncate if needed
        if len(answer) > request.max_length:
            answer = answer[:request.max_length] + "\n\n[Answer truncated for length]"
        
        return QueryResponse(answer=answer)
    
    except Exception as e:
        print(f"Error processing query: {e}")
        import traceback
        traceback.print_exc()
        # Don't expose internal errors to users
        raise HTTPException(status_code=500, detail="Unable to process query. Please try again.")

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("Thunderclap AI - Secure API Server")
    print("=" * 60)
    print("Starting server on http://localhost:8000")
    print("\nEndpoints:")
    print("  GET  / - API info")
    print("  GET  /health - Health check")
    print("  POST /query - Submit questions")
    print("\nPress Ctrl+C to stop")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000)

