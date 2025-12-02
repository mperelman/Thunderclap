"""
Panic Indexer
=============
Indexes specific panics (Panic of 1763, Panic of 1825, etc.) as searchable terms.
Per user instruction: Each panic should be individually searchable.
"""

import re
from typing import Dict, List

# All panics mentioned in documents (per user's Thunderclap framework)
KNOWN_PANICS = [
    1763, 1772, 1792, 1797, 1810, 1819, 1825, 1837, 1847, 1857, 
    1866, 1873, 1884, 1890, 1893, 1896, 1901, 1907, 1914, 1920,
    1929, 1931, 1933, 1937, 1987, 1989, 1997, 1998, 2000, 2001, 2007, 2008
]

def index_panics(chunks: List[str], chunk_ids: List[str]) -> Dict[str, List[str]]:
    """
    Index specific panics as searchable terms.
    
    Args:
        chunks: List of chunk text
        chunk_ids: List of chunk IDs
    
    Returns:
        Dict of {panic_term: [chunk_ids]}
        e.g., {'panic_of_1914': ['chunk_123', 'chunk_456'], ...}
    """
    panic_index = {}
    
    # Build patterns for each panic
    # Panics are often in italics (e.g., *Panic of 1763*), so we need to handle HTML tags
    for year in KNOWN_PANICS:
        # Pattern 1: Normal text "Panic of 1763" or "panic of 1763"
        panic_pattern = rf'\b[Pp]anic\s+of\s+{year}\b'
        crisis_pattern = rf'\b[Cc]risis\s+of\s+{year}\b'
        
        # Pattern 2: In italics (HTML <em> or <i> tags, or markdown *text*)
        # Remove HTML tags first for matching, but keep original for context
        panic_term = f'panic_of_{year}'
        matching_chunks = []
        
        for chunk_id, chunk_text in zip(chunk_ids, chunks):
            # Remove HTML tags for pattern matching (panics are often italicized)
            text_for_matching = re.sub(r'<[^>]+>', '', chunk_text)
            if re.search(panic_pattern, text_for_matching) or re.search(crisis_pattern, text_for_matching):
                matching_chunks.append(chunk_id)
        
        if matching_chunks:
            panic_index[panic_term] = matching_chunks
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






