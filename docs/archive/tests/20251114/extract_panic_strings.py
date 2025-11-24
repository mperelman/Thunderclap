"""Extract panic strings from prompts.pyc"""
import marshal

with open('lib/__pycache__/prompts.cpython-313.pyc', 'rb') as f:
    f.read(16)
    code = marshal.load(f)

strings = [c for c in code.co_consts if isinstance(c, str) and len(c) > 50]
panic_strings = [s for s in strings if 'panic' in s.lower() or 'PANIC' in s]

print(f'Found {len(panic_strings)} panic-related strings from prompts.py:')
print('='*70)
print()

for i, s in enumerate(panic_strings, 1):
    print(f"STRING {i}:")
    print(s)
    print()
    print('-'*70)
    print()

# Save to file
with open('temp/PANIC_FRAMEWORK_RECOVERED.txt', 'w', encoding='utf-8') as f:
    f.write(f'Found {len(panic_strings)} panic-related strings:\n\n')
    for i, s in enumerate(panic_strings, 1):
        f.write(f"STRING {i}:\n")
        f.write(s)
        f.write('\n\n')
        f.write('-'*70 + '\n\n')

print(f"[SAVED] Full content saved to temp/PANIC_FRAMEWORK_RECOVERED.txt")




