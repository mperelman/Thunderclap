"""Recover TERM_GROUPS from index_builder.pyc"""
import dis
import marshal
import sys

print("="*70)
print("RECOVERING TERM_GROUPS FROM BYTECODE")
print("="*70)
print()

# Read the .pyc file
with open('lib/__pycache__/index_builder.cpython-313.pyc', 'rb') as f:
    # Skip magic number and timestamp (16 bytes for Python 3.13)
    f.read(16)
    code = marshal.load(f)

print(f"Code object loaded: {code.co_name}")
print(f"Total constants: {len(code.co_consts)}")
print()

# Search for dictionaries that might be TERM_GROUPS
print("Searching for TERM_GROUPS dictionary...")
print()

found_term_groups = False

for i, const in enumerate(code.co_consts):
    # TERM_GROUPS would be a dict with string keys
    if isinstance(const, dict) and len(const) > 10:
        # Check if keys look like term names
        keys = list(const.keys())
        if all(isinstance(k, str) for k in keys[:5]):
            print(f"Found dictionary at position {i} with {len(const)} entries:")
            print()
            
            # Show first 30 entries
            for key in sorted(keys)[:30]:
                value = const[key]
                if isinstance(value, list):
                    print(f"  '{key}': {value}")
                else:
                    print(f"  '{key}': ...")
            
            if len(keys) > 30:
                print(f"  ... and {len(keys)-30} more entries")
            
            print()
            
            # Save full dict to file
            import json
            with open('temp/TERM_GROUPS_FULL.json', 'w') as out:
                json.dump(const, out, indent=2)
            
            print(f"[SAVED] Full dictionary saved to temp/TERM_GROUPS_FULL.json")
            found_term_groups = True
            break

if not found_term_groups:
    print("Could not find TERM_GROUPS dictionary in bytecode constants")
    print()
    print("Showing all large data structures:")
    for i, const in enumerate(code.co_consts):
        if isinstance(const, (dict, list, tuple)) and len(str(const)) > 100:
            print(f"  Position {i}: {type(const).__name__} - {len(str(const))} chars")




