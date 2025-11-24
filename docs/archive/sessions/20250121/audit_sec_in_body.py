import sys
import os
import re

# Ensure lib on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib.query_engine import QueryEngine

SEC_PATTERNS = [
    re.compile(r"\bSEC\b"),
    re.compile(r"\bS\.E\.C\b", re.IGNORECASE),
    re.compile(r"\bS\s*E\s*C\b", re.IGNORECASE),
    re.compile(r"securities\s*&\s*exchange\s*commission", re.IGNORECASE),
    re.compile(r"securities\s+and\s+exchange\s+commission", re.IGNORECASE),
]

TARGET_FILE = "Thunderclap Part III.docx"


def text_has_sec(text: str) -> bool:
    if not isinstance(text, str):
        return False
    # Handle simple markup like <italic>SEC</italic>
    t = text
    for pat in SEC_PATTERNS:
        if pat.search(t):
            return True
    return False


def main():
    eng = QueryEngine(use_async=False)
    # Gather all chunk ids and texts for target file
    all_ids = eng.collection.get(ids=None)  # not supported; fetch by where clause instead
    # Workaround: fetch by term index union across all terms, then filter by filename
    # Use collection.get with where filter if available
    try:
        data = eng.collection.get(where={"filename": TARGET_FILE})
    except Exception:
        # Fallback: iterate via term_to_chunks union
        all_chunk_ids = set()
        for ids in eng.term_to_chunks.values():
            all_chunk_ids.update(ids)
        pulled = eng.collection.get(ids=list(all_chunk_ids))
        data = {
            'ids': [],
            'documents': [],
            'metadatas': []
        }
        for cid, doc, meta in zip(pulled['ids'], pulled['documents'], pulled['metadatas']):
            if (meta or {}).get('filename') == TARGET_FILE:
                data['ids'].append(cid)
                data['documents'].append(doc)
                data['metadatas'].append(meta)

    ids = data['ids']
    docs = data['documents']
    metas = data['metadatas']

    body_sec_ids = set()
    for cid, doc in zip(ids, docs):
        if text_has_sec(doc):
            body_sec_ids.add(cid)

    index_sec_ids = set(eng.term_to_chunks.get('sec', []))

    print(f"In-body SEC matches in {TARGET_FILE}: {len(body_sec_ids)}")
    print(f"Index term_to_chunks['sec'] total (all files): {len(index_sec_ids)}")

    missing_in_index = sorted(body_sec_ids - index_sec_ids)
    extra_in_index = sorted(index_sec_ids - body_sec_ids)

    print(f"\nBody has SEC but index missing ({len(missing_in_index)}):")
    for cid in missing_in_index[:50]:
        print(f"  {cid}")
    if len(missing_in_index) > 50:
        print(f"  ... and {len(missing_in_index)-50} more")

    print(f"\nIndex has SEC but body doesn't ({len(extra_in_index)}):")
    for cid in extra_in_index[:50]:
        # file name for context
        # fetch metadata
        try:
            idx = ids.index(cid)
            fname = metas[idx].get('filename', 'Unknown')
        except ValueError:
            fname = 'Unknown'
        print(f"  {cid}  {fname}")

if __name__ == "__main__":
    main()

