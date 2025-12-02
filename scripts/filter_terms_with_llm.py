"""
Filter indexed terms using LLM to identify only meaningful entities.
This removes generic words like "bank", "treasury", "significant", etc.
and keeps only proper nouns, specific entities, and meaningful terms.
"""
import sys
import os
sys.path.insert(0, '.')

import json
import google.generativeai as genai
from tqdm import tqdm

# Load API key (same method as query_engine.py)
from dotenv import load_dotenv
load_dotenv()

gemini_key = os.getenv('GEMINI_API_KEY')
if not gemini_key:
    print("ERROR: GEMINI_API_KEY environment variable not set!")
    print("Please set it in .env file or environment")
    sys.exit(1)

print(f"   Using API key: {gemini_key[:20]}...")
genai.configure(api_key=gemini_key)

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

# Filter terms in batches using LLM
print("2. Filtering terms with LLM...")
print("   This will identify which terms are meaningful entities vs generic words")
print()

model = genai.GenerativeModel('gemini-2.0-flash-exp')

BATCH_SIZE = 200  # Process 200 terms at a time
filtered_terms = []

for i in tqdm(range(0, len(terms), BATCH_SIZE), desc="Filtering batches"):
    batch = terms[i:i+BATCH_SIZE]
    
    prompt = f"""You are filtering indexed terms for a historical banking database.

Your task: Identify which terms should be KEPT for hyperlinking (meaningful entities) vs EXCLUDED (generic words).

**KEEP (output these):**
- Proper nouns: names of people, institutions, places (e.g., "Rothschild", "Morgan", "Bank of Montreal", "London")
- Specific entities: firm names, family names, acronyms (e.g., "SEC", "FDIC", "BA1933")
- Identity terms: religious/ethnic/gender terms (e.g., "Jewish", "Quaker", "female", "widow")
- Panic terms: "Panic of 1763", "Panic of 1929", etc.
- Specific law codes: "TA1813", "BA1933", etc.

**EXCLUDE (do NOT output these):**
- Generic banking/finance words: "bank", "banking", "finance", "credit", "investment", "treasury", "capital", "interest", "loan", "deposit", "transaction", "purchase", "investor", "commercial", "financial", "regulatory", "industrial", "correspondent"
- Generic descriptive words: "significant", "substantial", "major", "subsequent", "prior", "dominant", "important", "large", "small", "successful", "unsuccessful"
- Generic action verbs: "establish", "create", "form", "collapse", "decline", "increase", "decrease"
- Generic geographic adjectives: "American", "European", "British", "French", "German" (unless part of a specific entity name)
- Common words: "after", "before", "during", "and", "the", etc.

**Input terms:**
{json.dumps(batch, indent=2)}

**Output format:**
Return ONLY a JSON array of terms to KEEP (meaningful entities). Example:
["Rothschild", "Bank of Montreal", "Panic of 1929", "Jewish", "SEC"]

Do NOT include explanations, just the JSON array.
"""
    
    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Extract JSON from response (handle markdown code blocks)
        if '```json' in response_text:
            response_text = response_text.split('```json')[1].split('```')[0].strip()
        elif '```' in response_text:
            response_text = response_text.split('```')[1].split('```')[0].strip()
        
        kept_terms = json.loads(response_text)
        filtered_terms.extend(kept_terms)
        
    except Exception as e:
        print(f"\n   [WARNING] Error processing batch {i//BATCH_SIZE + 1}: {e}")
        print(f"   [WARNING] Keeping all terms in this batch as fallback")
        filtered_terms.extend(batch)

print()
print(f"3. Filtering complete!")
print(f"   Original terms: {len(terms)}")
print(f"   Filtered terms: {len(filtered_terms)}")
print(f"   Removed: {len(terms) - len(filtered_terms)} ({100*(len(terms) - len(filtered_terms))/len(terms):.1f}%)")
print()

# Save filtered terms list
output_file = 'data/filtered_terms.json'
print(f"4. Saving filtered terms to {output_file}...")
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(sorted(set(filtered_terms)), f, indent=2, ensure_ascii=False)

print()
print("="*80)
print("DONE!")
print("="*80)
print()
print("Next step: Update server.py to load filtered_terms.json instead of filtering on-the-fly")

