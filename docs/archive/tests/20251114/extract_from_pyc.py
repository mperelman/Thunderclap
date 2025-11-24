"""Extract TERM_GROUPS from index_builder.pyc"""

import marshal
import types

print("="*70)
print("EXTRACTING FROM index_builder.cpython-313.pyc")
print("="*70)
print()

try:
    with open('lib/__pycache__/index_builder.cpython-313.pyc', 'rb') as f:
        # Skip header (16 bytes in Python 3.13)
        f.read(16)
        
        # Load code object
        code = marshal.load(f)
        
        print("Code object loaded successfully")
        print(f"Constants found: {len(code.co_consts)}")
        print()
        
        # Look for dictionaries (TERM_GROUPS would be a dict)
        print("Looking for TERM_GROUPS dictionary...")
        print()
        
        for const in code.co_consts:
            if isinstance(const, dict) and len(const) > 5:
                print(f"Found dictionary with {len(const)} entries:")
                for key in list(const.keys())[:10]:
                    print(f"  {key}: {const[key]}")
                print()
        
        # Look for strings mentioning panic
        print("Looking for panic-related strings...")
        panic_strings = []
        for const in code.co_consts:
            if isinstance(const, str) and 'panic' in const.lower():
                panic_strings.append(const)
        
        if panic_strings:
            print(f"Found {len(panic_strings)} panic-related strings:")
            for s in panic_strings[:20]:
                print(f"  {s}")
        else:
            print("No panic-related strings in top-level constants")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()




