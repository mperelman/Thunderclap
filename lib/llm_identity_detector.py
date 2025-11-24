"""
LLM-Based Identity Detector - Uses AI to classify banking family attributes.

More accurate and maintainable than regex patterns, with efficient caching.

Architecture:
1. Extract candidate names near identity keywords (simple regex)
2. Batch chunks and send to LLM for classification
3. Cache results by chunk hash (only reprocess changed chunks)
4. Allow selective re-runs per identity (prompt refinement)
"""

import os
import sys
import json
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Set, Optional
from collections import defaultdict
from dotenv import load_dotenv

# Fix module imports when run as script
if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()


class LLMIdentityDetector:
    """Detects banking family identities using LLM classification with intelligent caching."""
    
    # Prompt version - increment to invalidate cache when improving prompts
    PROMPT_VERSION = "v2"  # Fixed broken candidate extraction
    
    # Batch size for API calls (balance latency vs cost)
    BATCH_SIZE = 20
    
    # Rate limiting for free tier (15 requests/minute = 4 seconds per request)
    SECONDS_PER_REQUEST = 5  # Conservative (12 requests/minute)
    
    # Identities to detect (organized by type)
    IDENTITIES = {
        'religious': ['jewish', 'sephardi', 'ashkenazi', 'court_jew', 'quaker', 'huguenot', 
                     'mennonite', 'puritan', 'calvinist', 'presbyterian', 'catholic_irish',
                     'muslim', 'sunni', 'shia', 'parsee', 'hindu'],
        'ethnic': ['armenian', 'greek', 'lebanese', 'palestinian', 'basque', 
                  'hausa', 'yoruba', 'igbo', 'scottish', 'irish', 'welsh'],
        'racial': ['black', 'white'],
        'gender': ['female', 'male'],
        'geographic': ['american', 'british', 'french', 'german', 'nigerian', 'lebanese_diaspora']
    }
    
    def __init__(self, gemini_api_key: Optional[str] = None):
        """Initialize detector with API key."""
        from dotenv import load_dotenv
        load_dotenv()
        
        # Get API key
        if gemini_api_key:
            self.api_key = gemini_api_key
        else:
            self.api_key = os.getenv('GEMINI_API_KEY')
        
        if not self.api_key:
            raise ValueError("No API key found. Set GEMINI_API_KEY in .env")
        
        # Initialize Gemini
        import google.generativeai as genai
        self.genai = genai
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Cache file
        self.cache_file = Path('data/llm_identity_cache.json')
        self.cache = self._load_cache()
        
        print(f"[INIT] LLM Identity Detector")
        print(f"  Prompt version: {self.PROMPT_VERSION}")
        print(f"  Cached chunks: {len(self.cache)}")
    
    def _load_cache(self) -> Dict:
        """Load cached identity classifications."""
        if self.cache_file.exists():
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_cache(self):
        """Save cache to disk."""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, indent=2, ensure_ascii=False)
    
    def _hash_chunk(self, chunk: str) -> str:
        """Generate stable hash for chunk text."""
        return hashlib.md5(chunk.encode('utf-8')).hexdigest()
    
    def _has_identity_keywords(self, chunk: str) -> bool:
        """
        Fast check if chunk has ANY identity keywords using pre-filter.
        
        Returns:
            True if chunk contains identity keywords (worth sending to LLM)
        """
        from lib.identity_prefilter import IdentityPrefilter
        
        if not hasattr(self, '_prefilter'):
            self._prefilter = IdentityPrefilter()
        
        return self._prefilter.has_identity_keywords(chunk)
    
    def _build_batch_prompt(self, chunks_data: List[Dict]) -> str:
        """Build prompt for BATCH of chunks - more efficient!"""
        
        prompt = """You are a banking historian extracting identity attributes from MULTIPLE text excerpts.

TASK: For EACH surname in EACH chunk, list ALL identity attributes explicitly stated.

IDENTITY CATEGORIES - Extract the MOST SPECIFIC term available:

Religion (BE SPECIFIC):
- Muslim subgroups: sunni, shia, alawite, ismaili, druze, ahmadi
- Christian subgroups: maronite, coptic, orthodox, greek_orthodox, melkite, nestorian, catholic, protestant
- Jewish subgroups: sephardi, ashkenazi, mizrahi, court_jew, kohanim
- Other: hindu, parsee, zoroastrian, buddhist
- Denominations: quaker, huguenot, mennonite, puritan, calvinist, presbyterian

Ethnicity (BE SPECIFIC):
- Levantine: lebanese, syrian, palestinian, jordanian, alawite
- African: hausa, yoruba, igbo, fulani, akan, zulu (NOT generic 'african')
- European: basque, german, french, scottish, irish, welsh, greek, armenian
- Asian: chinese, korean, japanese, indian
- Latin American: mexican, cuban, puerto_rican, colombian, brazilian

Race: black, white (only if explicit)

Gender: female, male (only if explicit, include titles: queen, princess)

Status: converted, royal, aristocrat

Geography: Where born/operated (american, british, russian, nigerian, saudi, etc.)

IMPORTANT: Return SPECIFIC terms (sunni NOT muslim, maronite NOT christian, hausa NOT african).
The system will automatically group them for general searches.

Also extract ANY OTHER identity attributes mentioned, even if not in above list (e.g., druze, coptic, ismaili).

RULES (COMPREHENSIVE - Option A):
1. Include ALL explicitly stated attributes: origin, ancestry, conversion, current state, geography
2. Multi-generational: "converted Jewish Hambro" → ["jewish", "converted", "christian"]
3. Ancestry: "descended from Sephardi" → ["sephardi"]
4. Self-ID: "identified as Hispanic" → ["hispanic", "latino"]
5. Geography: "German Knopp active in Russia" → ["german", "russian"]
6. Multiple attributes OK: Sursock = ["greek_orthodox", "lebanese"]

EXAMPLES:
- "Jewish Rothschild" → {"rothschild": ["jewish"]}
- "converted Jewish Hambro married Anglican Smyth" → {"hambro": ["jewish", "converted", "christian"], "smyth": ["anglican"]}
- "Martin Chavez descended from Sephardi, mother of Basque descent, identified as Hispanic" → {"chavez": ["sephardi", "basque", "hispanic", "latino"]}
- "Greek Orthodox Sursock" in Lebanese context → {"sursock": ["greek_orthodox", "lebanese"]}

---

"""
        # Add each chunk (FULL TEXT, don't truncate!)
        for i, chunk_data in enumerate(chunks_data):
            prompt += f"\n**CHUNK {i+1}:**\n{chunk_data['text']}\n"
        
        prompt += """
---

ANSWER (JSON format, one entry per chunk):
{
  "chunk_1": {"surname1": ["attr1", "attr2"], "surname2": ["attr1"]},
  "chunk_2": {"surname1": ["attr1"]}
}
"""
        return prompt
    
    def _classify_batch_with_llm(self, chunks_data: List[Dict]) -> Dict[str, Dict[str, List[str]]]:
        """
        Use LLM to classify identities for BATCH of chunks.
        Tries ALL available API keys in sequence before giving up.
        
        Returns:
            {chunk_hash: {surname: [identities]}}
        """
        if not chunks_data:
            return {}
        
        prompt = self._build_batch_prompt(chunks_data)
        
        # Make API call with single key
        try:
            response = self.model.generate_content(prompt)
            result = response.text.strip()
            
            # Parse JSON response
            if '```json' in result:
                result = result.split('```json')[1].split('```')[0].strip()
            elif '```' in result:
                result = result.split('```')[1].split('```')[0].strip()
            
            batch_results = json.loads(result)
            
            # Map chunk_N back to chunk_hash
            parsed = {}
            for i, chunk_data in enumerate(chunks_data):
                chunk_key = f"chunk_{i+1}"
                if chunk_key in batch_results:
                    parsed[chunk_data['hash']] = batch_results[chunk_key]
            
            print(f"  [SUCCESS] Processed {len(chunks_data)} chunks")
            return parsed
        
        except Exception as e:
            error_str = str(e)
            
            # Check for quota exhaustion
            if '429' in error_str or 'quota' in error_str.lower():
                print(f"  [QUOTA] API quota exceeded")
                return {}
            else:
                # Non-quota error (parsing, network, etc)
                print(f"  [ERROR] {error_str[:150]}")
                return {}
    
    def detect_from_chunks(
        self, 
        chunks: List[str],
        identities_to_process: Optional[List[str]] = None,
        force_rerun: bool = False
    ) -> Dict:
        """
        Detect identities from chunks using LLM with intelligent caching.
        
        Args:
            chunks: Document chunks to process
            identities_to_process: Specific identities to detect (None = all)
            force_rerun: Ignore cache and reprocess everything
        
        Returns:
            Detection results by identity
        """
        print(f"\nProcessing {len(chunks)} chunks with LLM detection...")
        print(f"  Batch size: {self.BATCH_SIZE} chunks per API call")
        print(f"  Force rerun: {force_rerun}")
        
        # Flatten identity list
        all_identities = []
        for category, ids in self.IDENTITIES.items():
            all_identities.extend(ids)
        
        if identities_to_process:
            all_identities = [i for i in all_identities if i in identities_to_process]
            print(f"  Processing only: {', '.join(identities_to_process)}")
        
        # Track processing
        total_api_calls = 0
        cache_hits = 0
        new_chunks = 0
        start_time = time.time()
        
        # Batch process chunks (more efficient!)
        chunks_to_process = []
        
        for i, chunk in enumerate(chunks):
            chunk_hash = self._hash_chunk(chunk)
            
            # Check cache
            if not force_rerun and chunk_hash in self.cache:
                cached = self.cache[chunk_hash]
                if cached.get('prompt_version') == self.PROMPT_VERSION:
                    cache_hits += 1
                    continue  # Use cached result
            
            # Check if chunk has identity keywords (fast regex pre-filter)
            has_identities = self._has_identity_keywords(chunk)
            
            if not has_identities:
                # No identity keywords in chunk - cache empty result
                self.cache[chunk_hash] = {
                    'text_preview': chunk[:100],
                    'identities': {},
                    'prompt_version': self.PROMPT_VERSION
                }
                continue
            
            # Add to batch (LLM will extract surnames)
            chunks_to_process.append({
                'hash': chunk_hash,
                'text': chunk
            })
            new_chunks += 1
            
            # Process batch when full or at end
            if len(chunks_to_process) >= self.BATCH_SIZE or i == len(chunks) - 1:
                if chunks_to_process:
                    # ONE API call for entire batch
                    batch_results = self._classify_batch_with_llm(chunks_to_process)
                    total_api_calls += 1
                    
                    # Cache all results from batch
                    for chunk_data in chunks_to_process:
                        chunk_hash = chunk_data['hash']
                        surname_to_identities = batch_results.get(chunk_hash, {})
                        
                        # Invert: convert {surname: [identities]} to {identity: [surnames]}
                        chunk_identities = defaultdict(list)
                        for surname, identity_list in surname_to_identities.items():
                            for identity in identity_list:
                                chunk_identities[identity].append(surname.lower())
                        
                        # Cache result
                        self.cache[chunk_hash] = {
                            'text_preview': chunk_data['text'][:100],
                            'identities': dict(chunk_identities),
                            'prompt_version': self.PROMPT_VERSION
                        }
                    
                    # Rate limiting between batches
                    time.sleep(self.SECONDS_PER_REQUEST)
                    
                    # Progress report
                    elapsed = time.time() - start_time
                    remaining_batches = (len(chunks) - (i + 1)) / self.BATCH_SIZE
                    eta_minutes = (remaining_batches * self.SECONDS_PER_REQUEST) / 60
                    print(f"  Processed {i+1}/{len(chunks)} chunks ({total_api_calls} API calls, ETA: {eta_minutes:.1f} min)")
                    
                    # Save cache
                    if total_api_calls % 5 == 0:  # Every 5 batches
                        self._save_cache()
                        print(f"  [CACHE] Saved {len(self.cache)} entries")
                    
                    # Clear batch
                    chunks_to_process = []
        
        # Final cache save
        self._save_cache()
        
        print(f"\n[COMPLETE]")
        print(f"  Total chunks: {len(chunks)}")
        print(f"  Cache hits: {cache_hits}")
        print(f"  New chunks processed: {new_chunks}")
        print(f"  API calls made: {total_api_calls}")
        
        # Aggregate results
        return self._aggregate_results()
    
    def _aggregate_results(self) -> Dict:
        """Aggregate cached results into final identity->families mapping."""
        aggregated = defaultdict(lambda: defaultdict(int))
        
        for chunk_hash, data in self.cache.items():
            for identity, surnames in data.get('identities', {}).items():
                for surname in surnames:
                    aggregated[identity][surname] += 1
        
        # Format results
        results = {
            'identities': {},
            'statistics': {
                'cached_chunks': len(self.cache),
                'prompt_version': self.PROMPT_VERSION
            }
        }
        
        for identity, surname_counts in aggregated.items():
            # Sort by frequency
            sorted_families = sorted(surname_counts.items(), key=lambda x: x[1], reverse=True)
            
            results['identities'][identity] = {
                'families': [f[0] for f in sorted_families],
                'counts': dict(sorted_families),
                'type': 'llm_detected'
            }
        
        return results


def detect_identities_from_index(
    identities_to_process: Optional[List[str]] = None,
    force_rerun: bool = False,
    save_results: bool = True
) -> Dict:
    """
    Convenience function - detect identities from indexed chunks.
    
    Args:
        identities_to_process: Specific identities (None = all)
        force_rerun: Ignore cache and reprocess
        save_results: Save to detected_identities.json
    
    Returns:
        Detection results
    """
    # Load chunks from cache files
    from lib.document_parser import load_all_documents
    from lib.index_builder import split_into_chunks
    
    # Load all documents
    documents = load_all_documents(use_cache=True)
    
    all_chunks = []
    for doc in documents:
        doc_chunks = split_into_chunks(doc['text'])
        all_chunks.extend(doc_chunks)
    
    chunks = all_chunks
    print(f"Loaded {len(chunks)} chunks from {len(documents)} documents")
    
    # Run detection
    detector = LLMIdentityDetector()
    results = detector.detect_from_chunks(
        chunks,
        identities_to_process=identities_to_process,
        force_rerun=force_rerun
    )
    
    if save_results:
        output_file = Path('data/detected_identities.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n[SAVED] Results saved to {output_file}")
    
    return results, detector


if __name__ == '__main__':
    import sys
    
    # Command line args
    force = '--force' in sys.argv
    identity = None
    if '--identity' in sys.argv:
        idx = sys.argv.index('--identity')
        if idx + 1 < len(sys.argv):
            identity = sys.argv[idx + 1]
    
    identities_to_process = [identity] if identity else None
    
    # Run detection
    results, detector = detect_identities_from_index(
        identities_to_process=identities_to_process,
        force_rerun=force,
        save_results=True
    )
    
    # Display results
    print("\n" + "="*80)
    print("LLM IDENTITY DETECTION RESULTS")
    print("="*80)
    
    for identity, data in results['identities'].items():
        families = data['families'][:15]  # Top 15
        print(f"\n{identity.upper()}:")
        for fam in families:
            count = data['counts'][fam]
            print(f"  {fam} ({count} mentions)")
    
    print(f"\n[STATS]")
    print(f"  Cached chunks: {results['statistics']['cached_chunks']}")
    print(f"  Prompt version: {results['statistics']['prompt_version']}")

