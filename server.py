"""
Thunderclap AI - Web API Server
Run this file to start the server: python server.py
"""
import sys
import os

# Ensure lib is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from collections import defaultdict
import time

# Import query engine
from lib.query_engine import QueryEngine
from lib.config import MAX_ANSWER_LENGTH

app = FastAPI(title="Thunderclap AI - Banking History")

# CORS - allow all origins for testing (restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific domain in production
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

# Store API key for creating QueryEngine instances
gemini_key = os.getenv('GEMINI_API_KEY')
if not gemini_key:
    print("ERROR: GEMINI_API_KEY environment variable not set!")
    sys.exit(1)

print("Initializing Thunderclap AI...")
print("Server ready! (QueryEngine created per-request)\n")

class QueryRequest(BaseModel):
    question: str
    max_length: int = MAX_ANSWER_LENGTH  # Maximum answer length in characters

class QueryResponse(BaseModel):
    answer: str
    source: str = "Thunderclap AI"

# Simple rate limiting
request_counts = defaultdict(list)
RATE_LIMIT = 10000  # requests per hour (relaxed for production)

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
        "version": "2.0",
        "endpoints": {
            "POST /query": "Submit a question about banking history",
            "GET /health": "Check service health",
            "GET /": "This information page"
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
    client_ip = "demo_user"  # In production: extract from Request object if needed
    check_rate_limit(client_ip)
    
    # Validate input
    if not request.question or len(request.question) < 3:
        raise HTTPException(status_code=400, detail="Question too short (minimum 3 characters)")
    
    if len(request.question) > 500:
        raise HTTPException(status_code=400, detail="Question too long (maximum 500 characters)")
    
    try:
        # Generate answer (all data access happens server-side)
        print(f"Processing query: {request.question}")
        
        # Create query engine with async disabled for FastAPI compatibility
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
    # Railway uses PORT environment variable, default to 8000
    port = int(os.getenv('PORT', 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
