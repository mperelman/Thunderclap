#!/bin/bash
# Download LFS files if they're missing or pointer files

echo "=== Checking LFS files ==="

# Check if chroma.sqlite3 exists and is a real file (not pointer)
if [ -f "data/vectordb/chroma.sqlite3" ]; then
    SIZE=$(stat -f%z data/vectordb/chroma.sqlite3 2>/dev/null || stat -c%s data/vectordb/chroma.sqlite3 2>/dev/null || echo 0)
    if [ "$SIZE" -lt 1000000 ]; then
        echo "chroma.sqlite3 is a pointer file ($SIZE bytes), need to download..."
        NEED_DOWNLOAD=true
    else
        echo "chroma.sqlite3 exists and is large enough ($SIZE bytes)"
        NEED_DOWNLOAD=false
    fi
else
    echo "chroma.sqlite3 not found"
    NEED_DOWNLOAD=true
fi

if [ "$NEED_DOWNLOAD" = true ]; then
    echo "=== Initializing git and downloading LFS files ==="
    git init
    git remote add origin https://github.com/mperelman/Thunderclap.git || true
    git fetch origin main:main
    git checkout -f main
    git lfs pull origin main || (git lfs fetch origin main && git lfs checkout)
    echo "=== Verification ==="
    SIZE=$(stat -f%z data/vectordb/chroma.sqlite3 2>/dev/null || stat -c%s data/vectordb/chroma.sqlite3 2>/dev/null || echo 0)
    echo "chroma.sqlite3 size: $SIZE bytes"
fi

