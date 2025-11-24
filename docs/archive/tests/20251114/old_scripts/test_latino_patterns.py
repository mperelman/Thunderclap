"""Test Latino detection on actual passages"""
import re

test_cases = [
    ("Romana Bañuelos", "Mexican", "deported from America to Mexico... first non-White woman... established California's first Hispanic-owned bank"),
    ("Patricia Diaz", "New Mexico-born", "appointed... as the first Hispanic Assistant Secretary"),
    ("Carlos Arboleya", "Cuban", "Cuban refugee Carlos Arboleya remained Vice Chair"),
    ("Dennis Nixon", "Laredo", "President and CEO of... largest MWO-BHC"),
    ("Martin Chavez", "New Mexico-born", "New Mexico-born Martin Chavez... identified as Hispanic and gay"),
    ("Christina Seix", "Puerto Rican", "daughter of a working-class Puerto Rican immigrant"),
    ("Roberto Goizueta", "Cuban", "Fellow Cuban Roberto Goizueta"),
]

# Current patterns
patterns = {
    'P1 (Country Name)': r'(?:Puerto Rican|Mexican|Colombian|Honduran|Venezuelan|Guatemalan|Salvadoran|Dominican|Cuban|Argentinian|Chilean|Peruvian|Ecuadorian|Bolivian|Paraguayan|Uruguayan|Costa Rican|Panamanian|Nicaraguan|Haitian|Jamaican|Barbadian|Trinidadian|Brazilian)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
    'P2 (first Latina/Hispanic)': r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\s+became\s+the\s+first\s+(?:Latina?|Hispanic)',
    'P3 (appointed first)': r'(?:appointed|named)\s+([A-Z][a-z]+\s+[A-Z][a-z]+).{0,20}first\s+(?:Latina?|Hispanic)',
    'P4 (first... to serve)': r'first\s+(?:Latina?|Hispanic).{0,50}?to\s+serve.{0,50}?\b([A-Z][a-z]+\s+[A-Z][a-z]+)',
    'P5 (a Latina/Hispanic)': r'\b([A-Z][a-z]+\s+[A-Z][a-z]+),\s+a\s+(?:Latina?|Hispanic)(?:\s+(?:banker|executive))?',
    'NEW: Hispanic-owned': r'([A-Z][a-z]+).{0,100}Hispanic-owned',
    'NEW: identified as Hispanic': r'([A-Z][a-z]+\s+[A-Z][a-z]+).{0,50}identified\s+as\s+Hispanic',
    'NEW: daughter... Puerto Rican': r'daughter\s+of.{0,50}Puerto Rican.{0,50}([A-Z][a-z]+\s+[A-Z][a-z]+)',
}

print("TESTING LATINO PATTERNS:")
print("="*60)

for name, origin, context in test_cases:
    print(f"\n{name} ({origin}):")
    found_by = []
    for pattern_name, pattern in patterns.items():
        if re.search(pattern, context):
            found_by.append(pattern_name)
    if found_by:
        print(f"  [OK] Matched by: {', '.join(found_by)}")
    else:
        print(f"  [FAIL] NOT MATCHED")
        print(f"  Context: {context[:80]}...")

