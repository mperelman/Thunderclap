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
MAX_SNIPPET = 600


def has_any_sec(text: str) -> bool:
    if not isinstance(text, str):
        return False
    visible = re.sub(r"<[^>]+>", " ", text)
    return (
        SEC_TOKEN.search(visible) or SEC_SPELLED_AND.search(visible) or
        SEC_SPELLED_AMP.search(visible) or SEC_SEPARATED.search(visible) or
        SEC_DOTTED.search(visible)
    )


def main():
    eng = QueryEngine(use_async=False)
    index_ids = set(eng.term_to_chunks.get('sec', []))
    data = eng.collection.get(ids=list(index_ids))

    extras = []
    for cid, doc, meta in zip(data['ids'], data['documents'], data['metadatas']):
        if not has_any_sec(doc):
            extras.append((cid, meta.get('filename', 'Unknown'), doc))

    print(f"SEC-indexed but no direct body match: {len(extras)}\n")
    for i, (cid, fname, doc) in enumerate(extras, start=1):
        snippet = (doc or '')[:MAX_SNIPPET]
        print(f"[{i}] id={cid}  file={fname}")
        print('-' * 80)
        print(snippet)
        if doc and len(doc) > MAX_SNIPPET:
            print("\n... [truncated] ...")
        print("\n")

if __name__ == '__main__':
    main()

