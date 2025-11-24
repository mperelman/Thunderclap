import sys
import os
import re

# Ensure lib on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib.query_engine import QueryEngine

SEC_TOKEN = re.compile(r"\bSEC\b")
SEC_SPELLED_AND = re.compile(r"securities\s+and\s+exchange\s+commission", re.IGNORECASE)
SEC_SPELLED_AMP = re.compile(r"securities\s*&\s*exchange\s*commission", re.IGNORECASE)
SEC_SEPARATED = re.compile(r"\bS\s*E\s*C\b", re.IGNORECASE)
SEC_DOTTED = re.compile(r"\bS\.E\.C\b", re.IGNORECASE)


def has_any_sec(text: str) -> bool:
    if not isinstance(text, str):
        return False
    # strip simple tags
    visible = re.sub(r"<[^>]+>", " ", text)
    return (
        SEC_TOKEN.search(visible) or SEC_SPELLED_AND.search(visible) or
        SEC_SPELLED_AMP.search(visible) or SEC_SEPARATED.search(visible) or
        SEC_DOTTED.search(visible)
    )


def reason(text: str) -> str:
    visible = re.sub(r"<[^>]+>", " ", text or "")
    if SEC_TOKEN.search(visible):
        return "SEC token"
    if SEC_DOTTED.search(visible) or SEC_SEPARATED.search(visible):
        return "S.E.C / S E C variant"
    if SEC_SPELLED_AND.search(visible):
        return "Full name (and)"
    if SEC_SPELLED_AMP.search(visible):
        return "Full name (&)"
    return "No direct body match"


def main():
    eng = QueryEngine(use_async=False)
    index_ids = set(eng.term_to_chunks.get('sec', []))
    data = eng.collection.get(ids=list(index_ids))

    rows = []
    for cid, doc, meta in zip(data['ids'], data['documents'], data['metadatas']):
        fname = (meta or {}).get('filename', 'Unknown')
        r = reason(doc)
        rows.append((cid, fname, r))

    # Show those without direct body SEC token but indexed
    extras = [(cid, fname, r) for cid, fname, r in rows if r == 'No direct body match']
    print(f"SEC-indexed chunks total: {len(rows)}")
    print(f"Indexed but no direct body match: {len(extras)}\n")
    for cid, fname, r in extras[:100]:
        print(f"  {cid}  {fname}  -> {r}")

    # Also show counts by reason
    from collections import Counter
    rc = Counter(r for _, _, r in rows)
    print("\nReasons count:")
    for k, v in rc.most_common():
        print(f"  {k}: {v}")

if __name__ == '__main__':
    main()

