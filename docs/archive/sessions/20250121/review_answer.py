"""Test script to review an answer against criteria."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.answer_reviewer import AnswerReviewer
from query import ask
import json

def review_query(question: str, use_llm: bool = True):
    """Run a query and review the answer."""
    print(f"Query: {question}")
    print("Running query...")
    
    # Get answer
    answer = ask(question, use_llm=use_llm)
    
    # Get chunks from query engine for comparison
    from lib.query_engine import QueryEngine
    engine = QueryEngine(use_async=False)
    
    # Extract keywords and get chunks (similar to query method)
    keywords = engine._extract_keywords(question)
    subject_terms, subject_phrases = engine._extract_subject_filters(question, keywords)
    
    # Get chunk IDs
    chunk_ids = set()
    for keyword in keywords:
        if keyword in engine.term_to_chunks:
            chunk_ids.update(engine.term_to_chunks[keyword])
    
    if chunk_ids:
        # Fetch chunks
        data = engine.collection.get(ids=list(chunk_ids))
        chunks = [
            (text, meta)
            for text, meta in zip(data['documents'], data['metadatas'])
        ]
    else:
        chunks = []
    
    reviewer = AnswerReviewer()
    
    # Review answer with chunks
    results = reviewer.review(answer, chunks=chunks)
    
    # Print report
    reviewer.print_report(results, answer)
    
    return results, answer, chunks

if __name__ == "__main__":
    question = sys.argv[1] if len(sys.argv) > 1 else "Tell me about Vienna Rothschild banking"
    review_query(question)

