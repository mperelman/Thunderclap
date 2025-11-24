"""Test paragraph enforcement on a sample paragraph."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.query_engine import QueryEngine

# Create a test instance
engine = QueryEngine(use_async=False)

# Test paragraph with many sentences
test_para = """Antisemitism in Vienna required Solomon Rothschild to seek permission from Metternich for his cousin Anton Schnapper to move to Vienna. By 1823, Schnapper married Maria Wertheim, daughter of Rothschild's clerk Leo Wertheim, who was a Katz-cousin descendant of Samson Wertheim. After Anton's brother wed Maria's second cousin in 1829, Rothschild sought renewal of 'toleration' for another Frankfurt-born cousin and employee, Moritz Goldschmidt. Michael Daniel, a Jewish moneylender in Moldova, established financial ties with Rothschild in Frankfurt, Paris, and London by 1829. Austria, part of the Holy Alliance, mandated the quashing of revolts across southern Italy in 1822. Rothschild Naples funded the Austrian invasion and occupation, leading to the family's ennoblement."""

print("Original paragraph:")
print(test_para)
print(f"\nNumber of sentences (estimated): {test_para.count('. ') + test_para.count('! ') + test_para.count('? ')}")

print("\n" + "="*70)
print("After enforcement:")
print("="*70)

result = engine._enforce_paragraph_limit(test_para, max_sentences=3)
print(result)

# Count sentences in result
paras = result.split("\n\n")
for i, para in enumerate(paras, 1):
    sentences = para.count('. ') + para.count('! ') + para.count('? ')
    print(f"\nParagraph {i}: {sentences} sentences")


