"""Check if specific key exists"""
import os
from dotenv import load_dotenv

load_dotenv()

target = 'AIzaSyD-xExhXC66P-eUuYzx5wwXifBvCwZYGMw'

# Check all possible key locations
found = False
for i in range(20):
    if i == 0:
        key_name = 'GEMINI_API_KEY'
    else:
        key_name = f'GEMINI_API_KEY_{i}'
    
    val = os.getenv(key_name)
    if val == target:
        print(f"[FOUND] {key_name} = {val[:20]}...")
        found = True
        break

if not found:
    print(f"[NOT FOUND] Key {target[:20]}... is NOT in .env")


