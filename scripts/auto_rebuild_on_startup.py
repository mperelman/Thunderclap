"""
Auto-Rebuild Index on Startup
==============================
Checks if source documents have changed and rebuilds the index if needed.
Runs automatically when Railway starts up.
"""
import os
import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.config import SOURCE_DOCS_DIR, DATA_DIR, INDICES_FILE
from lib.document_parser import get_cache_path

def get_source_doc_mtimes():
    """Get modification times for all source documents."""
    mtimes = {}
    if not os.path.exists(SOURCE_DOCS_DIR):
        return mtimes
    
    for filename in os.listdir(SOURCE_DOCS_DIR):
        if filename.endswith('.docx'):
            filepath = os.path.join(SOURCE_DOCS_DIR, filename)
            mtimes[filename] = os.path.getmtime(filepath)
    return mtimes

def get_last_build_info():
    """Get info about the last build."""
    build_info_file = os.path.join(DATA_DIR, '.last_build_info.json')
    if os.path.exists(build_info_file):
        with open(build_info_file, 'r') as f:
            return json.load(f)
    return None

def save_build_info(mtimes):
    """Save info about this build."""
    build_info_file = os.path.join(DATA_DIR, '.last_build_info.json')
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(build_info_file, 'w') as f:
        json.dump({
            'source_doc_mtimes': mtimes,
            'build_timestamp': os.path.getmtime(INDICES_FILE) if os.path.exists(INDICES_FILE) else 0
        }, f, indent=2)

def needs_rebuild():
    """Check if index needs to be rebuilt."""
    # If no index exists, we need to build
    if not os.path.exists(INDICES_FILE):
        print("  [REBUILD] No index found - rebuild needed")
        return True
    
    # Get current source document mtimes
    current_mtimes = get_source_doc_mtimes()
    if not current_mtimes:
        print("  [SKIP] No source documents found")
        return False
    
    # Get last build info
    last_build = get_last_build_info()
    if not last_build:
        print("  [REBUILD] No build info found - rebuild needed")
        return True
    
    # Check if any source documents changed
    last_mtimes = last_build.get('source_doc_mtimes', {})
    
    # Quick check: if file count changed, definitely need rebuild
    if len(current_mtimes) != len(last_mtimes):
        print(f"  [REBUILD] Source document count changed ({len(current_mtimes)} vs {len(last_mtimes)})")
        return True
    
    # Check for new or modified files (only check mtimes if counts match)
    for filename, mtime in current_mtimes.items():
        if filename not in last_mtimes:
            print(f"  [REBUILD] New source document: {filename}")
            return True
        if abs(mtime - last_mtimes[filename]) > 1:  # 1 second tolerance
            print(f"  [REBUILD] Modified source document: {filename}")
            return True
    
    # Check for deleted files
    for filename in last_mtimes:
        if filename not in current_mtimes:
            print(f"  [REBUILD] Deleted source document: {filename}")
            return True
    
    print("  [SKIP] No changes detected - using existing index")
    return False

def rebuild_index():
    """Rebuild the index."""
    print("\n" + "="*80)
    print("AUTO-REBUILDING INDEX")
    print("="*80 + "\n")
    
    try:
        from build_index import build_complete_index
        build_complete_index()
        
        # Save build info
        save_build_info(get_source_doc_mtimes())
        
        print("\n[SUCCESS] Index rebuilt successfully!")
        return True
    except Exception as e:
        print(f"\n[ERROR] Failed to rebuild index: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_and_rebuild():
    """Check if rebuild is needed and rebuild if so."""
    print("\n[STARTUP] Checking if index needs rebuild...")
    
    if needs_rebuild():
        return rebuild_index()
    else:
        return True

if __name__ == "__main__":
    success = check_and_rebuild()
    sys.exit(0 if success else 1)
