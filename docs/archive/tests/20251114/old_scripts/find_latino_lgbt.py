"""Quick script to find Latino and LGBT banker mentions in documents"""
import json
import re

files = [
    'data/cache/Thunderclap Part I.docx.cache.json',
    'data/cache/Thunderclap Part II.docx.cache.json', 
    'data/cache/Thunderclap Part III.docx.cache.json'
]

latino_mentions = []
lgbt_mentions = []

for filepath in files:
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        text = data['text']
        
        # Find Latino/Hispanic mentions
        latino_matches = re.findall(r'.{80}(?:Puerto Rican|Latina|Hispanic|Latino|Mexican).{80}', text, re.IGNORECASE)
        latino_mentions.extend(latino_matches)
        
        # Find LGBT mentions
        lgbt_matches = re.findall(r'.{80}(?:openly gay|openly lesbian|first gay|first lesbian|LGBT).{80}', text, re.IGNORECASE)
        lgbt_mentions.extend(lgbt_matches)

print(f"Latino/Hispanic mentions: {len(latino_mentions)}")
print(f"LGBT mentions: {len(lgbt_mentions)}\n")

if latino_mentions:
    print("=== LATINO/HISPANIC EXAMPLES ===")
    for i, mention in enumerate(latino_mentions[:5], 1):
        print(f"\n{i}. {mention[:200]}...")

if lgbt_mentions:
    print("\n\n=== LGBT EXAMPLES ===")
    for i, mention in enumerate(lgbt_mentions[:5], 1):
        print(f"\n{i}. {mention[:200]}...")

