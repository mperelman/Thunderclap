#!/bin/bash
# Download LFS files if they're missing, pointer files, or corrupted
# Updated: 2025-01-21 - Added volume space checks and cleanup

echo "=== Checking LFS files ==="

# Check if /app/data is on a volume (Railway volumes are mounted)
if mountpoint -q /app/data 2>/dev/null; then
    echo "SUCCESS: /app/data is mounted on a volume (persistent storage)"
elif [ -d "/var/lib/containers/railwayapp/bind-mounts" ]; then
    echo "WARNING: Railway volume detected but NOT mounted at /app/data"
    echo "The volume is mounted elsewhere. /app/data is using container filesystem (limited space)."
    echo "To fix: In Railway dashboard, mount the volume at /app/data"
else
    echo "INFO: No Railway volume detected. Using container filesystem (limited space)."
fi

NEED_DOWNLOAD=false
NEED_VERIFY=true

# Check if chroma.sqlite3 exists and is a real file (not pointer)
if [ -f "data/vectordb/chroma.sqlite3" ]; then
    SIZE=$(stat -f%z data/vectordb/chroma.sqlite3 2>/dev/null || stat -c%s data/vectordb/chroma.sqlite3 2>/dev/null || echo 0)
    SIZE_MB=$((SIZE / 1024 / 1024))
    echo "chroma.sqlite3 exists, size: $SIZE bytes ($SIZE_MB MB)"
    
    if [ "$SIZE" -lt 1000000 ]; then
        echo "File is a pointer file (too small), need to download..."
        NEED_DOWNLOAD=true
    elif [ "$SIZE" -lt 150000000 ]; then
        echo "WARNING: File is smaller than expected (~177MB). May be incomplete. Will verify integrity..."
        NEED_VERIFY=true
    else
        echo "File size looks good, verifying integrity..."
        NEED_VERIFY=true
    fi
else
    echo "chroma.sqlite3 not found"
    NEED_DOWNLOAD=true
fi

# Always verify integrity if file exists
if [ "$NEED_VERIFY" = true ] && [ -f "data/vectordb/chroma.sqlite3" ]; then
    echo "=== Verifying SQLite database integrity ==="
    sqlite3 data/vectordb/chroma.sqlite3 "PRAGMA integrity_check;" > /tmp/integrity_check.txt 2>&1
    INTEGRITY_RESULT=$(cat /tmp/integrity_check.txt)
    if echo "$INTEGRITY_RESULT" | grep -q "ok"; then
        echo "SUCCESS: Database integrity check passed"
    else
        echo "ERROR: Database integrity check failed:"
        echo "$INTEGRITY_RESULT"
        echo "Database is corrupted. Will re-download..."
        rm -f data/vectordb/chroma.sqlite3
        NEED_DOWNLOAD=true
    fi
fi

if [ "$NEED_DOWNLOAD" = true ]; then
    echo "=== Initializing git and downloading LFS files ==="
    echo "Checking git availability..."
    which git || (echo "ERROR: git not found!" && exit 1)
    which git-lfs || (echo "ERROR: git-lfs not found!" && exit 1)
    
    echo "=== Checking disk space ==="
    df -h /app/data 2>/dev/null || df -h /app
    # Check space on /app/data if it's a volume, otherwise /app
    if mountpoint -q /app/data 2>/dev/null; then
        AVAILABLE=$(df /app/data | tail -1 | awk '{print $4}')
        TOTAL=$(df /app/data | tail -1 | awk '{print $2}')
        USED=$(df /app/data | tail -1 | awk '{print $3}')
        PERCENT=$((USED * 100 / TOTAL))
        echo "Volume space: $USED KB used / $TOTAL KB total ($PERCENT% used)"
        echo "Available space: $AVAILABLE KB"
    else
        AVAILABLE=$(df /app | tail -1 | awk '{print $4}')
        echo "Available space: $AVAILABLE KB"
    fi
    
    # Need at least 250MB free (197MB data + overhead)
    if [ "$AVAILABLE" -lt 250000 ]; then
        echo "WARNING: Low disk space ($AVAILABLE KB). Cleaning up volume..."
        # Remove corrupted/partial database files
        echo "Removing corrupted/incomplete database files..."
        rm -f data/vectordb/chroma.sqlite3 2>/dev/null || true
        rm -rf data/vectordb/*/ 2>/dev/null || true  # Remove ChromaDB index directories
        # Remove old cache files if they exist
        find data/ -name "*.tmp" -delete 2>/dev/null || true
        find data/ -name "*.bak" -delete 2>/dev/null || true
        # Remove git history if it exists on volume
        rm -rf .git/objects/* 2>/dev/null || true
        rm -rf .git/lfs/* 2>/dev/null || true
        
        echo "After cleanup:"
        if mountpoint -q /app/data 2>/dev/null; then
            AVAILABLE=$(df /app/data | tail -1 | awk '{print $4}')
            TOTAL=$(df /app/data | tail -1 | awk '{print $2}')
            USED=$(df /app/data | tail -1 | awk '{print $3}')
            PERCENT=$((USED * 100 / TOTAL))
            echo "Volume space: $USED KB used / $TOTAL KB total ($PERCENT% used)"
            echo "Available space: $AVAILABLE KB"
        else
            AVAILABLE=$(df /app | tail -1 | awk '{print $4}')
            echo "Available space: $AVAILABLE KB"
        fi
        
        if [ "$AVAILABLE" -lt 250000 ]; then
            echo "ERROR: Still not enough space after cleanup ($AVAILABLE KB)."
            echo ""
            echo "SOLUTION: Increase Railway Volume size:"
            echo "1. Go to Railway dashboard → Volumes"
            echo "2. Find 'web-volume' (currently 99% full)"
            echo "3. Increase size to at least 1GB (or create new 1GB+ volume)"
            echo "4. Remount at /app/data"
            echo ""
            exit 1
        fi
    fi
    
    echo "Initializing git repo..."
    git init || (echo "ERROR: git init failed!" && exit 1)
    git config user.name "Railway" || true
    git config user.email "railway@railway.app" || true
    
    echo "Adding remote..."
    git remote add origin https://github.com/mperelman/Thunderclap.git || git remote set-url origin https://github.com/mperelman/Thunderclap.git
    
    echo "Fetching main branch..."
    git fetch origin main || (echo "ERROR: git fetch failed!" && exit 1)
    
    echo "Removing corrupted/incomplete files before checkout..."
    rm -rf data/vectordb/* 2>/dev/null || true
    
    echo "Checking out main..."
    git checkout -f origin/main || git checkout -f main || (echo "ERROR: git checkout failed!" && exit 1)
    
    echo "Pulling LFS files..."
    git lfs pull origin main || (echo "LFS pull failed, trying fetch+checkout..." && git lfs fetch origin main && git lfs checkout) || (echo "ERROR: LFS download failed!" && exit 1)
    
    echo "=== Verification ==="
    SIZE=$(stat -f%z data/vectordb/chroma.sqlite3 2>/dev/null || stat -c%s data/vectordb/chroma.sqlite3 2>/dev/null || echo 0)
    echo "chroma.sqlite3 size: $SIZE bytes ($(echo "scale=2; $SIZE/1024/1024" | bc) MB)"
    if [ "$SIZE" -lt 1000000 ]; then
        echo "ERROR: File is still a pointer file after download!"
        exit 1
    fi
    # Verify SQLite database integrity
    echo "=== Verifying SQLite database integrity ==="
    sqlite3 data/vectordb/chroma.sqlite3 "PRAGMA integrity_check;" > /tmp/integrity_check.txt 2>&1
    INTEGRITY_RESULT=$(cat /tmp/integrity_check.txt)
    if echo "$INTEGRITY_RESULT" | grep -q "ok"; then
        echo "SUCCESS: Database integrity check passed"
    else
        echo "WARNING: Database integrity check failed:"
        echo "$INTEGRITY_RESULT"
        echo "Database may be corrupted. Attempting to re-download..."
        rm -f data/vectordb/chroma.sqlite3
        git lfs pull origin main || (git lfs fetch origin main && git lfs checkout)
        echo "Re-verifying after re-download..."
        sqlite3 data/vectordb/chroma.sqlite3 "PRAGMA integrity_check;" > /tmp/integrity_check2.txt 2>&1
        if ! grep -q "ok" /tmp/integrity_check2.txt; then
            echo "ERROR: Database still corrupted after re-download!"
            exit 1
        fi
    fi
    echo "SUCCESS: LFS files downloaded and verified"
fi

