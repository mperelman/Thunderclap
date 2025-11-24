"""Count API keys in .env"""
import os
from dotenv import load_dotenv

load_dotenv()

keys = []

# Check GEMINI_API_KEY
key = os.getenv('GEMINI_API_KEY')
if key:
    keys.append(('GEMINI_API_KEY', key))

# Check numbered keys
i = 1
while True:
    key = os.getenv(f'GEMINI_API_KEY_{i}')
    if key:
        keys.append((f'GEMINI_API_KEY_{i}', key))
        i += 1
    else:
        break

print(f"Total API keys in .env: {len(keys)}")
print()

for name, key in keys:
    print(f"{name}: {key[:20]}...")

