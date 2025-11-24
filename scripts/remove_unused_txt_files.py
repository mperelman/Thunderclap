"""
Remove unused individual .txt files from data/deduplicated_terms/
Only keeps deduplicated_cache.json which is actually used.
"""
import os
from pathlib import Path

def main():
    dedup_dir = Path("data/deduplicated_terms")
    
    if not dedup_dir.exists():
        print(f"Directory {dedup_dir} does not exist.")
        return
    
    # Find all .txt files
    txt_files = list(dedup_dir.glob("*.txt"))
    json_file = dedup_dir / "deduplicated_cache.json"
    
    print("Unused file cleanup:")
    print("=" * 60)
    print(f"  Directory: {dedup_dir}")
    print(f"  .txt files found: {len(txt_files)}")
    print(f"  JSON cache exists: {json_file.exists()}")
    
    if not txt_files:
        print("\n  No .txt files to remove.")
        return
    
    # Calculate total size
    total_size = sum(f.stat().st_size for f in txt_files)
    print(f"  Total size: {total_size / 1024 / 1024:.1f} MB")
    
    # Auto-proceed (non-interactive)
    print("\nProceeding with removing .txt files...")
    
    # Remove files
    print("\nRemoving .txt files...")
    removed = 0
    errors = 0
    
    for txt_file in txt_files:
        try:
            txt_file.unlink()
            removed += 1
            if removed % 1000 == 0:
                print(f"  Removed {removed} files...")
        except Exception as e:
            print(f"  Error removing {txt_file}: {e}")
            errors += 1
    
    print(f"\n✓ Cleanup complete!")
    print(f"  Removed: {removed} files")
    print(f"  Errors: {errors}")
    print(f"  Space freed: {total_size / 1024 / 1024:.1f} MB")
    print(f"  Kept: {json_file.name}")

if __name__ == "__main__":
    main()


