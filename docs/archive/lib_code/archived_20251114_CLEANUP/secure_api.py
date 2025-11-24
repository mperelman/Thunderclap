"""
Secure API for Thunderclap AI
Only exposes query endpoint - no access to raw data or code
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from query import ask
import os

app = FastAPI(
    title="Thunderclap AI - Banking History",
    docs_url=None,  # Disable API docs in production
    redoc_url=None   # Disable redoc in production
)

# CORS - restrict to your frontend domain only
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],  # Change this!
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    question: str
    max_length: int = 2000  # Limit response size

class QueryResponse(BaseModel):
    answer: str
    source: str = "Thunderclap AI"

# Rate limiting (simple version - use Redis for production)
from collections import defaultdict
import time

request_counts = defaultdict(list)
RATE_LIMIT = 10  # requests per hour per IP

def check_rate_limit(ip: str):
    """Simple rate limiting"""
    now = time.time()
    hour_ago = now - 3600
    
    # Clean old requests
    request_counts[ip] = [t for t in request_counts[ip] if t > hour_ago]
    
    if len(request_counts[ip]) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")
    
    request_counts[ip].append(now)

@app.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest):
    """
    Main query endpoint - ONLY returns generated narratives.
    No access to raw chunks, documents, or code.
    """
    
    # Rate limiting (using simple IP for demo - in production use Request object)
    client_ip = "demo_user"  # In production: get from Request.client.host
    check_rate_limit(client_ip)
    
    # Validate input
    if not request.question or len(request.question) < 3:
        raise HTTPException(status_code=400, detail="Question too short")
    
    if len(request.question) > 500:
        raise HTTPException(status_code=400, detail="Question too long (max 500 chars)")
    
    try:
        # Generate answer (all data access happens server-side)
        answer = ask(request.question, use_llm=True)
        
        # Truncate if needed
        if len(answer) > request.max_length:
            answer = answer[:request.max_length] + "..."
        
        return QueryResponse(answer=answer)
    
    except Exception as e:
        # Don't expose internal errors
        raise HTTPException(status_code=500, detail="Query processing failed")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}

# DO NOT EXPOSE THESE ENDPOINTS IN PRODUCTION
# No endpoint for:
# - /download - NO
# - /chunks - NO
# - /raw-data - NO
# - /indices - NO
# - /debug - NO

