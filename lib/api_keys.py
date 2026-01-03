"""
Centralized API Keys Configuration
===================================
ALL API keys are managed in this single file.
To add, remove, or update keys, edit ONLY this file.

IMPORTANT: This file should NOT be committed to git if it contains real keys.
Add it to .gitignore or use environment variables for production.
"""

# List of all API keys for multi-key rotation
# Format: List of key strings (starting with "AIza")
# Keys marked as "REVOKED_KEY_REMOVED" are excluded automatically

API_KEYS = [
    "AIzaSyBlqE1F2G_L5l2Lg81gyt0UWcME_K3inFo",  # Key #1
    "AIzaSyBaj9wvbB3n6ZjvI89fFACl4SQgUfTaC4s",  # Key #2
    "AIzaSyAXr9YBivlfndzZ4azcm7g3yfgan4Xl_ls",  # Key #3
    "AIzaSyBPeY_SCL9EdpmnDbmeYSI7r5wJ-JaT6Fc",  # Key #4
    "AIzaSyD-xExhXC66P-eUuYzx5wwXifBvCwZYGMw",  # Key #5
    "AIzaSyBcl-noOJDWb3tTXSQYibMsH6kOf9uQn0o",  # Key #6
    "AIzaSyArWNIqSYcmh_KvWLxlxew2TZxj4lASfo4",  # Key #7
    "AIzaSyBwFhYh5ri6tBvFPtpuFgV1SzyEbObt1lo",  # Key #8
    "AIzaSyAYF4mxq6tnL_eYWU0JVHVUOEXTVCfo1vU",  # Key #9
    "AIzaSyC2Rwp54ZJFVK173fMV2G6agGIjqjG0-aA",  # Key #10
    # Key #11: REVOKED (was exposed, removed from git history)
    "AIzaSyBCFDWaXScB3Da9JzkWQKr7YdzvdPyYhfg",  # Key #12
    "AIzaSyCnqzks44i0YRoKTNISuzKFsWO7TeK4nO8",  # Key #13
    "AIzaSyCdiaYw8WDVMHJzyVcwE0MKv7XwN7n3-HY",  # Key #14
    "AIzaSyB6dV7ltiedJ7m37Dt61I4rQNavz5-RoXo",  # Key #15
    "AIzaSyBiTjP0b0m7Dc26VnLsnXbjtpkNxWCewlo",  # Key #16
    "AIzaSyBWBg-vd6SkWCeLz386d8R7oUaHrkEesQg",  # Key #17
]


def get_api_keys() -> list:
    """
    Get list of valid API keys.
    
    Returns:
        List of API key strings (filters out revoked/invalid keys)
    """
    return [
        key for key in API_KEYS
        if key and key != "REVOKED_KEY_REMOVED" and key.startswith("AIza")
    ]
