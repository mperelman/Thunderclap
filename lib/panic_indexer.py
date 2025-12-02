"""
Panic Indexer
=============
Indexes specific panics (Panic of 1763, Panic of 1825, etc.) as searchable terms.
Per user instruction: Each panic should be individually searchable.

CRITICAL: This module dynamically scans for ALL panics in documents using regex pattern.
It does NOT use a hardcoded list - it finds whatever "Panic of XXXX" appears in the text.
"""

import re
from typing import Dict, List, Set

def index_panics(chunks: List[str], chunk_ids: List[str]) -> Dict[str, List[str]]:
    """
    Index specific panics as searchable terms by scanning for ALL "Panic of XXXX" patterns.
    
    Args:
        chunks: List of chunk text
        chunk_ids: List of chunk IDs
    
    Returns:
        Dict of {panic_term: [chunk_ids]}
        e.g., {'panic_of_1914': ['chunk_123', 'chunk_456'], ...}
    """
    panic_index = {}
    years_found: Set[int] = set()
    
    # First pass: Find all years mentioned with "Panic of" or "Crisis of"
    panic_pattern = re.compile(r'\b[Pp]anic\s+of\s+(\d{4})\b')
    crisis_pattern = re.compile(r'\b[Cc]risis\s+of\s+(\d{4})\b')
    
    for chunk_text in chunks:
        # Remove HTML tags for pattern matching (panics are often italicized)
        text_for_matching = re.sub(r'<[^>]+>', '', chunk_text)
        
        # Find all panic years
        for match in panic_pattern.finditer(text_for_matching):
            year = int(match.group(1))
            years_found.add(year)
        
        # Find all crisis years
        for match in crisis_pattern.finditer(text_for_matching):
            year = int(match.group(1))
            years_found.add(year)
    
    # Second pass: Index chunks for each year found
    for year in sorted(years_found):
        panic_year_pattern = rf'\b[Pp]anic\s+of\s+{year}\b'
        crisis_year_pattern = rf'\b[Cc]risis\s+of\s+{year}\b'
        
        matching_chunks = []
        
        for chunk_id, chunk_text in zip(chunk_ids, chunks):
            # Remove HTML tags for pattern matching
            text_for_matching = re.sub(r'<[^>]+>', '', chunk_text)
            if re.search(panic_year_pattern, text_for_matching) or re.search(crisis_year_pattern, text_for_matching):
                matching_chunks.append(chunk_id)
        
        if matching_chunks:
            # Index with underscore (for internal use)
            panic_index[f'panic_of_{year}'] = matching_chunks
            # Also index without underscore for natural search
            panic_index[f'panic of {year}'] = matching_chunks
    
    return panic_index


def augment_index_with_panics(term_to_chunks: Dict, chunks: List[str], chunk_ids: List[str]) -> Dict:
    """
    Add panic-specific terms to existing index.
    
    Args:
        term_to_chunks: Existing term index
        chunks: List of chunk texts
        chunk_ids: List of chunk IDs
    
    Returns:
        Augmented term_to_chunks with panic terms added
    """
    panic_terms = index_panics(chunks, chunk_ids)
    
    print(f"  [PANICS] Indexing specific panics...")
    for panic_term, panic_chunks in panic_terms.items():
        if '_' not in panic_term:  # Only report the readable version
            print(f"    {panic_term}: {len(panic_chunks)} chunks")
        term_to_chunks[panic_term] = panic_chunks
    
    print(f"  [OK] Indexed {len(panic_terms)//2} specific panics")
    
    return term_to_chunks






