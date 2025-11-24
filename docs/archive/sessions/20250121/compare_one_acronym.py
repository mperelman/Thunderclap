import sys
import os
import re
from collections import Counter

# Ensure lib on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib.query_engine import QueryEngine
from lib.acronyms import ACRONYM_EXPANSIONS

MAX_SNIPPET = 300

STRICT_CACHE = {}

def visible_text(s: str) -> str:
    return re.sub(r"<[^>]+>", " ", s or "")


def strict_patterns(acronym: str):
    if acronym in STRICT_CACHE:
        return STRICT_CACHE[acronym]
    full = ACRONYM_EXPANSIONS.get(acronym, "")
    pats = [
        re.compile(r"\\b" + re.escape(acronym) + r"\\b"),                # SEC
        re.compile(r"\\b" + re.escape(acronym) + r"['’]s\\b"),           # SEC's
        re.compile(r"\\b" + r"\\.".join(list(acronym)) + r"\\.\\b", re.IGNORECASE),  # S.E.C.
        re.compile(r"\\b" + r"\\s".join(list(acronym)) + r"\\b", re.IGNORECASE),       # S E C
    ]
    if full:
        pats.append(re.compile(r"\\b" + re.escape(full) + r"\\b", re.IGNORECASE))
        pats.append(re.compile(r"\\b" + re.escape(full.replace("and", "&")) + r"\\b", re.IGNORECASE))
    STRICT_CACHE[acronym] = pats
    return pats


def main():
    if len(sys.argv) < 2:
        print("Usage: python temp/compare_one_acronym.py ACRONYM (e.g., SEC)")
        sys.exit(1)
    A = sys.argv[1].upper()

    eng = QueryEngine(use_async=False)

    # Gather all chunk docs for faster scanning
    # Union of all ids in indices
    all_ids = set()
    for ids in eng.term_to_chunks.values():
        all_ids.update(ids)
    pulled = eng.collection.get(ids=list(all_ids))

    docs = dict(zip(pulled['ids'], pulled['documents']))
    metas = dict(zip(pulled['ids'], pulled['metadatas']))

    # Current index picks
    indexed_ids = set(eng.term_to_chunks.get(A.lower(), [])) | set(eng.term_to_chunks.get(A, []))

    # Strict picks (scan body text)
    pats = strict_patterns(A)
    strict_ids = set()
    for cid, doc in docs.items():
        vis = visible_text(doc)
        if any(p.search(vis) for p in pats):
            strict_ids.add(cid)

    overlap = indexed_ids & strict_ids
    only_index = indexed_ids - strict_ids
    only_strict = strict_ids - indexed_ids

    print(f"Acronym: {A}")
    print(f"  Indexed: {len(indexed_ids)}")
    print(f"  Strict : {len(strict_ids)}")
    print(f"  Overlap: {len(overlap)}")
    print(f"  Only in index: {len(only_index)}")
    print(f"  Only in strict: {len(only_strict)}\n")

    def show_samples(title, ids):
        print(title)
        for i, cid in enumerate(list(ids)[:10], start=1):
            fname = (metas.get(cid) or {}).get('filename', 'Unknown')
            snippet = visible_text(docs.get(cid, ''))[:MAX_SNIPPET]
            print(f"[{i}] {cid}  {fname}\n--\n{snippet}\n")

    show_samples("Samples: Only in index", only_index)
    show_samples("Samples: Only in strict", only_strict)

if __name__ == '__main__':
    main()

