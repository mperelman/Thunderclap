"""Test the fixed candidate extraction"""
import sys
sys.path.insert(0, '.')

from lib.llm_identity_detector import LLMIdentityDetector

sample_text = """
Jewish Rothschild merged with Quaker Barclay in London. 
The Sephardi Sassoon family traded with Parsee Tata in India.
Black banker Richard Parsons joined Citi.
Lebanese Maronite George Boutros worked at CSFB.
Muslim Sunni trader Ahmad al-Rashid operated in Damascus.
"""

print("Testing FIXED candidate extraction...\n")
print("Sample text:")
print(sample_text)
print("\n" + "="*70)

detector = LLMIdentityDetector()
candidates = detector._extract_candidates(sample_text)

print("EXTRACTED CANDIDATES:")
print("="*70)
for identity, surnames in sorted(candidates.items()):
    print(f"  {identity}: {surnames}")

print("\n" + "="*70)
print("EXPECTED RESULTS:")
print("="*70)
print("  jewish: ['Rothschild']")
print("  quaker: ['Barclay']")
print("  sephardi: ['Sassoon']")
print("  parsee: ['Tata']")
print("  black: ['Parsons'] or ['Richard', 'Parsons']")
print("  lebanese: ['Boutros']")
print("  maronite: ['Boutros']")
print("  muslim: ['al-Rashid'] or ['Ahmad', 'al-Rashid']")
print("  sunni: ['al-Rashid'] or ['Ahmad', 'al-Rashid']")
print("\n[RESULT] If extraction looks clean, the detector is FIXED!")

