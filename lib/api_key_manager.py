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

# After a key returns 429, don't reuse it for this many seconds (avoids same key within 60s when rotating)
RATE_LIMIT_COOLDOWN_SEC = 60.0


@dataclass
class KeyStatus:
    """Status tracking for an API key."""
    key: str
    name: str
    last_used: float = 0.0
    request_count: int = 0
    exhausted: bool = False
    error_count: int = 0
    # When this key last got 429 (rate limit); skip key until cooldown expires
    last_rate_limit_at: float = 0.0
    # Rate limiting: track requests per minute (maxlen set by APIKeyManager)
    request_times: deque = None

    def __post_init__(self):
        if self.request_times is None:
            self.request_times = deque(maxlen=5)  # overwritten by APIKeyManager if rpm_per_key set


class APIKeyManager:
    """
    Manages multiple API keys with rotation, rate limiting, and exhaustion tracking.
    
    Features:
    - Cycles through available keys
    - Tracks rate limits per key (configurable RPM, default 5)
    - Marks keys as exhausted on quota errors
    - Distributes load across all keys
    """
    
    def __init__(
        self,
        api_keys: Optional[List[str]] = None,
        initial_key: Optional[str] = None,
        include_env_keys: bool = True,
        rpm_per_key: int = 5,
    ):
        """
        Initialize key manager.

        Args:
            api_keys: List of API keys. If None, loads from test file or env.
            initial_key: Optional single key (e.g. from server/Railway) to seed the manager.
                         Use this so keys work when env is not visible in request context.
            include_env_keys: Whether to load keys from environment variables.
            rpm_per_key: Max requests per minute per key (model-dependent; e.g. Gemini 2.5 Flash free tier ~3–5).
        """
        self.keys: List[KeyStatus] = []
        self.current_index = 0
        self.lock = threading.Lock()
        self.rpm_per_key = max(1, rpm_per_key)

        def _valid(k: Optional[str]) -> bool:
            if not k or not isinstance(k, str):
                return False
            k = k.strip()
            return k != "REVOKED_KEY_REMOVED" and k.startswith("AIza")

        # 1) Seed with server/passed key first (Railway: server has key at startup, request context may not)
        if initial_key and _valid(initial_key):
            self.keys.append(KeyStatus(key=initial_key.strip(), name="Server/Env Key"))

        # 2) Load from explicit list or file
        if api_keys:
            for i, key in enumerate(api_keys):
                if _valid(key):
                    self.keys.append(KeyStatus(key=key.strip(), name=f"Key #{i+1}"))
        elif not self.keys:
            self._load_keys_from_test_file()

        # 3) Add environment variables (GEMINI_API_KEY, GOOGLE_API_KEY, GEMINI_API_KEY_1, ...); avoid duplicates
        if include_env_keys:
            seen = {ks.key for ks in self.keys}
            for env_name in ('GEMINI_API_KEY', 'GOOGLE_API_KEY'):
                env_key = os.getenv(env_name)
                if env_key and _valid(env_key):
                    k = env_key.strip()
                    if k not in seen:
                        self.keys.append(KeyStatus(key=k, name=f"Env ({env_name})"))
                        seen.add(k)
            for i in range(1, 21):
                numbered_key = os.getenv(f'GEMINI_API_KEY_{i}')
                if numbered_key and _valid(numbered_key):
                    k = numbered_key.strip()
                    if k not in seen:
                        self.keys.append(KeyStatus(key=k, name=f"Env Key #{i}"))
                        seen.add(k)

        # 4) Fallback: file-based (local dev only)
        if not self.keys:
            self._load_keys_from_test_file()

        if not self.keys:
            raise ValueError("No valid API keys found. Set GEMINI_API_KEY or provide keys list.")

        # Apply RPM limit to all keys (model-dependent; e.g. 3–5 for Gemini 2.5 Flash free tier)
        for ks in self.keys:
            ks.request_times = deque(maxlen=self.rpm_per_key)

        print(f"[KEY_MANAGER] Initialized with {len(self.keys)} API keys (RPM/key={self.rpm_per_key})")
        for i, key_status in enumerate(self.keys):
            print(f"  [{i+1}] {key_status.name}: {key_status.key[:20]}...")
    
    def _load_keys_from_test_file(self):
        """
        Load keys from files (LOCAL DEV ONLY - files should NOT contain real keys).
        SECURITY: This is only for local development. In production (Railway),
        keys should come from environment variables only.
        """
        try:
            # PRIMARY: Load from centralized lib/api_keys.py (if it exists locally)
            # NOTE: This file is gitignored and should NOT be committed
            try:
                from lib.api_keys import get_api_keys
                keys = get_api_keys()
                for i, key in enumerate(keys):
                    if key and key != "REVOKED_KEY_REMOVED" and key.startswith("AIza"):
                        self.keys.append(KeyStatus(key=key, name=f"Local Key #{i+1}"))
                if self.keys:
                    print(f"[KEY_MANAGER] Loaded {len(self.keys)} keys from lib/api_keys.py (LOCAL DEV ONLY)")
                    return
            except ImportError:
                # File doesn't exist or can't import - that's fine, use env vars
                pass
            except Exception as e:
                print(f"[KEY_MANAGER] Warning: Error loading from lib/api_keys.py: {e}")
            
            # FALLBACK 1: Try JSON config file (local dev only)
            try:
                import json
                config_file = "data/api_keys.json"
                if os.path.exists(config_file):
                    with open(config_file, 'r') as f:
                        data = json.load(f)
                        keys = data.get('keys', [])
                        for i, key in enumerate(keys):
                            if key and key != "REVOKED_KEY_REMOVED" and key.startswith("AIza"):
                                self.keys.append(KeyStatus(key=key, name=f"Local Key #{i+1}"))
                        if self.keys:
                            print(f"[KEY_MANAGER] Loaded {len(self.keys)} keys from data/api_keys.json (LOCAL DEV ONLY)")
                            return
            except Exception as e:
                pass  # File doesn't exist - that's fine
                
        except Exception as e:
            print(f"[KEY_MANAGER] Warning: Could not load keys from files: {e}")
    
    def get_next_key(self, delay_seconds: float = 4.0) -> Optional[str]:
        """
        Get the next available API key with rate limiting.
        
        Args:
            delay_seconds: Minimum delay between requests for the same key (default 4s)
                          Set to 0 to skip rate limiting (useful when rotating from expired keys)
        
        Returns:
            API key string, or None if all keys exhausted
        """
        with self.lock:
            # Find next available key
            attempts = 0
            start_index = self.current_index  # Track where we started to detect full cycle
            
            now = time.time()
            while attempts < len(self.keys):
                key_status = self.keys[self.current_index]
                
                # Check if key is exhausted - skip it
                if key_status.exhausted:
                    print(f"  [KEY_SKIP] Skipping exhausted key: {key_status.name}")
                    self.current_index = (self.current_index + 1) % len(self.keys)
                    attempts += 1
                    # If we've cycled through all keys, break
                    if self.current_index == start_index:
                        break
                    continue
                
                # After 429, don't reuse this key until cooldown (avoid same key within 60s)
                now = time.time()
                if getattr(key_status, "last_rate_limit_at", 0) and (now - key_status.last_rate_limit_at) < RATE_LIMIT_COOLDOWN_SEC:
                    self.current_index = (self.current_index + 1) % len(self.keys)
                    attempts += 1
                    if self.current_index == start_index:
                        break
                    continue
                
                # Check rate limit: need at least delay_seconds since last use
                time_since_last = now - key_status.last_used
                
                if time_since_last < delay_seconds:
                    # This key needs to wait - try next key
                    self.current_index = (self.current_index + 1) % len(self.keys)
                    attempts += 1
                    continue
                
                # Check RPM limit: remove requests older than 1 minute
                while key_status.request_times and (now - key_status.request_times[0]) > 60:
                    key_status.request_times.popleft()
                
                # If we've hit RPM limit in the last minute, skip this key
                if len(key_status.request_times) >= self.rpm_per_key:
                    self.current_index = (self.current_index + 1) % len(self.keys)
                    attempts += 1
                    continue
                
                # Key is available - use it
                key_status.last_used = now
                key_status.request_count += 1
                if delay_seconds > 0:  # Only track request times if rate limiting is enabled
                    key_status.request_times.append(now)
                
                # Move to next key for round-robin
                next_index = (self.current_index + 1) % len(self.keys)
                self.current_index = next_index
                
                print(f"  [KEY_SELECTED] Using {key_status.name}: {key_status.key[:20]}...")
                return key_status.key
            
            # All keys exhausted or rate-limited
            available = self.get_available_count()
            print(f"  [KEY_NONE] No available keys ({available}/{len(self.keys)} available)")
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
        """Increment error count and start 60s cooldown for this key (e.g. 429 RPM).
        Does NOT mark exhausted. Ensures we don't reuse the same key within 60s when rotating."""
        with self.lock:
            for key_status in self.keys:
                if key_status.key == key:
                    key_status.error_count += 1
                    key_status.last_rate_limit_at = time.time()
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
