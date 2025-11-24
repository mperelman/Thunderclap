"""Debug why Latino patterns aren't matching"""
import json
import re

# Load Part III cache
with open('data/cache/Thunderclap Part III.docx.cache.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    text = data['text']

# Test each missing person
missing_people = [
    ('Romana Bañuelos', 'first non-White woman.*Hispanic-owned bank'),
    ('Patricia Diaz', 'first Hispanic Assistant Secretary'),
    ('Martin Chavez', 'identified as Hispanic')
]

print("DEBUGGING LATINO PATTERN MATCHES:")
print("="*60)

for name, context_pattern in missing_people:
    print(f"\n{name}:")
    
    # Find context
    match = re.search(context_pattern, text, re.IGNORECASE)
    if match:
        start = max(0, match.start() - 100)
        end = min(len(text), match.end() + 100)
        context = text[start:end]
        print(f"  Context found: ...{context}...")
        
        # Test Latino patterns
        latino_countries = r'(?:Puerto Rican|Mexican|Colombian|Honduran|Venezuelan|Guatemalan|Salvadoran|Dominican|Cuban|Argentinian|Chilean|Peruvian|Ecuadorian|Bolivian|Paraguayan|Uruguayan|Costa Rican|Panamanian|Nicaraguan|Haitian|Jamaican|Barbadian|Trinidadian|Brazilian)'
        
        patterns = {
            'P7 (Hispanic-owned bank)': r'([A-Z][a-z]+\s+[A-Z][a-z]+).{0,150}?first\s+Hispanic-owned\s+bank',
            'P8 (identified as Hispanic)': r'([A-Z][a-z]+\s+[A-Z][a-z]+).{0,100}?(?:he|she)\s+identified\s+as\s+Hispanic',
            'P10 (first Hispanic)': r'([A-Z][a-z]+\s+[A-Z][a-z]+).{0,150}?first\s+Hispanic\s+(?:Assistant|Director|CEO)',
        }
        
        for pname, pattern in patterns.items():
            matches = re.findall(pattern, context)
            if matches:
                print(f"    {pname}: {matches}")
    else:
        print(f"  Context NOT found with pattern: {context_pattern}")

