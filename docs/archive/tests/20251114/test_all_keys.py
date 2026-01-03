"""Test all API keys provided by user"""
import google.generativeai as genai

# SECURITY: All keys removed - use environment variables only
# Never commit real API keys to git
# This file is kept for reference but should not contain real keys
keys = [
    ("Key #1", "REVOKED_KEY_REMOVED"),
    ("Key #2", "REVOKED_KEY_REMOVED"),
    ("Key #3", "REVOKED_KEY_REMOVED"),
    ("Key #4", "REVOKED_KEY_REMOVED"),
    ("Key #5", "REVOKED_KEY_REMOVED"),
    ("Key #6", "REVOKED_KEY_REMOVED"),
    ("Key #7", "REVOKED_KEY_REMOVED"),
    ("Key #8", "REVOKED_KEY_REMOVED"),
    ("Key #9", "REVOKED_KEY_REMOVED"),
    ("Key #10", "REVOKED_KEY_REMOVED"),
    ("Key #11", "REVOKED_KEY_REMOVED"),
    ("Key #12", "REVOKED_KEY_REMOVED"),
    ("Key #13", "REVOKED_KEY_REMOVED"),
    ("Key #14", "REVOKED_KEY_REMOVED"),
    ("Key #15", "REVOKED_KEY_REMOVED"),
    ("Key #16", "REVOKED_KEY_REMOVED"),
    ("Key #17", "REVOKED_KEY_REMOVED"),
]

print("="*70)
print("TESTING ALL API KEYS")
print("="*70)
print()

working_keys = []
quota_exceeded = []
invalid_keys = []

for name, key in keys:
    print(f"Testing {name}: {key[:20]}...")
    
    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content("Say: ok")
        
        print(f"  [SUCCESS] Working! Response: {response.text}")
        working_keys.append(name)
        
    except Exception as e:
        error_msg = str(e)
        
        if "429" in error_msg or "quota" in error_msg.lower():
            print(f"  [QUOTA] Exhausted")
            quota_exceeded.append(name)
        elif "400" in error_msg or "API_KEY_INVALID" in error_msg or "expired" in error_msg.lower():
            print(f"  [INVALID] Key invalid or expired")
            invalid_keys.append(name)
        else:
            print(f"  [ERROR] {error_msg[:80]}")
    
    print()

print("="*70)
print("SUMMARY")
print("="*70)
print(f"Working keys: {len(working_keys)}")
for k in working_keys:
    print(f"  - {k}")
print()

print(f"Quota exceeded: {len(quota_exceeded)}")
for k in quota_exceeded:
    print(f"  - {k}")
print()

print(f"Invalid/Expired: {len(invalid_keys)}")
for k in invalid_keys:
    print(f"  - {k}")

