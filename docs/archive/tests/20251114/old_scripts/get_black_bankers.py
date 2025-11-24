"""Quick script to get Black bankers narrative"""
from query import ask
import sys

# Set UTF-8 encoding for output
sys.stdout.reconfigure(encoding='utf-8')

result = ask('tell me about black bankers', use_llm=True)

# Write to file as backup
with open('black_bankers_final.txt', 'w', encoding='utf-8') as f:
    f.write(result)

print(result)

