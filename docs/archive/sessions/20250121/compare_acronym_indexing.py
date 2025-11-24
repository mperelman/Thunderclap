import sys
import os
import re
from collections import defaultdict

# Ensure lib on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib.query_engine import QueryEngine
from lib.acronyms import ACRONYM_EXPANSIONS

# Choose a representative set (can be expanded)
ACRONYMS = [
    "SEC", "FRS", "FPC", "FTC", "ICC", "RFC", "NYSE", "BOE"
]

# Strict patterns (exact tokens only)
STRICT_PATTERNS = {
    a: [
        re.compile(r"\\b" + re.escape(a) + r"\\b"),
        re.compile(r"\\b" + re.escape(a) + r"['’]s\\b"),
        re.compile(r"\\b" + r"\\.".join(list(a)) + r"\\.\\b", re.IGNORECASE),  # S.E.C.
        re.compile(r"\\b" + r"\\s".join(list(a)) + r"\\b", re.IGNORECASE),       # S E C
        re.compile(r"\\b" + re.escape(ACRONYM_EXPANSIONS.get(a, "")) + r"\\b", re.IGNORECASE) if ACRONYM_EXPANSIONS.get(a) else None,
        re.compile(r"\\b" + re.escape(ACRONYM_EXPANSIONS.get(a, "").replace("and", "&")) + r"\\b", re.IGNORECASE) if ACRONYM_EXPANSIONS.get(a) else None,
    ]
    for a in ACRONYM_EXPANSIONS.keys()
}

# Loose (legacy) patterns
def loose_match(a: str, text_lower: str, text_raw: str) -> bool:
    if re.search(r"\\b" + re.escape(a) + r"\\b", text_raw):
        return True
    full = ACRONYM_EXPANSIONS.get(a, "").lower()
    if full and full in text_lower:
        return True
    # very loose variant of spaced/dotted
    if re.search(r"\\b" + r"[\\s\\.]?".join(list(a)) + r"\\b", text_raw, flags=re.IGNORECASE):
        return True
    return False


def visible_text(s: str) -> str:
    return re.sub(r"<[^>]+>", " ", s or "")


def main():
    eng = QueryEngine(use_async=False)
    # Pull all chunks once
    # Chroma doesn't have list-all; union ids from indices
    all_ids = set()
    for ids in eng.term_to_chunks.values():
        all_ids.update(ids)
    data = eng.collection.get(ids=list(all_ids))

    # Build maps for fast lookup
    docs = dict(zip(data['ids'], data['documents']))
    metas = dict(zip(data['ids'], data['metadatas']))

    results = []
    for a in ACRONYMS:
        strict_ids = set()
        loose_ids = set()
        pats = [p for p in STRICT_PATTERNS.get(a, []) if p is not None]
        for cid, doc in docs.items():
            vis = visible_text(doc)
            vis_lower = vis.lower()
            # strict
            if any(p.search(vis) for p in pats):
                strict_ids.add(cid)
            # loose
            if loose_match(a, vis_lower, vis):
                loose_ids.add(cid)
        indexed_ids = set(eng.term_to_chunks.get(a.lower(), [])) | set(eng.term_to_chunks.get(a, []))
        results.append((a, len(strict_ids), len(loose_ids), len(indexed_ids)))

    print("Acronym  strict  loose  indexed")
    for a, s, l, i in results:
        print(f"{a:6s}  {s:6d}  {l:5d}  {i:7d}")

if __name__ == "__main__":
    main()

