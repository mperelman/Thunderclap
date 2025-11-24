"""
Cleanup script to organize archives while preserving them.
Moves archives to organized structure in docs/archive/
"""
import os
import shutil
from pathlib import Path

def main():
    base_dir = Path(".")
    archive_dir = base_dir / "docs" / "archive"
    
    # Create archive structure
    archive_dir.mkdir(parents=True, exist_ok=True)
    (archive_dir / "lib_code").mkdir(exist_ok=True)
    (archive_dir / "sessions").mkdir(exist_ok=True)
    (archive_dir / "tests").mkdir(exist_ok=True)
    
    moves = []
    
    # Move lib archives
    lib_archives = [
        ("lib/archived", "lib_code/archived"),
        ("lib/archived_20251113_RESTORED", "lib_code/archived_20251113_RESTORED"),
        ("lib/archived_20251114_CLEANUP", "lib_code/archived_20251114_CLEANUP"),
        ("lib/archived_deduplication", "lib_code/archived_deduplication"),
    ]
    
    for src, dst in lib_archives:
        src_path = base_dir / src
        dst_path = archive_dir / dst
        if src_path.exists():
            moves.append((src_path, dst_path))
    
    # Move session archives
    session_archives = [
        ("temp/archived_session_20250121", "sessions/20250121"),
        ("temp/archived_tests_20251114", "tests/20251114"),
    ]
    
    for src, dst in session_archives:
        src_path = base_dir / src
        dst_path = archive_dir / dst
        if src_path.exists():
            moves.append((src_path, dst_path))
    
    # Show what will be moved
    print("Archive cleanup plan:")
    print("=" * 60)
    for src, dst in moves:
        if src.exists():
            size = sum(f.stat().st_size for f in src.rglob('*') if f.is_file())
            print(f"  {src} -> {archive_dir / dst}")
            print(f"    ({len(list(src.rglob('*')))} items, {size / 1024 / 1024:.1f} MB)")
    
    if not moves:
        print("  No archives found to move.")
        return
    
    # Auto-proceed (non-interactive)
    print("\nProceeding with moving archives...")
    
    # Perform moves
    print("\nMoving archives...")
    for src, dst in moves:
        if src.exists():
            dst_full = archive_dir / dst
            if dst_full.exists():
                print(f"  WARNING: {dst_full} already exists, skipping {src}")
                continue
            try:
                shutil.move(str(src), str(dst_full))
                print(f"  ✓ Moved {src} -> {dst_full}")
            except Exception as e:
                print(f"  ✗ Error moving {src}: {e}")
    
    print("\n✓ Archive cleanup complete!")
    print(f"  Archives are now in: {archive_dir}")

if __name__ == "__main__":
    main()


