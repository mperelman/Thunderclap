"""
Identity Pre-filter - Fast regex screening to identify chunks worth LLM processing.

Purpose: Reduce 1,516 chunks → ~200-300 chunks that mention identity keywords.
Then LLM only processes those ~200 chunks (saves API calls).
"""

import re
from typing import List, Set


class IdentityPrefilter:
    """Fast regex-based pre-filter to identify chunks with identity keywords."""
    
    # All identity keywords to search for
    IDENTITY_KEYWORDS = {
        # Religious
        'jewish', 'jew', 'jews', 'sephardi', 'sephardim', 'ashkenazi', 'ashkenazim',
        'court jew', 'court jews', 'kohanim', 'katz',
        'quaker', 'quakers', 'huguenot', 'huguenots', 'mennonite', 'mennonites',
        'puritan', 'puritans', 'calvinist', 'presbyterian', 'catholic irish',
        'muslim', 'muslims', 'islam', 'islamic', 'sunni', 'shia', 'shiite',
        'alawite', 'druze', 'ismaili', 'maronite', 'maronites',
        'coptic', 'greek orthodox', 'orthodox',
        'parsee', 'parsees', 'zoroastrian', 'hindu', 'brahmin', 'bania',
        
        # Ethnic
        'armenian', 'armenians', 'greek', 'greeks',
        'lebanese', 'syrian', 'syrians', 'palestinian', 'palestinians',
        'basque', 'basques',
        'hausa', 'yoruba', 'igbo', 'fulani', 'akan', 'zulu',
        'scottish', 'scots', 'irish', 'welsh',
        
        # Racial
        'black', 'african american', 'african-american',
        
        # Gender
        'female', 'woman', 'women', 'widow', 'widows',
        'queen', 'princess', 'lady', 'heiress',
        
        # Latino/Hispanic
        'latino', 'latina', 'latinos', 'latinas',
        'hispanic', 'hispanics',
        'mexican', 'cuban', 'puerto rican',
        
        # LGBT (contextual)
        'gay', 'homosexual', 'homosexuality', 'bisexual',
        'lesbian', 'lgbt', 'lavender marriage', 'lavender marriages',
        
        # Other
        'overseas chinese', 'chaebol', 'zaibatsu',
        'boston brahmin', 'knickerbocker',
    }
    
    def __init__(self):
        """Initialize pre-filter with compiled patterns."""
        # Compile patterns for speed
        self.patterns = []
        for keyword in self.IDENTITY_KEYWORDS:
            # Word boundary pattern
            pattern = rf'\b{re.escape(keyword)}\b'
            self.patterns.append(re.compile(pattern, re.IGNORECASE))
    
    def has_identity_keywords(self, chunk: str) -> bool:
        """
        Check if chunk contains ANY identity keywords.
        
        Args:
            chunk: Text chunk to check
        
        Returns:
            True if chunk mentions identities (worth LLM processing)
        """
        for pattern in self.patterns:
            if pattern.search(chunk):
                return True
        return False
    
    def filter_chunks(self, chunks: List[str]) -> List[int]:
        """
        Filter chunks to find which ones mention identities.
        
        Args:
            chunks: List of all chunks
        
        Returns:
            List of chunk indices that have identity keywords
        """
        relevant_indices = []
        
        for i, chunk in enumerate(chunks):
            if self.has_identity_keywords(chunk):
                relevant_indices.append(i)
        
        return relevant_indices
    
    def get_statistics(self, chunks: List[str]) -> dict:
        """Get filtering statistics."""
        relevant = self.filter_chunks(chunks)
        
        return {
            'total_chunks': len(chunks),
            'relevant_chunks': len(relevant),
            'filtered_out': len(chunks) - len(relevant),
            'reduction_pct': (1 - len(relevant)/len(chunks)) * 100 if chunks else 0
        }


def prefilter_for_llm(chunks: List[str]) -> tuple[List[str], List[int]]:
    """
    Pre-filter chunks before LLM processing.
    
    Args:
        chunks: All document chunks
    
    Returns:
        (filtered_chunks, original_indices)
    """
    prefilter = IdentityPrefilter()
    relevant_indices = prefilter.filter_chunks(chunks)
    filtered_chunks = [chunks[i] for i in relevant_indices]
    
    print(f"[PREFILTER] {len(chunks)} chunks → {len(filtered_chunks)} relevant ({len(filtered_chunks)/len(chunks)*100:.1f}%)")
    print(f"[SAVINGS] Reduced LLM processing by {100 - len(filtered_chunks)/len(chunks)*100:.1f}%")
    
    return filtered_chunks, relevant_indices


if __name__ == '__main__':
    """Test the pre-filter."""
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from lib.document_parser import load_all_documents
    from lib.index_builder import split_into_chunks
    
    print("Testing Identity Pre-filter\n")
    
    # Load chunks
    docs = load_all_documents(use_cache=True)
    all_chunks = []
    for doc in docs:
        all_chunks.extend(split_into_chunks(doc['text']))
    
    # Get statistics
    prefilter = IdentityPrefilter()
    stats = prefilter.get_statistics(all_chunks)
    
    print(f"Total chunks: {stats['total_chunks']}")
    print(f"Relevant chunks: {stats['relevant_chunks']}")
    print(f"Filtered out: {stats['filtered_out']}")
    print(f"Reduction: {stats['reduction_pct']:.1f}%")
    print()
    
    print(f"LLM API calls saved: {stats['filtered_out'] / 20:.0f} batches")
    print(f"This pre-filter makes detection {stats['reduction_pct']:.0f}% more efficient!")

