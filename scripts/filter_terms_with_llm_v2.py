"""
Filter indexed terms using LLM (centralized config via lib/llm.py).
Batches conservatively to respect free tier token limits.
"""
import sys
import os
sys.path.insert(0, '.')

import json
import time
from tqdm import tqdm
from lib.llm import LLMAnswerGenerator

print("="*80)
print("FILTERING INDEXED TERMS WITH LLM")
print("="*80)
print()

# Load current index
print("1. Loading current index...")
from lib.config import INDICES_FILE
with open(INDICES_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

terms = list(data.get('term_to_chunks', {}).keys())
print(f"   Total terms in index: {len(terms)}")
print()

# Test LLM initialization
print("2. Testing LLM...")
test_llm = LLMAnswerGenerator()
if not test_llm.client:
    print("ERROR: LLM initialization failed!")
    sys.exit(1)
print()

# Filter terms in batches (250 terms = smaller output to avoid token limit truncation)
BATCH_SIZE = 250
num_batches = (len(terms) + BATCH_SIZE - 1) // BATCH_SIZE

print(f"3. Filtering terms with LLM...")
print(f"   Batching: {num_batches} batches of {BATCH_SIZE} terms each")
print(f"   Rate limit: 15 requests/minute (5 seconds between batches)")
print(f"   Estimated time: ~{num_batches * 5 / 60:.1f} minutes")
print(f"   Progress will be shown for each batch")
print()

filtered_terms = []

progress_bar = tqdm(range(0, len(terms), BATCH_SIZE), desc="Filtering batches", unit="batch")
for i in progress_bar:
    batch = terms[i:i+BATCH_SIZE]
    batch_num = i//BATCH_SIZE + 1
    
    # Update progress bar description with current stats
    progress_bar.set_description(f"Batch {batch_num}/{num_batches} ({batch_num*100//num_batches}%)")
    
    # Wait BEFORE making request (except first batch) to respect 15 RPM limit
    if i > 0:
        time.sleep(5)  # 5 seconds = 12 requests/minute (safe margin under 15 RPM)
    
    # Create a FRESH LLM client for each batch (workaround for key invalidation issue)
    llm = LLMAnswerGenerator()
    
    prompt = f"""You are filtering indexed terms for a historical banking database.

Your task: Return ONLY the terms that are meaningful entities (proper nouns, specific concepts).

**KEEP:**
- Multi-word proper nouns: "Bank of Montreal", "David David", "Aaron Hart"
- Full family names: "Rothschild", "Morgan", "Lehman" (distinctive surnames)
- Identity terms: "Jewish", "Quaker", "female", "widow", "Black", "Armenian"
- Panics: "Panic of 1763", "Panic of 1929" (NOT "hispanic")
- Law codes: "TA1813", "BA1933"
- Acronyms: "SEC", "FDIC", "WWI"
- Specific places when part of institution: "Bank of London", "New York Stock Exchange"

**EXCLUDE:**
- Generic words: "bank", "after", "establish", "dominant", "AMERICA", "BRITISH", "financial", "commercial", "american", "european"
- Common single-word first names: "John", "David", "James", "William", "George", "Charles", "Henry", "Thomas", "Robert", "Joseph", "Aaron", "Jacob", "Louis", "Samuel"
- Common single-word place names when standalone: "York", "London", "Paris", "Boston", "Columbia", "Brunswick" (unless part of "Bank of York", etc.)
- Generic single words: "son", "father", "brother", "president", "director", "governor"

**Terms to filter:**
{json.dumps(batch)}

**Output:** JSON array of terms to KEEP only. No explanations.
"""
    
    try:
        response_text = llm.call_api(prompt).strip()
        
        # Extract JSON from response
        if '```json' in response_text:
            response_text = response_text.split('```json')[1].split('```')[0].strip()
        elif '```' in response_text:
            response_text = response_text.split('```')[1].split('```')[0].strip()
        
        kept_terms = json.loads(response_text)
        filtered_terms.extend(kept_terms)
        
        # Calculate statistics
        kept_pct = (len(kept_terms) / len(batch)) * 100
        removed_pct = 100 - kept_pct
        overall_pct = (batch_num / num_batches) * 100
        total_removed_so_far = (batch_num * BATCH_SIZE) - len(filtered_terms)
        
        # Update progress bar with detailed stats
        progress_bar.set_postfix({
            'kept': f'{len(kept_terms)}/{len(batch)}',
            'total': len(filtered_terms),
            'removed': total_removed_so_far
        })
        
        print(f"\n   ✅ Batch {batch_num}/{num_batches} ({overall_pct:.0f}%): Kept {len(kept_terms)}/{len(batch)} ({kept_pct:.0f}%), Removed {len(batch)-len(kept_terms)} ({removed_pct:.0f}%)")
        print(f"      Total: {len(filtered_terms)} kept, {total_removed_so_far} removed")
        
    except Exception as e:
        print(f"\n   [ERROR] Batch {batch_num} failed: {str(e)[:300]}")
        print(f"   [FALLBACK] Keeping all {len(batch)} terms from this batch")
        filtered_terms.extend(batch)
        time.sleep(15)  # Wait longer after error

print()
print(f"4. Filtering complete!")
print(f"   Original terms: {len(terms)}")
print(f"   Filtered terms: {len(filtered_terms)}")
print(f"   Removed: {len(terms) - len(filtered_terms)} ({100*(len(terms) - len(filtered_terms))/len(terms):.1f}%)")
print()

# Save filtered terms list
output_file = 'data/filtered_terms.json'
print(f"5. Saving filtered terms to {output_file}...")
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(sorted(set(filtered_terms)), f, indent=2, ensure_ascii=False)

print()
print("="*80)
print("DONE!")
print("="*80)
print()
print("Filtered terms saved. server.py will now load this file for hyperlinking.")
