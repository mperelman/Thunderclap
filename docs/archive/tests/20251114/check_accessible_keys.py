"""Check how many API keys are accessible"""
import os
from dotenv import load_dotenv

load_dotenv()

print("Checking accessible API keys...\n")

# Check main key
gemini_main = os.getenv('GEMINI_API_KEY')
print(f"GEMINI_API_KEY: {'SET' if gemini_main else 'NOT SET'}")

# Check numbered keys
numbered_keys = []
i = 1
while True:
    key = os.getenv(f'GEMINI_API_KEY_{i}')
    if key:
        numbered_keys.append(key)
        i += 1
    else:
        break

print(f"GEMINI_API_KEY_1 to GEMINI_API_KEY_{len(numbered_keys)}: {len(numbered_keys)} keys")

# Count unique
all_keys = [gemini_main] if gemini_main else []
all_keys.extend(numbered_keys)

unique_keys = len(set(all_keys))

print()
print("="*60)
print(f"TOTAL KEYS IN .ENV: {len(all_keys)}")
print(f"UNIQUE KEYS: {unique_keys}")
print("="*60)

if unique_keys == 0:
    print("\n[RESULT] NO API KEYS - System has zero keys")
else:
    print(f"\n[RESULT] System has {unique_keys} unique API keys")


