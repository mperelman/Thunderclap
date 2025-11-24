import sys
import os
from collections import defaultdict

# Ensure lib on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from query import search

TERMS = [
    "SEC",
    "Securities and Exchange Commission",
    "Securities & Exchange Commission",
    "S.E.C",
    "S. E. C."
]

def main():
    per_file = defaultdict(int)
    seen = set()
    per_term_counts = {}

    for t in TERMS:
        try:
            results = search(t, max_results=100000) or []
        except Exception as e:
            print(f"[ERROR] search('{t}') -> {e}")
            results = []
        term_ids = set()
        for r in results:
            cid = r.get("rowid") or r.get("id") or r.get("chunk_id")
            if not cid:
                continue
            term_ids.add(cid)
            if cid not in seen:
                seen.add(cid)
                fn = r.get("filename") or "Unknown"
                per_file[fn] += 1
        per_term_counts[t] = len(term_ids)

    print("=== SEC Index Audit ===")
    print(f"Total distinct chunks (union): {len(seen)}")
    for t in TERMS:
        print(f"  {t!r}: {per_term_counts.get(t, 0)} chunks")

    print("\nBy source file (chapter):")
    for fn, cnt in sorted(per_file.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"  {cnt:5d}  {fn}")

if __name__ == "__main__":
    main()

