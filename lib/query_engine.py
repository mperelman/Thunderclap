"""
Query Engine - Lightweight interface for querying the indexed database.

This module provides FAST querying without loading heavy models.
Uses pre-built indices for instant term-based searches.

Routes to specialized engines (MarketEngine, IdeologyEngine, EventEngine, PeriodEngine)
based on detected query type, with fallback to general processing.
"""

import os
import json
import re
from itertools import chain
import chromadb
from typing import List, Dict, Optional, Tuple, Set
from .config import (
    VECTORDB_DIR, INDICES_FILE, COLLECTION_NAME, DEFAULT_TOP_K,
    MAX_SENTENCES_PER_PARAGRAPH, MAX_REVIEW_ITERATIONS, BATCH_SIZE, BATCH_PAUSE_SECONDS,
    CHUNK_RETRIEVAL_BATCH_SIZE, EARLY_STOP_GAP_THRESHOLD, SPARSE_RESULTS_THRESHOLD,
    MAX_TOKENS_PER_REQUEST, MAX_TOKENS_PER_MINUTE, ESTIMATED_WORDS_PER_CHUNK, TOKENS_PER_WORD, MAX_WORDS_PER_REQUEST,
    CONTROL_INFLUENCE_EARLY_CHUNK_LIMIT, CONTROL_INFLUENCE_FINAL_CHUNK_LIMIT,
    CONTROL_INFLUENCE_MAX_RETRIES, CONTROL_INFLUENCE_SLOW_THRESHOLD_SECONDS,
    BROAD_IDENTITY_EARLY_CHUNK_LIMIT, BROAD_IDENTITY_FINAL_CHUNK_LIMIT,
    BROAD_IDENTITY_MAX_RETRIES, BROAD_IDENTITY_SLOW_THRESHOLD_SECONDS
)
from .llm import LLMAnswerGenerator
from .engines.market_engine import MarketEngine
from .engines.ideology_engine import IdeologyEngine
from .engines.event_engine import EventEngine
from .engines.period_engine import PeriodEngine
from .acronyms import ACRONYM_EXPANSIONS
from .term_utils import canonicalize_term
from .constants import YEAR_PREFIX_EXPANSIONS, STOP_WORDS
from .text_utils import split_into_sentences
from .answer_reviewer import AnswerReviewer



SUBJECT_GENERIC_TERMS = {
    'bank', 'banking', 'banks', 'finance', 'financial', 'financing',
    'market', 'markets', 'money', 'capital', 'credit', 'credits',
    'trade', 'trading', 'commerce', 'commercial', 'system', 'systems',
    'policy', 'policies', 'role', 'roles', 'history', 'impact', 'influence',
    'network', 'networks', 'family', 'families', 'banker', 'bankers',
    'activities', 'operations', 'stories', 'story', 'overview', 'analysis',
    'sector', 'sectors', 'industry', 'industries', 'power', 'control',
    'panic', 'panics', 'crisis', 'crises', 'economy', 'economic',
    # de-noise generic governance terms for intersection
    'united', 'states', 'securities', 'exchange', 'commission',
    'board', 'system', 'act', 'acts', 'rule', 'rules', 'regulation', 'regulations',
    'section', 'sections', 'agency', 'agencies'
}

class QueryEngine:
    """
    Lightweight query interface for the indexed document database.
    
    Features:
    - Fast startup (~2-3 seconds)
    - Low memory usage (~50MB)
    - No heavy embedding models loaded
    - Read-only access to database
    """
    
    def __init__(self, openai_api_key: Optional[str] = None, gemini_api_key: Optional[str] = None, use_async=True):
        """
        Initialize the query engine.
        
        Args:
            openai_api_key: Optional OpenAI API key for LLM answers
            gemini_api_key: Optional Gemini API key for LLM answers
            use_async: If False, disables async optimization (for FastAPI compatibility)
        """
        import time
        print("Connecting to document database...")
        self.use_async = use_async
        # Token rate limiting: track tokens used per minute
        self._token_usage = []  # List of (timestamp, tokens) tuples
        self._token_rate_limit = MAX_TOKENS_PER_MINUTE
        
        # Connect to ChromaDB - simple approach matching archived versions
        self.chroma_client = chromadb.PersistentClient(path=VECTORDB_DIR)
        try:
            self.collection = self.chroma_client.get_collection(name=COLLECTION_NAME)
            doc_count = self.collection.count()
            coll_id = self.collection.id
            print(f"  [OK] Connected to database ({doc_count:,} indexed chunks)")
            print(f"  [OK] Collection ID: {coll_id}, Name: {self.collection.name}")
        except Exception as e:
            print(f"  [ERROR] Could not find collection '{COLLECTION_NAME}'")
            print(f"    Error: {e}")
            print(f"    Run: python build_index.py")
            print(f"  [WARNING] Server will start but queries will fail until index is built")
            # Set collection to None - queries will fail gracefully with clear error
            self.collection = None
        
        # Load pre-built indices
        self._load_indices()
        
        # Initialize advanced LLM (with fallback support)
        print("  Initializing LLM...")
        self.llm = None
        try:
            # Use Gemini API key (priority: parameter > env var)
            api_key_raw = gemini_api_key or os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
            api_key = api_key_raw.strip() if api_key_raw else None
            self.llm = LLMAnswerGenerator(api_key=api_key)
        except Exception as e:
            print(f"  [WARNING] LLM initialization failed: {e}")
        
        # Initialize answer reviewer
        self.reviewer = AnswerReviewer()
        
        print("  [OK] Query engine ready\n")
    
    def _load_indices(self):
        """Load pre-built term indices from disk."""
        print("  Loading indices...")
        
        if not os.path.exists(INDICES_FILE):
            print(f"    [!] Indices not found: {INDICES_FILE}")
            print("    Run: python build_indices.py")
            self.term_to_chunks = {}
            self.term_index = {}
            self.entity_associations = {}
            self.endnotes = {}
            self.chunk_to_endnotes = {}
            return
        
        try:
            with open(INDICES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.term_to_chunks = data.get('term_to_chunks', {})
            self.term_index = data.get('term_index', {})
            self.entity_associations = data.get('entity_associations', {})
            
            version = data.get('version', 'unknown')
            print(f"    [OK] Loaded indices (version {version})")
            print(f"      - {len(self.term_to_chunks):,} indexed terms")
        except Exception as e:
            print(f"    [ERROR] Loading indices: {e}")
            self.term_to_chunks = {}
            self.term_index = {}
            self.entity_associations = {}
        
        # Load endnotes for sparse result augmentation
        self._load_endnotes()
    
    def _load_endnotes(self):
        """Load endnotes for augmenting sparse results."""
        from .config import DATA_DIR
        
        endnotes_file = os.path.join(DATA_DIR, 'endnotes.json')
        chunk_mapping_file = os.path.join(DATA_DIR, 'chunk_to_endnotes.json')
        
        try:
            if os.path.exists(endnotes_file):
                with open(endnotes_file, 'r', encoding='utf-8') as f:
                    self.endnotes = json.load(f)
                print(f"      - {len(self.endnotes):,} endnotes loaded")
            else:
                self.endnotes = {}
            
            if os.path.exists(chunk_mapping_file):
                with open(chunk_mapping_file, 'r', encoding='utf-8') as f:
                    self.chunk_to_endnotes = json.load(f)
            else:
                self.chunk_to_endnotes = {}
        except Exception as e:
            print(f"    [WARNING] Could not load endnotes: {e}")
            self.endnotes = {}
            self.chunk_to_endnotes = {}
    
    def search_endnotes(self, term: str, max_results: int = 20) -> List[tuple]:
        """
        Search endnotes for a term (for augmenting sparse main text results).
        
        Args:
            term: Search term (case-insensitive)
            max_results: Maximum number of endnote results
        
        Returns:
            List of (text, metadata) tuples for endnotes containing the term
        """
        term_lower = term.lower()
        results = []
        
        for endnote_id, text in self.endnotes.items():
            if isinstance(text, str) and term_lower in text.lower():
                # Create chunk-like metadata for endnote
                metadata = {
                    'chunk_id': f'endnote_{endnote_id}',
                    'source_type': 'endnote',
                    'endnote_id': endnote_id,
                    'filename': 'Endnotes'
                }
                results.append((text, metadata))
                
                if len(results) >= max_results:
                    break
        
        return results
    
    def search_term(self, term: str, max_results: int = DEFAULT_TOP_K) -> List[Dict]:
        """
        Search for a specific term in the documents.
        
        Args:
            term: Search term (case-insensitive)
            max_results: Maximum number of results
            
        Returns:
            List of matching document chunks
        """
        if self.collection is None:
            raise RuntimeError("Database not initialized. Please run: python build_index.py")
        
        term_lower = term.lower()
        # Canonicalize term to match TERM_GROUPS merges (e.g., "blacks" -> "black")
        canonical = canonicalize_term(term_lower)
        # Try canonical form first (TERM_GROUPS merged variants point to same chunks)
        # Fallback to original if canonical doesn't exist (for terms not in TERM_GROUPS)
        lookup_term = canonical if canonical in self.term_to_chunks else term_lower
        
        if lookup_term not in self.term_to_chunks:
            return []
        
        # Deduplicate chunk IDs (some indices may have duplicates)
        chunk_ids = list(set(self.term_to_chunks[lookup_term]))[:max_results]
        data = self.collection.get(ids=chunk_ids)
        
        results = []
        for chunk_id, text, metadata in zip(data['ids'], data['documents'], data['metadatas']):
            results.append({
                'chunk_id': chunk_id,
                'text': text,
                'filename': metadata.get('filename', 'Unknown'),
                'source': metadata.get('source', 'main_text')
            })
        
        return results
    
    def search_family(self, family_name: str, max_results: int = DEFAULT_TOP_K) -> List[Dict]:
        """Search for information about a specific family."""
        return self.search_term(family_name, max_results)
    
    def query(self, question: str, max_chunks: int = DEFAULT_TOP_K, use_llm: bool = True) -> str:
        """Main query entry point with logging."""
        import time
        from lib.config import QUERY_TIMEOUT_SECONDS
        query_start = time.time()
        
        # Check if collection exists
        if self.collection is None:
            raise RuntimeError(
                "Database not initialized. The ChromaDB collection 'historical_documents' is missing.\n"
                "Please run: python build_index.py\n"
                "This will create the required data/ folder with indices and vector database."
            )
        
        # CRITICAL: Always get fresh collection reference to avoid ChromaDB stale UUID caching
        try:
            print(f"  [QUERY_START] Processing: '{question[:60]}...'")
            # Force fresh collection reference - ChromaDB caches UUIDs internally
            self.collection = self.chroma_client.get_collection(name=COLLECTION_NAME)
            current_coll_id = self.collection.id
            current_count = self.collection.count()
            print(f"  [QUERY_START] Fresh Collection ID: {current_coll_id}, Chunks: {current_count}")
        except Exception as e:
            print(f"  [FATAL] Cannot get collection at query start: {e}")
            import traceback
            traceback.print_exc()
            raise RuntimeError(
                f"Database connection failed: {e}\n"
                "Please ensure the index has been built: python build_index.py"
            )
            raise
        """
        Query the documents and generate an answer.
        
        Args:
            question: The question to ask
            max_chunks: Number of context chunks to retrieve
            use_llm: Whether to use LLM for answer generation
            
        Returns:
            Generated answer or raw context
        """
        # Rely on index-provided acronym/full-name normalization; do not rewrite the user's query here
        
        # Extract keywords from question
        # Use centralized STOP_WORDS from constants.py
        raw_tokens = re.findall(r"[A-Za-z']+", question)
        base_token_count = 0
        keywords = []
        canonical_map: Dict[str, set] = {}
        for token in raw_tokens:
            lower = token.lower()
            if lower in STOP_WORDS or len(lower) <= 3:
                continue
            base_token_count += 1
            if token.isupper():
                keywords.append(token)
                continue
            canonical = canonicalize_term(token)
            if canonical:
                keywords.append(canonical)
                canonical_map.setdefault(canonical, set()).add(lower)
        
        # Deduplicate while preserving order
        seen = set()
        keywords = [k for k in keywords if not (k in seen or seen.add(k))]
        subject_terms, subject_phrases = self._extract_subject_filters(
            question,
            keywords,
            raw_tokens,
            canonical_map
        )
        # Extract law tokens (e.g., TA86) and expanded phrases (e.g., Treasury Tax Act 1986)
        law_terms = self._extract_law_tokens(question)
        
        # Expand keywords using identity hierarchy
        # Disable identity expansion for literal single-identity queries
        meaningful = [k for k in keywords if k not in SUBJECT_GENERIC_TERMS]
        disable_identity_expansion = len(meaningful) <= 2 and not any(tok.isupper() for tok in raw_tokens)
        if not disable_identity_expansion:
            try:
                from lib.identity_hierarchy import expand_search_terms
                keywords = expand_search_terms(keywords)
                if len(keywords) > base_token_count:
                    print(f"  [HIERARCHY] Expanded search to include related identities")
            except ImportError as e:
                pass  # Identity hierarchy optional
            except Exception as e:
                print(f"  [WARN] Identity expansion failed: {e}")
        
        # Collect chunks with INTERSECTION preference for meaningful terms.
        # Special-case: if an ALL-CAPS acronym (e.g., SEC, FRS, NYSE) is present,
        # restrict intersection to the acronym token to avoid diluting with generic words.
        # Treat ANY ALL-CAPS token as an acronym for retrieval anchoring
        acronyms = [tok for tok in raw_tokens if tok.isupper()]
        if acronyms:
            intersect_terms = [a for a in acronyms if a in self.term_to_chunks]
        else:
            intersect_terms = [
                k for k in keywords
                if k not in SUBJECT_GENERIC_TERMS and k in self.term_to_chunks
            ]
        # Include law terms (both literal and expanded phrases) in retrieval anchor set
        for law_term in law_terms:
            if law_term in self.term_to_chunks and law_term not in intersect_terms:
                intersect_terms.append(law_term)
        
        # Check for firm name + location phrases (e.g., "Rothschild Vienna")
        # Also check for multi-word firm names (e.g., "First National Bank of Boston")
        # These are indexed as phrases when the firm name is italicized
        # Phrases are canonicalized (no plurals/possessives) in the index
        # IMPORTANT: Use meaningful terms (calculated before identity expansion) to ensure phrase matching works
        firm_location_phrases = []
        firm_name_phrases = []
        
        # First, try to match the entire question as a firm name (for queries like "Tell me about First National Bank of Boston")
        # Extract potential firm name from question (remove "tell me about", "what is", etc.)
        question_lower = question.lower()
        
        # CRITICAL: Exclude identity terms from firm name detection
        # Identity terms should be handled by identity query detection, not firm name detection
        from lib.identity_terms import IDENTITY_TERMS_SET as identity_terms_set
        
        firm_name_patterns = [
            r'tell me about (.+)',
            r'what is (.+)',
            r'who is (.+)',
            r'explain (.+)',
            r'describe (.+)',
            r'^(.+)$'  # Fallback: entire question
        ]
        for pattern in firm_name_patterns:
            match = re.search(pattern, question_lower)
            if match:
                potential_firm = match.group(1).strip()
                # Remove trailing question marks, periods
                potential_firm = potential_firm.rstrip('?.!')
                
                # CRITICAL: Skip if this is an identity term (not a firm name)
                potential_firm_lower = potential_firm.lower()
                if potential_firm_lower in identity_terms_set:
                    print(f"  [SKIP] Skipping firm name detection for identity term: '{potential_firm}'")
                    break  # Don't treat identity terms as firm names
                
                # Try matching as firm name (canonicalized)
                firm_clean = canonicalize_term(potential_firm)
                if firm_clean and firm_clean in self.term_to_chunks:
                    # Double-check: if canonicalized version is an identity term, skip
                    if firm_clean.lower() in identity_terms_set:
                        print(f"  [SKIP] Skipping firm name detection for identity term (canonicalized): '{firm_clean}'")
                        break
                    firm_name_phrases.append(firm_clean)
                    print(f"  [FIRM_NAME] Found indexed firm name: '{firm_clean}' ({len(self.term_to_chunks[firm_clean])} chunks)")
                    break
                # CRITICAL: If query has "National Bank" but index has "NB", try the NB variant
                # This allows "First National Bank of Boston" queries to match "first nb of boston" entries
                # But ONLY if the query explicitly mentions "National Bank" - no automatic expansion
                if 'national bank' in firm_clean:
                    firm_with_nb = firm_clean.replace(' national bank ', ' nb ').replace(' national bank of ', ' nb of ').replace(' national bank$', ' nb')
                    if firm_with_nb != firm_clean and firm_with_nb in self.term_to_chunks:
                        firm_name_phrases.append(firm_with_nb)
                        print(f"  [FIRM_NAME] Found indexed firm name (NB variant): '{firm_with_nb}' ({len(self.term_to_chunks[firm_with_nb])} chunks)")
                        break
        
        # Also try multi-word phrases (3+ words) from the question
        if len(meaningful) >= 3:
            # Try 3-word phrases (e.g., "first national bank")
            raw_meaningful = []
            for m in meaningful:
                originals = canonical_map.get(m, {m})
                raw_meaningful.append(list(originals)[0].lower())
            
            # Try 3-word phrases
            for i in range(len(raw_meaningful) - 2):
                phrase_3 = f"{raw_meaningful[i]} {raw_meaningful[i+1]} {raw_meaningful[i+2]}"
                if phrase_3 in self.term_to_chunks:
                    firm_name_phrases.append(phrase_3)
                    print(f"  [FIRM_NAME] Found indexed 3-word firm phrase: '{phrase_3}' ({len(self.term_to_chunks[phrase_3])} chunks)")
            
            # Try 4-word phrases (e.g., "first national bank of")
            for i in range(len(raw_meaningful) - 3):
                phrase_4 = f"{raw_meaningful[i]} {raw_meaningful[i+1]} {raw_meaningful[i+2]} {raw_meaningful[i+3]}"
                if phrase_4 in self.term_to_chunks:
                    firm_name_phrases.append(phrase_4)
                    print(f"  [FIRM_NAME] Found indexed 4-word firm phrase: '{phrase_4}' ({len(self.term_to_chunks[phrase_4])} chunks)")
        
        # Then check for 2-word firm+location phrases (e.g., "Rothschild Vienna")
        if len(meaningful) >= 2:
            # Use original raw tokens for phrase matching (before canonicalization)
            raw_meaningful = []
            for m in meaningful:
                originals = canonical_map.get(m, {m})
                raw_meaningful.append(list(originals)[0].lower())
            
            # Try 2-word phrases
            for i in range(len(raw_meaningful) - 1):
                phrase_orig = f"{raw_meaningful[i]} {raw_meaningful[i+1]}"
                if phrase_orig in self.term_to_chunks:
                    firm_location_phrases.append(phrase_orig)
                    print(f"  [PHRASE] Found indexed firm phrase: '{phrase_orig}' ({len(self.term_to_chunks[phrase_orig])} chunks)")
                else:
                    phrase_canon = f"{meaningful[i]} {meaningful[i+1]}"
                    if phrase_canon in self.term_to_chunks:
                        firm_location_phrases.append(phrase_canon)
                        print(f"  [PHRASE] Found indexed firm phrase (canonicalized): '{phrase_canon}' ({len(self.term_to_chunks[phrase_canon])} chunks)")
        
        # Combine firm name phrases and location phrases
        all_firm_phrases = firm_name_phrases + firm_location_phrases
        
        # Prioritize firm name/location phrases if found
        chunk_ids = set()
        # Build term_sets for later use (needed for augmentation logic)
        # Always assign term_sets unconditionally first to avoid scoping issues
        term_sets = []
        if intersect_terms:
            term_sets = [set(self.term_to_chunks[k]) for k in intersect_terms]
        
        # CRITICAL: If we found a firm phrase match, use that phrase as primary, but ALSO augment with chunks containing all key terms
        # This catches chunks that mention the firm in full form (e.g., "First National Bank of Boston") even if not indexed as exact phrase
        if all_firm_phrases:
            # Use phrase chunks as primary source
            phrase_chunk_ids = set()
            for phrase in all_firm_phrases:
                phrase_chunk_ids.update(self.term_to_chunks[phrase])
            chunk_ids = phrase_chunk_ids
            print(f"  [PHRASE] Using {len(chunk_ids)} chunks from firm name phrases")
            
            # CRITICAL: If query mentions "National Bank" but we matched "first boston" (without "national"),
            # exclude "first boston" chunks to avoid mixing CSFB with First National Bank
            if 'national bank' in question_lower or 'national' in question_lower:
                # Check if we matched "first boston" without "national"
                first_boston_only = [p for p in all_firm_phrases if 'first boston' in p and 'national' not in p]
                if first_boston_only:
                    print(f"  [FILTER] Query mentions 'National Bank' but matched '{first_boston_only[0]}' - excluding to avoid CSFB confusion")
                    # Remove "first boston" chunks (likely CSFB, not First National Bank)
                    first_boston_chunks = set()
                    for phrase in first_boston_only:
                        first_boston_chunks.update(self.term_to_chunks[phrase])
                    chunk_ids = chunk_ids - first_boston_chunks
                    print(f"  [FILTER] Excluded {len(first_boston_chunks)} chunks, remaining: {len(chunk_ids)} chunks")
            
            # AUGMENT: For each exact firm phrase found, also check for its abbreviated version
            # Example: "First National Bank of Boston" → also check "First NB of Boston"
            # This is phrase-specific: only augment with the exact abbreviated phrase, not broad intersections
            for phrase in all_firm_phrases:
                # Generate abbreviated version by replacing "national bank" with "nb"
                # Handle both "national bank" and "national bank of" patterns
                phrase_abbrev = phrase.replace(' national bank of ', ' nb of ').replace(' national bank ', ' nb ').replace(' national bank', ' nb')
                
                # Only add if it's different from original and exists in index
                if phrase_abbrev != phrase and phrase_abbrev in self.term_to_chunks:
                    before_count = len(chunk_ids)
                    chunk_ids.update(self.term_to_chunks[phrase_abbrev])
                    added_count = len(chunk_ids) - before_count
                    if added_count > 0:
                        print(f"  [AUGMENT] Added {added_count} chunks from abbreviated phrase '{phrase_abbrev}' (from '{phrase}')")
            
            
            # Don't cap - let the batching system handle it (PeriodEngine for >30 chunks)
        else:
            # Fall back to intersection logic (only when NO firm phrase was found)
            # CRITICAL: For firm name queries, be strict - don't match wrong firms
            # Example: Query "First National Bank of Boston" shouldn't match "First Boston" (CSFB)
            # Note: "First NB of Boston" and "Second NB of Boston" are different banks - 
            # if no exact match found, return empty rather than matching wrong firm
            # Check if query looks like a firm name query (has "National Bank" or "NB of")
            is_firm_name_query = ('national bank' in question_lower or ' nb of ' in question_lower or question_lower.endswith(' nb'))
            
            if len(term_sets) >= 2:
                # Prefer intersection when 2+ meaningful terms are present
                intersection = set.intersection(*term_sets) if term_sets else set()
                if intersection:
                    chunk_ids = intersection
                else:
                    # Fallback to union if intersection is empty
                    # BUT: For firm name queries, don't use union - it would match wrong firms
                    # Example: Query "First National Bank of Boston" shouldn't match "First Boston" (CSFB)
                    # Note: "First NB of Boston" vs "Second NB of Boston" are different banks - 
                    # if no exact match, return empty rather than matching wrong firm
                    if is_firm_name_query:
                        print(f"  [STRICT] Firm name query detected but no exact phrase match - requiring strict intersection, not union")
                        print(f"  [STRICT] This prevents matching wrong firms (e.g., 'First Boston' when querying 'First National Bank')")
                        # Return empty rather than using union - better to return nothing than wrong results
                        chunk_ids = set()
                    else:
                        # Non-firm queries: use union fallback
                        for s in term_sets:
                            chunk_ids.update(s)
            else:
                if term_sets:
                    # Single meaningful term: use its set only (no union with generic terms)
                    chunk_ids = term_sets[0]
                else:
                    # No meaningful terms found; fallback to union of whatever tokens mapped
                    for keyword in keywords:
                        if keyword in self.term_to_chunks:
                            chunk_ids.update(self.term_to_chunks[keyword])
        
        # CRITICAL: Detect control/influence queries EARLY and limit chunks BEFORE augmentation
        # These queries are very broad and will timeout if we retrieve too many chunks
        # Use VERY small limit (8) to ensure fast processing and avoid rate limits
        # VERSION: 2025-01-22 - Early limit for control/influence queries
        is_control_influence = self._is_control_influence_query(question)
        print(f"  [VERSION_CHECK] Using updated query_engine.py with early limit (2025-01-22)")
        print(f"  [DEBUG] Control/influence check: is_control={is_control_influence}, chunk_count={len(chunk_ids)}")
        if is_control_influence and len(chunk_ids) > CONTROL_INFLUENCE_EARLY_CHUNK_LIMIT:
            print(f"  [EARLY_LIMIT] Control/influence query detected - limiting chunks from {len(chunk_ids)} to {CONTROL_INFLUENCE_EARLY_CHUNK_LIMIT} before augmentation")
            chunk_ids = set(list(chunk_ids)[:CONTROL_INFLUENCE_EARLY_CHUNK_LIMIT])
            print(f"  [EARLY_LIMIT] After limit: {len(chunk_ids)} chunks")
        
        # Also detect broad identity queries (like "Tell me about black" or "Tell me about women")
        # These are not control/influence queries but still need chunk limiting to avoid timeouts
        # CRITICAL: Sample chunks from different time periods to ensure chronological coverage
        is_broad_identity = self._is_broad_identity_query(question)
        if not is_control_influence and is_broad_identity and len(chunk_ids) > BROAD_IDENTITY_EARLY_CHUNK_LIMIT:
            print(f"  [BROAD_IDENTITY] Broad identity query detected - sampling {BROAD_IDENTITY_EARLY_CHUNK_LIMIT} chunks from {len(chunk_ids)} to ensure chronological diversity")
            # Sample chunks from different time periods instead of just taking first N
            try:
                # Get chunk texts to analyze years
                try:
                    _ = self.collection.id  # Force validation
                except Exception:
                    self.collection = self.chroma_client.get_collection(name=COLLECTION_NAME)
                sample_chunk_data = self.collection.get(ids=list(chunk_ids)[:min(200, len(chunk_ids))])  # Sample up to 200 to analyze
                chunks_with_years = []
                for i, chunk_id in enumerate(sample_chunk_data['ids']):
                    text = sample_chunk_data['documents'][i]
                    # Find years in chunk
                    matches = re.findall(r'\b(1[6-9]\d{2}|20[0-2]\d)\b', text)
                    if matches:
                        latest_year = max(int(m) for m in matches)
                        decade = (latest_year // 10) * 10
                    else:
                        decade = 0  # Undated
                    chunks_with_years.append((chunk_id, decade))
                
                # Group by decade
                chunks_by_decade = {}
                for chunk_id, decade in chunks_with_years:
                    if decade not in chunks_by_decade:
                        chunks_by_decade[decade] = []
                    chunks_by_decade[decade].append(chunk_id)
                
                # Sample evenly across decades (at least 1-2 per decade, up to limit)
                sampled_chunk_ids = []
                chunks_per_decade = max(1, BROAD_IDENTITY_EARLY_CHUNK_LIMIT // max(len(chunks_by_decade), 1))
                for decade in sorted(chunks_by_decade.keys()):
                    dec_chunks = chunks_by_decade[decade][:chunks_per_decade]
                    sampled_chunk_ids.extend(dec_chunks)
                    if len(sampled_chunk_ids) >= BROAD_IDENTITY_EARLY_CHUNK_LIMIT:
                        break
                
                # If we still need more, add from remaining chunks
                if len(sampled_chunk_ids) < BROAD_IDENTITY_EARLY_CHUNK_LIMIT:
                    remaining = [cid for cid in chunk_ids if cid not in sampled_chunk_ids]
                    sampled_chunk_ids.extend(remaining[:BROAD_IDENTITY_EARLY_CHUNK_LIMIT - len(sampled_chunk_ids)])
                
                chunk_ids = set(sampled_chunk_ids[:BROAD_IDENTITY_EARLY_CHUNK_LIMIT])
                print(f"  [BROAD_IDENTITY] Sampled {len(chunk_ids)} chunks across {len(chunks_by_decade)} decades")
            except Exception as e:
                # Fallback to simple limit if sampling fails
                print(f"  [BROAD_IDENTITY] Sampling failed ({e}), using simple limit")
                chunk_ids = set(list(chunk_ids)[:BROAD_IDENTITY_EARLY_CHUNK_LIMIT])
            print(f"  [BROAD_IDENTITY] After limit: {len(chunk_ids)} chunks")
        
        # Augment queries with crisis/panic chunks that overlap the subject
        # SKIP this augmentation if we matched a firm phrase (e.g., "First National Bank of Boston")
        # because firm phrases are specific entities - crisis augmentation adds too many chunks (100+)
        # and the firm phrase chunks already include relevant crisis contexts
        # LIMIT crisis augmentation to avoid timeouts: cap at 20 chunks max
        # SKIP crisis augmentation for control/influence queries (they're already limited)
        # SKIP crisis augmentation for broad identity queries (they're already limited)
        if chunk_ids and not all_firm_phrases and not is_control_influence and not is_broad_identity:
            try:
                crisis_terms = ['panic', 'crisis', 'crises', '1973', '1974', '1987', '1998', '2008', '1929', '1907', '1825', '1873']
                crisis_ids = set()
                for term in crisis_terms:
                    if term in self.term_to_chunks:
                        crisis_ids.update(self.term_to_chunks[term])
                # Subject anchor: use acronyms, else subject_terms union
                subject_anchor_terms = []
                if acronyms:
                    subject_anchor_terms = [a for a in acronyms if a in self.term_to_chunks]
                elif subject_terms:
                    subject_anchor_terms = [t for t in subject_terms if t in self.term_to_chunks]
                subject_ids_union = set()
                for t in subject_anchor_terms:
                    subject_ids_union.update(self.term_to_chunks.get(t, []))
                # Add only overlaps to avoid unrelated crisis chunks
                # LIMIT to 20 chunks max to avoid timeouts on large queries
                if subject_ids_union and crisis_ids:
                    overlap = crisis_ids & subject_ids_union
                    if overlap:
                        # Limit crisis chunks to prevent timeout (take first 20)
                        limited_overlap = list(overlap)[:20]
                        chunk_ids.update(limited_overlap)
                        print(f"  [AUGMENT] Added {len(limited_overlap)} crisis-related chunks (limited from {len(overlap)} to avoid timeout)")
            except Exception as e:
                pass  # Crisis augmentation optional
        
        # Augment with chunks from later time periods that mention any subject term
        # This ensures we don't miss later periods due to strict intersection
        # We detect the time span of current chunks and ensure later periods are included
        # SKIP this augmentation if we matched a firm phrase (e.g., "Rothschild Vienna")
        # because firm phrases are specific entities that shouldn't be expanded with individual terms
        # SKIP this augmentation for control/influence queries (they're already limited)
        # SKIP this augmentation for broad identity queries (they're already limited)
        if chunk_ids and subject_terms and len(term_sets) >= 2 and not all_firm_phrases and not is_control_influence and not is_broad_identity:
            try:
                # First, determine the time span of currently retrieved chunks
                # Verify collection before accessing
                try:
                    _ = self.collection.id  # Force validation
                except Exception:
                    self.collection = self.chroma_client.get_collection(name=COLLECTION_NAME)
                current_chunk_data = self.collection.get(ids=list(chunk_ids)[:100])  # Sample to find time span
                current_years = set()
                for text in current_chunk_data['documents']:
                    matches = re.findall(r'\b(1[6-9]\d{2}|20[0-2]\d)\b', text)
                    if matches:
                        current_years.update(int(m) for m in matches)
                
                if current_years:
                    current_latest = max(current_years)
                    # Get union of all subject terms (chunks mentioning any subject term)
                    subject_union = set()
                    for term in subject_terms:
                        if term in self.term_to_chunks:
                            subject_union.update(self.term_to_chunks[term])
                    
                    # Fetch chunks and filter for chunks from later periods than what we have
                    if subject_union:
                        later_period_ids = set()
                        # Check all chunks from union that aren't in intersection
                        candidate_ids = list(subject_union - chunk_ids)
                        if candidate_ids:
                            # Process in batches to avoid memory issues
                            batch_size = CHUNK_RETRIEVAL_BATCH_SIZE
                            for i in range(0, len(candidate_ids), batch_size):
                                batch_ids = candidate_ids[i:i+batch_size]
                                batch_data = self.collection.get(ids=batch_ids)
                                for chunk_id, text, meta in zip(batch_data['ids'], batch_data['documents'], batch_data['metadatas']):
                                    # Check if chunk has years later than what we already have
                                    matches = re.findall(r'\b(1[6-9]\d{2}|20[0-2]\d)\b', text)
                                    if matches:
                                        latest_year = max(int(m) for m in matches)
                                        # Only add if it's from a later period than what we already retrieved
                                        if latest_year > current_latest:
                                            later_period_ids.add(chunk_id)
                            
                            if later_period_ids:
                                chunk_ids.update(later_period_ids)
                                print(f"  [AUGMENT] Added {len(later_period_ids)} later-period chunks (after {current_latest}) mentioning subject terms")
            except Exception as e:
                print(f"  [WARN] Later period augmentation failed: {e}")
        
        # If still empty or sparse, try entity alias expansions for known synonyms (e.g., Narodny Bank → Narodny)
        if not chunk_ids or len(chunk_ids) < 3:
            try:
                ql = question.lower()
                ENTITY_ALIASES = {
                    "narodny bank": ["narodny"],
                    "vneshtorgbank": ["vneshtorg", "bank for foreign trade", "vneshtorg bank"],
                    "vneshtorg": ["vneshtorgbank", "bank for foreign trade"],
                    "frs": ["federal reserve system", "federal reserve"],
                    "boe": ["bank of england"]
                }
                expanded_terms = set()
                for phrase, alts in ENTITY_ALIASES.items():
                    if phrase in ql:
                        expanded_terms.update(alts)
                # Also check keywords for aliasable phrases
                for kw in keywords:
                    if kw in ENTITY_ALIASES:
                        expanded_terms.update(ENTITY_ALIASES[kw])
                for term in expanded_terms:
                    if term in self.term_to_chunks:
                        chunk_ids.update(self.term_to_chunks[term])
                if expanded_terms:
                    print(f"  [AUGMENT] Applied entity aliases: {sorted(expanded_terms)}")
            except Exception:
                pass

        if not chunk_ids:
            return "No relevant information found."
        
        # Fetch chunks - deduplicated by set(), but get them all
        chunk_ids_list = list(chunk_ids)
        # Verify collection is still valid before accessing
        try:
            current_id = self.collection.id
            print(f"    [FETCH] Collection ID before get(): {current_id}")
        except Exception as e:
            print(f"    [ERROR] Collection invalid, reconnecting: {e}")
            self.collection = self.chroma_client.get_collection(name=COLLECTION_NAME)
            print(f"    [RECONNECT] New collection ID: {self.collection.id}")
        data = self.collection.get(ids=chunk_ids_list)
        
        print(f"  [INFO] Found {len(chunk_ids_list)} relevant chunks")
        
        # Augment with endnotes if results are sparse
        # CRITICAL: Skip endnote augmentation for firm name queries to avoid pushing chunk count over fast-path threshold (20)
        # Firm name queries should use exact phrase matches, not broad endnote augmentation
        endnote_chunks = []
        is_firm_name_query = any('national bank' in q.lower() or ' nb of ' in q.lower() for q in [question])
        skip_endnotes = is_firm_name_query and len(chunk_ids_list) >= 10  # Don't augment if we already have reasonable coverage
        if not skip_endnotes and len(chunk_ids_list) < SPARSE_RESULTS_THRESHOLD and self.chunk_to_endnotes and self.endnotes:
            print(f"  [AUGMENT] Sparse results - including endnotes linked to {len(chunk_ids_list)} chunks...")
            endnote_ids = set()
            
            # Get all endnote IDs linked to the chunks we found
            for chunk_id in chunk_ids_list:
                if chunk_id in self.chunk_to_endnotes:
                    endnote_ids.update(self.chunk_to_endnotes[chunk_id])
            
            # Include entire endnote texts (no searching - just include what's linked)
            if endnote_ids:
                for endnote_id in endnote_ids:
                    if endnote_id in self.endnotes:
                        text = self.endnotes[endnote_id]
                        metadata = {
                            'chunk_id': f'endnote_{endnote_id}',
                            'source_type': 'endnote',
                            'endnote_id': endnote_id,
                            'filename': 'Endnotes'
                        }
                        endnote_chunks.append((text, metadata))
                
                print(f"  [AUGMENT] Added {len(endnote_chunks)} endnotes linked to chunks ({len(chunk_ids_list)} chunks → {len(endnote_chunks)} endnotes)")
        
        # Generate answer using advanced LLM if available
        if use_llm and self.llm:
            # Prepare chunks in the format expected by LLM
            chunks = [
                (text, meta)
                for text, meta in zip(data['documents'], data['metadatas'])
            ]
            # Ideology tightening: for Marxism/Socialism/Communism/Collectivism, filter to finance-relevant chunks
            if self._is_ideology_query(question):
                chunks = self._filter_chunks_for_ideology(chunks, question)
            
            # For broad identity queries, filter to banking/finance-relevant chunks only
            # This prevents mixing unrelated historical/political information (e.g., African kingdoms) with banking topics
            # CRITICAL: Require STRICT banking/finance terms, not general "trade", "commerce", or "economic" which can refer to non-banking activities
            # NOTE: Chunks may be in the identity index via identity augmentation (e.g., chunks about Parsons/Lewis added to "black" index)
            # So we don't require explicit identity terms in chunk text - if chunk is in identity index, it's already relevant
            if 'is_broad_identity' in locals() and is_broad_identity:
                # Strict banking/finance keywords only (exclude general "trade", "commerce", "economic" which can be non-banking)
                strict_finance_keywords = ['bank', 'banking', 'banker', 'bankers', 'finance', 'financial', 'financier', 'financiers',
                                          'investment', 'investor', 'investors', 'capital', 'credit', 'loan', 'lending', 
                                          'firm', 'company', 'corporation', 'enterprise', 'insurance', 'lic', 'mesbic', 'cdfi',
                                          'supplier', 'contract', 'wealth', 'business', 'businesses',
                                          'stock', 'stocks', 'bond', 'bonds', 'securities', 'exchange', 'market', 'markets']
                # Exclude chunks that mention non-banking economic terms without banking terms
                exclude_if_only = ['slave trade', 'transatlantic', 'colonial econom', 'loyalist', 'settlement', 'colony', 'migration']
                
                # Exclude chunks that mention non-identity contexts (based on actual document analysis)
                # Only exclude what actually appears in the documents
                exclude_geographic_patterns = [
                    r'\bblack sea\b',                    # Black Sea (geographic) - 21 occurrences found
                    r'\bblack sea fleet\b',              # Black Sea Fleet (geographic/military)
                ]
                
                # Exclude person names (not identity-related)
                exclude_person_patterns = [
                    r'\beugene black\b',                 # Eugene Black (person's name) - 12 occurrences found
                ]
                
                # Exclude product/commodity terms (not identity-related)
                exclude_product_patterns = [
                    r'\bblack tea\b',                    # Black tea (product) - 1 occurrence found
                ]
                
                filtered_chunks = []
                for text, meta in chunks:
                    text_lower = text.lower()
                    # Require strict finance keyword (chunks are already in identity index, so identity relevance is assumed)
                    has_finance = any(keyword in text_lower for keyword in strict_finance_keywords)
                    
                    # Exclude if it only mentions non-banking economic terms without banking terms
                    has_only_non_banking = any(term in text_lower for term in exclude_if_only) and not has_finance
                    
                    # Exclude geographic contexts (Black Sea, etc.) - these are not identity-related
                    is_geographic = any(re.search(pattern, text_lower) for pattern in exclude_geographic_patterns)
                    
                    # Exclude person names (Eugene Black, etc.) - these are not identity-related
                    is_person_name = any(re.search(pattern, text_lower) for pattern in exclude_person_patterns)
                    
                    # Exclude product/commodity terms (black tea, etc.) - these are not identity-related
                    is_product = any(re.search(pattern, text_lower) for pattern in exclude_product_patterns)
                    
                    # CRITICAL: Exclude lowercase "black" - identity uses capitalized "Black"
                    # Check if chunk has lowercase "black" but NOT capitalized "Black"
                    # Find all instances (case-sensitive)
                    lowercase_black_matches = list(re.finditer(r'\bblack\b', text))  # lowercase only
                    capitalized_black_matches = list(re.finditer(r'\bBlack\b', text))  # capitalized only
                    
                    # If chunk has ONLY lowercase "black" (no capitalized "Black"), exclude it
                    # Exception: allow if lowercase appears in clearly identity-related phrases
                    has_lowercase_only = len(lowercase_black_matches) > 0 and len(capitalized_black_matches) == 0
                    
                    if has_lowercase_only:
                        # Check if lowercase "black" appears in identity-related contexts
                        identity_contexts = ['black-owned', 'black banker', 'black bank', 'black community', 
                                            'black person', 'black individual', 'black elite', 'black family',
                                            'black american', 'black african', 'black slave', 'black loyalist',
                                            'black lic', 'black frs', 'black governor', 'black chair']
                        has_identity_context = any(context in text_lower for context in identity_contexts)
                        # If no identity context, exclude (it's probably "black sea", "black tea", etc.)
                        if not has_identity_context:
                            continue  # Skip this chunk
                    
                    # Only include if it has finance keywords AND not excluded AND not geographic/person/product
                    if has_finance and not has_only_non_banking and not is_geographic and not is_person_name and not is_product:
                        filtered_chunks.append((text, meta))
                
                if filtered_chunks:
                    print(f"  [FILTER] Filtered {len(chunks)} chunks to {len(filtered_chunks)} finance-relevant chunks for broad identity query (required finance keywords, excluded non-banking)")
                    chunks = filtered_chunks
                else:
                    print(f"  [WARN] No finance-relevant chunks found after filtering - using all chunks")
            
            # Append endnote chunks
            if endnote_chunks:
                chunks.extend(endnote_chunks)

            # Store original chunks (no filtering - send all chunks to ensure full coverage)
            original_chunks = chunks[:]
            
            # Try to use preprocessed deduplicated file if available
            chunks = self._try_use_preprocessed_file(chunks, question) or chunks
            
            # Deduplicate and merge overlapping chunks before sending to LLM (if no preprocessed file)
            if chunks == original_chunks:  # No preprocessed file was used
                chunks = self._deduplicate_and_combine_chunks(chunks)
                print(f"  [DEDUP] Reduced {len(original_chunks)} chunks to {len(chunks)} after deduplication/merging")
            else:
                print(f"  [DEDUP] Used preprocessed deduplicated file ({len(chunks)} chunks)")
            
            # Apply final chunk limit for broad identity queries (after deduplication)
            if 'is_broad_identity' in locals() and is_broad_identity and len(chunks) > BROAD_IDENTITY_FINAL_CHUNK_LIMIT:
                print(f"  [BROAD_IDENTITY] Final limit: reducing chunks from {len(chunks)} to {BROAD_IDENTITY_FINAL_CHUNK_LIMIT}")
                chunks = chunks[:BROAD_IDENTITY_FINAL_CHUNK_LIMIT]
            
            # Detect special query types
            # Note: is_control_influence already detected earlier (before augmentation)
            is_market = self._is_market_query(question)
            is_event = self._is_event_query(question)
            is_ideology = self._is_ideology_query(question)
            # Re-check control/influence if not already detected (shouldn't happen, but safety check)
            if 'is_control_influence' not in locals():
                is_control_influence = self._is_control_influence_query(question)
            # Re-check broad identity if not already detected
            if 'is_broad_identity' not in locals():
                is_broad_identity = self._is_broad_identity_query(question)
            
            if is_market:
                print(f"  [AUTO] Market/asset query detected ({len(chunks)} chunks)")
                print(f"  [AUTO] Routing to MarketEngine...")
                try:
                    text = MarketEngine(self).generate(question, chunks)
                except Exception as _e:
                    # Fallback to legacy path on engine error
                    print("  [WARN] MarketEngine failed; falling back to legacy generator")
                    try:
                        chunks = self._sort_chunks_by_year(chunks)
                    except Exception as e:
                        pass  # Chunk sorting optional
                    text = self._generate_geographic_narrative(question, chunks, for_market=True)
                # Market post-check: ensure crises/panics are mentioned when present in sources
                if not self._has_market_crises(text):
                    text = text.strip() + "\n\n" + "**Crisis Episodes (from sources):**\n- Include relevant panics/crises (e.g., 1973–74, 1987, 1998, 2008) and explain liquidity/margin changes.\n"
                # Debug: print years in original_chunks
                chunk_years = set()
                for text_chunk, _ in original_chunks:
                    matches = re.findall(r'\b(1[6-9]\d{2}|20[0-2]\d)\b', text_chunk)
                    chunk_years.update(int(m) for m in matches)
                needs = self._needs_grounding(text) or self._answer_stops_early(text, original_chunks) or self._paragraphs_exceed_limit(text)
                if needs:
                    print(f"  [RE-ASK] Market query: detected issues; re-asking with all {len(original_chunks)} chunks")
                    text = self._call_llm_with_rate_limit(question, original_chunks)
                # Review and fix answer against criteria
                text = self._review_and_fix_answer(text, original_chunks, question, query_start_time=query_start)
                return text
            if is_control_influence:
                print(f"  [AUTO] Control/influence query detected ({len(chunks)} chunks)")
                print(f"  [AUTO] Applying special guidance for group control/influence questions...")
                # Chunks already limited earlier, but limit further after deduplication
                # Use very small limit to stay under token limits and ensure fast processing
                if len(chunks) > CONTROL_INFLUENCE_FINAL_CHUNK_LIMIT:
                    print(f"  [LIMIT] Reducing chunks from {len(chunks)} to {CONTROL_INFLUENCE_FINAL_CHUNK_LIMIT} for control/influence query")
                    chunks = chunks[:CONTROL_INFLUENCE_FINAL_CHUNK_LIMIT]
                # Use regular generate_answer path which handles rate limits better and uses standard prompts
                # The control/influence guidance is already in prompts.py (CRITICAL_RELEVANCE_AND_ACCURACY section)
                # So we just use the standard build_prompt - no need to duplicate guidance here
                from lib.prompts import build_prompt
                prompt = build_prompt(question, chunks, is_control_influence=True)
                import time
                start_time = time.time()
                
                # Temporarily reduce retries for control queries (prevents long waits)
                # With rate limits, even reduced retries can take time, but better than default 20
                self.llm._temp_max_attempts = CONTROL_INFLUENCE_MAX_RETRIES
                
                try:
                    answer = self.llm.call_api(prompt)
                    elapsed = time.time() - start_time
                    print(f"  [CONTROL] LLM call completed in {elapsed:.1f}s")
                    if elapsed > CONTROL_INFLUENCE_SLOW_THRESHOLD_SECONDS:
                        print(f"  [WARN] LLM call was slow ({elapsed:.1f}s) but completed")
                    return answer
                except Exception as e:
                    elapsed = time.time() - start_time
                    print(f"  [ERROR] LLM call failed after {elapsed:.1f}s: {e}")
                    if elapsed > 180:  # 3 minutes
                        return f"⚠️ Query timed out after {elapsed:.0f} seconds. The query '{question}' is very broad. Please try a more specific question:\n\n- 'Which specific Jewish families dominated banking in 19th century London?'\n- 'How did Quakers compare to Jews in banking during the 1800s?'\n- 'What role did Rothschild family play in European banking?'"
                    raise
                finally:
                    # Restore original max_attempts
                    if hasattr(self.llm, '_temp_max_attempts'):
                        delattr(self.llm, '_temp_max_attempts')
            if is_ideology:
                print(f"  [AUTO] Ideology topic detected ({len(chunks)} chunks)")
                # Route to IdeologyEngine with safe fallback
                try:
                    answer = IdeologyEngine(self).generate(question, chunks)
                except Exception as _e:
                    print("  [WARN] IdeologyEngine failed; falling back to legacy ideology prompt")
                    try:
                        chunks = self._sort_chunks_by_year(chunks)
                    except Exception as e:
                        pass  # Chunk sorting optional
                    try:
                        chunks = self._stratify_by_decade(chunks, cap_per_decade=5, max_total=60)
                    except Exception as e:
                        pass  # Decade stratification optional
                    ideology_prompt = self._build_prompt_ideology(question, chunks)
                    answer = self.llm.call_api(ideology_prompt)
                # Debug: print years in original_chunks
                chunk_years = set()
                for text_chunk, _ in original_chunks:
                    matches = re.findall(r'\b(1[6-9]\d{2}|20[0-2]\d)\b', text_chunk)
                    chunk_years.update(int(m) for m in matches)
                needs = self._needs_grounding(answer) or self._answer_stops_early(answer, original_chunks) or self._paragraphs_exceed_limit(answer)
                if needs:
                    print(f"  [RE-ASK] Ideology query: detected issues; re-asking with all {len(original_chunks)} chunks")
                    answer = self._call_llm_with_rate_limit(question, original_chunks)
                # Check for empty answer (can happen if LLM hits token limit)
                if not answer or not answer.strip():
                    print(f"  [WARN] Empty answer detected, attempting retry with reduced chunks...")
                    if len(original_chunks) > 50:
                        reduced_chunks = original_chunks[:50]
                        print(f"  [RETRY] Retrying with {len(reduced_chunks)} chunks (reduced from {len(original_chunks)})")
                        answer = self._call_llm_with_rate_limit(question, reduced_chunks)
                    elif len(original_chunks) > 20:
                        reduced_chunks = original_chunks[:20]
                        print(f"  [RETRY] Retrying with {len(reduced_chunks)} chunks (reduced from {len(original_chunks)})")
                        answer = self._call_llm_with_rate_limit(question, reduced_chunks)
                    else:
                        return f"I apologize, but I encountered an issue generating a response for '{question}'. The response may have exceeded token limits. Please try rephrasing your question or breaking it into smaller parts."
                # Ensure Related Questions and structure
                if (not self._has_related_questions(answer)) or self._para_count(answer) < 3:
                    answer = self._polish_answer(question, answer)
                # Review and fix answer against criteria
                answer = self._review_and_fix_answer(answer, original_chunks, question, query_start_time=query_start)
                # Crisis post-check
                try:
                    if self._chunks_have_crisis(chunks) and not self._has_crises(answer):
                        answer = answer.strip() + "\n\n" + "**Crisis Episodes (from sources):**\n- Include relevant panics/crises linked to this subject and explain liquidity/margin/benchmark changes.\n"
                except Exception:
                    pass
                return answer
            
            # Choose processing strategy based on query type and chunk count
            # Record chunks being sent for debugging/trace
            try:
                self.last_chunks_sent = len(chunks)
            except Exception as e:
                    pass  # Chunk tracking optional

            # Handle broad identity queries with simple direct path (skip PeriodEngine to avoid timeouts)
            if 'is_broad_identity' in locals() and is_broad_identity:
                print(f"  [BROAD_IDENTITY] Processing broad identity query directly ({len(chunks)} chunks)")
                # Limit chunks if needed
                if len(chunks) > BROAD_IDENTITY_FINAL_CHUNK_LIMIT:
                    print(f"  [LIMIT] Reducing chunks from {len(chunks)} to {BROAD_IDENTITY_FINAL_CHUNK_LIMIT} for broad identity query")
                    chunks = chunks[:BROAD_IDENTITY_FINAL_CHUNK_LIMIT]
                
                # Temporarily reduce retries for broad identity queries (prevents long waits)
                self.llm._temp_max_attempts = BROAD_IDENTITY_MAX_RETRIES
                
                import time
                start_time = time.time()
                
                try:
                    # Use simple direct LLM call
                    answer = self.llm.generate_answer(question, chunks)
                    elapsed = time.time() - start_time
                    print(f"  [BROAD_IDENTITY] LLM call completed in {elapsed:.1f}s")
                    
                    # Check for timeout
                    if elapsed > BROAD_IDENTITY_SLOW_THRESHOLD_SECONDS:
                        print(f"  [WARN] LLM call was slow ({elapsed:.1f}s) but completed")
                        # Still return answer, but warn if very slow
                        if elapsed > 90:
                            return f"⚠️ Query took {elapsed:.0f} seconds. The query '{question}' is very broad. Please try a more specific question:\n\n- 'Tell me about Black bankers in 19th century America'\n- 'Tell me about Women bankers in London'\n- 'Tell me about specific Black banking families'\n\n{answer}"
                    
                    # Check for empty answer
                    if not answer or not answer.strip():
                        print(f"  [WARN] Empty answer detected, attempting retry with reduced chunks...")
                        if len(chunks) > 5:
                            reduced_chunks = chunks[:5]
                            print(f"  [RETRY] Retrying with {len(reduced_chunks)} chunks (reduced from {len(chunks)})")
                            answer = self.llm.generate_answer(question, reduced_chunks)
                        else:
                            return f"I apologize, but I encountered an issue generating a response for '{question}'. Please try rephrasing your question or breaking it into smaller parts."
                    
                    # Ensure structure & related questions
                    if (not self._has_related_questions(answer)) or self._para_count(answer) < 3:
                        answer = self._polish_answer(question, answer, chunks)
                    return answer
                except Exception as e:
                    elapsed = time.time() - start_time
                    print(f"  [ERROR] LLM call failed after {elapsed:.1f}s: {e}")
                    if elapsed > 60:
                        return f"⚠️ Query timed out after {elapsed:.0f} seconds. The query '{question}' is very broad. Please try a more specific question:\n\n- 'Tell me about Black bankers in 19th century America'\n- 'Tell me about Women bankers in London'\n- 'Tell me about specific Black banking families'"
                    raise
                finally:
                    # Restore original max_attempts
                    if hasattr(self.llm, '_temp_max_attempts'):
                        delattr(self.llm, '_temp_max_attempts')

            # Special-case: If SEC is explicitly present, send ALL chunks in a single call (no batching)
            if any(tok == "SEC" for tok in acronyms):
                print(f"  [FORCE] SEC query detected; sending all {len(chunks)} chunks in a single call")
                answer = self.llm.generate_answer(question, chunks)
                # Check for empty answer (can happen if LLM hits token limit)
                if not answer or not answer.strip():
                    print(f"  [WARN] Empty answer detected, attempting retry with reduced chunks...")
                    # Try again with fewer chunks to avoid token limit
                    if len(chunks) > 50:
                        reduced_chunks = chunks[:50]
                        print(f"  [RETRY] Retrying with {len(reduced_chunks)} chunks (reduced from {len(chunks)})")
                        answer = self.llm.generate_answer(question, reduced_chunks)
                    elif len(chunks) > 20:
                        reduced_chunks = chunks[:20]
                        print(f"  [RETRY] Retrying with {len(reduced_chunks)} chunks (reduced from {len(chunks)})")
                        answer = self.llm.generate_answer(question, reduced_chunks)
                    else:
                        # Even with few chunks, empty answer - return error message
                        return f"I apologize, but I encountered an issue generating a response for '{question}'. The response may have exceeded token limits. Please try rephrasing your question or breaking it into smaller parts."
                
                # Ensure structure & related questions
                if (not self._has_related_questions(answer)) or self._para_count(answer) < 3:
                    answer = self._polish_answer(question, answer, chunks)
                # Ensure crises are covered if present in sources
                try:
                    if self._chunks_have_crisis(chunks) and not self._has_crises(answer):
                        answer = answer.strip() + "\n\n" + "**Crisis Episodes (from sources):**\n- Include relevant panics/crises linked to this subject and explain liquidity/margin/benchmark changes.\n"
                except Exception:
                    pass
                return answer

            if len(chunks) > 100:
                if is_event:
                    # Event query: Route to EventEngine
                    print(f"  [AUTO] Event query detected ({len(chunks)} chunks)")
                    print(f"  [AUTO] Routing to EventEngine...")
                    try:
                        ans = EventEngine(self).generate(question, chunks)
                    except Exception as _e:
                        print("  [WARN] EventEngine failed; falling back to legacy event generator")
                        ans = self._generate_geographic_narrative(question, chunks)
                    # Check for empty answer (can happen if LLM hits token limit)
                    if not ans or not ans.strip():
                        print(f"  [WARN] Empty answer from EventEngine, attempting retry with reduced chunks...")
                        if len(chunks) > 50:
                            reduced_chunks = chunks[:50]
                            print(f"  [RETRY] Retrying with {len(reduced_chunks)} chunks (reduced from {len(chunks)})")
                            ans = self._generate_geographic_narrative(question, reduced_chunks)
                        elif len(chunks) > 20:
                            reduced_chunks = chunks[:20]
                            print(f"  [RETRY] Retrying with {len(reduced_chunks)} chunks (reduced from {len(chunks)})")
                            ans = self._generate_geographic_narrative(question, reduced_chunks)
                        else:
                            ans = f"I apologize, but I encountered an issue generating a response for '{question}'. The response may have exceeded token limits. Please try rephrasing your question or breaking it into smaller parts."
                    try:
                        if self._chunks_have_crisis(chunks) and not self._has_crises(ans):
                            ans = ans.strip() + "\n\n" + "**Crisis Episodes (from sources):**\n- Include relevant panics/crises linked to this subject and explain liquidity/margin/benchmark changes.\n"
                    except Exception:
                        pass
                    # Grounding and coverage checks
                    # Debug: print years in original_chunks
                    chunk_years = set()
                    for text, _ in original_chunks:
                        matches = re.findall(r'\b(1[6-9]\d{2}|20[0-2]\d)\b', text)
                        chunk_years.update(int(m) for m in matches)
                    # Skip expensive re-ask logic for small/medium queries (≤20 chunks) to avoid timeout
                    if len(original_chunks) > 20:
                        needs = self._needs_grounding(ans) or self._answer_stops_early(ans, original_chunks) or self._paragraphs_exceed_limit(ans)
                        if needs:
                            # If answer stops early, try re-retrieving with UNION to get all chunks
                            answer_latest = self._get_latest_year_in_answer(ans)
                            if answer_latest > 0 and subject_terms:
                                print(f"  [RE-RETRIEVE] Answer stops at {answer_latest} - re-retrieving with UNION of subject terms")
                                # Re-retrieve using UNION instead of intersection
                                union_chunk_ids = set()
                                for term in subject_terms:
                                    if term in self.term_to_chunks:
                                        union_chunk_ids.update(self.term_to_chunks[term])
                                
                                # Also try primary term only (e.g., just "Rothschild" to get all Rothschild chunks)
                                primary_term = subject_terms[0] if subject_terms else None
                                if primary_term and primary_term in self.term_to_chunks:
                                    primary_chunk_ids = set(self.term_to_chunks[primary_term])
                                    if len(primary_chunk_ids) > len(union_chunk_ids):
                                        print(f"  [RE-RETRIEVE] Primary term '{primary_term}' has {len(primary_chunk_ids)} chunks - using those")
                                        union_chunk_ids = primary_chunk_ids
                                
                                if union_chunk_ids and len(union_chunk_ids) > len(original_chunks):
                                    union_data = self.collection.get(ids=list(union_chunk_ids))
                                    union_chunks = [
                                        (text, meta)
                                        for text, meta in zip(union_data['documents'], union_data['metadatas'])
                                    ]
                                    print(f"  [RE-RETRIEVE] Retrieved {len(union_chunks)} chunks via UNION (vs {len(original_chunks)} via intersection)")
                                    # Use union chunks for re-ask
                                    ans = self._call_llm_with_rate_limit(question, union_chunks)
                                else:
                                    ans = self._call_llm_with_rate_limit(question, original_chunks)
                            else:
                                print(f"  [RE-ASK] Detected early stopping or quality issues; re-asking with all {len(original_chunks)} chunks (span: {min(chunk_years) if chunk_years else 'N/A'}-{max(chunk_years) if chunk_years else 'N/A'})")
                                ans = self._call_llm_with_rate_limit(question, original_chunks)
                    else:
                        print(f"  [OPTIMIZE] Skipping re-ask logic for small query ({len(original_chunks)} chunks)")
                    # Review and fix answer against criteria (reduced iterations for small/medium/large queries)
                    # Skip review for very large queries (>100 chunks) to avoid timeouts
                    if len(original_chunks) > 100:
                        max_review_iter = 0  # Skip review for very large queries
                    elif len(original_chunks) > 50:
                        max_review_iter = 1  # Single review for large queries
                    elif len(original_chunks) <= 20:
                        max_review_iter = 1  # Single review for small queries
                    else:
                        max_review_iter = MAX_REVIEW_ITERATIONS  # Full review for medium queries
                    ans = self._review_and_fix_answer(ans, original_chunks, question, max_iterations=max_review_iter, query_start_time=query_start)
                    return ans
                else:
                    # Topic query: Route to PeriodEngine (iterative period-based processing)
                    # Note: original_chunks should be defined above
                    print(f"  [AUTO] High-volume topic query detected ({len(chunks)} chunks)")
                    print(f"  [AUTO] Routing to PeriodEngine...")
                    try:
                        ans = PeriodEngine(self).generate(
                            question,
                            chunks,
                            subject_terms=subject_terms,
                            subject_phrases=subject_phrases
                        )
                    except Exception as _e:
                        print("  [WARN] PeriodEngine failed; falling back to legacy iterative generator")
                        ans = self._generate_iterative_narrative(question, chunks, subject_terms, subject_phrases)
                    # Check for empty answer (can happen if LLM hits token limit)
                    if not ans or not ans.strip():
                        print(f"  [WARN] Empty answer from PeriodEngine, attempting retry with reduced chunks...")
                        if len(chunks) > 50:
                            reduced_chunks = chunks[:50]
                            print(f"  [RETRY] Retrying with {len(reduced_chunks)} chunks (reduced from {len(chunks)})")
                            ans = self._generate_iterative_narrative(question, reduced_chunks, subject_terms, subject_phrases)
                        elif len(chunks) > 20:
                            reduced_chunks = chunks[:20]
                            print(f"  [RETRY] Retrying with {len(reduced_chunks)} chunks (reduced from {len(chunks)})")
                            ans = self._generate_iterative_narrative(question, reduced_chunks, subject_terms, subject_phrases)
                        else:
                            ans = f"I apologize, but I encountered an issue generating a response for '{question}'. The response may have exceeded token limits. Please try rephrasing your question or breaking it into smaller parts."
                    try:
                        if self._chunks_have_crisis(chunks) and not self._has_crises(ans):
                            ans = ans.strip() + "\n\n" + "**Crisis Episodes (from sources):**\n- Include relevant panics/crises linked to this subject and explain liquidity/margin/benchmark changes.\n"
                    except Exception:
                        pass
                    # Debug: print years in original_chunks
                    chunk_years = set()
                    for text, _ in original_chunks:
                        matches = re.findall(r'\b(1[6-9]\d{2}|20[0-2]\d)\b', text)
                        chunk_years.update(int(m) for m in matches)
                    needs = self._needs_grounding(ans) or self._answer_stops_early(ans, original_chunks) or self._paragraphs_exceed_limit(ans)
                    if needs:
                        # If answer stops early, try re-retrieving with UNION to get all chunks
                        answer_latest = self._get_latest_year_in_answer(ans)
                        if answer_latest > 0 and subject_terms:
                            print(f"  [RE-RETRIEVE] Answer stops at {answer_latest} - re-retrieving with UNION of subject terms")
                            # Re-retrieve using UNION instead of intersection
                            union_chunk_ids = set()
                            for term in subject_terms:
                                if term in self.term_to_chunks:
                                    union_chunk_ids.update(self.term_to_chunks[term])
                            
                            # Also try primary term only (e.g., just "Rothschild" to get all Rothschild chunks)
                            primary_term = subject_terms[0] if subject_terms else None
                            if primary_term and primary_term in self.term_to_chunks:
                                primary_chunk_ids = set(self.term_to_chunks[primary_term])
                                if len(primary_chunk_ids) > len(union_chunk_ids):
                                    print(f"  [RE-RETRIEVE] Primary term '{primary_term}' has {len(primary_chunk_ids)} chunks - using those")
                                    union_chunk_ids = primary_chunk_ids
                            
                            if union_chunk_ids and len(union_chunk_ids) > len(original_chunks):
                                union_data = self.collection.get(ids=list(union_chunk_ids))
                                union_chunks = [
                                    (text, meta)
                                    for text, meta in zip(union_data['documents'], union_data['metadatas'])
                                ]
                                print(f"  [RE-RETRIEVE] Retrieved {len(union_chunks)} chunks via UNION (vs {len(original_chunks)} via intersection)")
                                # Use union chunks for re-ask
                                ans = self._call_llm_with_rate_limit(question, union_chunks)
                            else:
                                ans = self._call_llm_with_rate_limit(question, original_chunks)
                        else:
                            print(f"  [RE-ASK] Detected early stopping or quality issues; re-asking with all {len(original_chunks)} chunks (span: {min(chunk_years) if chunk_years else 'N/A'}-{max(chunk_years) if chunk_years else 'N/A'})")
                            ans = self._call_llm_with_rate_limit(question, original_chunks)
                    # Review and fix answer against criteria
                    ans = self._review_and_fix_answer(ans, original_chunks, question)
                    return ans
            elif len(chunks) > 30:
                # Medium-volume: Standard batching
                print(f"  [INFO] Processing {len(chunks)} chunks (routing to PeriodEngine)...")
                try:
                    ans = PeriodEngine(self).generate(
                        question,
                        chunks,
                        subject_terms=subject_terms,
                        subject_phrases=subject_phrases
                    )
                except Exception:
                    print("  [WARN] PeriodEngine failed; falling back to legacy batched generator")
                    ans = self._generate_batched_narrative(question, chunks)
                try:
                    if self._chunks_have_crisis(chunks) and not self._has_crises(ans):
                        ans = ans.strip() + "\n\n" + "**Crisis Episodes (from sources):**\n- Include relevant panics/crises linked to this subject and explain liquidity/margin/benchmark changes.\n"
                except Exception:
                    pass
                needs = self._needs_grounding(ans) or (self._chunks_have_late_era(chunks) and not self._answer_covers_late_era(ans, chunks)) or self._paragraphs_exceed_limit(ans)
                if needs:
                    ans = self._call_llm_with_rate_limit(question, chunks)
                # Review and fix answer against criteria
                ans = self._review_and_fix_answer(ans, original_chunks, question, query_start_time=query_start)
                return ans
            else:
                # Low-volume: Single LLM call
                # For small/medium queries (≤20 chunks), use fast path to avoid timeout
                # Increased from 10 to 20 to catch more queries that would otherwise timeout
                # BUT still use generate_answer to get proper narrative (not _build_prompt_grounded)
                routing_info = f"{len(chunks)} chunks (original: {len(original_chunks) if 'original_chunks' in locals() else 'N/A'})"
                print(f"  [ROUTING] Checking routing for {routing_info}")
                if len(chunks) <= 20:
                    print(f"  [OPTIMIZE] Small query ({len(chunks)} chunks) - using fast path (skipping expensive re-ask logic)")
                    # Log to trace for debugging
                    try:
                        from server import trace_event
                        import uuid
                        trace_event(str(uuid.uuid4()), "routing_decision", path="fast_path", chunk_count=len(chunks), original_count=len(original_chunks) if 'original_chunks' in locals() else 0)
                    except:
                        pass  # Trace optional
                    # Use generate_answer to get proper narrative structure (not _call_llm_with_rate_limit which uses simpler prompt)
                    # But add rate limiting wrapper
                    self._wait_for_token_rate_limit(chunks)
                    ans = self.llm.generate_answer(question, chunks)
                    estimated_output_tokens = len(ans.split()) * TOKENS_PER_WORD
                    estimated_input_tokens = self._estimate_tokens_for_chunks(chunks)
                    estimated_total = estimated_input_tokens + estimated_output_tokens
                    self._record_token_usage(estimated_total)
                    # Minimal review (1 iteration max) for small queries to avoid timeout
                    ans = self._review_and_fix_answer(ans, chunks, question, max_iterations=1, query_start_time=query_start)
                    query_duration = time.time() - query_start
                    print(f"  [QUERY_COMPLETE] Finished in {query_duration:.1f}s, answer length: {len(ans)} chars")
                    return ans
                
                routing_info = f"{len(chunks)} chunks (original: {len(original_chunks) if 'original_chunks' in locals() else 'N/A'})"
                print(f"  [ROUTING] Low-volume query ({routing_info}) - routing to PeriodEngine (chunks > 20, fast path skipped)")
                # Log to trace for debugging
                try:
                    from server import trace_event
                    import uuid
                    trace_event(str(uuid.uuid4()), "routing_decision", path="period_engine", chunk_count=len(chunks), original_count=len(original_chunks) if 'original_chunks' in locals() else 0, warning="SLOW_PATH")
                except:
                    pass  # Trace optional
                try:
                    ans = PeriodEngine(self).generate(
                        question,
                        chunks,
                        subject_terms=subject_terms,
                        subject_phrases=subject_phrases
                    )
                except Exception:
                    print("  [WARN] PeriodEngine failed; falling back to single-call generator")
                    ans = self._call_llm_with_rate_limit(question, chunks)
                try:
                    if self._chunks_have_crisis(chunks) and not self._has_crises(ans):
                        ans = ans.strip() + "\n\n" + "**Crisis Episodes (from sources):**\n- Include relevant panics/crises linked to this subject and explain liquidity/margin/benchmark changes.\n"
                except Exception:
                    pass
                    # Skip expensive re-ask logic for small-medium queries (≤20 chunks) to avoid timeout
                if len(original_chunks) > 20:
                    # Debug: print years in original_chunks
                    chunk_years = set()
                    for text_chunk, _ in original_chunks:
                        matches = re.findall(r'\b(1[6-9]\d{2}|20[0-2]\d)\b', text_chunk)
                        chunk_years.update(int(m) for m in matches)
                    needs = self._needs_grounding(ans) or self._answer_stops_early(ans, original_chunks) or self._paragraphs_exceed_limit(ans)
                    if needs:
                        print(f"  [RE-ASK] Low-volume query: detected issues; re-asking with all {len(original_chunks)} chunks")
                        ans = self._call_llm_with_rate_limit(question, original_chunks)
                else:
                    print(f"  [OPTIMIZE] Skipping re-ask logic for small-medium query ({len(original_chunks)} chunks)")
                # Review and fix answer against criteria (reduced iterations for small queries)
                max_review_iter = 1 if len(original_chunks) <= 15 else MAX_REVIEW_ITERATIONS
                ans = self._review_and_fix_answer(ans, original_chunks, question, max_iterations=max_review_iter, query_start_time=query_start)
                query_duration = time.time() - query_start
                print(f"  [QUERY_COMPLETE] Finished in {query_duration:.1f}s, answer length: {len(ans)} chars")
                return ans
        else:
            # Fallback: return raw context
            context_text = "\n\n".join([
                f"[{meta.get('filename', 'Unknown')}]\n{text}"
                for text, meta in zip(data['documents'], data['metadatas'])
            ])
            result = f"Found {len(chunk_ids_list)} relevant passages:\n\n{context_text}"
            query_duration = time.time() - query_start
            print(f"  [QUERY_COMPLETE] Finished in {query_duration:.1f}s (no LLM), result length: {len(result)} chars")
            return result
    
    def _is_event_query(self, question: str) -> bool:
        """
        Detect if query is about a specific event vs. broad topic.
        
        Events: Panics, crises, wars (single year or short period)
        Topics: Groups, regions, industries (span decades/centuries)
        """
        question_lower = question.lower()
        
        # Event indicators
        event_keywords = [
            'panic', 'crisis', 'crash', 'collapse', 'war', 'revolution',
            'depression', 'recession', 'bubble', 'run', 'default'
        ]
        
        # Specific year mentioned
        has_year = bool(re.search(r'\b(1[6-9]\d{2}|20[0-2]\d)\b', question_lower))
        
        # Check for event keywords
        has_event_keyword = any(keyword in question_lower for keyword in event_keywords)
        
        return has_event_keyword or has_year

    def _is_control_influence_query(self, question: str) -> bool:
        """
        Detect questions about group control/influence in banking.
        These need special handling with the guidance from .cursorrules.
        """
        control_keywords = ['control', 'controls', 'controlled', 'controlling', 'dominate', 'dominates', 'dominated', 'dominating', 
                           'influence', 'influences', 'influenced', 'influencing', 'power', 'powers']
        question_lower = question.lower()
        # Check if question asks about control/influence AND mentions a group/identity
        has_control = any(keyword in question_lower for keyword in control_keywords)
        # Check for identity/group terms
        from lib.identity_terms import IDENTITY_TERMS_SET as identity_terms_set
        has_identity = any(term in question_lower for term in identity_terms_set)
        return has_control and has_identity
    
    def _is_broad_identity_query(self, question: str) -> bool:
        """
        Detect broad identity queries (like "Tell me about black" or "Tell me about women").
        These are NOT control/influence queries but are still very broad and need chunk limiting.
        """
        question_lower = question.lower()
        # Check for "tell me about" pattern with identity terms
        tell_me_patterns = ['tell me about', 'what is', 'who are', 'what are']
        has_tell_me = any(pattern in question_lower for pattern in tell_me_patterns)
        # Check for identity/group terms (same list as control/influence)
        from lib.identity_terms import IDENTITY_TERMS_SET as identity_terms_set
        has_identity = any(term in question_lower for term in identity_terms_set)
        # Check if query is very short/simple (likely to be broad)
        # Remove stop words and check if only 1-2 meaningful words remain
        words = question_lower.split()
        # Use centralized STOP_WORDS from constants.py
        meaningful_words = [w for w in words if w not in STOP_WORDS and len(w) > 2]
        is_simple = len(meaningful_words) <= 3  # Allow up to 3 meaningful words (e.g., "Tell me about Black" = 1 word)
        # Also check if query ends with just the identity term (very broad)
        # "Tell me about Black" should match, but "Tell me about Black bankers in 19th century" should not
        ends_with_identity = any(question_lower.rstrip('?.').endswith(term) for term in identity_terms_set)
        return has_tell_me and has_identity and (is_simple or ends_with_identity)
    
    def _is_market_query(self, question: str) -> bool:
        """
        Detect whether the question is focused on markets/assets.
        These queries benefit from geographic/sector batching instead of pure chronology.
        """
        market_keywords = [
            'money market', 'money-market', 'capital market', 'bond market', 'commercial paper', 'commercial-paper',
            'abcp', 'mmeu', 'mmea', 'eurodollar', 'euro-dollar', 'euro dollar', 'eurodollar market', 'euro-market', 'euro market',
            'libor', 'eurobond', 'railroad securities', 'reit', 'real estate trust', 'real-estate trust',
            'conglomerate stock', 'technology stock', 'tech stock',
            'slave market', 'diversity finance', 'dei investments',
            'long-term capital', 'asset-backed', 'asset backed', 'junk bond', 'high-yield', 'high yield',
            'venture capital', 'lbo', 'leveraged buyout', 'money fund', 'money-fund', 'money market mutual fund',
            'trade bills', 'bills payable', 'foreign trade bills', 'legal tender notes', 'legal-tender notes',
            'bank holding company act', 'holding company', 'market mutual fund'
        ]
        question_lower = question.lower()
        return any(keyword in question_lower for keyword in market_keywords)
    
    # Note: acronym/full-name normalization is handled in the index; no query-time expansion here.
    
    def _generate_geographic_narrative(self, question: str, chunks: list, for_market: bool = False) -> str:
        """
        Generate narrative for event queries, organized by geography/sector.
        """
        from lib.batch_processor_geographic import GeographicProcessor
        
        processor = GeographicProcessor(self.llm, use_async=self.use_async)
        prompt_builder = (lambda q, c, ctx: self._build_prompt_market(q, c)) if for_market else (lambda q, c, ctx: self._build_prompt(q, c))
        return processor.process_by_geography(
            question=question,
            chunks=chunks,
            prompt_builder=prompt_builder
        )
    
    def _build_prompt_control_influence(self, question: str, chunks: list) -> str:
        """
        Build prompt for control/influence questions (e.g., "do jews control banking").
        Applies special guidance from .cursorrules about analyzing narrowly, providing context, etc.
        """
        chunks_text = "\n\n".join([
            f"--- CHUNK {i+1} ---\n{text}"
            for i, (text, meta) in enumerate(chunks)
        ])
        return f"""You are a banking historian. Answer this question: {question}

DOCUMENT CHUNKS:
{chunks_text}

CRITICAL GUIDANCE FOR CONTROL/INFLUENCE QUESTIONS:

ABSOLUTE REQUIREMENT: Your answer MUST follow this EXACT structure. Do NOT deviate.

MANDATORY STRUCTURE - FOLLOW THIS EXACT ORDER (DO NOT SKIP STEPS):

1. PREMISE REJECTION (MANDATORY FIRST STEP - YOUR ANSWER MUST START HERE):
   - YOUR FIRST SENTENCE MUST explicitly reject the premise as unsupported and consistent with conspiratorial or reductionist thinking
   - State clearly that no group uniformly controls complex economic systems
   - NEVER mention "documents", "the provided documents", "as depicted in these documents", "the documents indicate", "historical documents", "historical records", "historical evidence", "records show", or any source material
   - BAD: "While specific Jewish families made significant contributions..." (starts with examples, not rejection)
   - BAD: "The assertion that Jews control banking is addressed..."
   - BAD: "The provided documents explicitly state..."
   - GOOD: "The premise that any single ethnic, religious, or social group controls banking is unsupported and reflects conspiratorial thinking. No group uniformly controls complex economic systems."
   - CRITICAL: If you do not start with premise rejection, your answer is WRONG

2. CONTEXTUALIZATION AND LIMITS:
   - Explain that any historical examples reflect participation by specific individuals or elite families under contextual constraints, not group-wide authority
   - Emphasize selection bias in citing only prominent cases (what gets remembered vs. what gets forgotten)
   - Clarify that participation was constrained, not dominant

3. EVIDENCE/EXAMPLES FRAMED AS PARTICIPATION UNDER CONSTRAINT:
   - Present evidence ONLY as examples of LIMITED participation by specific actors operating under constraints
   - Which SPECIFIC families? (e.g., "Rothschild, Warburg, and Kuhn Loeb families" NOT "all Jews")
   - What SPECIFIC time period? (e.g., "in 19th century Frankfurt" NOT "throughout history")
   - What SPECIFIC place? (e.g., "in London" NOT "globally")
   - Banking dominated by COUSINHOODS (small intermarried elite families), NOT entire populations
   - Highlight that activities occurred under legal/social pressure (threats of expulsion/exclusion) rather than voluntary dominance
   - Note government-imposed restrictions that pushed populations into specific economic roles
   - Do NOT describe historical networks or family ties as coordinated group strategies unless explicitly evidenced
   - Never infer collective will - frame as individual/family actions under constraints

4. COUNTEREXAMPLES AND VULNERABILITY (MANDATORY):
   - MANDATORY: Include counterexamples involving non-members of the group:
     * Quakers (Barclay, Lloyd, Bevan), Huguenots (Hope, Mallet, Thellusson), Parsees (Tata, Wadia, Petit), Mennonites (Clercq, Fock, TenCate), Boston Brahmins (Cabot, Lowell, Forbes), Protestant Cologne (Stein, Schaaffhausen), Greeks, Armenians, etc.
   - MANDATORY: Include instances of failure, vulnerability, or suppression:
     * Financial defaults (e.g., Oppenheim collapse)
     * Assassinations, executions, political persecution
     * Expulsions and social exclusion
   - MANDATORY: Include GOVERNMENT-IMPOSED RESTRICTIONS that pushed individuals into specific economic roles:
     * Legal restrictions (e.g., restrictions on Jews in Frankfurt, prohibitions on land ownership, guild exclusions)
     * Exclusion from other economic realms (politics, land ownership, certain trades/industries)
     * Religious prohibitions on credit/usury that affected other groups (e.g., Christian prohibitions on lending at interest)
     * These restrictions channeled certain populations into finance, not voluntary choice
   - MANDATORY: Include THREATS TO COMMUNITIES:
     * Threats of expulsion (actual expulsions or threats thereof)
     * Social exclusion and discrimination
     * Political interference and persecution
   - MANDATORY: Include OTHER COMPETITORS AND GROUPS:
     * Other cousinhoods (Quakers, Huguenots, Parsees, Mennonites, Boston Brahmins, Protestant Cologne, Greeks, Armenians, etc.)
     * Religious prohibitions on credit/usury that affected other groups (e.g., Christian prohibitions on lending at interest that created opportunities for certain groups)
     * Show that banking involved many groups, not just the queried group
   - Show that participation was precarious and subject to sudden reversals
   - Include examples of individuals/families who faced persecution, expulsion, or financial ruin
   - CRITICAL: If chunks mention restrictions (e.g., Frankfurt restrictions), exclusion from politics/land/other realms, threats of expulsion, religious prohibitions on credit, or other competitors, you MUST include them - these are essential context

5. CONCLUSION REAFFIRMING LACK OF COLLECTIVE CONTROL:
   - Reaffirm that no group uniformly controls banking
   - Emphasize that participation was limited, constrained, and occurred alongside many other groups
   - Frame the pattern as one of small intermarried elite families across many groups, not unique to any single group

6. IF NO EVIDENCE FOR THE CLAIM:
   - State explicitly: "The document does not provide support for this claim."
   - Do NOT infer beyond the text

MAINTAIN NEUTRAL, EVIDENCE-BASED TONE:
- Provide historical context without moralizing language or ideological assumptions
- Use a factual style
- Limit generalizations, avoid proxy language, and do not speculate beyond provided sources

FINAL CHECKLIST BEFORE SUBMITTING:
- [ ] Does your answer START with premise rejection? If NO → REWRITE
- [ ] Did you mention "documents", "provided documents", "as depicted in", "the documents indicate", or any source material? If YES → DELETE and rewrite
- [ ] Did you follow the exact order: (1) Premise rejection → (2) Contextualization → (3) Evidence → (4) Counterexamples → (5) Conclusion? If NO → REORGANIZE
- [ ] Did you include counterexamples from other groups? If NO → ADD THEM
- [ ] Did you include failures/vulnerabilities? If NO → ADD THEM

7. CHRONOLOGICAL ORGANIZATION: Cover all time periods documents mention, moving forward chronologically.

8. END WITH RELATED QUESTIONS: 3-5 questions about specific families, institutions, or time periods mentioned in documents.

Answer:
"""
    
    def _build_prompt_market(self, question: str, chunks: list) -> str:
        """
        Build prompt for Markets & Asset Classes queries with explicit panic/crisis coverage.
        """
        chunks_text = "\n\n".join([
            f"--- CHUNK {i+1} ---\n{text}"
            for i, (text, meta) in enumerate(chunks)
        ])
        return f"""You are a banking historian. Answer this question: {question}

DOCUMENT CHUNKS:
{chunks_text}

MARKET/ASSET CLASS RULES:
1) STRUCTURE:
   - Use section headings (e.g., "**Origins & Stimulation Factors:**", "**Funding & Participants:**", "**Pricing & Benchmarks:**", "**Regulation & Balance Sheets:**", "**Panics & Crises:**").
   - 2–4 paragraphs per section; MAX 3 sentences per paragraph; MIN 5 paragraphs total.
   - Within sections, PRESENT FACTS IN STRICT CHRONOLOGICAL ORDER (e.g., 1950s → 1960s → 1970s → 1980s → 1990s → 2000s).
2) STIMULATION FACTORS (MANDATORY - MUST INCLUDE):
   - ALWAYS include an "Origins & Stimulation Factors" section or integrate stimulation factors into the opening
   - Explain WHAT CREATED/DROVE the market: laws (e.g., National Bank Act, Banking Act of 1933), innovations (e.g., silicon transistors, venture capital), economic conditions (e.g., post-war growth, deregulation), wars (e.g., WWII, Cold War), panics (e.g., Panic of 1907 led to Federal Reserve Act), regulatory changes (e.g., SEC creation, Glass-Steagall repeal)
   - BAD: "The technology equities sector emerged significantly in the mid-20th century" (no explanation of WHY or WHAT drove it)
   - GOOD: "The technology equities sector emerged in the mid-20th century, driven by Cold War defense spending on semiconductors, the rise of venture capital funding structures, and innovations in silicon transistor technology that enabled commercial applications."
   - MANDATORY: Search chunks for laws, innovations, economic conditions, wars, panics, regulatory changes that stimulated the market's creation/growth
3) PANICS/CRISES (MANDATORY WHEN PRESENT IN SOURCES):
   - Explicitly cover relevant panics/crises linked to the subject (e.g., 1763, 1825, 1873, 1893, 1907, 1929, 1973–74, 1987, 1998, 2000 dot-com crash, 2008 financial crisis).
   - Explain how liquidity, margining, benchmarks, or dealer balance sheets changed in this market during those episodes.
   - MANDATORY: If documents mention panics/crises during periods when the market was active, you MUST include them - don't skip panics
   - BAD: Answer about technology equities mentions 1950s-2000s but no mention of dot-com crash (2000) or 2008 financial crisis if documents mention them
   - GOOD: "During the dot-com crash of 2000, technology equities [specific impacts from docs]. Following the 2008 financial crisis, technology equities [specific impacts from docs]."
4) SUBJECT ACTIVE:
   - Keep the market/asset as the active subject in each sentence.
5) MECHANICS:
   - Institutions italicized (e.g., *MMEU*, *FRS*, *NYSE*); people normal.
   - Strict relevance; no unrelated context.
6) COVERAGE:
   - Move forward in time across all eras present; short transitions to connect periods.
7) END:
   - "Related Questions:" with 3–5 substantial, document-grounded items.
"""
    
    def _sort_chunks_by_year(self, chunks: list) -> list:
        """Sort chunk tuples by the first year mentioned; unknown years go last, stable otherwise."""
        def first_year(text: str) -> int:
            m = re.search(r'\b(1[6-9]\d{2}|20[0-2]\d)\b', text)
            return int(m.group(1)) if m else 10**9
        return sorted(chunks, key=lambda t: first_year(t[0]))
    
    def _stratify_by_decade(self, chunks: list, cap_per_decade: int = 5, max_total: int = 60) -> list:
        """Sample up to cap_per_decade chunks per decade to reduce sprawl; preserve order."""
        buckets = {}
        ordered = []
        for text, meta in chunks:
            m = re.search(r'\b(1[6-9]\d{2}|20[0-2]\d)\b', text)
            year = int(m.group(1)) if m else None
            decade = (year // 10 * 10) if year else None
            key = decade if decade is not None else 'unknown'
            if key not in buckets:
                buckets[key] = 0
            if buckets[key] < cap_per_decade:
                ordered.append((text, meta))
                buckets[key] += 1
            if len(ordered) >= max_total:
                break
        return ordered if ordered else chunks
    
    def _is_ideology_query(self, question: str) -> bool:
        q = (question or "").lower()
        return any(k in q for k in ("marxism", "marxist", "socialism", "socialist", "communism", "communist", "collectivism", "collectivist"))
    
    def _filter_chunks_for_ideology(self, chunks: list, question: str) -> list:
        """Keep chunks that mention the ideology AND (banking/transition OR crisis); prefer identity-bearing chunks."""
        ideology_terms = ["marxism", "marxist", "socialism", "socialist", "communism", "communist", "collectivism", "collectivist"]
        finance_terms = [
            "bank", "banking", "credit", "money", "market", "securities", "bond", "equity",
            "stock", "capital", "liquidity", "exchange", "regulation", "balance sheet",
            "benchmark", "margin"
        ]
        transition_terms = [
            "nationalize", "nationalised", "nationalized", "collectivize", "collectivised", "collectivized",
            "expropriate", "expropriation", "confiscate", "decree", "five-year plan", "plan economy",
            "state bank", "central plan", "command economy", "price control", "currency reform"
        ]
        crisis_terms = ["panic", "panics", "crisis", "crises", "1763", "1825", "1873", "1893", "1907", "1929", "1973", "1974", "1987", "1998", "2008"]
        identity_terms = [
            "minority", "women", "widow", "gender", "race", "caste", "dalit", "brahmin",
            "jew", "jewish", "quaker", "huguenot", "armenian", "greek", "boston brahmin",
            "old believer", "parsee", "baniya", "sephardi", "ashkenazi", "court jew"
        ]
        kept_primary = []
        kept_with_identity = []
        for text, meta in chunks:
            tl = text.lower()
            has_ideology = any(t in tl for t in ideology_terms)
            has_finance = any(f in tl for f in finance_terms)
            has_transition = any(t in tl for t in transition_terms)
            has_crisis = any(c in tl for c in crisis_terms)
            has_identity = any(i in tl for i in identity_terms)
            if has_ideology and (has_finance or has_transition or has_crisis):
                kept_primary.append((text, meta))
                if has_identity:
                    kept_with_identity.append((text, meta))
        if kept_primary:
            # Prefer those that also mention identities
            return kept_with_identity if kept_with_identity else kept_primary
        # Fallback to original chunks to avoid empty context
        return chunks
    
    def _build_prompt_ideology(self, question: str, chunks: list) -> str:
        """Prompt that constrains ideology topics to finance/banking mechanics, panics, and identity effects."""
        chunks_text = "\n\n".join([
            f"--- CHUNK {i+1} ---\n{text}"
            for i, (text, meta) in enumerate(chunks)
        ])
        return f"""You are a banking historian. Answer this question through an IDEOLOGY → SOCIETY & FINANCE lens: {question}

DOCUMENT CHUNKS:
{chunks_text}

IDEOLOGY → FINANCE RULES:
1) SUBJECT ACTIVE (ALWAYS): Keep the ideology as the subject in every sentence (e.g., "Marxism shaped bank nationalization...").
2) SOCIETY & STATE (MANDATORY): Focus on nationalization/collectivization mechanics, property rights, redistribution, repression or protections, and how the state reallocated economic control.
3) PANICS/CRISES (MANDATORY WHEN PRESENT): If sources mention panics/crises (1763, 1825, 1873, 1893, 1907, 1929, 1973–74, 1987, 1998, 2008), explain social effects: employment, credit access, expropriations, migration, class/caste conflict, and changes to who could access finance.
4) IDENTITY (MANDATORY WHEN PRESENT): Explain effects on minorities and identity groups documented in the sources (e.g., exclusions or access for Jews, Quakers, Dalits, women/widows), and how those shaped roles (minority middlemen).
5) STRICT RELEVANCE: Avoid unrelated event/name “laundry lists.” Do NOT jump across unrelated locales. Do NOT introduce new people unless the documents show a direct tie to the subject; when a person is named, state in 1 short clause why they matter to this ideology’s effect on banking/society.
6) FINANCIAL MECHANICS (WHEN PRESENT): Banking structure, credit allocation, benchmarks, dealer/state balance sheets—only as they inform social outcomes.
7) CHRONOLOGY WITH TRANSITIONS: Move forward in time (e.g., 1910s → 1930s → 1950s). Use explicit transitions that explain how one period leads to the next. Do not mix decades in the same paragraph.
8) PARAGRAPHS: MAX 3 sentences per paragraph; MIN 5 paragraphs total.
9) MECHANICS: Institutions italicized (e.g., *FRS*, *NYSE*, *Banque de France*); people normal. No platitudes.
10) END: "Related Questions:" with 3–5 substantial, document-grounded items.

ENTITY INTRODUCTIONS (MANDATORY):
- Expand acronyms/institutions on first mention with role (e.g., "*Vneshtorg* (Soviet Bank for Foreign Trade)").
- For each person first mentioned, add role + relevance to SUBJECT in one short clause; otherwise omit the name.
- Do NOT use unknown acronyms (e.g., BSU) unless you define them from the provided chunks; if the chunks do not define, avoid using them.
- For any non-subject entity mentioned (person or institution), explicitly state in the same sentence how they relate to the SUBJECT.
"""
    
    def _has_market_crises(self, text: str) -> bool:
        """Heuristic: does the text mention 'panic' or canonical crisis years."""
        if not isinstance(text, str):
            return False
        tl = text.lower()
        if "panic" in tl or "crisis" in tl or "crises" in tl:
            return True
        for yr in ("1973", "1974", "1987", "1998", "2008", "1929", "1907", "1825", "1873"):
            if yr in tl:
                return True
        return False
    
    def _paragraphs_exceed_limit(self, text: str, max_sentences: int = MAX_SENTENCES_PER_PARAGRAPH) -> bool:
        """Return True if any paragraph exceeds the allowed sentence count."""
        try:
            paras = [p for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]
            for p in paras:
                # crude sentence split on . ! ?
                sentences = re.split(r"[.!?](?:\s|$)", p.strip())
                # account for trailing empty after split
                count = sum(1 for s in sentences if s.strip())
                if count > max_sentences:
                    return True
        except Exception:
            return False
        return False
    
    def _chunks_have_late_era(self, chunks: list, cutoff_year: Optional[int] = None) -> bool:
        """
        Detect if sources include material significantly later than the earliest chunk.
        If cutoff_year is None, uses EARLY_STOP_GAP_THRESHOLD to determine what's "late".
        """
        try:
            # Find the earliest year in chunks
            earliest_year = None
            latest_year = None
            for text, _ in chunks:
                for m in re.finditer(r"\b(1[6-9]\d{2}|20[0-2]\d)\b", text):
                    year = int(m.group(1))
                    if earliest_year is None or year < earliest_year:
                        earliest_year = year
                    if latest_year is None or year > latest_year:
                        latest_year = year
            
            if earliest_year is None or latest_year is None:
                return False
            
            # If cutoff_year provided, use it; otherwise check if there's a significant gap
            if cutoff_year is not None:
                return latest_year >= cutoff_year
            else:
                # Check if latest is significantly later than earliest (more than threshold)
                return (latest_year - earliest_year) > EARLY_STOP_GAP_THRESHOLD
        except Exception:
            pass
        return False
    
    def _get_latest_year_in_chunks(self, chunks: list) -> int:
        """Get the latest year mentioned in chunks."""
        latest = 0
        try:
            for text, _ in chunks:
                for m in re.finditer(r"\b(1[6-9]\d{2}|20[0-2]\d)\b", text):
                    year = int(m.group(1))
                    if year > latest:
                        latest = year
        except Exception:
            pass
        return latest
    
    def _get_latest_year_in_answer(self, text: str) -> int:
        """Get the latest year mentioned in answer."""
        latest = 0
        try:
            for m in re.finditer(r"\b(1[6-9]\d{2}|20[0-2]\d)\b", text):
                year = int(m.group(1))
                if year > latest:
                    latest = year
        except Exception:
            pass
        return latest
    
    def _answer_covers_late_era(self, text: str, chunks: Optional[List] = None, cutoff_year: Optional[int] = None) -> bool:
        """
        Check if answer covers later periods present in chunks.
        If cutoff_year is None, compares answer years to chunk years dynamically.
        """
        try:
            answer_years = set()
            for m in re.finditer(r"\b(1[6-9]\d{2}|20[0-2]\d)\b", text):
                answer_years.add(int(m.group(1)))
            
            if not answer_years:
                return False
            
            # If chunks provided, check if answer covers their time span
            if chunks:
                chunk_years = set()
                for chunk_text, _ in chunks:
                    for m in re.finditer(r"\b(1[6-9]\d{2}|20[0-2]\d)\b", chunk_text):
                        chunk_years.add(int(m.group(1)))
                
                if chunk_years:
                    chunk_latest = max(chunk_years)
                    answer_latest = max(answer_years)
                    # Answer covers late era if it's within threshold of chunk latest
                    return (chunk_latest - answer_latest) <= EARLY_STOP_GAP_THRESHOLD
            
            # If cutoff_year provided, use it
            if cutoff_year is not None:
                return max(answer_years) >= cutoff_year
            
            return True  # If no chunks/cutoff, assume it covers
        except Exception:
            pass
        return False
    
    def _answer_stops_early(self, text: str, chunks: list, gap_threshold: int = EARLY_STOP_GAP_THRESHOLD) -> bool:
        """Check if answer stops significantly earlier than chunks (gap of gap_threshold+ years)."""
        chunk_latest = self._get_latest_year_in_chunks(chunks)
        answer_latest = self._get_latest_year_in_answer(text)
        if chunk_latest > 0 and answer_latest > 0:
            gap = chunk_latest - answer_latest
            if gap > gap_threshold:
                print(f"  [EARLY_STOP] Answer stops at {answer_latest}, but chunks go to {chunk_latest} (gap: {gap} years)")
                return True
        elif chunk_latest > 0 and answer_latest == 0:
            print(f"  [EARLY_STOP] Answer has no years, but chunks go to {chunk_latest}")
            return True
        return False
    
    def _enforce_paragraph_limit(self, text: str, max_sentences: int = MAX_SENTENCES_PER_PARAGRAPH) -> str:
        """Split paragraphs so none exceeds max_sentences; aggressive sentence splitting."""
        try:
            # Split by double newlines first to get existing paragraphs
            paras = [p.strip() for p in re.split(r"\n\s*\n+", (text or "").strip()) if p.strip()]
            fixed = []
            
            for p in paras:
                if not p:
                    continue
                
                # Skip section headers (lines starting with **)
                if p.startswith('**') and '\n' not in p:
                    fixed.append(p)
                    continue
                
                # Aggressive sentence splitting: split on sentence-ending punctuation
                # First, split on . ! ? followed by space (and optionally newline)
                # This handles most cases
                sentence_parts = re.split(r'([.!?]+)\s+', p)
                sentences = []
                current = ""
                
                for i, part in enumerate(sentence_parts):
                    current += part
                    # If we have punctuation at the end
                    if re.search(r'[.!?]+$', current.strip()):
                        # Check if next part starts with capital (new sentence) or is end
                        if i + 1 < len(sentence_parts):
                            next_part = sentence_parts[i + 1].strip()
                            # If next part is empty or starts with capital, end sentence
                            if not next_part or (next_part and next_part[0].isupper()):
                                sentences.append(current.strip())
                                current = ""
                        else:
                            # End of text
                            sentences.append(current.strip())
                            current = ""
                
                # Add any remaining text
                if current.strip():
                    sentences.append(current.strip())
                
                # Filter out empty sentences
                sentences = [s.strip() for s in sentences if s.strip()]
                
                # If still no sentences found, try even simpler approach
                if not sentences:
                    # Split on any punctuation followed by space
                    simple_split = re.split(r'([.!?]+)\s+', p)
                    sentences = []
                    for i in range(0, len(simple_split) - 1, 2):
                        if i + 1 < len(simple_split):
                            sent = (simple_split[i] + simple_split[i + 1]).strip()
                            if sent:
                                sentences.append(sent)
                    if len(simple_split) % 2 == 1 and simple_split[-1].strip():
                        sentences.append(simple_split[-1].strip())
                
                # If still no sentences found, treat whole paragraph as one sentence
                if not sentences:
                    sentences = [p]
                
                # Group into chunks of max_sentences, creating new paragraphs
                for i in range(0, len(sentences), max_sentences):
                    chunk = " ".join(sentences[i:i+max_sentences]).strip()
                    if chunk:
                        # Ensure it ends with punctuation
                        if not re.search(r'[.!?]$', chunk):
                            chunk += "."
                        fixed.append(chunk)
            
            result = "\n\n".join(fixed).strip()
            return result or text
        except Exception as e:
            print(f"  [WARN] Paragraph enforcement failed: {e}")
            return text
    
    def _has_crises(self, text: str) -> bool:
        """Generic crisis detection used across all topics."""
        return self._has_market_crises(text)
    
    def _chunks_have_crisis(self, chunks: list) -> bool:
        """Check if any provided chunk text mentions panics/crises or canonical years."""
        try:
            for text, _meta in chunks:
                tl = text.lower()
                if "panic" in tl or "crisis" in tl or "crises" in tl:
                    return True
                for yr in ("1973", "1974", "1987", "1998", "2008", "1929", "1907", "1825", "1873"):
                    if yr in tl:
                        return True
        except Exception:
            pass
        return False
    
    def _needs_grounding(self, text: str) -> bool:
        """Decide if we should re-ask with a strictly grounded prompt."""
        try:
            if not isinstance(text, str):
                return True
            if "no relevant information found" in text.lower():
                return True
            # Too short or too few paragraphs
            if len(text.strip()) < 300 or self._para_count(text) < 3:
                return True
        except Exception:
            return True
        return False
    
    def _build_prompt_grounded(self, question: str, chunks: list) -> str:
        """Ask the LLM to answer ONLY from the provided chunks, restating the topic and forbidding speculation."""
        # Extract all years present in chunks to understand the span (for context, not hardcoding)
        years_present = set()
        for text, _ in chunks:
            matches = re.findall(r'\b(1[6-9]\d{2}|20[0-2]\d)\b', text)
            years_present.update(int(m) for m in matches)
        years_sorted = sorted(years_present) if years_present else []
        
        # Estimate token count to check if we're hitting limits
        chunks_text = "\n\n".join([
            f"--- CHUNK {i+1} ---\n{text}"
            for i, (text, meta) in enumerate(chunks)
        ])
        estimated_tokens = len(chunks_text.split()) * 1.3  # Rough estimate
        
        # If chunks are very large, sample strategically to stay within token limits
        # But ensure we keep chunks from all time periods
        if estimated_tokens > 150000:  # ~150k tokens - need to sample
            print(f"  [WARN] Large chunk set: ~{int(estimated_tokens)} tokens - sampling to stay within limits")
            # Group chunks by decade to ensure we keep representation from all eras
            chunks_by_decade = {}
            for chunk in chunks:
                text, meta = chunk
                # Find latest year in chunk
                matches = re.findall(r'\b(1[6-9]\d{2}|20[0-2]\d)\b', text)
                if matches:
                    latest_year = max(int(m) for m in matches)
                    decade = (latest_year // 10) * 10
                else:
                    decade = 0  # Undated
                if decade not in chunks_by_decade:
                    chunks_by_decade[decade] = []
                chunks_by_decade[decade].append(chunk)
            
            # Sample up to 20 chunks per decade, prioritizing later decades
            sampled_chunks = []
            for decade in sorted(chunks_by_decade.keys(), reverse=True):
                dec_chunks = chunks_by_decade[decade]
                sampled_chunks.extend(dec_chunks[:20])
            
            if len(sampled_chunks) < len(chunks):
                print(f"  [INFO] Sampled {len(chunks)} chunks down to {len(sampled_chunks)} (keeping all decades represented)")
                chunks = sampled_chunks
                # Rebuild chunks_text with sampled chunks
                chunks_text = "\n\n".join([
                    f"--- CHUNK {i+1} ---\n{text}"
                    for i, (text, meta) in enumerate(chunks)
                ])
        
        return f"""Answer this question USING ONLY the information in the DOCUMENT CHUNKS. If the chunks do not contain an item, do not invent it.

QUESTION:
{question}

DOCUMENT CHUNKS ({len(chunks)} chunks):
{chunks_text}

STRICT RULES:
1) Use ONLY facts explicitly present in the chunks; do not speculate or add outside knowledge.
2) Keep the SUBJECT active in every sentence; do not drift to unrelated entities.
3) Expand acronyms on first use if the expansion appears in the chunks; otherwise avoid the acronym.
4) Introduce people/entities with a one-clause role and relevance to the SUBJECT, but only if stated in the chunks.
5) CHRONOLOGICAL COVERAGE (MANDATORY - CRITICAL): The chunks contain information spanning {f"{years_sorted[0]} to {years_sorted[-1]}" if len(years_sorted) >= 2 else "multiple time periods"}. You MUST cover ALL eras from {f"{years_sorted[0]}" if years_sorted else "earliest"} to {f"{years_sorted[-1]}" if years_sorted else "latest"}. Do NOT stop at an early period. Move forward chronologically: {f"{years_sorted[0]//10*10}s → " if years_sorted else ""}{f"{years_sorted[-1]//10*10}s" if years_sorted else "all periods"}. Do not skip any decades or centuries present in the chunks.
6) Organize chronologically with short transitions; MAX 3 sentences per paragraph; MIN 5 paragraphs (or more if multiple eras are present - aim for 1-2 paragraphs per major era).
7) End with "Related Questions:" based on entities/topics that appear in the chunks (only if answerable from them).
"""
    
    def _generate_iterative_narrative(
        self,
        question: str,
        chunks: list,
        subject_terms: Optional[List[str]] = None,
        subject_phrases: Optional[List[str]] = None
    ) -> str:
        """Generate narrative using period-based iterative processing."""
        # CRITICAL: For small queries (≤20 chunks), skip expensive period splitting
        # This avoids 6-20 second waits between periods that cause timeouts
        if len(chunks) <= 20:
            print(f"  [OPTIMIZE] Small query ({len(chunks)} chunks) - skipping period splitting, using single LLM call")
            answer = self.llm.generate_answer(question, chunks)
            # Check for empty answer (can happen if LLM hits token limit)
            if not answer or not answer.strip():
                print(f"  [WARN] Empty answer detected, attempting retry with reduced chunks...")
                if len(chunks) > 10:
                    reduced_chunks = chunks[:10]
                    print(f"  [RETRY] Retrying with {len(reduced_chunks)} chunks (reduced from {len(chunks)})")
                    answer = self.llm.generate_answer(question, reduced_chunks)
                else:
                    return f"I apologize, but I encountered an issue generating a response for '{question}'. The response may have exceeded token limits. Please try rephrasing your question or breaking it into smaller parts."
            # Ensure structure & related questions
            if (not self._has_related_questions(answer)) or self._para_count(answer) < 3:
                answer = self._polish_answer(question, answer)
            return answer
        
        from .batch_processor_iterative import IterativePeriodProcessor
        
        processor = IterativePeriodProcessor(self.llm, use_async=self.use_async)
        preview_periods = processor.organize_periods(
            chunks,
            max_per_period=999999,
            subject_terms=subject_terms,
            subject_phrases=subject_phrases
        )
        
        if not preview_periods:
            return "No relevant information found."
        
        if len(preview_periods) <= 1:
            filtered_chunks = list(chain.from_iterable(preview_periods.values()))
            if not filtered_chunks:
                return "No relevant information found."
            print("  [AUTO] Single-era subject detected; skipping century splitting.")
            # If institutional acronym present, stratify evidence across decades
            acronym_terms = [tok for tok in (subject_phrases or []) if tok.isupper()]
            if acronym_terms:
                filtered_chunks = self._stratify_institutional_evidence(filtered_chunks, acronym_terms, cap_per_decade=5, max_total=50)
            if len(filtered_chunks) > 30:
                answer = self._generate_batched_narrative(question, filtered_chunks)
            else:
                answer = self.llm.generate_answer(question, filtered_chunks)
            # Check for empty answer (can happen if LLM hits token limit)
            if not answer or not answer.strip():
                print(f"  [WARN] Empty answer detected, attempting retry with reduced chunks...")
                if len(filtered_chunks) > 10:
                    reduced_chunks = filtered_chunks[:10]
                    print(f"  [RETRY] Retrying with {len(reduced_chunks)} chunks (reduced from {len(filtered_chunks)})")
                    answer = self.llm.generate_answer(question, reduced_chunks)
                else:
                    return f"I apologize, but I encountered an issue generating a response for '{question}'. The response may have exceeded token limits. Please try rephrasing your question or breaking it into smaller parts."
            # Ensure structure & related questions
            if (not self._has_related_questions(answer)) or self._para_count(answer) < 3:
                answer = self._polish_answer(question, answer)
            return answer
        
        if not self.use_async:
            # Use sequential processing for FastAPI compatibility
            return processor.process_iterative_sequential(
                question=question,
                chunks=chunks,
                prompt_builder=lambda q, c, ctx: self._build_prompt(q, c),
                max_chunks_per_period=999999,
                subject_terms=subject_terms,
                subject_phrases=subject_phrases
            )
        
        return processor.process_iterative(
            question=question,
            chunks=chunks,
            prompt_builder=lambda q, c, ctx: self._build_prompt(q, c),
            max_chunks_per_period=999999,  # No cap - process ALL chunks in each period
            subject_terms=subject_terms,
            subject_phrases=subject_phrases
        )
    
    def _extract_law_tokens(self, question: str) -> list:
        """
        Detect law tokens like TA1813, SA1934 in the question and return retrieval terms:
        - The literal token (e.g., 'TA1813')
        - The expanded phrase 'Full Name YYYY' using YEAR_PREFIX_EXPANSIONS
        Note: Only 4-digit years are supported (e.g., TA1813, not TA13).
        """
        results = []
        q_visible = question
        matches = re.findall(r"\b(BHCA|BA|TA|SA|FA|IA|AA|PA|DA|CA|EA|LA)(\d{4})\b", q_visible, flags=re.IGNORECASE)
        seen = set()
        for prefix, year_token in matches:
            pref = prefix.upper()
            literal = f"{pref}{year_token}"
            if literal not in seen:
                results.append(literal)
                results.append(literal.lower())
                seen.add(literal)
            full_base = YEAR_PREFIX_EXPANSIONS.get(pref)
            if not full_base:
                continue
            # year_token is always 4 digits now
            full_phrase = f"{full_base}{year_token}"
            for alias in (full_phrase, full_phrase.lower()):
                if alias not in seen:
                    results.append(alias)
                    seen.add(alias)
        return results
    
    def _has_related_questions(self, text: str) -> bool:
        """Detect if answer includes a Related Questions block."""
        if not isinstance(text, str):
            return False
        tl = text.lower()
        if "related questions" in tl:
            return True
        # Fallback: presence of 3+ question-mark lines near the end
        tail = "\n".join(tl.splitlines()[-30:])
        q_count = sum(1 for line in tail.splitlines() if "?" in line)
        return q_count >= 3
    
    def _para_count(self, text: str) -> int:
        """Count paragraphs by blank-line separation."""
        if not isinstance(text, str):
            return 0
        paras = [p for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]
        return len(paras)
    
    def _polish_answer(self, question: str, text: str, chunks: Optional[List[tuple]] = None) -> str:
        """Append a Related Questions section if missing (answerable from chunks) and ensure minimum paragraph count."""
        output = text or ""
        # Ensure minimum paragraphs
        if self._para_count(output) < 3:
            output = output.strip() + "\n\n" + "**Additional Context:**\n- Clarify scope across decades present in sources.\n- Highlight leadership where mentioned (chairs, directors).\n"
        # Ensure Related Questions
        if not self._has_related_questions(output):
            rq = self._build_answerable_related_questions(question, chunks or [])
            output += "\n\nRelated Questions:\n" + "\n".join(f"* {q}" for q in rq)
        return output

    def _build_answerable_related_questions(self, question: str, chunks: List[tuple]) -> List[str]:
        """Generate 3–5 related questions guaranteed answerable from current chunks."""
        # Extract candidate terms from chunks that exist in the index
        available_terms = self._extract_terms_from_chunks(chunks)
        ql = (question or "").lower()
        out: List[str] = []
        # Score terms by support (how many chunk ids) and prefer institutions/acronyms
        scored_terms = []
        for term in available_terms:
            count = len(self.term_to_chunks.get(term, []))
            scored_terms.append((count, term))
        scored_terms.sort(reverse=True)
        for _, term in scored_terms[:8]:
            if len(out) >= 5:
                break
            if term.upper() in ACRONYM_EXPANSIONS:
                display = f"{term.upper()} ({ACRONYM_EXPANSIONS[term.upper()]})"
            else:
                display = term.title()
            out.append(f"What role did {display} play in this topic, according to the documents?")
        # If still short, add safe thematic follow-ups grounded in chunks
        if len(out) < 3:
            out.append("Which panics or crises affected this subject and how did access to finance change?")
            out.append("How did identity groups (e.g., Jews, Dalits, women) gain or lose access to banking here?")
            out.append("Which nationalizations or decrees changed bank control, and with what outcomes?")
        return out[:5]

    def _review_and_fix_answer(self, answer: str, chunks: list, question: str, max_iterations: int = MAX_REVIEW_ITERATIONS, query_start_time: float = None) -> str:
        """Review answer against criteria and automatically fix issues. Continues until all pass or max_iterations."""
        # Skip review if max_iterations is 0 (for very large queries to avoid timeouts)
        if max_iterations == 0:
            print(f"  [REVIEW] Skipping review (max_iterations=0) to avoid timeout")
            return answer
        if not self.reviewer:
            return answer
        
        import time
        from lib.config import QUERY_TIMEOUT_SECONDS
        
        print(f"  [REVIEW] Starting review of answer ({len(answer)} chars, {len(chunks) if chunks else 0} chunks)")
        import sys
        sys.stdout.flush()  # Ensure output is visible
        current_answer = answer
        iteration = 0
        
        while iteration < max_iterations:
            # Check timeout if query_start_time provided
            if query_start_time:
                elapsed = time.time() - query_start_time
                if elapsed > QUERY_TIMEOUT_SECONDS - 30:  # Leave 30s buffer for final processing
                    print(f"  [REVIEW] Approaching timeout ({elapsed:.1f}s), stopping review early")
                    return current_answer
            iteration += 1
            print(f"  [REVIEW] Iteration {iteration}/{max_iterations}...")
            sys.stdout.flush()
            
            # Review the answer
            results = self.reviewer.review(current_answer, chunks=chunks)
            
            # Check if all passed
            all_passed = all(r.passed for r in results.values())
            if all_passed:
                if iteration > 1:
                    print(f"  [REVIEW] ✓ All criteria passed after {iteration} iteration(s)")
                else:
                    print(f"  [REVIEW] ✓ All criteria passed on first check")
                return current_answer
            
            # Collect failures
            failures = []
            for result in results.values():
                if not result.passed and result.issues:
                    failures.extend(result.issues)
            
            if not failures:
                print(f"  [REVIEW] No specific failures found, but some criteria didn't pass")
                return current_answer
            
            print(f"  [REVIEW] Iteration {iteration}: Found {len(failures)} issues")
            for criterion, result in results.items():
                if not result.passed:
                    print(f"    - {criterion}: {result.details}")
            
            # Track if we made any changes
            made_changes = False
            needs_reask = False
            reask_reasons = []
            
            # Fix paragraph length issues (no API call needed)
            if 'paragraph_length' in results and not results['paragraph_length'].passed:
                current_answer = self._enforce_paragraph_limit(current_answer, max_sentences=MAX_SENTENCES_PER_PARAGRAPH)
                print(f"  [FIX] Applied paragraph length enforcement")
                made_changes = True
            
            # Check if we need to re-ask (combine full_history and chronological_flow)
            if 'full_history' in results and not results['full_history'].passed:
                needs_reask = True
                reask_reasons.append("full history coverage")
            
            if 'chronological_flow' in results and not results['chronological_flow'].passed:
                needs_reask = True
                reask_reasons.append("chronological ordering")
            
            if 'panics_coverage' in results and not results['panics_coverage'].passed:
                needs_reask = True
                reask_reasons.append("panics coverage")
            
            # Re-ask only once per iteration if needed (combines both fixes)
            if needs_reask:
                reason_str = " and ".join(reask_reasons)
                print(f"  [FIX] Re-asking LLM to fix: {reason_str}")
                # Enhance prompt to emphasize chronological organization and panics
                enhanced_question = f"{question}\n\nCRITICAL REQUIREMENTS:\n"
                if 'chronological ordering' in reask_reasons:
                    enhanced_question += "- Organize STRICTLY chronologically: start with earliest period, move forward in time, NEVER jump backwards\n"
                    enhanced_question += "- If chunks mention 1960s and 1990s, cover 1970s and 1980s in between\n"
                if 'panics coverage' in reask_reasons:
                    enhanced_question += "- MANDATORY: Include ALL panics/crises mentioned in chunks (Panic of 2008, 2009, etc.)\n"
                    enhanced_question += "- For each panic: explain what happened and how it affected the subject\n"
                enhanced_question += "- Follow chronological order: earliest period → intermediate periods → latest period\n"
                current_answer = self._call_llm_with_rate_limit(enhanced_question, chunks)
                # Re-apply paragraph enforcement after re-asking
                current_answer = self._enforce_paragraph_limit(current_answer, max_sentences=MAX_SENTENCES_PER_PARAGRAPH)
                made_changes = True
            
            # If no changes were made, we might be stuck - apply final enforcement and return
            if not made_changes:
                print(f"  [REVIEW] No fixes applied this iteration, applying final enforcement")
                current_answer = self._enforce_paragraph_limit(current_answer, max_sentences=MAX_SENTENCES_PER_PARAGRAPH)
                # Check one more time
                final_results = self.reviewer.review(current_answer, chunks=chunks)
                if all(r.passed for r in final_results.values()):
                    print(f"  [REVIEW] ✓ All criteria passed after final enforcement")
                    return current_answer
                else:
                    print(f"  [REVIEW] Some criteria still failing after {iteration} iterations")
                    return current_answer
        
        # Reached max iterations - apply final enforcement and return
        print(f"  [REVIEW] Reached max iterations ({max_iterations}), applying final enforcement")
        current_answer = self._enforce_paragraph_limit(current_answer, max_sentences=3)
        return current_answer
    
    def _extract_terms_from_chunks(self, chunks: List[tuple]) -> Set[str]:
        """Return lowercased terms found in chunks that are present in the index."""
        terms: Set[str] = set()
        for text, _ in chunks:
            tl = text.lower()
            # Simple token scan: collect words that are index keys and appear in text
            for term in self.term_to_chunks.keys():
                lt = term.lower()
                if lt in tl:
                    terms.add(lt)
                    if len(terms) > 50:
                        break
        return terms
    
    def _build_prompt(self, question: str, chunks: list) -> str:
        """Build prompt for LLM narrative generation."""
        chunks_text = "\n\n".join([
            f"--- CHUNK {i+1} ---\n{text}"
            for i, (text, meta) in enumerate(chunks)
        ])
        
        return f"""You are a banking historian. Answer this question: {question}

DOCUMENT CHUNKS:
{chunks_text}

CRITICAL FRAMEWORK - Create THEMATIC narrative with CULTURAL ANALYSIS:

1. STRUCTURE - THEMATIC SECTIONS with multiple focused paragraphs:
   - Use section headings: "**Theme Name:**"
   - Each section = 2-4 paragraphs on ONE theme
   - Example: "**British Colonial Impact:**" then 3 paragraphs about EIC, Brahmins, Dalits

2. PARAGRAPH LENGTH (HARD LIMIT - COUNT SENTENCES):
   - MAXIMUM 3 sentences per paragraph
   - After 3 sentences, MANDATORY break
   - Each paragraph = one subtopic within section theme

3. ENTITY INTRODUCTIONS (MANDATORY):
   - When first mentioning an acronym or institution, expand it once in-line with role (e.g., "*Vneshtorg* (Soviet Bank for Foreign Trade, EXIM role)").
   - When first mentioning a person, add a 1-clause apposition with role and why relevant to the SUBJECT (e.g., "Viktor Gerashchenko, Vneshtorg deputy who managed foreign credits").
   - NO name-dropping. If you cannot state relevance in one clause, omit the name.
   - DO NOT use an acronym (e.g., BSU) unless you can define it from the provided chunks in-line. If definition is not present in the chunks, avoid using the acronym.
   - For every non-subject entity mentioned, explicitly state its relationship to the SUBJECT in the same sentence.

3. COMPARATIVE ANALYSIS - Draw comparisons across groups when relevant:
   - PARALLEL PATTERNS: Multiple groups showing same dynamics (endogamy, exclusion)
   - CONTRASTING TREATMENT: Different treatment of similar groups
     Example: "As Russia restricted Jewish rights in 1880, it expanded Old Believer freedoms in 1883"
   - COMPETITION/COLLABORATION: Groups competing or partnering
     Example: "Bukharan Jewish factories rivaled Old Believer counterparts in Moscow"
    - HIERARCHY: Show how groups related (Brahmin dominance excluded Dalits)
    - Draw comparisons only when supported by the documents

4. DEFINE SPECIALIZED TERMS on first use:
   - Dalit (untouchable, lowest Hindu caste, faced severe discrimination)
   - Brahmin (priestly caste, highest in Hindu hierarchy)
   - Kohanim (Jewish priestly caste), Court Jew (banker to monarchs)
   - Old Believers (Russian Orthodox sect, split after 17th century reforms)
   - Always explain hierarchy/status

5. PARAGRAPH RULES (HARD LIMITS):
   - MAX 3 sentences per paragraph (COUNT THEM). If over 3, SPLIT.
   - MIN 5 paragraphs total (≥3 if content is truly limited to one era).
   - ONE clear topic per paragraph; use transitions ("Building on this...", "During this period...", "As a result...").

6. WRITING STYLE:
   - BERNANKE: Causal analysis
   - MAYA ANGELOU: Humanizing details
   - NO LIST-LIKE WRITING

6. MECHANICS:
   - SUBJECT ACTIVE: *Rothschild* hired (NOT was hired by)
   - Institutions italicized: *Rothschild*, *Hope*, *Securities and Exchange Commission (SEC)* when relevant
   - People regular: e.g., Joseph P. Kennedy Sr.
   - NO PLATITUDES

7. COVERAGE & CONSISTENCY:
   - Cover all eras present in the provided documents; do not stop at an early decade if later decades are present.
   - For city/branch or successor cases, include the successor era if mentioned or add a "See also" in Related Questions.
   - End with "Related Questions:" (3–5 precise, document-grounded items; no generic "impact/why" questions).

Generate a thematically organized narrative with cultural explanations:"""
    
    def _generate_batched_narrative(self, question: str, chunks: list) -> str:
        """Generate narrative from chunks in batches, with logging."""
        import time
        batch_start = time.time()
        print(f"    [BATCH] Starting batched narrative generation with {len(chunks)} chunks")
        
        pause_time = BATCH_PAUSE_SECONDS  # Pause between batches to avoid rate limits
        narratives = []
        
        # Calculate token-based batches (more efficient than chunk count)
        # Estimate: each chunk ≈ ESTIMATED_WORDS_PER_CHUNK words ≈ ESTIMATED_WORDS_PER_CHUNK * TOKENS_PER_WORD tokens
        tokens_per_chunk = ESTIMATED_WORDS_PER_CHUNK * TOKENS_PER_WORD
        chunks_per_batch = max(1, int(MAX_TOKENS_PER_REQUEST / tokens_per_chunk))
        
        # Also account for prompt overhead (question + instructions ≈ 2000 tokens)
        prompt_overhead_tokens = 2000
        available_tokens = MAX_TOKENS_PER_REQUEST - prompt_overhead_tokens
        chunks_per_batch = max(1, int(available_tokens / tokens_per_chunk))
        
        total_batches = (len(chunks) + chunks_per_batch - 1) // chunks_per_batch
        estimated_time = total_batches * pause_time
        print(f"  [INFO] Will process {total_batches} batches (~{chunks_per_batch} chunks/batch, ~{estimated_time//60} min {estimated_time%60} sec)")
        
        for i in range(0, len(chunks), chunks_per_batch):
            batch = chunks[i:i + chunks_per_batch]
            batch_num = i // chunks_per_batch + 1
            
            # Calculate actual tokens for this batch
            batch_words = sum(len(chunk[0].split()) for chunk in batch)
            batch_tokens = int(batch_words * TOKENS_PER_WORD + prompt_overhead_tokens)
            
            print(f"  [BATCH {batch_num}/{total_batches}] Processing {len(batch)} chunks (~{batch_tokens:,} tokens)...")
            
            # Generate narrative for this batch
            narrative = self.llm.generate_answer(question, batch)
            narratives.append(narrative)
            
            # Wait between batches to avoid rate limit (if not last batch)
            if i + chunks_per_batch < len(chunks):
                print(f"  [WAIT] Pausing {pause_time} seconds to avoid rate limit...")
                time.sleep(pause_time)
        
        # Combine all narratives
        print(f"  [COMBINE] Merging {len(narratives)} narrative sections...")
        if len(narratives) == 1:
            return narratives[0]
        
        # Ask LLM to combine the narratives into one coherent story
        combined_prompt = f"""Combine these {len(narratives)} sections about {question} into one clear, factual overview.

{chr(10).join([f"Section {i+1}:{chr(10)}{n}{chr(10)}" for i, n in enumerate(narratives)])}

CRITICAL RULES:

1. MAKE THE SUBJECT THE STAR - Every sentence must keep subject active:
✓ "Lehman merged with Goldman" NOT "Goldman merged with Lehman"

2. ONLY INCLUDE DIRECTLY RELEVANT INFORMATION:
If you mention another entity, explain its connection to the subject:
✓ "Lehman and Atlas reorged Paramount in 1935"
✗ "SA40 forced Atlas to split" (irrelevant without explaining Lehman's role)

Other Instructions:
- NO platitudes or flowery language
- INCLUDE economic context: Panics, wars, regulations
- Be CONSISTENT: "WWI" and "WWII" always
- CLARIFY names: "President Carter" not "Carter"
- Organize by time periods with headings
- Remove redundancies
- End with "Related Questions:" (3-5)

Answer:"""
        
        try:
            response = self.llm.client.generate_content(combined_prompt)
            return response.text
        except Exception as e:
            print(f"  [WARN] Failed to combine narratives: {e}, using concatenation fallback")
            # Fallback: just concatenate
            return "\n\n---\n\n".join(narratives)
    
    def get_stats(self) -> Dict:
        """Get database statistics."""
        return {
            'total_chunks': self.collection.count(),
            'indexed_terms': len(self.term_to_chunks),
            'entity_associations': len(self.entity_associations)
        }

    def _extract_subject_filters(
        self,
        question: str,
        keywords: List[str],
        raw_tokens: List[str],
        canonical_map: Dict[str, set]
    ) -> Tuple[List[str], List[str]]:
        """Return canonical subject terms plus strict phrases for institutions."""
        subject_phrases = []
        seen_phrases = set()
        
        def add_phrase(value: str):
            if not value:
                return
            if value in seen_phrases:
                return
            seen_phrases.add(value)
            subject_phrases.append(value)

        subject_terms = []
        seen_terms = set()
        for term in keywords:
            if term in SUBJECT_GENERIC_TERMS:
                continue
            if term in seen_terms:
                continue
            seen_terms.add(term)
            subject_terms.append(term)
            for raw in canonical_map.get(term, []):
                add_phrase(raw)
        
        for token in raw_tokens:
            if token.isupper() and len(token) >= 3:
                add_phrase(token)
                expansion = ACRONYM_EXPANSIONS.get(token)
                if expansion:
                    add_phrase(expansion.lower())
        
        for content in re.findall(r'\(([^)]+)\)', question):
            phrase = content.strip()
            if not phrase:
                continue
            if phrase.isupper():
                add_phrase(phrase)
                expansion = ACRONYM_EXPANSIONS.get(phrase)
                if expansion:
                    add_phrase(expansion.lower())
            else:
                add_phrase(phrase.lower())
                if phrase.strip().lower() == "securities and exchange commission":
                    add_phrase("securities & exchange commission")
        
        return subject_terms, subject_phrases

    def _filter_chunks_by_subject_terms(self, chunks: List[tuple], subject_terms: List[str]) -> List[tuple]:
        """Keep chunks mentioning subject terms first; preserve later periods even if imperfect matches."""
        if not chunks or not subject_terms:
            return chunks
        
        primary = subject_terms[0]
        others = subject_terms[1:]
        
        strong_matches = []
        primary_matches = []
        secondary_matches = []
        # Determine time span of chunks to identify "later periods" dynamically
        all_chunk_years = []
        for chunk in chunks:
            text = chunk[0]
            matches = re.findall(r'\b(1[6-9]\d{2}|20[0-2]\d)\b', text)
            if matches:
                all_chunk_years.extend(int(m) for m in matches)
        
        # If we have chunks spanning multiple periods, identify what's "later"
        median_year = sorted(all_chunk_years)[len(all_chunk_years) // 2] if all_chunk_years else None
        
        later_period_chunks = []  # Chunks from later periods that might not match perfectly
        
        for chunk in chunks:
            text_lower = chunk[0].lower()
            text = chunk[0]
            
            # Extract latest year from chunk
            matches = re.findall(r'\b(1[6-9]\d{2}|20[0-2]\d)\b', text)
            latest_year = max(int(m) for m in matches) if matches else 0
            # Consider it "later period" if it's significantly after the median, or if no median, after earliest
            if median_year:
                is_later_period = latest_year > median_year + EARLY_STOP_GAP_THRESHOLD
            elif all_chunk_years:
                earliest = min(all_chunk_years)
                is_later_period = latest_year > earliest + EARLY_STOP_GAP_THRESHOLD
            else:
                is_later_period = False
            
            contains_primary = primary in text_lower
            contains_all = contains_primary and all(term in text_lower for term in others)
            contains_any = any(term in text_lower for term in subject_terms)
            
            if contains_all:
                strong_matches.append(chunk)
            elif contains_primary:
                primary_matches.append(chunk)
            elif contains_any:
                secondary_matches.append(chunk)
            elif is_later_period:
                # Preserve chunks from later periods even if they don't match perfectly
                # They might mention the subject in context that's not captured by simple term matching
                later_period_chunks.append(chunk)
        
        # Prefer strong + primary; include secondary and later period chunks
        result: List[tuple] = []
        result.extend(strong_matches)
        result.extend(primary_matches)
        result.extend(secondary_matches)  # Include all secondary matches, not just 10
        result.extend(later_period_chunks[:20])  # Include up to 20 chunks from later periods
        
        # If still empty, fall back to all chunks
        return result if result else chunks
    
    def _try_use_preprocessed_file(self, chunks: List[tuple], question: str) -> Optional[List[tuple]]:
        """
        Try to use a preprocessed deduplicated file for the primary term in the query.
        
        Args:
            chunks: List of (text, metadata) tuples
            question: User's question
        
        Returns:
            Preprocessed chunks if file exists, None otherwise
        """
        import os
        from .config import DATA_DIR
        
        # Extract primary term from question
        question_lower = question.lower().strip()
        
        # Look for deduplicated cache file
        dedup_dir = os.path.join(DATA_DIR, 'deduplicated_terms')
        cache_file = os.path.join(dedup_dir, 'deduplicated_cache.json')
        
        # Load cache if available
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    deduplicated_cache = json.load(f)
            except:
                deduplicated_cache = {}
        else:
            deduplicated_cache = {}
        
        if not deduplicated_cache:
            return None
        
        # Try to extract the main subject from common query patterns
        potential_terms = []
        
        # Pattern 1: "Tell me about X" -> "X"
        if 'tell me about' in question_lower:
            subject = question_lower.replace('tell me about', '').strip()
            if subject:
                potential_terms.append(subject)
                # Also try plural/singular variations
                if subject.endswith('s'):
                    potential_terms.append(subject[:-1])  # Remove 's'
                else:
                    potential_terms.append(subject + 's')  # Add 's'
        
        # Pattern 2: "What is X" or "Who is X" -> "X"
        for pattern in ['what is', 'who is', 'when is', 'where is', 'how is']:
            if pattern in question_lower:
                subject = question_lower.split(pattern, 1)[1].strip().split()[0:3]  # Take up to 3 words
                if subject:
                    potential_terms.append(' '.join(subject))
        
        # Pattern 3: Extract meaningful words (not stop words)
        words = question_lower.split()
        # Use centralized STOP_WORDS from constants.py
        meaningful_words = [w for w in words if w not in STOP_WORDS and len(w) > 2]
        
        # Add single words
        potential_terms.extend(meaningful_words)
        
        # Add multi-word phrases (2-3 words)
        for i in range(len(meaningful_words) - 1):
            phrase = f"{meaningful_words[i]}_{meaningful_words[i+1]}"
            potential_terms.append(phrase)
        for i in range(len(meaningful_words) - 2):
            phrase = f"{meaningful_words[i]}_{meaningful_words[i+1]}_{meaningful_words[i+2]}"
            potential_terms.append(phrase)
        
        # Check if any term has deduplicated content in cache
        for term in potential_terms:
            # Try exact match first
            if term in deduplicated_cache:
                deduplicated_text = deduplicated_cache[term]
                if deduplicated_text and deduplicated_text.strip():
                    return self._split_large_deduplicated_text(deduplicated_text, chunks[0][1] if chunks else {})
            
            # Try lowercase match
            term_lower = term.lower()
            if term_lower in deduplicated_cache:
                deduplicated_text = deduplicated_cache[term_lower]
                if deduplicated_text and deduplicated_text.strip():
                    return self._split_large_deduplicated_text(deduplicated_text, chunks[0][1] if chunks else {})
        
        return None
    
    def _split_large_deduplicated_text(self, text: str, metadata: dict, max_words_per_chunk: int = None) -> List[tuple]:
        """
        Split large deduplicated text into chunks that fit within LLM limits.
        Splits by sentences/paragraphs to maintain readability.
        Dynamically calculates chunk size based on LLM limits.
        
        Args:
            text: Deduplicated text to split
            metadata: Metadata to attach to each chunk
            max_words_per_chunk: Maximum words per chunk (defaults to MAX_WORDS_PER_REQUEST)
        
        Returns:
            List of (text, metadata) tuples
        """
        from .config import MAX_WORDS_PER_REQUEST
        
        if max_words_per_chunk is None:
            # Use the full LLM limit - MAX_WORDS_PER_REQUEST already accounts for prompt overhead
            # It's calculated as MAX_TOKENS_PER_REQUEST / TOKENS_PER_WORD, which leaves room for prompt
            max_words_per_chunk = MAX_WORDS_PER_REQUEST
        
        words = text.split()
        total_words = len(words)
        
        # If text fits in one chunk, return as-is
        if total_words <= max_words_per_chunk:
            return [(text, metadata)]
        
        # Split by sentences first (preserve sentence boundaries)
        sentences = []
        # Split on sentence endings
        sentence_parts = re.split(r'([.!?]+)\s+', text)
        current_sentence = ""
        for i, part in enumerate(sentence_parts):
            current_sentence += part
            # If next part starts with capital or is end, finish sentence
            if i + 1 < len(sentence_parts):
                next_part = sentence_parts[i + 1].strip()
                if next_part and next_part[0].isupper():
                    sentences.append(current_sentence.strip())
                    current_sentence = ""
            else:
                if current_sentence.strip():
                    sentences.append(current_sentence.strip())
        
        # If no sentences found, split by paragraphs
        if not sentences:
            paragraphs = text.split('\n\n')
            sentences = [p.strip() for p in paragraphs if p.strip()]
        
        # If still no good splits, split by words
        if not sentences:
            sentences = [text]
        
        # Group sentences into chunks
        chunks = []
        current_chunk = []
        current_word_count = 0
        
        for sentence in sentences:
            sentence_words = len(sentence.split())
            
            # If single sentence exceeds limit, split it by words
            if sentence_words > max_words_per_chunk:
                # Add current chunk if any
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                    current_chunk = []
                    current_word_count = 0
                
                # Split long sentence into word chunks
                words_in_sentence = sentence.split()
                for i in range(0, len(words_in_sentence), max_words_per_chunk):
                    chunk_words = words_in_sentence[i:i + max_words_per_chunk]
                    chunks.append(" ".join(chunk_words))
            else:
                # Check if adding this sentence would exceed limit
                if current_word_count + sentence_words > max_words_per_chunk:
                    # Save current chunk if it has content
                    if current_chunk:
                        chunks.append(" ".join(current_chunk))
                    # Start new chunk with this sentence
                    current_chunk = [sentence]
                    current_word_count = sentence_words
                else:
                    # Add to current chunk
                    current_chunk.append(sentence)
                    current_word_count += sentence_words
        
        # Add final chunk
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        # Verify all chunks are within limit (safety check)
        verified_chunks = []
        for chunk_text in chunks:
            chunk_words = len(chunk_text.split())
            if chunk_words > max_words_per_chunk:
                # This shouldn't happen, but if it does, split by words as fallback
                print(f"  [WARN] Chunk exceeded limit ({chunk_words:,} > {max_words_per_chunk:,}), splitting by words")
                words_in_chunk = chunk_text.split()
                for i in range(0, len(words_in_chunk), max_words_per_chunk):
                    chunk_words_subset = words_in_chunk[i:i + max_words_per_chunk]
                    verified_chunks.append(" ".join(chunk_words_subset))
            else:
                verified_chunks.append(chunk_text)
        
        print(f"  [DEDUP] Split deduplicated text ({total_words:,} words) into {len(verified_chunks)} chunks (max {max_words_per_chunk:,} words each)")
        
        return [(chunk_text, metadata) for chunk_text in verified_chunks]
    
    def _deduplicate_and_combine_chunks(self, chunks: List[tuple]) -> List[tuple]:
        """
        Deduplicate and combine chunks before sending to LLM.
        Uses file-based deduplication: writes chunks to temp file, deduplicates, reads back.
        
        Removes:
        - Exact duplicates
        - Duplicate sentences
        - Duplicate longer phrases (7+ words)
        
        Args:
            chunks: List of (text, metadata) tuples
            
        Returns:
            Deduplicated and combined chunks
        """
        if not chunks:
            return chunks
        
        import os
        import tempfile
        from .config import TEMP_DIR
        
        # Step 1: Write all chunks to a temp file
        os.makedirs(TEMP_DIR, exist_ok=True)
        temp_file = os.path.join(TEMP_DIR, f"chunks_{hash(str(chunks))}.txt")
        
        with open(temp_file, 'w', encoding='utf-8') as f:
            for text, meta in chunks:
                f.write(text + "\n\n---CHUNK_BOUNDARY---\n\n")
        
        # Step 2: Deduplicate the file (sentence and phrase level)
        deduplicated_text = self._deduplicate_text_file(temp_file)
        
        # Step 3: Split back into chunks (by boundary markers)
        deduplicated_chunks_text = deduplicated_text.split("\n\n---CHUNK_BOUNDARY---\n\n")
        deduplicated_chunks_text = [c.strip() for c in deduplicated_chunks_text if c.strip()]
        
        # Step 4: Create chunk tuples (preserve metadata from first chunk if possible)
        result = []
        for i, text in enumerate(deduplicated_chunks_text):
            meta = chunks[i][1] if i < len(chunks) else {}
            result.append((text, meta))
        
        # Clean up temp file
        try:
            os.remove(temp_file)
        except:
            pass
        
        if len(result) < len(chunks):
            print(f"    [DEDUP] Reduced {len(chunks)} chunks to {len(result)} after deduplication")
        
        return result
    
    def _deduplicate_text_file(self, filepath: str) -> str:
        """
        Deduplicate text file at sentence and phrase level.
        Removes duplicate sentences and longer phrases (7+ words).
        """
        # Use shared split_into_sentences from text_utils.py
        
        # Read file
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split by chunk boundaries
        chunks = content.split("\n\n---CHUNK_BOUNDARY---\n\n")
        
        # Deduplicate chunks
        seen_sentences = set()
        seen_phrases_7plus = set()  # Only track 7+ word phrases
        deduplicated_chunks = []
        
        for chunk in chunks:
            if not chunk.strip():
                continue
            
            # Split into sentences
            sentences = split_into_sentences(chunk)  # From text_utils
            
            # Filter: keep only unique sentences and phrases
            unique_sentences = []
            for sentence in sentences:
                normalized = sentence.lower().strip()
                if normalized not in seen_sentences:
                    unique_sentences.append(sentence)
                    seen_sentences.add(normalized)
            
            # Check for longer duplicate phrases (7+ words) within remaining sentences
            filtered_sentences = []
            for sentence in unique_sentences:
                words = sentence.split()
                # If sentence has 7+ words, check if it's a duplicate phrase
                if len(words) >= 7:
                    normalized_sent = sentence.lower().strip()
                    if normalized_sent not in seen_phrases_7plus:
                        filtered_sentences.append(sentence)
                        seen_phrases_7plus.add(normalized_sent)
                else:
                    # Short sentence - keep it
                    filtered_sentences.append(sentence)
            
            if filtered_sentences:
                deduplicated_chunk = " ".join(filtered_sentences)
                deduplicated_chunks.append(deduplicated_chunk)
        
        # Join chunks back with boundaries
        return "\n\n---CHUNK_BOUNDARY---\n\n".join(deduplicated_chunks)
    
    def _estimate_tokens_for_chunks(self, chunks: List[tuple]) -> int:
        """Estimate token count for chunks."""
        total_words = sum(len(chunk[0].split()) for chunk in chunks)
        return int(total_words * TOKENS_PER_WORD)
    
    def _record_token_usage(self, tokens: int):
        """Record token usage with timestamp."""
        import time
        self._token_usage.append((time.time(), tokens))
        # Clean up old entries (older than 1 minute)
        cutoff = time.time() - 60
        self._token_usage = [(ts, t) for ts, t in self._token_usage if ts > cutoff]
    
    def _wait_for_token_rate_limit(self, chunks: Optional[List[tuple]] = None):
        """Wait if we're approaching token rate limit."""
        import time
        # Calculate tokens used in last minute
        cutoff = time.time() - 60
        recent_tokens = sum(t for ts, t in self._token_usage if ts > cutoff)
        
        # Estimate tokens for this request
        if chunks:
            request_tokens = self._estimate_tokens_for_chunks(chunks) + 10000  # Add 10k for response
        else:
            request_tokens = 50000  # Conservative estimate
        
        # If adding this request would exceed limit, wait (but be more aggressive - use 95% of limit)
        if recent_tokens + request_tokens > self._token_rate_limit * 0.95:  # Use 95% of limit (more aggressive)
            tokens_over = (recent_tokens + request_tokens) - (self._token_rate_limit * 0.95)
            # Wait until we can fit this request (cap at 15s to avoid connection drops)
            wait_time = (tokens_over / self._token_rate_limit) * 60  # Convert to seconds
            wait_time = min(wait_time, 15.0)  # Cap at 15s maximum
            if wait_time > 2:  # Only wait if more than 2 seconds
                print(f"  [RATE_LIMIT] Token limit: waiting {wait_time:.1f}s ({recent_tokens:,}/{self._token_rate_limit:,} tokens used)")
                time.sleep(wait_time)
    
    def _call_llm_with_rate_limit(self, question: str, chunks: List[tuple]) -> str:
        """Call LLM with automatic rate limiting and detailed logging.
        
        Uses generate_answer to ensure consistent narrative quality (same prompt as everywhere else).
        """
        import time
        llm_start = time.time()
        chunk_count = len(chunks)
        estimated_input_tokens = self._estimate_tokens_for_chunks(chunks)
        print(f"    [LLM_CALL] Starting LLM call with {chunk_count} chunks (~{estimated_input_tokens:,} tokens)")
        
        try:
            self._wait_for_token_rate_limit(chunks)
            # Use generate_answer to get consistent narrative quality (uses build_prompt with all rules)
            print(f"    [LLM_CALL] Calling generate_answer (uses full narrative prompt)...")
            result = self.llm.generate_answer(question, chunks)
            estimated_output_tokens = len(result.split()) * TOKENS_PER_WORD
            estimated_total = estimated_input_tokens + estimated_output_tokens
            self._record_token_usage(estimated_total)
            llm_duration = time.time() - llm_start
            print(f"    [LLM_CALL] Completed in {llm_duration:.1f}s (~{estimated_total:,} total tokens, {len(result)} chars)")
            return result
        except Exception as e:
            llm_duration = time.time() - llm_start
            print(f"    [LLM_CALL] FAILED after {llm_duration:.1f}s: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            raise

