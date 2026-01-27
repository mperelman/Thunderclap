"""
Keyword-based LGBTQ+ identity detector.

This supplements LLM detection by finding surnames near LGBTQ+ keywords
(gay, homosexual, bisexual, lavender marriage, etc.) using regex patterns.

This is non-LLM based and uses the same keyword approach that previously worked.
"""

import re
from typing import Dict, List, Set
from collections import defaultdict


class KeywordLGBTQDetector:
    """Find surnames near LGBTQ+ keywords using regex patterns."""
    
    # LGBTQ+ keywords to search for
    LGBTQ_KEYWORDS = [
        'gay', 'gays', 'homosexual', 'homosexuals', 'homosexuality',
        'bisexual', 'bisexuals', 'lesbian', 'lesbians',
        'lavender marriage', 'lavender marriages',
        'lgbt', 'lgbtq', 'lgbtq+', 'queer', 'transgender', 'trans'
    ]
    
    # Proximity window: look for surnames within this many words of LGBTQ+ keywords
    PROXIMITY_WORDS = 20
    
    def __init__(self):
        """Initialize with compiled patterns."""
        # Compile keyword patterns (word boundaries, case-insensitive)
        self.keyword_patterns = []
        for keyword in self.LGBTQ_KEYWORDS:
            pattern = rf'\b{re.escape(keyword)}\b'
            self.keyword_patterns.append(re.compile(pattern, re.IGNORECASE))
        
        # Pattern to find capitalized words (potential surnames)
        # Match: word starting with capital letter, 2+ chars, not at start of sentence
        self.surname_pattern = re.compile(r'\b[A-Z][a-z]{1,}\b')
    
    def find_surnames_near_keywords(self, chunk: str) -> Set[str]:
        """
        Find surnames that appear near LGBTQ+ keywords in a chunk.
        
        Args:
            chunk: Text chunk to search
            
        Returns:
            Set of surnames found near LGBTQ+ keywords
        """
        surnames = set()
        
        # Find all LGBTQ+ keyword positions
        keyword_positions = []
        for pattern in self.keyword_patterns:
            for match in pattern.finditer(chunk):
                keyword_positions.append((match.start(), match.end()))
        
        if not keyword_positions:
            return surnames
        
        # Find all potential surnames in the chunk
        # Split chunk into words with positions
        words = []
        for match in re.finditer(r'\b\w+\b', chunk):
            word = match.group(0)
            start, end = match.span()
            words.append((word, start, end))
        
        # For each keyword, find surnames within proximity
        for kw_start, kw_end in keyword_positions:
            # Look for surnames within PROXIMITY_WORDS before and after keyword
            for word, word_start, word_end in words:
                # Check if word is capitalized (potential surname)
                if word and word[0].isupper() and len(word) > 1:
                    # Check proximity (within PROXIMITY_WORDS words)
                    # Calculate word distance
                    word_idx = words.index((word, word_start, word_end))
                    kw_word_idx = None
                    for i, (w, s, e) in enumerate(words):
                        if s <= kw_start < e:
                            kw_word_idx = i
                            break
                    
                    if kw_word_idx is not None:
                        distance = abs(word_idx - kw_word_idx)
                        if distance <= self.PROXIMITY_WORDS:
                            # Additional filter: exclude common words that start with capital
                            # (like "The", "A", "In", "On", etc.)
                            common_words = {'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 
                                          'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are',
                                          'were', 'be', 'been', 'being', 'have', 'has', 'had',
                                          'do', 'does', 'did', 'will', 'would', 'could', 'should',
                                          'may', 'might', 'must', 'can', 'this', 'that', 'these',
                                          'those', 'it', 'he', 'she', 'we', 'they', 'i', 'you'}
                            
                            if word.lower() not in common_words:
                                surnames.add(word)
        
        return surnames
    
    def detect_from_chunks(self, chunks: List[str]) -> Dict[str, List[str]]:
        """
        Detect LGBTQ+ identities from chunks using keyword matching.
        
        Args:
            chunks: List of text chunks
            
        Returns:
            Dict mapping identity -> list of surnames
            Format: {'gay': ['drexel', 'singer', 'barney'], ...}
        """
        # Map identity -> surnames
        identity_to_surnames = defaultdict(set)
        
        print(f"[KEYWORD_LGBTQ] Scanning {len(chunks)} chunks for LGBTQ+ keywords...")
        
        for chunk_idx, chunk in enumerate(chunks):
            surnames = self.find_surnames_near_keywords(chunk)
            
            if surnames:
                # Check which keywords appear in this chunk
                chunk_lower = chunk.lower()
                has_gay = any(kw in chunk_lower for kw in ['gay', 'gays', 'homosexual', 'homosexuals', 'homosexuality'])
                has_bisexual = any(kw in chunk_lower for kw in ['bisexual', 'bisexuals'])
                has_lesbian = any(kw in chunk_lower for kw in ['lesbian', 'lesbians'])
                has_lavender = any(kw in chunk_lower for kw in ['lavender marriage', 'lavender marriages'])
                
                # Assign identities based on keywords found
                for surname in surnames:
                    if has_gay or has_lavender:
                        identity_to_surnames['gay'].add(surname.lower())
                    if has_bisexual:
                        identity_to_surnames['bisexual'].add(surname.lower())
                    if has_lesbian:
                        identity_to_surnames['lesbian'].add(surname.lower())
                    # Also add to general lgbtq category
                    if has_gay or has_bisexual or has_lesbian or has_lavender:
                        identity_to_surnames['lgbtq'].add(surname.lower())
        
        # Convert sets to lists
        result = {identity: sorted(list(surnames)) for identity, surnames in identity_to_surnames.items()}
        
        total_surnames = len(set(s for surnames in identity_to_surnames.values() for s in surnames))
        print(f"[KEYWORD_LGBTQ] Found {total_surnames} unique surnames with LGBTQ+ identities")
        for identity, surnames in result.items():
            print(f"  {identity}: {len(surnames)} surnames")
        
        return result


def augment_llm_results_with_keywords(llm_results: Dict, chunks: List[str]) -> Dict:
    """
    Augment LLM identity detection results with keyword-based LGBTQ+ detection.
    
    Args:
        llm_results: Results from LLM detection (format from _aggregate_results)
        chunks: List of all text chunks
        
    Returns:
        Augmented results with keyword-based LGBTQ+ identities added
    """
    detector = KeywordLGBTQDetector()
    keyword_results = detector.detect_from_chunks(chunks)
    
    # Merge keyword results into LLM results
    for identity, surnames in keyword_results.items():
        if identity not in llm_results['identities']:
            llm_results['identities'][identity] = {
                'families': surnames,
                'counts': {s: 1 for s in surnames},
                'type': 'keyword_detected'
            }
        else:
            # Merge: add keyword-detected surnames that aren't already in LLM results
            existing_surnames = set(llm_results['identities'][identity]['families'])
            new_surnames = [s for s in surnames if s.lower() not in existing_surnames]
            
            if new_surnames:
                llm_results['identities'][identity]['families'].extend(new_surnames)
                for surname in new_surnames:
                    llm_results['identities'][identity]['counts'][surname] = 1
                # Mark as mixed detection
                llm_results['identities'][identity]['type'] = 'llm_and_keyword_detected'
    
    return llm_results
