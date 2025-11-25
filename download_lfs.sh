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
    echo "Checking git availability..."
    which git || (echo "ERROR: git not found!" && exit 1)
    which git-lfs || (echo "ERROR: git-lfs not found!" && exit 1)
    
    echo "Initializing git repo..."
    git init || (echo "ERROR: git init failed!" && exit 1)
    git config user.name "Railway" || true
    git config user.email "railway@railway.app" || true
    
    echo "Adding remote..."
    git remote add origin https://github.com/mperelman/Thunderclap.git || git remote set-url origin https://github.com/mperelman/Thunderclap.git
    
    echo "Fetching main branch..."
    git fetch origin main:main || (echo "ERROR: git fetch failed!" && exit 1)
    
    echo "Checking out main..."
    git checkout -f main || (echo "ERROR: git checkout failed!" && exit 1)
    
    echo "Pulling LFS files..."
    git lfs pull origin main || (echo "LFS pull failed, trying fetch+checkout..." && git lfs fetch origin main && git lfs checkout) || (echo "ERROR: LFS download failed!" && exit 1)
    
    echo "=== Verification ==="
    SIZE=$(stat -f%z data/vectordb/chroma.sqlite3 2>/dev/null || stat -c%s data/vectordb/chroma.sqlite3 2>/dev/null || echo 0)
    echo "chroma.sqlite3 size: $SIZE bytes"
    if [ "$SIZE" -lt 1000000 ]; then
        echo "ERROR: File is still a pointer file after download!"
        exit 1
    fi
    echo "SUCCESS: LFS files downloaded"
fi

