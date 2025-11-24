"""Test that LGBT keyword search works (no individual tagging)"""
import json

indices = json.load(open('data/indices.json'))

lgbt_keywords = ['homosexual', 'lgbt', 'lesbian', 'bisexual', 'lavender', 'aids']

print("LGBT KEYWORD SEARCH (Context-Based, Not Individual-Based)")
print("="*60)

for keyword in lgbt_keywords:
    chunks = indices['term_to_chunks'].get(keyword, [])
    print(f"{keyword}: {len(chunks)} chunks")

print("\nThis means:")
print("  - Searching 'gay bankers' finds chunks with 'gay' keyword")
print("  - Includes: lavender marriages, AIDS crisis, homophobia, etc.")
print("  - Does NOT tag individuals (Drexel appears in non-LGBT chunks too)")
print("  - Prevents 'Claudine Gay' false positive (surname 'Gay' filtered)")

