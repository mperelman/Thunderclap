#!/usr/bin/env python3
"""
Upload Thunderclap data files to Railway via FastAPI admin endpoints (HTTP),
with a real progress bar (streamed multipart upload).

This avoids `railway run sh -c ...` which can be awkward on Windows shells.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Dict, Tuple

import requests
from tqdm import tqdm


DEFAULT_BASE_URL = "https://web-production-c4223.up.railway.app"

# filename -> (endpoint_path, extra_headers)
UPLOAD_TARGETS: Dict[str, Tuple[str, Dict[str, str]]] = {
    "identity_detection_v3.json": ("/admin/upload-identity", {}),
    "filtered_terms.json": ("/admin/upload-filtered-terms", {}),
    "indices.json": ("/admin/upload-index", {}),
    "endnotes.json": ("/admin/upload-endnotes", {}),
    "chunk_to_endnotes.json": ("/admin/upload-chunk-to-endnotes", {}),
    # NOTE: database upload supported, but usually large
    "chroma.sqlite3": ("/admin/upload-database", {}),
}


def _iter_multipart_bytes(
    file_path: str,
    field_name: str = "file",
    filename: str | None = None,
    content_type: str = "application/octet-stream",
    boundary: str | None = None,
    chunk_size: int = 1024 * 1024,
):
    """
    Stream a single-file multipart/form-data body as bytes.
    Yields bytes chunks without reading entire file into memory.
    """
    if boundary is None:
        # short random boundary
        import uuid

        boundary = f"--------------------------{uuid.uuid4().hex}"
    if filename is None:
        filename = os.path.basename(file_path)

    preamble = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'
        f"Content-Type: {content_type}\r\n"
        f"\r\n"
    ).encode("utf-8")
    epilogue = f"\r\n--{boundary}--\r\n".encode("utf-8")

    total_size = len(preamble) + os.path.getsize(file_path) + len(epilogue)

    def gen():
        yield preamble
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk
        yield epilogue

    return boundary, total_size, gen()


def upload_file(base_url: str, file_path: str) -> None:
    filename = os.path.basename(file_path)
    if filename not in UPLOAD_TARGETS:
        raise SystemExit(
            f"Don't know which endpoint to use for '{filename}'. "
            f"Supported: {', '.join(sorted(UPLOAD_TARGETS.keys()))}"
        )

    endpoint_path, extra_headers = UPLOAD_TARGETS[filename]
    url = base_url.rstrip("/") + endpoint_path

    # Railway/proxies sometimes reset connections on streamed/chunked uploads.
    # For JSON files (small), do the robust approach:
    # read the file with a progress bar, then send a normal multipart request.
    file_size = os.path.getsize(file_path)
    with tqdm(total=file_size, unit="B", unit_scale=True, desc=f"Reading {filename}") as pbar:
        buf = bytearray()
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(1024 * 1024)
                if not chunk:
                    break
                buf.extend(chunk)
                pbar.update(len(chunk))

    files = {"file": (filename, bytes(buf), "application/octet-stream")}
    headers = {**extra_headers}

    resp = requests.post(url, files=files, headers=headers, timeout=900)

    if resp.status_code != 200:
        raise SystemExit(f"Upload failed ({resp.status_code}): {resp.text[:2000]}")

    try:
        payload = resp.json()
    except Exception:
        payload = {"raw": resp.text}

    print(f"OK {filename} -> {endpoint_path}")
    if isinstance(payload, dict):
        msg = payload.get("message")
        if msg:
            print(f"  {msg}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default=DEFAULT_BASE_URL)
    ap.add_argument("files", nargs="+", help="Paths to files to upload (e.g., data/identity_detection_v3.json)")
    args = ap.parse_args()

    # Quick health check
    try:
        health = requests.get(args.base_url.rstrip("/") + "/health", timeout=30)
        if health.status_code != 200:
            print(f"WARN: /health returned {health.status_code}")
    except Exception as e:
        print(f"WARN: Could not reach /health: {e}")

    for path in args.files:
        if not os.path.exists(path):
            raise SystemExit(f"File not found: {path}")
        upload_file(args.base_url, path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

