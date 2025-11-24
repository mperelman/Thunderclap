"""Find all Latino/Hispanic banker mentions in documents"""
import json
import re

files = ['data/cache/Thunderclap Part I.docx.cache.json',
         'data/cache/Thunderclap Part II.docx.cache.json', 
         'data/cache/Thunderclap Part III.docx.cache.json']

# All Latin American/Caribbean countries
latino_countries = [
    'Puerto Rican', 'Mexican', 'Colombian', 'Honduran', 'Venezuelan', 
    'Guatemalan', 'Salvadoran', 'Dominican', 'Cuban', 'Argentinian',
    'Chilean', 'Peruvian', 'Ecuadorian', 'Bolivian', 'Paraguayan',
    'Uruguayan', 'Costa Rican', 'Panamanian', 'Nicaraguan',
    'Haitian', 'Jamaican', 'Barbadian', 'Trinidadian', 'Brazilian'
]

# Find all mentions
all_mentions = []

for filepath in files:
    text = json.load(open(filepath))['text']
    
    # Pattern 1: Country + Name
    for country in latino_countries:
        pattern = rf'{country}[- ](?:born\s+)?([A-Z][a-z]+\s+[A-Z][a-z]+)'
        matches = re.findall(pattern, text)
        for match in matches:
            all_mentions.append((match, country, filepath.split('/')[-1]))
    
    # Pattern 2: Latina/Latino/Hispanic
    patterns = [
        r'([A-Z][a-z]+\s+[A-Z][a-z]+).{0,30}(?:Latina?|Hispanic)',
        r'(?:Latina?|Hispanic)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
        r'first\s+(?:Latina?|Hispanic).{0,100}([A-Z][a-z]+\s+[A-Z][a-z]+)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            all_mentions.append((match, 'Latina/Hispanic', filepath.split('/')[-1]))

# Remove duplicates and noise
seen = {}
for name, origin, file in all_mentions:
    surname = name.strip().split()[-1].lower()
    if len(surname) > 3 and surname not in ['islands', 'bank', 'fannie', 'virgin']:
        if surname not in seen:
            seen[surname] = (name, origin, file)

print(f"LATINO/HISPANIC BANKERS FOUND: {len(seen)}")
print("="*60)

for surname, (full_name, origin, file) in sorted(seen.items()):
    print(f"\n{full_name}")
    print(f"  Origin: {origin}")
    print(f"  File: {file}")

