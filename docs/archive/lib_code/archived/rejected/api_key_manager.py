"""
API Key Manager - Rotates through multiple Gemini API keys to maximize throughput.
Each key has 200 RPD (requests per day), so N keys = 200N requests per day.
"""
import os
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()


class APIKeyManager:
    """Manages multiple API keys with automatic rotation on quota exhaustion."""
    
    def __init__(self, keys: Optional[List[str]] = None):
        """
        Initialize with list of API keys.
        
        Args:
            keys: List of API keys (if None, loads from environment)
        """
        if keys:
            self.keys = keys
        else:
            # Load from environment - supports multiple keys
            self.keys = []
            
            # Check for single key
            single_key = os.getenv('GEMINI_API_KEY')
            if single_key:
                self.keys.append(single_key)
            
            # Check for numbered keys (GEMINI_API_KEY_1, _2, _3, etc.)
            i = 1
            while True:
                key = os.getenv(f'GEMINI_API_KEY_{i}')
                if key:
                    self.keys.append(key)
                    i += 1
                else:
                    break
        
        if not self.keys:
            raise ValueError("No API keys found. Set GEMINI_API_KEY or GEMINI_API_KEY_1, _2, etc. in .env")
        
        self.current_index = 0
        self.failed_keys = set()
        
        print(f"[API KEY MANAGER] Loaded {len(self.keys)} API keys")
        print(f"  Daily capacity: {len(self.keys)} × 200 RPD = {len(self.keys) * 200} requests/day")
    
    def get_current_key(self) -> str:
        """Get the current active API key."""
        return self.keys[self.current_index]
    
    def rotate_to_next(self):
        """Rotate to next available API key."""
        self.failed_keys.add(self.current_index)
        
        # Try next key
        attempts = 0
        while attempts < len(self.keys):
            self.current_index = (self.current_index + 1) % len(self.keys)
            
            if self.current_index not in self.failed_keys:
                print(f"  [ROTATE] Switched to API key #{self.current_index + 1}")
                return True
            
            attempts += 1
        
        # All keys exhausted
        print(f"  [EXHAUSTED] All {len(self.keys)} API keys quota exceeded")
        return False
    
    def mark_key_exhausted(self, key_index: Optional[int] = None):
        """Mark a key as quota exhausted."""
        if key_index is None:
            key_index = self.current_index
        
        self.failed_keys.add(key_index)
        print(f"  [QUOTA] Key #{key_index + 1} exhausted ({len(self.failed_keys)}/{len(self.keys)} keys used)")
    
    def all_exhausted(self) -> bool:
        """Check if all keys are exhausted."""
        return len(self.failed_keys) >= len(self.keys)
    
    def get_remaining_capacity(self) -> int:
        """Get remaining daily capacity across all keys."""
        remaining_keys = len(self.keys) - len(self.failed_keys)
        return remaining_keys * 200  # Assume 200 RPD per key


# Example .env format:
# GEMINI_API_KEY_1=AIzaSyBlqE1F2G_L5l2Lg81gyt0UWcME_K3inFo
# GEMINI_API_KEY_2=AIzaSyBaj9wvbB3n6ZjvI89fFACl4SQgUfTaC4s
# GEMINI_API_KEY_3=AIzaSyAXr9YBivlfndzZ4azcm7g3yfgan4Xl_ls

