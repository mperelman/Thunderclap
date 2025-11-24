"""Check what years are in Vienna Rothschild chunks."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from query import ask
import re

# Run the actual query to see what chunks are retrieved
print("Running query to see what chunks are retrieved...")
result = ask("Tell me about Vienna Rothschild banking", use_llm=False)

# Extract years from the result
if "Found" in result and "relevant passages" in result:
    # Parse the chunks
    chunks_text = result.split("Found")[1] if "Found" in result else result
    
    # Extract all years
    years = re.findall(r'\b(1[6-9]\d{2}|20[0-2]\d)\b', chunks_text)
    years_int = [int(y) for y in years]
    
    if years_int:
        print(f"\nYears found in chunks: {sorted(set(years_int))}")
        print(f"Latest year: {max(years_int)}")
        print(f"Years >= 1900: {[y for y in sorted(set(years_int)) if y >= 1900]}")
        print(f"Years >= 1900 count: {len([y for y in years_int if y >= 1900])}")
    else:
        print("No years found in chunks")
else:
    print("Unexpected result format")
    print(result[:500])


