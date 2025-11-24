"""Test if quota actually reset"""
import google.generativeai as genai

# The 7 keys that were working (just exhausted)
keys = [
    ("Key #3", "AIzaSyAXr9YBivlfndzZ4azcm7g3yfgan4Xl_ls"),
    ("Key #5", "AIzaSyD-xExhXC66P-eUuYzx5wwXifBvCwZYGMw"),
    ("Key #7", "AIzaSyArWNIqSYcmh_KvWLxlxew2TZxj4lASfo4"),
    ("Key #8", "AIzaSyBwFhYh5ri6tBvFPtpuFgV1SzyEbObt1lo"),
    ("Key #9", "AIzaSyAYF4mxq6tnL_eYWU0JVHVUOEXTVCfo1vU"),
    ("Key #10", "AIzaSyC2Rwp54ZJFVK173fMV2G6agGIjqjG0-aA"),
    ("Key #11", "AIzaSyCGPsVN5zK8nWGRc6gNuniim4mJ16kNWZM"),
]

print("Testing if quota reset...\n")

working = None

for name, key in keys:
    print(f"Testing {name}: {key[:20]}...")
    
    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content("Say: working")
        
        print(f"  [SUCCESS] This key works! Response: {response.text}")
        working = (name, key)
        break
        
    except Exception as e:
        error = str(e)
        if "429" in error:
            print(f"  [QUOTA] Still exhausted")
        elif "400" in error or "invalid" in error.lower():
            print(f"  [INVALID] Key invalid")
        else:
            print(f"  [ERROR] {error[:50]}")

if working:
    print(f"\n[FOUND] {working[0]} has quota!")
    print("Updating .env and proceeding...")
else:
    print("\n[EXHAUSTED] All 7 keys still quota exceeded")
    print("Quotas have NOT reset yet")


