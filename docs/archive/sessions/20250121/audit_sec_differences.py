import sys
import os

# Ensure lib on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib.query_engine import QueryEngine
from query import search


def main():
    engine = QueryEngine(use_async=False)
    # engine indices are lowercased
    sec_term = 'sec'
    term_ids = set(engine.term_to_chunks.get(sec_term, []))
    print(f"Engine index term_to_chunks['{sec_term}']: {len(term_ids)} ids")

    # Retrieve those ids to get filenames
    if term_ids:
        data = engine.collection.get(ids=list(term_ids))
        id_to_file = {}
        for cid, meta in zip(data['ids'], data['metadatas']):
            id_to_file[cid] = meta.get('filename', 'Unknown')
    else:
        id_to_file = {}

    # Helper search path
    helper_results = search('SEC', max_results=100000) or []
    helper_ids = set()
    helper_id_to_file = {}
    for r in helper_results:
        cid = r.get('rowid') or r.get('id') or r.get('chunk_id')
        if cid:
            helper_ids.add(cid)
            helper_id_to_file[cid] = r.get('filename') or 'Unknown'

    print(f"Helper search('SEC'): {len(helper_ids)} ids")

    only_in_engine = sorted(term_ids - helper_ids)
    only_in_helper = sorted(helper_ids - term_ids)

    print(f"\nOnly in engine index ({len(only_in_engine)}):")
    for cid in only_in_engine[:50]:
        print(f"  {cid}  {id_to_file.get(cid, 'Unknown')}")
    if len(only_in_engine) > 50:
        print(f"  ... and {len(only_in_engine) - 50} more")

    print(f"\nOnly in helper search ({len(only_in_helper)}):")
    for cid in only_in_helper[:50]:
        print(f"  {cid}  {helper_id_to_file.get(cid, 'Unknown')}")
    if len(only_in_helper) > 50:
        print(f"  ... and {len(only_in_helper) - 50} more")

    # Per-file tallies for engine mapping
    from collections import Counter
    eng_counts = Counter(id_to_file.values())
    print("\nEngine per-file (top):")
    for fname, cnt in eng_counts.most_common(20):
        print(f"  {cnt:5d}  {fname}")

    helper_counts = Counter(helper_id_to_file.values())
    print("\nHelper per-file (top):")
    for fname, cnt in helper_counts.most_common(20):
        print(f"  {cnt:5d}  {fname}")

if __name__ == '__main__':
    main()

