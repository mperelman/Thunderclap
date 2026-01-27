"""
Keyword-based LGBTQ+ identity detector.

This supplements LLM detection by finding FULL NAMES (first name + surname) near LGBTQ+ keywords
(gay, homosexual, bisexual, lavender marriage, etc.) using regex patterns.

CRITICAL: LGBTQ+ identity is NAME-BASED, not surname-based. Only specific individuals
mentioned near LGBTQ+ keywords are tagged, not all people with that surname.

This is non-LLM based and uses the same keyword approach that previously worked.
"""

import re
from typing import Dict, List, Set, Tuple
from collections import defaultdict


class KeywordLGBTQDetector:
    """Find full names (first name + surname) near LGBTQ+ keywords using regex patterns."""
    
    # LGBTQ+ keywords to search for
    LGBTQ_KEYWORDS = [
        'gay', 'gays', 'homosexual', 'homosexuals', 'homosexuality',
        'bisexual', 'bisexuals', 'lesbian', 'lesbians',
        'lavender marriage', 'lavender marriages',
        'lgbt', 'lgbtq', 'lgbtq+', 'queer', 'transgender', 'trans'
    ]
    
    # Proximity window: look for full names within this many words of LGBTQ+ keywords
    PROXIMITY_WORDS = 20
    
    def __init__(self):
        """Initialize with compiled patterns."""
        # Compile keyword patterns (word boundaries, case-insensitive)
        self.keyword_patterns = []
        for keyword in self.LGBTQ_KEYWORDS:
            pattern = rf'\b{re.escape(keyword)}\b'
            self.keyword_patterns.append(re.compile(pattern, re.IGNORECASE))
        
        # Pattern to find full names: "FirstName Surname" or "J.P. Morgan" style
        # Matches: 2+ capitalized words in sequence
        self.full_name_pattern = re.compile(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b')
    
    def find_full_names_near_keywords(self, chunk: str) -> Set[str]:
        """
        Find full names (first name + surname) that appear near LGBTQ+ keywords in a chunk.
        
        Args:
            chunk: Text chunk to search
            
        Returns:
            Set of full names found near LGBTQ+ keywords (e.g., {"John Smith", "J.P. Morgan"})
        """
        full_names = set()
        
        # Find all LGBTQ+ keyword positions
        keyword_positions = []
        for pattern in self.keyword_patterns:
            for match in pattern.finditer(chunk):
                keyword_positions.append((match.start(), match.end()))
        
        if not keyword_positions:
            return full_names
        
        # Find all full names in the chunk (multi-word capitalized sequences)
        name_matches = []
        for match in self.full_name_pattern.finditer(chunk):
            full_name = match.group(0)
            start, end = match.span()
            name_matches.append((full_name, start, end))
        
        # For each keyword, find full names within proximity
        for kw_start, kw_end in keyword_positions:
            for full_name, name_start, name_end in name_matches:
                # Check if name is within proximity window
                # Calculate distance: if name ends before keyword, distance = keyword_start - name_end
                # If name starts after keyword, distance = name_start - keyword_end
                # If they overlap, distance = 0
                if name_end <= kw_start:
                    # Name appears before keyword
                    # Count words between name_end and kw_start
                    text_between = chunk[name_end:kw_start]
                    word_count = len(re.findall(r'\b\w+\b', text_between))
                    if word_count <= self.PROXIMITY_WORDS:
                        full_names.add(full_name)
                elif name_start >= kw_end:
                    # Name appears after keyword
                    text_between = chunk[kw_end:name_start]
                    word_count = len(re.findall(r'\b\w+\b', text_between))
                    if word_count <= self.PROXIMITY_WORDS:
                        full_names.add(full_name)
                else:
                    # Name and keyword overlap or are adjacent
                    full_names.add(full_name)
        
        return full_names
    
    def detect_from_chunks(self, chunks: List[str]) -> Dict[str, List[str]]:
        """
        Detect LGBTQ+ identities from chunks using keyword matching.
        
        Args:
            chunks: List of text chunks
            
        Returns:
            Dict mapping identity -> list of FULL NAMES (not just surnames)
            Format: {'gay': ['John Smith', 'J.P. Morgan'], ...}
        """
        # Map identity -> full names
        identity_to_names = defaultdict(set)
        
        print(f"[KEYWORD_LGBTQ] Scanning {len(chunks)} chunks for LGBTQ+ keywords...")
        
        for chunk_idx, chunk in enumerate(chunks):
            full_names = self.find_full_names_near_keywords(chunk)
            
            if full_names:
                # Check which keywords appear in this chunk
                chunk_lower = chunk.lower()
                has_gay = any(kw in chunk_lower for kw in ['gay', 'gays', 'homosexual', 'homosexuals', 'homosexuality'])
                has_bisexual = any(kw in chunk_lower for kw in ['bisexual', 'bisexuals'])
                has_lesbian = any(kw in chunk_lower for kw in ['lesbian', 'lesbians'])
                has_lavender = any(kw in chunk_lower for kw in ['lavender marriage', 'lavender marriages'])
                
                # Assign identities based on keywords found
                for full_name in full_names:
                    # Normalize: convert to lowercase for consistency
                    name_lower = full_name.lower()
                    
                    if has_gay or has_lavender:
                        identity_to_names['gay'].add(name_lower)
                    if has_bisexual:
                        identity_to_names['bisexual'].add(name_lower)
                    if has_lesbian:
                        identity_to_names['lesbian'].add(name_lower)
                    # Also add to general lgbtq category
                    if has_gay or has_bisexual or has_lesbian or has_lavender:
                        identity_to_names['lgbtq'].add(name_lower)
        
        # Convert sets to lists
        result = {identity: sorted(list(names)) for identity, names in identity_to_names.items()}
        
        total_names = len(set(n for names in identity_to_names.values() for n in names))
        print(f"[KEYWORD_LGBTQ] Found {total_names} unique full names with LGBTQ+ identities")
        for identity, names in result.items():
            print(f"  {identity}: {len(names)} full names")
        
        return result


# NOTE: The augment_llm_results_with_keywords function has been removed.
# Keyword detection is now integrated directly into llm_identity_detector.py
# and scripts/run_identity_detection.py to handle full names properly.
