"""Test only UNIQUE keys"""
import google.generativeai as genai

# Only UNIQUE keys from .env
unique_keys = [
    ("Key A", "AIzaSyCGPsVN5zK8nWGR..."), # Appears 4x in .env
    ("Key B", "AIzaSyBaj9wvbB3n6Zjv..."),
    ("Key C", "AIzaSyAXr9YBivlfndzZ..."),
    ("Key D", "AIzaSyD-xExhXC66P-eU..."),
]

print("Testing 4 UNIQUE keys...\n")

for name, key_prefix in unique_keys:
    # Get full key
    if key_prefix == "AIzaSyCGPsVN5zK8nWGR...":
        full_key = "AIzaSyCGPsVN5zK8nWGRc6gNuniim4mJ16kNWZM"
    elif key_prefix == "AIzaSyBaj9wvbB3n6Zjv...":
        full_key = "AIzaSyBaj9wvbB3n6ZjvI89fFACl4SQgUfTaC4s"
    elif key_prefix == "AIzaSyAXr9YBivlfndzZ...":
        full_key = "AIzaSyAXr9YBivlfndzZ4azcm7g3yfgan4Xl_ls"
    elif key_prefix == "AIzaSyD-xExhXC66P-eU...":
        full_key = "AIzaSyD-xExhXC66P-eUuYzx5wwXifBvCwZYGMw"
    
    print(f"Testing {name}: {key_prefix}")
    
    try:
        genai.configure(api_key=full_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content("Say: reset")
        
        print(f"  [SUCCESS] Quota reset! Response: {response.text}")
        print(f"\n[WORKING KEY FOUND] {name}")
        print(f"Full key: {full_key}")
        break
        
    except Exception as e:
        error = str(e)
        if "429" in error:
            print(f"  [QUOTA] Still exhausted")
        else:
            print(f"  [ERROR] {error[:80]}")
    print()

print("\n[RESULT] Testing complete")

