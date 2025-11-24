"""
Identity Detector v3 - 4-Step Process
======================================

Step 1: Regex prescreen → Find chunks with identity keywords
Step 2: LLM extraction → Extract surnames + their identities from those chunks
Step 3: Regex search → Find ALL chunks containing those surnames (even without identity keywords)
Step 4: Add to index → Index both keyword-based AND surname-based chunks

This solves the "Rothschild problem":
- Chunk A: "Jewish Rothschild founded..." → Has keyword
- Chunk B: "Rothschild merged with..." → NO keyword, but has surname
- Both chunks get indexed under "jewish"

False positives (e.g., Eugene Black) are acceptable - narrative LLM will handle context.
"""

import os
import sys
import json
import hashlib
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict

# Fix imports
if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.identity_prefilter import IdentityPrefilter
from lib.llm_identity_detector import LLMIdentityDetector
from lib.identity_hierarchy import get_parent_categories


class IdentityDetectorV3:
    """4-step identity detection with surname expansion."""
    
    def __init__(self, use_cache: bool = True):
        """Initialize detector."""
        self.prefilter = IdentityPrefilter()
        self.llm_detector = LLMIdentityDetector()
        self.use_cache = use_cache
        
        # Results cache
        self.cache_file = Path('data/identity_detection_v3.json')
        self.cache = self._load_cache() if use_cache else {}
    
    def _load_cache(self) -> Dict:
        """Load cached results."""
        if self.cache_file.exists():
            with open(self.cache_file, encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_cache(self):
        """Save results to cache."""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, indent=2, ensure_ascii=False)
    
    def detect_identities(self, chunks: List[str], force_rerun: bool = False) -> Dict:
        """
        4-step identity detection process.
        
        Args:
            chunks: All document chunks
            force_rerun: Ignore cache and reprocess
        
        Returns:
            {
                'identities': {identity: {surname: [chunk_ids]}},
                'surname_to_identity': {surname: [identities]},
                'stats': {...}
            }
        """
        print("\n" + "="*70)
        print("IDENTITY DETECTION V3 - 4-Step Process")
        print("="*70)
        print()
        
        # Check cache
        if not force_rerun and self.cache and 'identities' in self.cache:
            print("[CACHE] Using cached results")
            return self.cache
        
        # STEP 1: Regex prescreen
        print("STEP 1: Regex Prescreen")
        print("-" * 70)
        relevant_indices = self.prefilter.filter_chunks(chunks)
        relevant_chunks = [chunks[i] for i in relevant_indices]
        
        print(f"  Total chunks: {len(chunks)}")
        print(f"  Relevant chunks: {len(relevant_chunks)} ({len(relevant_chunks)/len(chunks)*100:.1f}%)")
        print(f"  Filtered out: {len(chunks) - len(relevant_chunks)} ({(1-len(relevant_chunks)/len(chunks))*100:.1f}%)")
        print()
        
        # STEP 2: LLM extraction (on relevant chunks only)
        print("STEP 2: LLM Extraction (on relevant chunks)")
        print("-" * 70)
        print(f"  Processing {len(relevant_chunks)} chunks with LLM...")
        print(f"  API calls: ~{len(relevant_chunks)/20:.0f} batches")
        print()
        
        llm_results = self.llm_detector.detect_from_chunks(relevant_chunks, force_rerun=True)
        
        # Extract surname → identities mapping
        surname_to_identity = defaultdict(set)
        
        for identity, families in llm_results.get('identities', {}).items():
            for surname in families:
                surname_to_identity[surname.lower()].add(identity)
        
        print(f"  Detected {len(surname_to_identity)} unique surnames")
        print(f"  Across {len(llm_results.get('identities', {}))} identity types")
        print()
        
        # STEP 3: Regex search for surnames (across ALL chunks)
        print("STEP 3: Surname Search (across ALL chunks)")
        print("-" * 70)
        print(f"  Searching {len(chunks)} chunks for {len(surname_to_identity)} surnames...")
        print()
        
        # For each surname, find ALL chunks containing it
        surname_to_chunks = defaultdict(set)
        
        for surname in surname_to_identity.keys():
            # Create pattern for surname (word boundary)
            pattern = rf'\b{re.escape(surname)}\b'
            compiled = re.compile(pattern, re.IGNORECASE)
            
            for chunk_id, chunk in enumerate(chunks):
                if compiled.search(chunk):
                    surname_to_chunks[surname].add(chunk_id)
        
        total_surname_matches = sum(len(chunk_ids) for chunk_ids in surname_to_chunks.values())
        print(f"  Found {total_surname_matches} total surname occurrences")
        print(f"  Average {total_surname_matches/len(surname_to_identity):.1f} chunks per surname")
        print()
        
        # STEP 4: Build final index (identity → chunk IDs)
        print("STEP 4: Building Index (identity → chunks)")
        print("-" * 70)
        
        identity_to_chunks = defaultdict(set)
        
        # For each surname, add its chunks to its identities
        for surname, chunk_ids in surname_to_chunks.items():
            identities = surname_to_identity.get(surname, set())
            
            for identity in identities:
                identity_to_chunks[identity].update(chunk_ids)
                
                # Also add to parent categories (hierarchy)
                parents = get_parent_categories(identity)
                for parent in parents:
                    identity_to_chunks[parent].update(chunk_ids)
        
        # Show results
        results = {
            'identities': {
                identity: {
                    'chunk_ids': sorted(list(chunk_ids)),
                    'chunk_count': len(chunk_ids)
                }
                for identity, chunk_ids in identity_to_chunks.items()
            },
            'surname_to_identity': {s: list(ids) for s, ids in surname_to_identity.items()},
            'stats': {
                'total_chunks': len(chunks),
                'chunks_with_keywords': len(relevant_chunks),
                'unique_surnames': len(surname_to_identity),
                'identity_types': len(identity_to_chunks),
                'keyword_reduction_pct': (1 - len(relevant_chunks)/len(chunks)) * 100,
            }
        }
        
        for identity in sorted(identity_to_chunks.keys())[:15]:
            count = len(identity_to_chunks[identity])
            print(f"  {identity:20} {count:4} chunks")
        
        if len(identity_to_chunks) > 15:
            print(f"  ... and {len(identity_to_chunks) - 15} more")
        
        print()
        print("="*70)
        print("PROCESS COMPLETE")
        print("="*70)
        print(f"  Detected {len(identity_to_chunks)} searchable identity types")
        print(f"  Covering {len(surname_to_identity)} unique surnames")
        print(f"  Efficiency: Pre-filter saved {results['stats']['keyword_reduction_pct']:.1f}% API calls")
        print()
        
        # Save cache
        self.cache = results
        self._save_cache()
        
        return results


if __name__ == '__main__':
    """Test v3 detector."""
    from lib.document_parser import load_all_documents
    from lib.index_builder import split_into_chunks
    
    print("Testing Identity Detector V3\n")
    
    # Load chunks
    docs = load_all_documents(use_cache=True)
    all_chunks = []
    for doc in docs:
        all_chunks.extend(split_into_chunks(doc['text']))
    
    # Run detection
    detector = IdentityDetectorV3()
    results = detector.detect_identities(all_chunks, force_rerun=False)
    
    print("\nRESULTS:")
    print(json.dumps(results['stats'], indent=2))


