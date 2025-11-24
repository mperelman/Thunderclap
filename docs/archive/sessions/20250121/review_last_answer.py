"""Review the last answer we got."""
import sys
import os
import re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.answer_reviewer import AnswerReviewer

# The answer from the last query
answer = """The Rothschild banking family established a branch in Vienna, Austria, becoming deeply embedded in the Austrian financial landscape through strategic kinship networks and involvement in major financial events.

**Early 19th Century: Establishing a Foothold**

Antisemitism in Vienna required Solomon Rothschild to seek permission from Metternich for his cousin Anton Schnapper to move to Vienna. By 1823, Schnapper married Maria Wertheim, a Katz-cousin descendant of Samson Wertheim. After Anton's brother married Maria's second cousin in 1829, Rothschild sought renewal of toleration for Moritz Goldschmidt, another Frankfurt-born cousin and employee. The Emperor ennobled Goldschmidt, Wertheim, and Schnapper between 1862 and 1865. Austria commissioned Rothschild Naples to fund the invasion and occupation of Southern Italy in 1822 and then ennobled the family. By 1829, Michael Daniel, a Jewish moneylender in Moldova, had established financial ties with Rothschild in Frankfurt, Paris, and London."""

# Get full answer from the API response
import requests
response = requests.post(
    "http://localhost:8000/query",
    json={"question": "Tell me about Vienna Rothschild banking", "max_length": 15000},
    timeout=600
)

if response.status_code == 200:
    data = response.json()
    answer = data.get("answer", answer)
    print(f"Got answer from API ({len(answer)} chars)")
else:
    print(f"API error: {response.status_code}")
    print("Using partial answer for review")

print("="*70)
print("REVIEWING ANSWER")
print("="*70)

reviewer = AnswerReviewer()
results = reviewer.review(answer, chunks=None)
reviewer.print_report(results, answer)

# Extract years
years = set()
for match in re.finditer(r'\b(1[6-9]\d{2}|20[0-2]\d)\b', answer):
    years.add(int(match.group(1)))
if years:
    print(f"\nTime frame: {min(years)} - {max(years)}")
    print(f"Latest year: {max(years)}")


