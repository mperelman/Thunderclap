"""Test all API keys provided by user"""
import google.generativeai as genai

# All keys provided by user
keys = [
    # SECURITY: Keys removed - use environment variables only
    # Never commit real API keys to git
    ("Key #1", "REVOKED_KEY_REMOVED"),
    ("Key #2", "REVOKED_KEY_REMOVED"),
    ("Key #3", "REVOKED_KEY_REMOVED"),
    ("Key #4", "REVOKED_KEY_REMOVED"),
    ("Key #5", "AIzaSyD-xExhXC66P-eUuYzx5wwXifBvCwZYGMw"),
    ("Key #6", "AIzaSyBcl-noOJDWb3tTXSQYibMsH6kOf9uQn0o"),
    ("Key #7 (new)", "AIzaSyArWNIqSYcmh_KvWLxlxew2TZxj4lASfo4"),
    ("Key #8 (fresh)", "AIzaSyBwFhYh5ri6tBvFPtpuFgV1SzyEbObt1lo"),
    ("Key #9 (replaced)", "AIzaSyAYF4mxq6tnL_eYWU0JVHVUOEXTVCfo1vU"),
    ("Key #10 (diff proj)", "AIzaSyC2Rwp54ZJFVK173fMV2G6agGIjqjG0-aA"),
    ("Key #11 (diff acct)", "REVOKED_KEY_REMOVED"),  # REMOVED: Exposed key revoked
    ("Key #12 (new)", "AIzaSyBCFDWaXScB3Da9JzkWQKr7YdzvdPyYhfg"),  # New key created after revoking Key #11
    ("Key #13", "AIzaSyCnqzks44i0YRoKTNISuzKFsWO7TeK4nO8"),  # New key (replaced exposed key)
    ("Key #14", "AIzaSyCdiaYw8WDVMHJzyVcwE0MKv7XwN7n3-HY"),  # New key (replaced exposed key)
    ("Key #15", "AIzaSyB6dV7ltiedJ7m37Dt61I4rQNavz5-RoXo"),  # New key (replaced exposed key)
    ("Key #16", "AIzaSyBiTjP0b0m7Dc26VnLsnXbjtpkNxWCewlo"),  # New key (replaced exposed key)
    ("Key #17", "AIzaSyBWBg-vd6SkWCeLz386d8R7oUaHrkEesQg"),  # New key (replaced exposed key)
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

