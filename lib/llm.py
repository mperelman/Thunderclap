"""
LLM Answer Generation - Simple API wrapper.
No prompt logic - just handles API calls to Gemini/OpenAI.
"""
import os
import asyncio
import re


class LLMAnswerGenerator:
    """Simplified LLM wrapper - just API calls, no prompt logic."""
    
    def __init__(self, api_key=None, key_manager=None):
        """
        Initialize LLM client.
        
        Args:
            api_key: Gemini API key (or set GEMINI_API_KEY env var). If key_manager is provided, this is ignored.
            key_manager: APIKeyManager instance for multi-key rotation. If None, uses single key.
        """
        self.key_manager = key_manager
        if key_manager:
            # Use key manager - get first key for initial client
            self.api_key = key_manager.get_next_key(delay_seconds=0) or os.getenv('GEMINI_API_KEY')
        else:
            # Single key mode
            self.api_key = api_key or os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        self.client = None
        
        # Try Gemini first
        if self.api_key:
            try:
                # Strip and validate key
                self.api_key = self.api_key.strip()
                if not self.api_key.startswith('AIza'):
                    raise Exception(f"Invalid API key format. Key should start with 'AIza'. Got: {self.api_key[:20]}...")
                
                from lib.llm_config import get_llm_client
                self.client = get_llm_client(api_key=self.api_key)
                
                # Verify client was created
                if not self.client:
                    raise Exception("Failed to create Gemini client")
                    
            except Exception as e:
                print(f"  [ERROR] Gemini setup failed: {e}")
                import traceback
                traceback.print_exc()
                self.client = None
        else:
            print("  [WARNING] No Gemini API key found")
    
    def _is_rate_limit_error(self, exc: Exception) -> bool:
        """Check if exception is a rate limit or quota error."""
        msg = str(exc).lower()
        # Be more specific - only match actual rate limit/quota errors
        # "quota" alone is too broad - could match other errors
        return (
            "rate limit" in msg or 
            "429" in msg or 
            "resource has been exhausted" in msg or 
            ("quota" in msg and ("exceeded" in msg or "exhausted" in msg or "limit" in msg)) or
            "too many requests" in msg
        )
    
    def _is_key_expired_error(self, exc: Exception) -> bool:
        """Check if exception is an expired or invalid API key error."""
        msg = str(exc).lower()
        return (
            "api key expired" in msg or
            "api key invalid" in msg or
            "api_key_invalid" in msg or
            ("api key" in msg and ("expired" in msg or "invalid" in msg)) or
            ("key" in msg and "expired" in msg) or
            ("key" in msg and "invalid" in msg and "api" in msg)
        )
    
    def _is_token_quota_error(self, exc: Exception) -> bool:
        """Check if this is a token quota error (TPM - tokens per minute), not request quota."""
        msg = str(exc).lower()
        # Token quota errors mention "input_token" or "output_token" or "token_count"
        return (
            "token" in msg and ("quota" in msg or "exceeded" in msg or "limit" in msg) or
            "input_token" in msg or
            "output_token" in msg or
            "token_count" in msg
        )
    
    def _is_actual_quota_exhaustion(self, exc: Exception) -> bool:
        """Check if this is actual daily quota exhaustion (not just rate limiting or token quota)."""
        msg = str(exc).lower()
        # Actual daily quota exhaustion has specific indicators
        # Token quota (TPM) is different from daily quota (RPD)
        return (
            ("quota" in msg and "exhausted" in msg and "daily" in msg) or
            ("quota" in msg and "exhausted" in msg and "per day" in msg) or
            ("quota" in msg and "exhausted" in msg and "200" in msg and "rpd" in msg) or
            ("resource has been exhausted" in msg and "daily" in msg)
        )
    
    def _extract_retry_delay(self, exc: Exception) -> float:
        """Extract retry delay from error message, or return default."""
        import re as re_module
        msg = str(exc)
        # Look for "retry in X.XXs" or "retry_delay { seconds: X }"
        match = re_module.search(r'retry in (\d+\.?\d*)s', msg, re_module.IGNORECASE)
        if match:
            return float(match.group(1))
        match = re_module.search(r'seconds[:\s]+(\d+\.?\d*)', msg, re_module.IGNORECASE)
        if match:
            return float(match.group(1))
        return None  # Use exponential backoff

    def call_api(self, prompt: str) -> str:
        """
        Make a single API call with the given prompt.
        
        Args:
            prompt: Complete prompt string (built by prompts.py)
        
        Returns:
            Generated text response
        
        Raises:
            Exception: If API call fails and no fallback available
        """
        if not self.client:
            raise Exception("No LLM client available. Set GEMINI_API_KEY environment variable.")
        
        backoff = 1.0
        attempts = 0
        last_err = None
        import time
        start_time = time.time()
        max_total_time = 300  # 5 minutes maximum total wait time
        # Allow temporary override for control queries (reduces retries to prevent timeout)
        max_attempts = getattr(self, '_temp_max_attempts', 20)  # Default 20, override for control queries
        quota_error_count = 0  # Track consecutive quota errors
        max_quota_retries = 5  # Retry rate limit errors up to 5 times (was 3)
        
        while attempts < max_attempts:
            # Check total timeout
            elapsed = time.time() - start_time
            if elapsed > max_total_time:
                raise Exception(f"API call timed out after {elapsed:.1f}s (max {max_total_time}s). Quota may be exhausted.")
            
            try:
                # Get API key (from manager if available, otherwise use stored key)
                if self.key_manager:
                    current_key = self.key_manager.get_next_key(delay_seconds=4.0)  # 4s = 15 RPM
                    if not current_key:
                        # If no key available, check if we have any keys at all
                        available = self.key_manager.get_available_count()
                        if available == 0:
                            raise Exception("All API keys exhausted. Please add new keys or wait for quotas to reset.")
                        else:
                            # Keys exist but are rate-limited, wait and retry
                            import time
                            time.sleep(5)
                            current_key = self.key_manager.get_next_key(delay_seconds=0)
                            if not current_key:
                                raise Exception("All API keys rate-limited. Please wait a moment and try again.")
                    key_to_use = current_key.strip()
                else:
                    current_key = self.api_key
                    if not current_key:
                        raise Exception("No API key available for API call")
                    key_to_use = current_key.strip()
                
                # Import and configure in one go to avoid state issues
                import google.generativeai as genai
                
                # CRITICAL: Configure BEFORE importing anything else that might use genai
                # This ensures the key is set in genai's internal state
                print(f"  [DEBUG] Configuring API key: {key_to_use[:20]}... (length: {len(key_to_use)})")
                genai.configure(api_key=key_to_use)
                
                # Verify the key was set by checking genai's internal client
                # The genai library stores the key in _client_config
                if hasattr(genai, '_client_config'):
                    print(f"  [DEBUG] genai._client_config exists")
                else:
                    print(f"  [DEBUG] WARNING: genai._client_config not found, but continuing...")
                
                # ALWAYS recreate the client after reconfiguring
                # The client must be created AFTER configure() to use the new key
                # Use get_llm_client which has model fallback built in
                from lib.llm_config import get_llm_client
                self.client = get_llm_client(api_key=key_to_use)
                print(f"  [DEBUG] Client created, making API call with key: {key_to_use[:20]}...")
                
                # Make the API call
                response = self.client.generate_content(prompt)
                
                # Reset errors on success
                if self.key_manager and current_key:
                    self.key_manager.reset_key_errors(current_key)
                
                # Check finish_reason: 0=UNSPECIFIED, 1=STOP (normal), 2=MAX_TOKENS, 3=SAFETY, 4=RECITATION
                if response.candidates and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'finish_reason'):
                        finish_reason = candidate.finish_reason
                        if finish_reason == 3:
                            raise Exception("Response was blocked by safety filter (finish_reason=3). Try rephrasing the query.")
                        elif finish_reason == 4:
                            raise Exception("Response was blocked by recitation filter (finish_reason=4). Try rephrasing the query.")
                        elif finish_reason == 2:
                            # MAX_TOKENS - response was truncated, but we can still use it
                            print(f"  [WARN] Response hit token limit (finish_reason=2), may be truncated")
                try:
                    return response.text
                except Exception as text_err:
                    # If response.text fails (e.g., finish_reason=2 MAX_TOKENS), try to get partial response
                    error_str = str(text_err)
                    if "finish_reason" in error_str or "Part" in error_str or "part" in error_str.lower():
                        if response.candidates and len(response.candidates) > 0:
                            candidate = response.candidates[0]
                            # Try multiple ways to extract text
                            if hasattr(candidate, 'content') and candidate.content:
                                if hasattr(candidate.content, 'parts') and candidate.content.parts:
                                    for part in candidate.content.parts:
                                        if hasattr(part, 'text') and part.text:
                                            return part.text
                            # Try direct access
                            if hasattr(candidate, 'parts') and candidate.parts:
                                for part in candidate.parts:
                                    if hasattr(part, 'text') and part.text:
                                        return part.text
                    # If we can't extract partial response, raise with clearer message
                    if "finish_reason" in error_str and "2" in error_str:
                        # finish_reason 2 = MAX_TOKENS, not a safety filter
                        print(f"  [ERROR] Could not extract partial response for finish_reason=2. Error: {error_str}")
                        print(f"  [WARN] Response hit token limit (finish_reason=2) and no partial response available. Returning empty string for review system to detect.")
                        return ""  # Return empty so review system can detect and re-ask
                    # Re-raise original exception if it's not finish_reason related
                    raise
            except Exception as e:
                last_err = e
                error_msg = str(e)
                print(f"  [ERROR] API call failed: {error_msg}")
                
                # Check for expired/invalid key first - mark as exhausted immediately
                if self._is_key_expired_error(e):
                    if self.key_manager and current_key:
                        print(f"  [KEY_EXPIRED] Marking {current_key[:20]}... as exhausted (expired/invalid)")
                        self.key_manager.mark_key_exhausted(current_key)
                        # Try to get next key immediately (skip rate limiting for expired keys)
                        next_key = self.key_manager.get_next_key(delay_seconds=0)
                        if next_key and next_key != current_key:
                            print(f"  [KEY_ROTATE] Rotating to next key: {next_key[:20]}... (attempt {attempts + 1}/{max_attempts})")
                            # Reset error count since we're trying a new key
                            quota_error_count = 0
                            attempts += 1
                            continue
                        else:
                            # No next key available - check status
                            available = self.key_manager.get_available_count()
                            total = len(self.key_manager.keys)
                            exhausted = total - available
                            print(f"  [KEY_STATUS] {exhausted}/{total} keys exhausted, {available} available")
                            if available == 0:
                                # Check if we only had one key
                                if total == 1:
                                    raise Exception(
                                        f"API key expired or invalid. Only 1 key was found in Railway environment variables.\n\n"
                                        f"Please add multiple keys to Railway:\n"
                                        f"1. GEMINI_API_KEY = (new key)\n"
                                        f"2. GEMINI_API_KEY_1 = (new key)\n"
                                        f"3. GEMINI_API_KEY_2 = (new key)\n"
                                        f"4. GEMINI_API_KEY_3 = (new key)\n"
                                        f"5. GEMINI_API_KEY_4 = (new key)\n"
                                        f"6. GEMINI_API_KEY_5 = (new key)\n\n"
                                        f"This allows automatic rotation if one key fails.\n\n"
                                        f"Error: {error_msg[:200]}"
                                    )
                                else:
                                    raise Exception(f"All {total} API keys are expired or invalid. Please add new keys to Railway environment variables (GEMINI_API_KEY, GEMINI_API_KEY_1, etc.).")
                            else:
                                # Keys exist but might be rate-limited, wait and retry
                                print(f"  [KEY_RETRY] Waiting 2s and retrying with available keys...")
                                time.sleep(2)
                                attempts += 1
                                continue
                    else:
                        # Single key mode - can't rotate
                        raise Exception(
                            f"API key expired or invalid. Only 1 key was found in Railway environment variables.\n\n"
                            f"Please add multiple keys to Railway for automatic rotation:\n"
                            f"1. GEMINI_API_KEY = (new key)\n"
                            f"2. GEMINI_API_KEY_1 = (new key)\n"
                            f"3. GEMINI_API_KEY_2 = (new key)\n"
                            f"4. GEMINI_API_KEY_3 = (new key)\n"
                            f"5. GEMINI_API_KEY_4 = (new key)\n"
                            f"6. GEMINI_API_KEY_5 = (new key)\n\n"
                            f"This allows automatic rotation if one key fails.\n\n"
                            f"Error: {error_msg[:200]}"
                        )
                
                if self._is_rate_limit_error(e):
                    # If using key manager, mark this key as having an error and try next key
                    if self.key_manager and current_key:
                        self.key_manager.mark_key_error(current_key)
                        # Try to get next key immediately
                        next_key = self.key_manager.get_next_key(delay_seconds=0)
                        if next_key and next_key != current_key:
                            print(f"  [KEY_ROTATE] Rotating to next key after error on {current_key[:20]}...")
                            attempts += 1
                            continue
                        # If token quota error, mark as exhausted
                        if self._is_token_quota_error(e):
                            self.key_manager.mark_key_exhausted(current_key)
                    
                    quota_error_count += 1
                    # Fail fast if we've hit quota errors too many times
                    if quota_error_count > max_quota_retries:
                        # Distinguish between different types of quota/rate limit errors
                        if self._is_token_quota_error(e):
                            # Token quota (TPM) - need to wait longer, usually 1-2 minutes
                            print(f"  [DEBUG] Token quota error details: {error_msg}")
                            error_snippet = error_msg[:150] if len(error_msg) > 150 else error_msg
                            available_keys = self.key_manager.get_available_count() if self.key_manager else 0
                            if available_keys > 0:
                                raise Exception(f"Token quota exceeded on current key. {available_keys} keys still available. Retrying with different key...")
                            raise Exception(f"Token quota exceeded (250,000 tokens/minute limit). Your query uses too many tokens. Please wait 1-2 minutes and try again, or simplify your question.\n\nAPI Error: {error_snippet}")
                        elif self._is_actual_quota_exhaustion(e):
                            if self.key_manager and current_key:
                                self.key_manager.mark_key_exhausted(current_key)
                            raise Exception(f"API daily quota exhausted after {quota_error_count} failures. Please try again later or check your API quota limits.")
                        else:
                            # This is likely a temporary rate limit (RPM), not quota exhaustion
                            # Log the actual error for debugging
                            print(f"  [DEBUG] Rate limit error details: {error_msg}")
                            # Include a snippet of the actual error in the message (first 100 chars)
                            error_snippet = error_msg[:100] if len(error_msg) > 100 else error_msg
                            raise Exception(f"Rate limit errors persisted after {quota_error_count} failures ({max_quota_retries} retries). The API may be temporarily rate-limited. Please wait 30-60 seconds and try again.\n\nAPI Error: {error_snippet}")
                    
                    # Try to extract retry delay from error message
                    retry_delay = self._extract_retry_delay(e)
                    if retry_delay:
                        wait_time = min(retry_delay + 1, 60)  # Cap at 60s, add 1 second buffer
                        print(f"  [RETRY] Rate limit detected, waiting {wait_time:.1f}s (from API) (attempt {quota_error_count}/{max_quota_retries})")
                    else:
                        # For rate limits, use longer backoff - start with 5s, cap at 60s
                        wait_time = min(backoff, 60)  # Cap at 60s for rate limits
                        print(f"  [RETRY] Rate limit detected, backing off {wait_time:.1f}s (attempt {quota_error_count}/{max_quota_retries})")
                        # Exponential backoff: 1s -> 2s -> 4s -> 8s -> 16s -> 32s -> 60s (capped)
                        max_backoff = 60.0
                        backoff = min(backoff * 2, max_backoff)
                    
                    time.sleep(wait_time)
                    attempts += 1
                    continue
                print(f"  [ERROR] Non-rate-limit API call failed: {e}")
                raise
        raise last_err or Exception(f"API call failed after {max_attempts} retries")
    
    def generate_answer(self, question: str, chunks: list) -> str:
        """
        Generate narrative answer from question and chunks.
        Builds prompt and calls API.
        
        Args:
            question: User's question
            chunks: List of relevant document chunks
        
        Returns:
            Generated narrative answer
        """
        # CRITICAL: Limit chunks here as a safety net (in case query_engine.py didn't limit)
        # This prevents token quota errors even if limiting was missed earlier
        # Use same conservative limits (40%) as query_engine.py
        from lib.config import MAX_TOKENS_PER_REQUEST, MAX_TOKENS_PER_MINUTE, TOKENS_PER_WORD
        estimated_tokens = sum(len(chunk[0].split()) for chunk in chunks) * TOKENS_PER_WORD
        prompt_overhead = 5000
        response_estimate = 15000
        # Use 35% limit (matching query_engine limits) to prevent timeouts
        available_for_chunks = int(MAX_TOKENS_PER_REQUEST * 0.35) - prompt_overhead - response_estimate
        minute_budget = int(MAX_TOKENS_PER_MINUTE * 0.35) - prompt_overhead - response_estimate
        effective_limit = min(available_for_chunks, minute_budget)
        
        if estimated_tokens > effective_limit:
            tokens_per_chunk = estimated_tokens / len(chunks) if chunks else 0
            max_chunks = int(effective_limit / tokens_per_chunk) if tokens_per_chunk > 0 else len(chunks)
            max_chunks = max(1, max_chunks)
            if len(chunks) > max_chunks:
                print(f"  [LLM_SAFETY_LIMIT] Limiting chunks from {len(chunks)} to {max_chunks} in generate_answer (~{estimated_tokens:,} > {effective_limit:,} tokens)")
                chunks = chunks[:max_chunks]
        
        from lib.prompts import build_prompt
        prompt = build_prompt(question, chunks)
        return self.call_api(prompt)
    
    async def call_api_async(self, prompt: str) -> str:
        """
        Make an async API call with the given prompt.
        
        Args:
            prompt: Complete prompt string (built by prompts.py)
        
        Returns:
            Generated text response
        
        Raises:
            Exception: If API call fails and no fallback available
        """
        if not self.client:
            raise Exception("No LLM client available. Set GEMINI_API_KEY environment variable.")
        
        backoff = 5.0  # Start with 5s for rate limits (more conservative)
        attempts = 0
        last_err = None
        import asyncio
        start_time = asyncio.get_event_loop().time()
        max_total_time = 300  # 5 minutes maximum total wait time
        max_attempts = 20  # Increased for quota errors
        quota_error_count = 0  # Track consecutive quota errors
        max_quota_retries = 5  # Retry rate limit errors up to 5 times (was 3)
        
        current_key = None  # Initialize for error handling
        while attempts < max_attempts:
            # Check total timeout
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > max_total_time:
                raise Exception(f"Async API call timed out after {elapsed:.1f}s (max {max_total_time}s). Quota may be exhausted.")
            try:
                # Get API key (from manager if available, otherwise use stored key)
                if self.key_manager:
                    current_key = self.key_manager.get_next_key(delay_seconds=4.0)  # 4s = 15 RPM
                    if not current_key:
                        # If no key available, check if we have any keys at all
                        available = self.key_manager.get_available_count()
                        if available == 0:
                            raise Exception("All API keys exhausted. Please add new keys or wait for quotas to reset.")
                        else:
                            # Keys exist but are rate-limited, wait and retry
                            await asyncio.sleep(5)
                            current_key = self.key_manager.get_next_key(delay_seconds=0)
                            if not current_key:
                                raise Exception("All API keys rate-limited. Please wait a moment and try again.")
                else:
                    current_key = self.api_key
                
                if not current_key:
                    raise Exception("No API key available for API call")
                
                import google.generativeai as genai
                # CRITICAL: Always reconfigure before each async call
                # Use get_llm_client which has model fallback built in
                from lib.llm_config import get_llm_client
                self.client = get_llm_client(api_key=current_key.strip())
                
                response = await self.client.generate_content_async(prompt)
                
                # Reset errors on success
                if self.key_manager:
                    self.key_manager.reset_key_errors(current_key)
                # Check finish_reason: 0=UNSPECIFIED, 1=STOP (normal), 2=MAX_TOKENS, 3=SAFETY, 4=RECITATION
                if response.candidates and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'finish_reason'):
                        finish_reason = candidate.finish_reason
                        if finish_reason == 3:
                            raise Exception("Response was blocked by safety filter (finish_reason=3). Try rephrasing the query.")
                        elif finish_reason == 4:
                            raise Exception("Response was blocked by recitation filter (finish_reason=4). Try rephrasing the query.")
                        elif finish_reason == 2:
                            # MAX_TOKENS - response was truncated, but we can still use it
                            print(f"  [WARN] Response hit token limit (finish_reason=2), may be truncated")
                try:
                    return response.text
                except Exception as text_err:
                    # If response.text fails (e.g., finish_reason=2 MAX_TOKENS), try to get partial response
                    error_str = str(text_err)
                    if "finish_reason" in error_str or "Part" in error_str or "part" in error_str.lower():
                        if response.candidates and len(response.candidates) > 0:
                            candidate = response.candidates[0]
                            # Try multiple ways to extract text
                            if hasattr(candidate, 'content') and candidate.content:
                                if hasattr(candidate.content, 'parts') and candidate.content.parts:
                                    for part in candidate.content.parts:
                                        if hasattr(part, 'text') and part.text:
                                            return part.text
                            # Try direct access
                            if hasattr(candidate, 'parts') and candidate.parts:
                                for part in candidate.parts:
                                    if hasattr(part, 'text') and part.text:
                                        return part.text
                    # If we can't extract partial response, raise with clearer message
                    if "finish_reason" in error_str and "2" in error_str:
                        # finish_reason 2 = MAX_TOKENS, not a safety filter
                        print(f"  [ERROR] Could not extract partial response for finish_reason=2. Error: {error_str}")
                        print(f"  [WARN] Response hit token limit (finish_reason=2) and no partial response available. Returning empty string for review system to detect.")
                        return ""  # Return empty so review system can detect and re-ask
                    # Re-raise original exception if it's not finish_reason related
                    raise
            except Exception as e:
                last_err = e
                error_msg = str(e)
                print(f"  [ERROR] Async API call failed: {error_msg}")
                
                # Check for expired/invalid key first - mark as exhausted immediately
                if self._is_key_expired_error(e):
                    if self.key_manager and current_key:
                        print(f"  [KEY_EXPIRED] Marking {current_key[:20]}... as exhausted (expired/invalid)")
                        self.key_manager.mark_key_exhausted(current_key)
                        # Try to get next key immediately
                        next_key = self.key_manager.get_next_key(delay_seconds=0)
                        if next_key and next_key != current_key:
                            print(f"  [KEY_ROTATE] Rotating to next key: {next_key[:20]}...")
                            attempts += 1
                            continue
                        else:
                            available = self.key_manager.get_available_count()
                            total = len(self.key_manager.keys)
                            if available == 0:
                                # Check if we only had one key
                                if total == 1:
                                    raise Exception(
                                        f"API key expired or invalid. Only 1 key was found in Railway environment variables.\n\n"
                                        f"Please add multiple keys to Railway:\n"
                                        f"1. GEMINI_API_KEY = (new key)\n"
                                        f"2. GEMINI_API_KEY_1 = (new key)\n"
                                        f"3. GEMINI_API_KEY_2 = (new key)\n"
                                        f"4. GEMINI_API_KEY_3 = (new key)\n"
                                        f"5. GEMINI_API_KEY_4 = (new key)\n"
                                        f"6. GEMINI_API_KEY_5 = (new key)\n\n"
                                        f"This allows automatic rotation if one key fails.\n\n"
                                        f"Error: {error_msg[:200]}"
                                    )
                                else:
                                    raise Exception(f"All {total} API keys are expired or invalid. Please add new keys to Railway environment variables (GEMINI_API_KEY, GEMINI_API_KEY_1, etc.).")
                            else:
                                # Wait a bit and try again with next key
                                await asyncio.sleep(1)
                                attempts += 1
                                continue
                    else:
                        # Single key mode - can't rotate
                        raise Exception(
                            f"API key expired or invalid. Only 1 key was found in Railway environment variables.\n\n"
                            f"Please add multiple keys to Railway for automatic rotation:\n"
                            f"1. GEMINI_API_KEY = (new key)\n"
                            f"2. GEMINI_API_KEY_1 = (new key)\n"
                            f"3. GEMINI_API_KEY_2 = (new key)\n"
                            f"4. GEMINI_API_KEY_3 = (new key)\n"
                            f"5. GEMINI_API_KEY_4 = (new key)\n"
                            f"6. GEMINI_API_KEY_5 = (new key)\n\n"
                            f"This allows automatic rotation if one key fails.\n\n"
                            f"Error: {error_msg[:200]}"
                        )
                
                # Check for leaked keys (same handling as expired)
                if self._is_key_leaked_error(e):
                    if self.key_manager and current_key:
                        print(f"  [KEY_LEAKED] Marking {current_key[:20]}... as exhausted (reported as leaked)")
                        self.key_manager.mark_key_exhausted(current_key)
                        # Try to get next key immediately
                        next_key = self.key_manager.get_next_key(delay_seconds=0)
                        if next_key and next_key != current_key:
                            print(f"  [KEY_ROTATE] Rotating to next key: {next_key[:20]}...")
                            attempts += 1
                            continue
                        else:
                            available = self.key_manager.get_available_count()
                            if available == 0:
                                raise Exception(f"All API keys are leaked or invalid. Please add new keys to Railway environment variables (GEMINI_API_KEY, GEMINI_API_KEY_1, etc.).")
                            else:
                                # Wait a bit and try again with next key
                                await asyncio.sleep(1)
                                attempts += 1
                                continue
                    else:
                        # Single key mode - can't rotate
                        raise Exception(f"API key was reported as leaked. Please update your API key in Railway environment variables.\n\nError: {error_msg[:200]}")
                
                # Check for leaked keys (same handling as expired)
                if self._is_key_leaked_error(e):
                    if self.key_manager and current_key:
                        print(f"  [KEY_LEAKED] Marking {current_key[:20]}... as exhausted (reported as leaked)")
                        self.key_manager.mark_key_exhausted(current_key)
                        # Try to get next key immediately
                        next_key = self.key_manager.get_next_key(delay_seconds=0)
                        if next_key and next_key != current_key:
                            print(f"  [KEY_ROTATE] Rotating to next key: {next_key[:20]}...")
                            attempts += 1
                            continue
                        else:
                            available = self.key_manager.get_available_count()
                            if available == 0:
                                raise Exception(f"All API keys are leaked or invalid. Please add new keys to Railway environment variables (GEMINI_API_KEY, GEMINI_API_KEY_1, etc.).")
                            else:
                                # Wait a bit and try again with next key
                                await asyncio.sleep(1)
                                attempts += 1
                                continue
                    else:
                        # Single key mode - can't rotate
                        raise Exception(f"API key was reported as leaked. Please update your API key in Railway environment variables.\n\nError: {error_msg[:200]}")
                
                if self._is_rate_limit_error(e):
                    # If using key manager, mark this key as having an error and try next key
                    if self.key_manager and current_key:
                        self.key_manager.mark_key_error(current_key)
                        # Try to get next key immediately
                        next_key = self.key_manager.get_next_key(delay_seconds=0)
                        if next_key and next_key != current_key:
                            print(f"  [KEY_ROTATE] Rotating to next key after error on {current_key[:20]}...")
                            attempts += 1
                            continue
                        # If token quota error, mark as exhausted
                        if self._is_token_quota_error(e):
                            self.key_manager.mark_key_exhausted(current_key)
                    
                    quota_error_count += 1
                    # Fail fast if we've hit quota errors too many times
                    if quota_error_count > max_quota_retries:
                        # Distinguish between different types of quota/rate limit errors
                        if self._is_token_quota_error(e):
                            # Token quota (TPM) - need to wait longer, usually 1-2 minutes
                            print(f"  [DEBUG] Async token quota error details: {error_msg}")
                            error_snippet = error_msg[:150] if len(error_msg) > 150 else error_msg
                            available_keys = self.key_manager.get_available_count() if self.key_manager else 0
                            if available_keys > 0:
                                raise Exception(f"Token quota exceeded on current key. {available_keys} keys still available. Retrying with different key...")
                            raise Exception(f"Token quota exceeded (250,000 tokens/minute limit). Your query uses too many tokens. Please wait 1-2 minutes and try again, or simplify your question.\n\nAPI Error: {error_snippet}")
                        elif self._is_actual_quota_exhaustion(e):
                            if self.key_manager and current_key:
                                self.key_manager.mark_key_exhausted(current_key)
                            raise Exception(f"API daily quota exhausted after {quota_error_count} failures. Please try again later or check your API quota limits.")
                        else:
                            # This is likely a temporary rate limit (RPM), not quota exhaustion
                            # Log the actual error for debugging
                            print(f"  [DEBUG] Async rate limit error details: {error_msg}")
                            # Include a snippet of the actual error in the message (first 100 chars)
                            error_snippet = error_msg[:100] if len(error_msg) > 100 else error_msg
                            raise Exception(f"Rate limit errors persisted after {quota_error_count} failures ({max_quota_retries} retries). The API may be temporarily rate-limited. Please wait 30-60 seconds and try again.\n\nAPI Error: {error_snippet}")
                    
                    # Try to extract retry delay from error message
                    retry_delay = self._extract_retry_delay(e)
                    if retry_delay:
                        wait_time = retry_delay + 1  # Add 1 second buffer
                        print(f"  [RETRY] Async rate limit detected, waiting {wait_time:.1f}s (from API) (attempt {quota_error_count}/{max_quota_retries})")
                    else:
                        # For rate limits, use longer backoff - start with 5s, cap at 60s
                        wait_time = min(backoff, 60)  # Cap at 60s for rate limits
                        print(f"  [RETRY] Async rate limit detected, backing off {wait_time:.1f}s (attempt {quota_error_count}/{max_quota_retries})")
                        backoff = min(backoff * 2, 60.0)  # Cap at 60 seconds
                    
                    import asyncio
                    await asyncio.sleep(wait_time)
                    attempts += 1
                    continue
                print(f"  [ERROR] Non-rate-limit async API call failed: {e}")
                raise
        raise last_err or Exception(f"Async API call failed after {max_attempts} retries")
    
    async def generate_answer_async(self, question: str, chunks: list) -> str:
        """
        Generate narrative answer asynchronously from question and chunks.
        Builds prompt and calls API async.
        
        Args:
            question: User's question
            chunks: List of relevant document chunks
        
        Returns:
            Generated narrative answer
        """
        from lib.prompts import build_prompt
        prompt = build_prompt(question, chunks)
        return await self.call_api_async(prompt)
