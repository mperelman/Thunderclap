"""
Batch API Identity Detector - Uses Gemini Batch API for efficient processing.

Advantages over interactive API:
- 50% cost reduction
- Different quota pool (no RPM/RPD exhaustion)
- Process all 1,500 chunks in one submission
- Async processing (submit and check back)

Workflow:
1. Create JSONL file with all chunk requests
2. Upload file to Gemini File API
3. Submit batch job
4. Poll for completion
5. Download and parse results
6. Cache results by chunk hash
"""

import os
import sys
import json
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict
from dotenv import load_dotenv

# Fix module imports when run as script
if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()


class BatchIdentityDetector:
    """Detects banking family identities using Gemini Batch API."""
    
    PROMPT_VERSION = "v1"
    
    # Identities to detect
    IDENTITIES = {
        'religious': ['jewish', 'sephardi', 'ashkenazi', 'court_jew', 'quaker', 'huguenot', 
                     'mennonite', 'puritan', 'calvinist', 'presbyterian', 'catholic_irish',
                     'muslim', 'sunni', 'shia', 'alawite', 'ismaili', 'druze', 'maronite',
                     'coptic', 'greek_orthodox', 'melkite', 'parsee', 'hindu'],
        'ethnic': ['armenian', 'greek', 'lebanese', 'syrian', 'palestinian', 'basque', 
                  'hausa', 'yoruba', 'igbo', 'fulani', 'akan', 'zulu',
                  'scottish', 'irish', 'welsh', 'overseas_chinese'],
        'racial': ['black', 'white'],
        'gender': ['female', 'male', 'queen', 'princess', 'lady'],
        'geographic': ['lebanese', 'palestinian', 'nigerian', 'ghanaian', 'kenyan', 
                      'south_african', 'mexican', 'cuban', 'puerto_rican'],
    }
    
    def __init__(self, gemini_api_key: Optional[str] = None):
        """Initialize batch detector."""
        from lib.api_key_manager import APIKeyManager
        
        # Get API key
        if gemini_api_key:
            self.api_key = gemini_api_key
        else:
            km = APIKeyManager()
            self.api_key = km.get_current_key()
        
        # Initialize Gemini Batch API
        from google import genai
        self.genai = genai
        self.client = genai.Client(api_key=self.api_key)
        
        # Cache
        self.cache_file = Path('data/llm_identity_cache.json')
        self.cache = self._load_cache()
        
        print("[INIT] Batch Identity Detector")
        print(f"  Mode: Gemini Batch API (50% cost reduction)")
        print(f"  Cached chunks: {len(self.cache)}")
    
    def _load_cache(self) -> Dict:
        """Load cached results."""
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
        """Generate stable hash for chunk."""
        return hashlib.md5(chunk.encode('utf-8')).hexdigest()
    
    def _build_prompt_for_chunk(self, chunk: str) -> str:
        """Build classification prompt for a single chunk."""
        
        prompt = """You are a banking historian extracting identity attributes from text.

TASK: For EACH surname mentioned, list ALL identity attributes explicitly stated.

IDENTITY CATEGORIES - Extract the MOST SPECIFIC term:

Religion (BE SPECIFIC):
- Muslim: sunni, shia, alawite, ismaili, druze, ahmadi
- Christian: maronite, coptic, orthodox, greek_orthodox, melkite, catholic, protestant, anglican, quaker, huguenot, mennonite, puritan, calvinist, presbyterian
- Jewish: sephardi, ashkenazi, mizrahi, court_jew, kohanim
- Other: hindu, parsee, zoroastrian, buddhist

Ethnicity (BE SPECIFIC):
- Levantine: lebanese, syrian, palestinian, jordanian
- African: hausa, yoruba, igbo, fulani, akan, zulu (NOT generic 'african')
- European: basque, german, french, scottish, irish, welsh, greek, armenian
- Asian: chinese, korean, japanese, indian
- Latin American: mexican, cuban, puerto_rican, hispanic, latino

Race: black, white (only if explicit)

Gender: female, male, queen, princess, lady (only if explicit)

Status: converted, royal, aristocrat

Geography: Where born/operated (american, british, nigerian, lebanese, etc.)

RULES:
1. Extract ALL explicitly stated attributes: origin, ancestry, conversion, current state
2. Multi-generational: "converted Jewish Hambro" → ["jewish", "converted", "christian"]
3. Ancestry: "descended from Sephardi" → ["sephardi"]
4. Self-ID: "identified as Hispanic" → ["hispanic", "latino"]
5. Geography: "German banker active in Russia" → ["german", "russian"]
6. Multiple attributes OK: Sursock = ["greek_orthodox", "lebanese"]
7. Return SPECIFIC terms (sunni NOT muslim, maronite NOT christian)

EXAMPLES:
- "Jewish Rothschild" → {"rothschild": ["jewish"]}
- "converted Jewish Hambro" → {"hambro": ["jewish", "converted", "christian"]}
- "Sephardi Chavez, mother of Basque descent, identified as Hispanic" → {"chavez": ["sephardi", "basque", "hispanic", "latino"]}
- "Greek Orthodox Sursock" in Lebanese context → {"sursock": ["greek_orthodox", "lebanese"]}

---

TEXT:
"""
        prompt += chunk
        
        prompt += """

---

ANSWER (JSON format):
{
  "surname1": ["attr1", "attr2"],
  "surname2": ["attr1"]
}
"""
        return prompt
    
    def _create_batch_requests_file(self, chunks: List[str], output_path: Path) -> int:
        """
        Create JSONL file with batch requests.
        
        Returns:
            Number of requests created (chunks not in cache)
        """
        print("\nCreating batch requests file...")
        
        requests_created = 0
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, chunk in enumerate(chunks):
                chunk_hash = self._hash_chunk(chunk)
                
                # Check cache
                if chunk_hash in self.cache:
                    cached = self.cache[chunk_hash]
                    if cached.get('prompt_version') == self.PROMPT_VERSION:
                        continue  # Skip cached chunks
                
                # Create request for this chunk
                prompt = self._build_prompt_for_chunk(chunk)
                
                request = {
                    "key": chunk_hash,  # Use hash as key for matching response
                    "request": {
                        "contents": [{
                            "parts": [{"text": prompt}],
                            "role": "user"
                        }],
                        "generation_config": {
                            "temperature": 0.3,  # Lower for consistency
                            "response_mime_type": "application/json"
                        }
                    }
                }
                
                f.write(json.dumps(request) + '\n')
                requests_created += 1
                
                if (i + 1) % 100 == 0:
                    print(f"  Processed {i + 1}/{len(chunks)} chunks...")
        
        print(f"  [OK] Created {requests_created} batch requests")
        print(f"  [CACHE] Skipped {len(chunks) - requests_created} cached chunks")
        
        return requests_created
    
    def submit_batch_job(self, chunks: List[str], job_name: str = "identity-detection") -> Optional[str]:
        """
        Submit batch job to Gemini.
        
        Returns:
            Batch job name (for polling status)
        """
        print("\n=== SUBMITTING BATCH JOB ===\n")
        
        # Create requests file
        requests_file = Path('temp/batch_requests.jsonl')
        requests_file.parent.mkdir(exist_ok=True)
        
        num_requests = self._create_batch_requests_file(chunks, requests_file)
        
        if num_requests == 0:
            print("  [SKIP] All chunks already cached!")
            return None
        
        # Upload file to Gemini
        print("\nUploading requests file to Gemini...")
        try:
            uploaded_file = self.client.files.upload(
                file=str(requests_file),
                config={'display_name': f'{job_name}-requests', 'mime_type': 'application/json'}
            )
            print(f"  [OK] Uploaded: {uploaded_file.name}")
        except Exception as e:
            print(f"  [ERROR] Upload failed: {e}")
            return None
        
        # Submit batch job
        print("\nSubmitting batch job...")
        try:
            batch_job = self.client.batches.create(
                model="models/gemini-2.5-flash",  # Use full model path
                src=uploaded_file.name,
                config={'display_name': job_name}
            )
            
            print(f"  [SUCCESS] Batch job submitted!")
            print(f"  Job name: {batch_job.name}")
            print(f"  State: {batch_job.state.name}")
            print(f"  Requests: {num_requests}")
            print(f"\nTarget completion: < 24 hours (often much faster)")
            print(f"Cost: 50% of standard API pricing")
            
            # Save job info
            job_info = {
                'job_name': batch_job.name,
                'state': batch_job.state.name,
                'num_requests': num_requests,
                'submitted_at': time.time()
            }
            
            job_info_file = Path('temp/batch_job_info.json')
            with open(job_info_file, 'w') as f:
                json.dump(job_info, f, indent=2)
            
            print(f"\n[SAVED] Job info: {job_info_file}")
            
            return batch_job.name
        
        except Exception as e:
            print(f"  [ERROR] Batch submission failed: {e}")
            return None
    
    def check_job_status(self, job_name: str) -> Dict:
        """Check status of batch job."""
        try:
            batch_job = self.client.batches.get(name=job_name)
            
            status = {
                'job_name': job_name,
                'state': batch_job.state.name,
                'completed': batch_job.state.name in [
                    'JOB_STATE_SUCCEEDED', 
                    'JOB_STATE_FAILED', 
                    'JOB_STATE_CANCELLED', 
                    'JOB_STATE_EXPIRED'
                ]
            }
            
            if hasattr(batch_job, 'batch_stats'):
                status['stats'] = {
                    'total': batch_job.batch_stats.total_request_count,
                    'succeeded': batch_job.batch_stats.succeeded_request_count,
                    'failed': batch_job.batch_stats.failed_request_count
                }
            
            return status
        
        except Exception as e:
            return {'error': str(e)}
    
    def poll_until_complete(self, job_name: str, poll_interval: int = 60) -> bool:
        """
        Poll job status until completion.
        
        Args:
            job_name: Batch job name
            poll_interval: Seconds between polls (default 60)
        
        Returns:
            True if succeeded, False otherwise
        """
        print(f"\n=== POLLING JOB STATUS ===")
        print(f"Job: {job_name}")
        print(f"Poll interval: {poll_interval}s\n")
        
        while True:
            status = self.check_job_status(job_name)
            
            if 'error' in status:
                print(f"[ERROR] {status['error']}")
                return False
            
            state = status['state']
            print(f"[{time.strftime('%H:%M:%S')}] State: {state}")
            
            if 'stats' in status:
                stats = status['stats']
                print(f"  Total: {stats['total']}, Succeeded: {stats['succeeded']}, Failed: {stats['failed']}")
            
            if status['completed']:
                if state == 'JOB_STATE_SUCCEEDED':
                    print("\n[SUCCESS] Job completed!")
                    return True
                else:
                    print(f"\n[FAILED] Job ended with state: {state}")
                    return False
            
            time.sleep(poll_interval)
    
    def retrieve_results(self, job_name: str) -> bool:
        """
        Retrieve and cache batch job results.
        
        Returns:
            True if successful
        """
        print(f"\n=== RETRIEVING RESULTS ===\n")
        
        try:
            batch_job = self.client.batches.get(name=job_name)
            
            if batch_job.state.name != 'JOB_STATE_SUCCEEDED':
                print(f"[ERROR] Job not successful: {batch_job.state.name}")
                return False
            
            # Download results file
            if not batch_job.dest or not batch_job.dest.file_name:
                print("[ERROR] No results file found")
                return False
            
            result_file_name = batch_job.dest.file_name
            print(f"Downloading results from: {result_file_name}")
            
            file_content = self.client.files.download(file=result_file_name)
            
            # Parse JSONL results
            results_text = file_content.decode('utf-8')
            lines = results_text.strip().split('\n')
            
            print(f"  [OK] Downloaded {len(lines)} result lines\n")
            
            # Process each result
            processed = 0
            errors = 0
            
            for line in lines:
                try:
                    result = json.loads(line)
                    
                    # Get chunk hash (key)
                    chunk_hash = result.get('key')
                    if not chunk_hash:
                        continue
                    
                    # Check for error
                    if 'error' in result:
                        print(f"  [ERROR] Chunk {chunk_hash[:8]}: {result['error']}")
                        errors += 1
                        continue
                    
                    # Parse response
                    if 'response' not in result:
                        continue
                    
                    response = result['response']
                    
                    # Extract text and parse JSON
                    if 'candidates' in response and response['candidates']:
                        candidate = response['candidates'][0]
                        if 'content' in candidate and 'parts' in candidate['content']:
                            parts = candidate['content']['parts']
                            if parts and 'text' in parts[0]:
                                text = parts[0]['text'].strip()
                                
                                # Parse JSON response
                                if '```json' in text:
                                    text = text.split('```json')[1].split('```')[0].strip()
                                elif '```' in text:
                                    text = text.split('```')[1].split('```')[0].strip()
                                
                                surname_to_identities = json.loads(text)
                                
                                # Invert: {surname: [identities]} -> {identity: [surnames]}
                                chunk_identities = defaultdict(list)
                                for surname, identity_list in surname_to_identities.items():
                                    for identity in identity_list:
                                        chunk_identities[identity].append(surname.lower())
                                
                                # Cache result
                                self.cache[chunk_hash] = {
                                    'identities': dict(chunk_identities),
                                    'prompt_version': self.PROMPT_VERSION
                                }
                                
                                processed += 1
                
                except Exception as e:
                    print(f"  [WARNING] Failed to parse result: {e}")
                    errors += 1
            
            # Save cache
            self._save_cache()
            
            print(f"\n[COMPLETE]")
            print(f"  Processed: {processed}")
            print(f"  Errors: {errors}")
            print(f"  Cached entries: {len(self.cache)}")
            
            return True
        
        except Exception as e:
            print(f"[ERROR] Failed to retrieve results: {e}")
            return False
    
    def _aggregate_results(self) -> Dict:
        """Aggregate cached results into final identity->families mapping."""
        aggregated = defaultdict(lambda: defaultdict(int))
        
        for chunk_hash, data in self.cache.items():
            for identity, surnames in data.get('identities', {}).items():
                for surname in surnames:
                    aggregated[identity][surname.lower()] += 1
        
        return dict(aggregated)
    
    def get_results(self) -> Dict:
        """Get aggregated detection results."""
        return {
            'identities': self._aggregate_results(),
            'total_chunks_cached': len(self.cache),
            'prompt_version': self.PROMPT_VERSION
        }


def detect_identities_batch(chunks: List[str], job_name: str = "identity-detection") -> Optional[str]:
    """
    Submit batch job for identity detection.
    
    Returns:
        Batch job name for polling
    """
    detector = BatchIdentityDetector()
    return detector.submit_batch_job(chunks, job_name)


def check_batch_status(job_name: str):
    """Check status of a batch job."""
    detector = BatchIdentityDetector()
    status = detector.check_job_status(job_name)
    
    print(f"\nJob: {job_name}")
    print(f"State: {status.get('state', 'UNKNOWN')}")
    
    if 'stats' in status:
        stats = status['stats']
        print(f"Progress: {stats['succeeded']}/{stats['total']} succeeded, {stats['failed']} failed")
    
    if status.get('completed'):
        print("\n[COMPLETE] Job finished!")
    else:
        print("\n[PENDING] Job still processing...")


def retrieve_batch_results(job_name: str):
    """Retrieve and cache results from completed batch job."""
    detector = BatchIdentityDetector()
    
    if detector.retrieve_results(job_name):
        # Show aggregated results
        results = detector.get_results()
        
        print("\n=== DETECTION SUMMARY ===\n")
        
        identities = results['identities']
        for identity in sorted(identities.keys()):
            families = identities[identity]
            print(f"{identity}: {len(families)} families")
        
        print(f"\nTotal chunks cached: {results['total_chunks_cached']}")


if __name__ == '__main__':
    print("Batch Identity Detector - Command Line Interface\n")
    print("Usage:")
    print("  1. Submit job: python lib/batch_identity_detector.py submit")
    print("  2. Check status: python lib/batch_identity_detector.py status <job_name>")
    print("  3. Get results: python lib/batch_identity_detector.py results <job_name>")
    print()
    
    if len(sys.argv) < 2:
        print("Please specify command: submit, status, or results")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'submit':
        # Load chunks from index
        from lib.index_builder import load_documents, split_into_chunks
        
        docs = load_documents('data/processed_documents.json')
        chunks = []
        for doc in docs:
            chunks.extend(split_into_chunks(doc['text']))
        
        job_name = detect_identities_batch(chunks)
        
        if job_name:
            print(f"\n[NEXT] Check status with:")
            print(f"  python lib/batch_identity_detector.py status {job_name}")
    
    elif command == 'status':
        if len(sys.argv) < 3:
            print("Please provide job name")
            sys.exit(1)
        
        check_batch_status(sys.argv[2])
    
    elif command == 'results':
        if len(sys.argv) < 3:
            print("Please provide job name")
            sys.exit(1)
        
        retrieve_batch_results(sys.argv[2])
    
    else:
        print(f"Unknown command: {command}")
        print("Valid commands: submit, status, results")

