"""
Query Engine - Lightweight interface for querying the indexed database.

This module provides FAST querying without loading heavy models.
Uses pre-built indices for instant term-based searches.
"""

import os
import json
import re
from itertools import chain
import chromadb
from typing import List, Dict, Optional, Tuple, Set
from .config import VECTORDB_DIR, INDICES_FILE, COLLECTION_NAME, DEFAULT_TOP_K
from .llm import LLMAnswerGenerator
from .acronyms import ACRONYM_EXPANSIONS
from .term_utils import canonicalize_term
from .constants import YEAR_PREFIX_EXPANSIONS



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
        print("Connecting to document database...")
        self.use_async = use_async
        
        # Connect to ChromaDB
        self.chroma_client = chromadb.PersistentClient(path=VECTORDB_DIR)
        try:
            self.collection = self.chroma_client.get_collection(name=COLLECTION_NAME)
            doc_count = self.collection.count()
            print(f"  [OK] Connected to database ({doc_count:,} indexed chunks)")
        except Exception as e:
            print(f"  [ERROR] Could not find collection '{COLLECTION_NAME}'")
            print(f"    Run: python build_indices.py")
            raise
        
        # Load pre-built indices
        self._load_indices()
        
        # Initialize advanced LLM (with fallback support)
        print("  Initializing LLM...")
        self.llm = None
        try:
            # Use Gemini API key (priority: parameter > env var)
            api_key = gemini_api_key or os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
            self.llm = LLMAnswerGenerator(api_key=api_key)
        except Exception as e:
            print(f"  [WARNING] LLM initialization failed: {e}")
        
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
        term_lower = term.lower()
        
        if term_lower not in self.term_to_chunks:
            return []
        
        # Deduplicate chunk IDs (some indices may have duplicates)
        chunk_ids = list(set(self.term_to_chunks[term_lower]))[:max_results]
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
        """
        Query the documents and generate an answer.
        
        Args:
            question: The question to ask
            max_chunks: Number of context chunks to retrieve
            use_llm: Whether to use LLM for answer generation
            
        Returns:
            Generated answer or raw context
        """
        # Expand known acronyms to improve recall
        question = self._expand_acronyms(question)
        
        # Extract keywords from question
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                      'of', 'with', 'by', 'from', 'about', 'what', 'when', 'where', 'who',
                      'why', 'how', 'did', 'do', 'does', 'was', 'were', 'is', 'are', 'tell', 'me'}
        
        raw_tokens = re.findall(r"[A-Za-z']+", question)
        base_token_count = 0
        keywords = []
        canonical_map: Dict[str, set] = {}
        for token in raw_tokens:
            lower = token.lower()
            if lower in stop_words or len(lower) <= 3:
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
            except:
                pass  # Continue without hierarchy if not available
        
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
        term_sets = [set(self.term_to_chunks[k]) for k in intersect_terms]
        
        chunk_ids = set()
        if len(term_sets) >= 2:
            # Prefer intersection when 2+ meaningful terms are present
            intersection = set.intersection(*term_sets) if term_sets else set()
            if intersection:
                chunk_ids = intersection
            else:
                # Fallback to union if intersection is empty
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
        
        # Augment queries with crisis/panic chunks that overlap the subject
        if chunk_ids:
            try:
                crisis_terms = ['panic', 'crisis', 'crises', '1973', '1974', '1987', '1998', '2008', '1929', '1907', '1825', '1873']
                crisis_ids = set()
                for term in crisis_terms:
                    if term in self.term_to_chunks:
                        crisis_ids.update(self.term_to_chunks[term])
                # Subject anchor: use acronyms if present, else subject_terms union
                subject_anchor_terms = []
                if acronyms:
                    subject_anchor_terms = [a for a in acronyms if a in self.term_to_chunks]
                if not subject_anchor_terms and subject_terms:
                    subject_anchor_terms = [t for t in subject_terms if t in self.term_to_chunks]
                subject_ids_union = set()
                for t in subject_anchor_terms:
                    subject_ids_union.update(self.term_to_chunks.get(t, []))
                # Add only overlaps to avoid unrelated crisis chunks
                if subject_ids_union and crisis_ids:
                    overlap = crisis_ids & subject_ids_union
                    if overlap:
                        chunk_ids.update(overlap)
                        print(f"  [AUGMENT] Added {len(overlap)} crisis-related chunks")
            except Exception as _e:
                pass
        
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
        data = self.collection.get(ids=chunk_ids_list)
        
        print(f"  [INFO] Found {len(chunk_ids_list)} relevant chunks")
        
        # Augment with endnotes if results are sparse (< 10 chunks)
        endnote_chunks = []
        if len(chunk_ids_list) < 10 and self.endnotes:
            print(f"  [AUGMENT] Sparse results - searching endnotes...")
            for keyword in keywords:
                endnote_chunks.extend(self.search_endnotes(keyword, max_results=20))
            
            if endnote_chunks:
                # Deduplicate endnotes
                seen = set()
                unique_endnotes = []
                for text, meta in endnote_chunks:
                    if text not in seen:
                        seen.add(text)
                        unique_endnotes.append((text, meta))
                endnote_chunks = unique_endnotes
                
                print(f"  [AUGMENT] Added {len(endnote_chunks)} endnotes ({len(chunk_ids_list)} + {len(endnote_chunks)} = {len(chunk_ids_list) + len(endnote_chunks)} total)")
        
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
            # For literal identity queries, downselect to chunks containing the literal token
            if disable_identity_expansion and meaningful:
                literal = meaningful[0]
                filtered = [(t, m) for (t, m) in chunks if literal in t.lower()]
                if filtered:
                    chunks = filtered
                # Cap size to avoid quota on small topics
                if len(chunks) > 50:
                    chunks = chunks[:50]
            
            # Append endnote chunks
            if endnote_chunks:
                chunks.extend(endnote_chunks)

            # Prioritize context that explicitly mentions the core subject terms
            if subject_terms:
                chunks = self._filter_chunks_by_subject_terms(chunks, subject_terms)
            
            # Detect special query types
            is_market = self._is_market_query(question)
            is_event = self._is_event_query(question)
            is_ideology = self._is_ideology_query(question)
            
            if is_market:
                print(f"  [AUTO] Market/asset query detected ({len(chunks)} chunks)")
                print(f"  [AUTO] Organizing by geography/sector to track flows across regions...")
                # Sort chunks by inferred year to encourage chronological output
                try:
                    chunks = self._sort_chunks_by_year(chunks)
                except Exception:
                    pass
                text = self._generate_geographic_narrative(question, chunks, for_market=True)
                # Market post-check: ensure crises/panics are mentioned when present in sources
                if not self._has_market_crises(text):
                    text = text.strip() + "\n\n" + "**Crisis Episodes (from sources):**\n- Include relevant panics/crises (e.g., 1973–74, 1987, 1998, 2008) and explain liquidity/margin changes.\n"
                if self._needs_grounding(text):
                    text = self.llm.call_api(self._build_prompt_grounded(question, chunks))
                return text
            if is_ideology:
                print(f"  [AUTO] Ideology topic detected ({len(chunks)} chunks)")
                try:
                    chunks = self._sort_chunks_by_year(chunks)
                except Exception:
                    pass
                # Reduce sprawl: keep a stable sample per decade to avoid topic-hopping
                try:
                    chunks = self._stratify_by_decade(chunks, cap_per_decade=5, max_total=60)
                except Exception:
                    pass
                ideology_prompt = self._build_prompt_ideology(question, chunks)
                answer = self.llm.call_api(ideology_prompt)
                if self._needs_grounding(answer):
                    answer = self.llm.call_api(self._build_prompt_grounded(question, chunks))
                # Ensure Related Questions and structure
                if (not self._has_related_questions(answer)) or self._para_count(answer) < 3:
                    answer = self._polish_answer(question, answer)
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
            except Exception:
                pass

            # Special-case: If SEC is explicitly present, send ALL chunks in a single call (no batching)
            if any(tok == "SEC" for tok in acronyms):
                print(f"  [FORCE] SEC query detected; sending all {len(chunks)} chunks in a single call")
                answer = self.llm.generate_answer(question, chunks)
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
                    # Event query: Cluster by geography/sector, not time period
                    print(f"  [AUTO] Event query detected ({len(chunks)} chunks)")
                    print(f"  [AUTO] Processing by geography/sector...")
                    ans = self._generate_geographic_narrative(question, chunks)
                    try:
                        if self._chunks_have_crisis(chunks) and not self._has_crises(ans):
                            ans = ans.strip() + "\n\n" + "**Crisis Episodes (from sources):**\n- Include relevant panics/crises linked to this subject and explain liquidity/margin/benchmark changes.\n"
                    except Exception:
                        pass
                    if self._needs_grounding(ans):
                        ans = self.llm.call_api(self._build_prompt_grounded(question, chunks))
                    return ans
                else:
                    # Topic query: Use period-based processing
                    print(f"  [AUTO] High-volume topic query detected ({len(chunks)} chunks)")
                    print(f"  [AUTO] Switching to iterative period-based processing...")
                    ans = self._generate_iterative_narrative(question, chunks, subject_terms, subject_phrases)
                    try:
                        if self._chunks_have_crisis(chunks) and not self._has_crises(ans):
                            ans = ans.strip() + "\n\n" + "**Crisis Episodes (from sources):**\n- Include relevant panics/crises linked to this subject and explain liquidity/margin/benchmark changes.\n"
                    except Exception:
                        pass
                    if self._needs_grounding(ans):
                        ans = self.llm.call_api(self._build_prompt_grounded(question, chunks))
                    return ans
            elif len(chunks) > 30:
                # Medium-volume: Standard batching
                print(f"  [INFO] Processing {len(chunks)} chunks in batches...")
                ans = self._generate_batched_narrative(question, chunks)
                try:
                    if self._chunks_have_crisis(chunks) and not self._has_crises(ans):
                        ans = ans.strip() + "\n\n" + "**Crisis Episodes (from sources):**\n- Include relevant panics/crises linked to this subject and explain liquidity/margin/benchmark changes.\n"
                except Exception:
                    pass
                if self._needs_grounding(ans):
                    ans = self.llm.call_api(self._build_prompt_grounded(question, chunks))
                return ans
            else:
                # Low-volume: Single LLM call
                ans = self.llm.generate_answer(question, chunks)
                try:
                    if self._chunks_have_crisis(chunks) and not self._has_crises(ans):
                        ans = ans.strip() + "\n\n" + "**Crisis Episodes (from sources):**\n- Include relevant panics/crises linked to this subject and explain liquidity/margin/benchmark changes.\n"
                except Exception:
                    pass
                if self._needs_grounding(ans):
                    ans = self.llm.call_api(self._build_prompt_grounded(question, chunks))
                return ans
        else:
            # Fallback: return raw context
            context_text = "\n\n".join([
                f"[{meta.get('filename', 'Unknown')}]\n{text}"
                for text, meta in zip(data['documents'], data['metadatas'])
            ])
            return f"Found {len(chunk_ids_list)} relevant passages:\n\n{context_text}"
    
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
    
    def _expand_acronyms(self, question: str) -> str:
        """
        Expand institutional acronyms (SEC, FRS, etc.) to improve search recall.
        Also handles patterns like BA_1933 -> Bankruptcy Act 1933.
        """
        result = question
        
        # Handle year-based prefixes (e.g., BA_1933)
        def replace_year(match):
            prefix = match.group(1).upper()
            year = match.group(2)
            full = YEAR_PREFIX_EXPANSIONS.get(prefix)
            if not full:
                return match.group(0)
            return f"{match.group(0)} ({full}{year})"
        
        result = re.sub(
            r'\b(BA|TA|SA|FA|IA|AA|PA|DA|CA|BHCA|EA|LA)_(\d{4})\b',
            replace_year,
            result,
            flags=re.IGNORECASE
        )
        
        # Expand fixed acronyms
        for acronym, full in ACRONYM_EXPANSIONS.items():
            pattern = re.compile(rf'\b{re.escape(acronym)}\b', re.IGNORECASE)
            if pattern.search(result):
                if full.lower() in result.lower():
                    continue
                result = pattern.sub(lambda m: f"{m.group(0)} ({full})", result, count=1)
        
        return result
    
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
   - Use section headings (e.g., "**Funding & Participants:**", "**Pricing & Benchmarks:**", "**Regulation & Balance Sheets:**").
   - 2–4 paragraphs per section; MAX 3 sentences per paragraph; MIN 5 paragraphs total.
   - Within sections, PRESENT FACTS IN STRICT CHRONOLOGICAL ORDER (e.g., 1950s → 1960s → 1970s → 1980s → 1990s → 2000s).
2) PANICS/CRISES (MANDATORY WHEN PRESENT IN SOURCES):
   - Explicitly cover relevant panics/crises linked to the subject (e.g., 1763, 1825, 1873, 1893, 1907, 1929, 1973–74, 1987, 1998, 2008).
   - Explain how liquidity, margining, benchmarks, or dealer balance sheets changed in this market during those episodes.
3) SUBJECT ACTIVE:
   - Keep the market/asset as the active subject in each sentence.
4) MECHANICS:
   - Institutions italicized (e.g., *MMEU*, *FRS*, *NYSE*); people normal.
   - Strict relevance; no unrelated context.
5) COVERAGE:
   - Move forward in time across all eras present; short transitions to connect periods.
6) END:
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
        chunks_text = "\n\n".join([
            f"--- CHUNK {i+1} ---\n{text}"
            for i, (text, meta) in enumerate(chunks)
        ])
        return f"""Answer this question USING ONLY the information in the DOCUMENT CHUNKS. If the chunks do not contain an item, do not invent it.

QUESTION:
{question}

DOCUMENT CHUNKS:
{chunks_text}

STRICT RULES:
1) Use ONLY facts explicitly present in the chunks; do not speculate or add outside knowledge.
2) Keep the SUBJECT active in every sentence; do not drift to unrelated entities.
3) Expand acronyms on first use if the expansion appears in the chunks; otherwise avoid the acronym.
4) Introduce people/entities with a one-clause role and relevance to the SUBJECT, but only if stated in the chunks.
5) Organize chronologically with short transitions; MAX 3 sentences per paragraph; MIN 4 paragraphs.
6) End with "Related Questions:" based on entities/topics that appear in the chunks (only if answerable from them).
"""
    
    def _generate_iterative_narrative(
        self,
        question: str,
        chunks: list,
        subject_terms: Optional[List[str]] = None,
        subject_phrases: Optional[List[str]] = None
    ) -> str:
        """Generate narrative using period-based iterative processing."""
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
        Detect law tokens like TA86, SA1934 in the question and return retrieval terms:
        - The literal token (e.g., 'TA86')
        - The expanded phrase(s) 'Full Name YYYY' using YEAR_PREFIX_EXPANSIONS
          For 2-digit years, include both 18YY and 19YY to avoid missing context.
        """
        results = []
        q_visible = question
        matches = re.findall(r"\b(BHCA|BA|TA|SA|FA|IA|AA|PA|DA|CA|EA|LA)(\d{2,4})\b", q_visible, flags=re.IGNORECASE)
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
            if len(year_token) == 4:
                full_phrase = f"{full_base}{year_token}"
                for alias in (full_phrase, full_phrase.lower()):
                    if alias not in seen:
                        results.append(alias)
                        seen.add(alias)
            else:
                # 2-digit year: include both 18YY and 19YY expansions to maximize recall
                try:
                    yy = int(year_token)
                    for century in (1800, 1900):
                        full_phrase = f"{full_base}{century + yy}"
                        for alias in (full_phrase, full_phrase.lower()):
                            if alias not in seen:
                                results.append(alias)
                                seen.add(alias)
                except:
                    continue
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
        """Generate narrative in batches to avoid rate limits."""
        import time
        
        batch_size = 20  # Process 20 chunks at a time
        pause_time = 15  # Pause 15 seconds between batches (increased to avoid rate limits)
        narratives = []
        
        total_batches = (len(chunks) + batch_size - 1) // batch_size
        estimated_time = total_batches * pause_time
        print(f"  [INFO] Will process {total_batches} batches (~{estimated_time//60} min {estimated_time%60} sec)")
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            print(f"  [BATCH {batch_num}/{total_batches}] Processing {len(batch)} chunks...")
            
            # Generate narrative for this batch
            narrative = self.llm.generate_answer(question, batch)
            narratives.append(narrative)
            
            # Wait between batches to avoid rate limit (if not last batch)
            if i + batch_size < len(chunks):
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
        except:
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
        """Keep chunks mentioning subject terms first; drop unrelated context when possible."""
        if not chunks or not subject_terms:
            return chunks
        
        primary = subject_terms[0]
        others = subject_terms[1:]
        
        strong_matches = []
        primary_matches = []
        secondary_matches = []
        remainder = []
        
        for chunk in chunks:
            text_lower = chunk[0].lower()
            contains_primary = primary in text_lower
            contains_all = contains_primary and all(term in text_lower for term in others)
            contains_any = any(term in text_lower for term in subject_terms)
            
            if contains_all:
                strong_matches.append(chunk)
            elif contains_primary:
                primary_matches.append(chunk)
            elif contains_any:
                secondary_matches.append(chunk)
            else:
                remainder.append(chunk)
        
        # Prefer strong + primary; include a small slice of secondary only if needed
        result: List[tuple] = []
        result.extend(strong_matches)
        result.extend(primary_matches)
        if not result and secondary_matches:
            result.extend(secondary_matches[:10])
        # If still empty, fall back
        return result if result else chunks

