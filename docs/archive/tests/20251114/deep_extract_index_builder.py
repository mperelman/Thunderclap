"""Deep extraction from index_builder.pyc"""
import marshal
import dis

with open('lib/__pycache__/index_builder.cpython-313.pyc', 'rb') as f:
    f.read(16)
    code = marshal.load(f)

print("="*70)
print("DEEP EXTRACTION FROM index_builder.cpython-313.pyc")
print("="*70)
print()

# Disassemble to see the code structure
print("Disassembling bytecode...")
print()
dis.dis(code)

print()
print("="*70)
print("Searching nested code objects for TERM_GROUPS...")
print("="*70)
print()

# Look in nested code objects
for const in code.co_consts:
    if hasattr(const, 'co_consts'):  # It's a code object
        for nested in const.co_consts:
            if isinstance(nested, dict) and len(nested) > 5:
                print(f"Found dict in nested code: {len(nested)} entries")
                for k in list(nested.keys())[:20]:
                    print(f"  {k}: {nested[k]}")




