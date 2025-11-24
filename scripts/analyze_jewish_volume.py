"""Analyze volume of Jewish-related chunks"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.document_parser import load_all_documents
from lib.index_builder import split_into_chunks
from lib.identity_prefilter import IdentityPrefilter

print("Analyzing identity distribution...\n")

# Load chunks
docs = load_all_documents(use_cache=True)
all_chunks = []
for doc in docs:
    all_chunks.extend(split_into_chunks(doc['text']))

print(f"Total chunks: {len(all_chunks)}\n")

# Check different identity groups
identity_groups = {
    'Jewish': ['jewish', 'jew', 'jews', 'sephardi', 'sephardim', 'ashkenazi', 
               'ashkenazim', 'kohanim', 'katz', 'court jew'],
    'Black': ['black', 'hausa', 'yoruba', 'igbo', 'african american'],
    'Lebanese': ['lebanese', 'lebanon', 'maronite'],
    'Latino': ['latino', 'latina', 'hispanic', 'mexican', 'cuban', 'puerto rican'],
    'Gay/LGBT': ['gay', 'homosexual', 'bisexual', 'lesbian', 'lavender'],
    'Muslim': ['muslim', 'islam', 'sunni', 'shia', 'alawite', 'druze'],
    'Female': ['female', 'woman', 'women', 'widow', 'queen', 'princess'],
    'Other': []  # Will calculate
}

chunk_counts = {}

for group, keywords in identity_groups.items():
    if group == 'Other':
        continue
    
    count = 0
    for chunk in all_chunks:
        chunk_lower = chunk.lower()
        if any(keyword in chunk_lower for keyword in keywords):
            count += 1
    
    chunk_counts[group] = count

# Calculate "Other" (has identity keywords but not in main groups)
prefilter = IdentityPrefilter()
total_with_identities = len(prefilter.filter_chunks(all_chunks))
accounted_for = sum(chunk_counts.values())
chunk_counts['Other'] = total_with_identities - accounted_for

# Show results
print("="*70)
print("CHUNKS BY IDENTITY GROUP")
print("="*70)

for group in sorted(chunk_counts.keys(), key=lambda x: chunk_counts[x], reverse=True):
    count = chunk_counts[group]
    pct = count / len(all_chunks) * 100
    batches = count / 20  # Batch size of 20
    
    print(f"{group:15} {count:4} chunks ({pct:5.1f}%) = {batches:5.1f} API batches")

print("="*70)
print(f"{'Total':15} {sum(chunk_counts.values()):4} chunks with identities")
print(f"{'No identities':15} {len(all_chunks) - sum(chunk_counts.values()):4} chunks")
print()

# Analyze Jewish split
jewish_count = chunk_counts.get('Jewish', 0)
non_jewish_count = sum(chunk_counts.values()) - jewish_count

print("="*70)
print("SPLIT SCENARIO: Jewish vs All Others")
print("="*70)
print(f"Jewish chunks:     {jewish_count:4} = {jewish_count/20:.1f} API batches")
print(f"Non-Jewish chunks: {non_jewish_count:4} = {non_jewish_count/20:.1f} API batches")
print(f"Total:             {jewish_count + non_jewish_count:4} = {(jewish_count + non_jewish_count)/20:.1f} API batches")
print()
print("Splitting doesn't save API calls - same total batches.")
print("BUT it allows separate processing strategies!")


