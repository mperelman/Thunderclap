"""
API Key Manager - Manages multiple API keys with rotation and rate limiting.
Distributes load across multiple keys to avoid quota exhaustion.
"""
import os
import time
import threading
from typing import List, Optional, Dict
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class KeyStatus:
    """Status tracking for an API key."""
    key: str
    name: str
    last_used: float = 0.0
    request_count: int = 0
    exhausted: bool = False
    error_count: int = 0
    # Rate limiting: track requests per minute
    request_times: deque = None
    
    def __post_init__(self):
        if self.request_times is None:
            self.request_times = deque(maxlen=15)  # Track last 15 requests (15 RPM limit)


class APIKeyManager:
    """
    Manages multiple API keys with rotation, rate limiting, and exhaustion tracking.
    
    Features:
    - Cycles through available keys
    - Tracks rate limits per key (15 RPM per key)
    - Marks keys as exhausted on quota errors
    - Distributes load across all keys
    """
    
    def __init__(self, api_keys: Optional[List[str]] = None):
        """
        Initialize key manager.
        
        Args:
            api_keys: List of API keys. If None, loads from test file or env.
        """
        self.keys: List[KeyStatus] = []
        self.current_index = 0
        self.lock = threading.Lock()
        
        # Load keys
        if api_keys:
            for i, key in enumerate(api_keys):
                if key and key != "REVOKED_KEY_REMOVED" and key.startswith("AIza"):
                    self.keys.append(KeyStatus(key=key, name=f"Key #{i+1}"))
        else:
            self._load_keys_from_test_file()
        
        if not self.keys:
            # Fallback to environment variable
            env_key = os.getenv('GEMINI_API_KEY')
            if env_key and env_key.startswith("AIza"):
                self.keys.append(KeyStatus(key=env_key, name="Env Key"))
        
        if not self.keys:
            raise ValueError("No valid API keys found. Set GEMINI_API_KEY or provide keys list.")
        
        print(f"[KEY_MANAGER] Initialized with {len(self.keys)} API keys")
        for i, key_status in enumerate(self.keys):
            print(f"  [{i+1}] {key_status.name}: {key_status.key[:20]}...")
    
    def _load_keys_from_test_file(self):
        """Load keys from test_all_keys.py file."""
        try:
            import json
            # Try to load from a config file first
            config_file = "data/api_keys.json"
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    data = json.load(f)
                    keys = data.get('keys', [])
                    for i, key in enumerate(keys):
                        if key and key != "REVOKED_KEY_REMOVED" and key.startswith("AIza"):
                            self.keys.append(KeyStatus(key=key, name=f"Key #{i+1}"))
                    return
            
            # Fallback: try to parse from test file
            test_file = "docs/archive/tests/20251114/test_all_keys.py"
            if os.path.exists(test_file):
                with open(test_file, 'r') as f:
                    content = f.read()
                    import re
                    # Extract keys from the keys list
                    pattern = r'"AIza[^"]+"'
                    matches = re.findall(pattern, content)
                    for i, match in enumerate(matches):
                        key = match.strip('"')
                        if key != "REVOKED_KEY_REMOVED":
                            self.keys.append(KeyStatus(key=key, name=f"Key #{i+1}"))
        except Exception as e:
            print(f"[KEY_MANAGER] Warning: Could not load keys from test file: {e}")
    
    def get_next_key(self, delay_seconds: float = 4.0) -> Optional[str]:
        """
        Get the next available API key with rate limiting.
        
        Args:
            delay_seconds: Minimum delay between requests for the same key (default 4s = 15 RPM)
        
        Returns:
            API key string, or None if all keys exhausted
        """
        with self.lock:
            # Find next available key
            attempts = 0
            while attempts < len(self.keys):
                key_status = self.keys[self.current_index]
                
                # Check if key is exhausted
                if key_status.exhausted:
                    self.current_index = (self.current_index + 1) % len(self.keys)
                    attempts += 1
                    continue
                
                # Check rate limit: need at least delay_seconds since last use
                now = time.time()
                time_since_last = now - key_status.last_used
                
                if time_since_last < delay_seconds:
                    # This key needs to wait - try next key
                    self.current_index = (self.current_index + 1) % len(self.keys)
                    attempts += 1
                    continue
                
                # Check RPM limit: remove requests older than 1 minute
                while key_status.request_times and (now - key_status.request_times[0]) > 60:
                    key_status.request_times.popleft()
                
                # If we've hit 15 requests in the last minute, skip this key
                if len(key_status.request_times) >= 15:
                    self.current_index = (self.current_index + 1) % len(self.keys)
                    attempts += 1
                    continue
                
                # Key is available - use it
                key_status.last_used = now
                key_status.request_count += 1
                key_status.request_times.append(now)
                
                # Move to next key for round-robin
                next_index = (self.current_index + 1) % len(self.keys)
                self.current_index = next_index
                
                return key_status.key
            
            # All keys exhausted or rate-limited
            return None
    
    def mark_key_exhausted(self, key: str):
        """Mark a key as exhausted (quota error)."""
        with self.lock:
            for key_status in self.keys:
                if key_status.key == key:
                    key_status.exhausted = True
                    print(f"[KEY_MANAGER] Marked {key_status.name} as exhausted")
                    return
    
    def mark_key_error(self, key: str):
        """Increment error count for a key."""
        with self.lock:
            for key_status in self.keys:
                if key_status.key == key:
                    key_status.error_count += 1
                    # Mark exhausted after 3 consecutive errors
                    if key_status.error_count >= 3:
                        key_status.exhausted = True
                        print(f"[KEY_MANAGER] Marked {key_status.name} as exhausted after {key_status.error_count} errors")
                    return
    
    def reset_key_errors(self, key: str):
        """Reset error count for a key (on successful request)."""
        with self.lock:
            for key_status in self.keys:
                if key_status.key == key:
                    key_status.error_count = 0
                    return
    
    def get_available_count(self) -> int:
        """Get count of non-exhausted keys."""
        with self.lock:
            return sum(1 for k in self.keys if not k.exhausted)
    
    def get_status(self) -> Dict:
        """Get status of all keys."""
        with self.lock:
            return {
                'total': len(self.keys),
                'available': sum(1 for k in self.keys if not k.exhausted),
                'exhausted': sum(1 for k in self.keys if k.exhausted),
                'keys': [
                    {
                        'name': k.name,
                        'exhausted': k.exhausted,
                        'requests': k.request_count,
                        'errors': k.error_count,
                        'last_used': k.last_used
                    }
                    for k in self.keys
                ]
            }
