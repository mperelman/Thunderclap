#!/usr/bin/env python3
"""
One-shot: upload the fixed indices.json to Railway.
Run from the Thunderclap repo root:
    python scripts/upload_fixed_index.py
"""
import gzip, json, os, sys
import requests

RAILWAY_URL = "https://web-production-c4223.up.railway.app"
INDICES_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "indices.json")

def main():
    if not os.path.exists(INDICES_PATH):
        print(f"ERROR: {INDICES_PATH} not found.")
        return 1

    print(f"Reading {INDICES_PATH}...")
    with open(INDICES_PATH, "rb") as f:
        raw = f.read()

    # Validate before upload
    data = json.loads(raw)
    ttc = data.get("term_to_chunks", {})
    wiss = ttc.get("Wissotsky", [])
    wiss_tea = ttc.get("Wissotsky Tea", [])
    if "chunk_816" in wiss or "chunk_816" in wiss_tea:
        print("ERROR: chunk_816 is still in Wissotsky entries — run the fix script first.")
        return 1

    print(f"  Wissotsky: {wiss}  ✓")
    print(f"  Wissotsky Tea: {wiss_tea}  ✓")
    print(f"  Total terms: {len(ttc)}")

    compressed = gzip.compress(raw)
    size_kb = len(compressed) / 1024
    print(f"\nUploading {size_kb:.1f} KB (compressed) to {RAILWAY_URL}...")

    try:
        resp = requests.post(
            f"{RAILWAY_URL}/admin/upload-index",
            files={"file": ("indices.json.gz", compressed, "application/octet-stream")},
            timeout=120,
        )
    except Exception as e:
        print(f"Upload failed: {e}")
        return 1

    if resp.status_code == 200:
        print(f"✅ Upload successful: {resp.json().get('message', resp.text[:200])}")
        print("\nThe fix is live — Wissotsky queries will no longer retrieve chunk_816.")
        print("Test: ask 'Wissotsky' on the site. The Havar ancestry should be gone.")
    else:
        print(f"❌ Upload failed ({resp.status_code}): {resp.text[:300]}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
