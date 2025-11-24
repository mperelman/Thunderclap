import sys
import os

# Ensure lib on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from query import search

MAX_SNIPPET = 500
TERM = "SEC"
MAX_RESULTS = 1000
TOP_N = 10

def main():
    results = search(TERM, max_results=MAX_RESULTS) or []
    # Dedup by chunk id
    seen = set()
    unique = []
    for r in results:
        cid = r.get("rowid") or r.get("id") or r.get("chunk_id")
        if cid in seen:
            continue
        seen.add(cid)
        unique.append(r)
    print(f"Found {len(unique)} unique chunks for term '{TERM}'. Showing first {min(TOP_N, len(unique))}...\n")
    for i, r in enumerate(unique[:TOP_N], start=1):
        cid = r.get('rowid') or r.get('id') or r.get('chunk_id')
        fname = r.get('filename') or 'Unknown'
        text = (r.get('text') or '').replace('\n', '\n')
        snippet = text[:MAX_SNIPPET]
        print(f"[{i}] id={cid}  file={fname}")
        print('-' * 80)
        print(snippet)
        if len(text) > MAX_SNIPPET:
            print("\n... [truncated] ...")
        print("\n")

if __name__ == "__main__":
    main()

