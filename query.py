#!/usr/bin/env python3
"""
Thunderclap AI - Query Historical Documents

Main entry point for querying the indexed Thunderclap documents.

Usage:
    # Interactive mode
    python query.py
    
    # Direct query
    python query.py smyth
    
    # Programmatic
    from query import search, ask
    results = search("rothschild")
    answer = ask("How did Quaker families influence banking?")
"""

import sys
import os

# Add lib to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

from lib.query_engine import QueryEngine
from typing import List, Dict

# Global instance (lazy loaded)
_engine = None

def get_engine() -> QueryEngine:
    """Get or create the global query engine."""
    global _engine
    if _engine is None:
        _engine = QueryEngine()
    return _engine


def search(term: str, max_results: int = 10) -> List[Dict]:
    """
    Search for a term in the documents.
    
    Args:
        term: Search term (family name, organization, etc.)
        max_results: Maximum results to return
        
    Returns:
        List of matching document chunks
        
    Example:
        >>> results = search("Smyth")
        >>> for r in results:
        ...     print(f"{r['filename']}: {r['text'][:100]}")
    """
    engine = get_engine()
    return engine.search_term(term, max_results)


def ask(question: str, use_llm: bool = True) -> str:
    """
    Ask a question about the historical documents.
    
    Args:
        question: Your question
        use_llm: Whether to use AI for answer generation
        
    Returns:
        Answer or relevant context
        
    Example:
        >>> answer = ask("What role did Quaker families play in banking?")
        >>> print(answer)
    """
    engine = get_engine()
    return engine.query(question, use_llm=use_llm)


def stats() -> Dict:
    """Get database statistics."""
    engine = get_engine()
    return engine.get_stats()


def interactive():
    """Run interactive query mode."""
    print("="*80)
    print("Thunderclap AI - Interactive Query Mode")
    print("="*80)
    print()
    
    engine = get_engine()
    
    print("\nCommands:")
    print("  search <term>      - Search for a term")
    print("  ask <question>     - Ask a question")
    print("  stats              - Show database statistics")
    print("  help               - Show this help")
    print("  quit               - Exit")
    print()
    
    while True:
        try:
            user_input = input("\n> ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!")
                break
            
            elif user_input.lower() in ['help', 'h', '?']:
                print("\nCommands:")
                print("  search <term>      - e.g., 'search Rothschild'")
                print("  ask <question>     - e.g., 'ask What role did Court Jews play?'")
                print("  stats              - Database statistics")
                print("  quit               - Exit")
            
            elif user_input.lower() == 'stats':
                s = stats()
                print("\nDatabase Statistics:")
                for key, value in s.items():
                    print(f"  {key.replace('_', ' ').title()}: {value:,}")
            
            elif user_input.lower().startswith('search '):
                term = user_input[7:].strip()
                results = search(term, max_results=5)
                
                if results:
                    print(f"\nFound {len(results)} results for '{term}':\n")
                    for i, r in enumerate(results[:3], 1):
                        print(f"{i}. [{r['filename']}]")
                        print(f"   {r['text'][:250]}...")
                        print()
                else:
                    print(f"\nNo results found for '{term}'")
            
            elif user_input.lower().startswith('ask '):
                question = user_input[4:].strip()
                print(f"\nSearching for: {question}\n")
                answer = ask(question)
                print(answer)
            
            else:
                # Assume it's a search term
                results = search(user_input, max_results=5)
                if results:
                    print(f"\nFound {len(results)} results:\n")
                    for i, r in enumerate(results[:3], 1):
                        print(f"{i}. [{r['filename']}]")
                        print(f"   {r['text'][:250]}...")
                        print()
                else:
                    print(f"\nNo results found. Try: search <term> or ask <question>")
        
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")


if __name__ == "__main__":
    # Check if term provided as argument
    if len(sys.argv) > 1:
        term = ' '.join(sys.argv[1:])
        print(f"Searching for: {term}\n")
        results = search(term, max_results=10)
        
        if results:
            print(f"Found {len(results)} results:\n")
            for i, r in enumerate(results[:5], 1):
                print(f"{i}. [{r['filename']}]")
                print(f"   {r['text'][:300]}...")
                print("\n" + "-"*80 + "\n")
        else:
            print("No results found.")
    else:
        # Interactive mode
        interactive()


