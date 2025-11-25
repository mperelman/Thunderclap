"""
LLM Answer Generation - Simple API wrapper.
No prompt logic - just handles API calls to Gemini/OpenAI.
"""
import os
import asyncio
import re


class LLMAnswerGenerator:
    """Simplified LLM wrapper - just API calls, no prompt logic."""
    
    def __init__(self, api_key=None):
        """
        Initialize LLM client.
        
        Args:
            api_key: Gemini API key (or set GEMINI_API_KEY env var)
        """
        # Get API key with fallback chain, then trim whitespace
        api_key_raw = api_key or os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        self.api_key = api_key_raw.strip() if api_key_raw else None
        self.client = None
        
        # Debug: Log API key status
        print(f"  [LLM INIT] API key provided: {bool(api_key)}")
        print(f"  [LLM INIT] API key from env: {bool(os.getenv('GEMINI_API_KEY'))}")
        print(f"  [LLM INIT] Final API key present: {bool(self.api_key)}")
        if self.api_key:
            print(f"  [LLM INIT] API key length: {len(self.api_key)}")
            print(f"  [LLM INIT] API key starts with: {self.api_key[:10]}...")
            # Validate format
            if len(self.api_key) != 39:
                print(f"  [WARNING] API key length is {len(self.api_key)}, expected 39")
            if not self.api_key.startswith('AIza'):
                print(f"  [WARNING] API key doesn't start with 'AIza'")
        
        # Try Gemini first
        if self.api_key:
            try:
                import google.generativeai as genai
                print(f"  [LLM INIT] Configuring Gemini with API key...")
                # Configure with trimmed key
                genai.configure(api_key=self.api_key)
                print(f"  [LLM INIT] Gemini configuration complete")
                # Use low-variance generation to stabilize output length/structure
                self._gen_config = {
                    "temperature": 0.2,
                    "top_p": 0.3,
                    "top_k": 1,
                    "max_output_tokens": 16384,  # Increased to handle very long responses
                    "candidate_count": 1,
                }
                self.client = genai.GenerativeModel(
                    model_name='gemini-2.5-flash',
                    generation_config=self._gen_config,
                )
                # Test API key by making a minimal test call
                print(f"  [LLM INIT] Testing API key with minimal call...")
                try:
                    test_response = self.client.generate_content("test", request_options={"timeout": 10})
                    print(f"  [OK] API key test successful")
                except Exception as test_err:
                    error_msg = str(test_err)
                    error_lower = error_msg.lower()
                    print(f"  [ERROR] API key test failed: {error_msg}")
                    print(f"  [ERROR] Full error type: {type(test_err).__name__}")
                    
                    # Check for specific error types
                    if "api key" in error_lower or "api_key" in error_lower or "invalid" in error_lower:
                        raise RuntimeError(f"Invalid or expired API key: {error_msg}\nCheck Railway Variables → GEMINI_API_KEY is correct and not expired.")
                    elif "quota" in error_lower or "429" in error_msg or "rate limit" in error_lower:
                        print(f"  [WARNING] API quota/rate limit hit during test, but API key is valid")
                        print(f"  [WARNING] Continuing anyway - quota may reset or you may need to wait")
                        # Don't fail - quota issues are temporary
                    elif "timeout" in error_lower or "network" in error_lower:
                        print(f"  [WARNING] Network/timeout issue during test, but API key format looks valid")
                        print(f"  [WARNING] Continuing anyway - network issues are temporary")
                        # Don't fail - network issues are temporary
                    else:
                        # Unknown error - still raise it but with context
                        raise RuntimeError(f"API key test failed: {error_msg}\nCheck Railway logs for full error details.")
                print("  [OK] Gemini API configured (2.5 Flash, 15 RPM / 1M TPM / 200 RPD)")
            except Exception as e:
                error_msg = str(e)
                print(f"  [ERROR] Gemini setup failed: {error_msg}")
                print(f"  [ERROR] API key was present: {bool(self.api_key)}")
                if self.api_key:
                    print(f"  [ERROR] API key length: {len(self.api_key)}")
                    print(f"  [ERROR] API key starts with: {self.api_key[:10]}...")
                import traceback
                traceback.print_exc()
                import sys
                sys.stdout.flush()
                
                # Store error for better error messages later
                self._init_error = error_msg
                self.client = None
                
                # If it's an invalid API key error, raise it immediately
                if "invalid" in error_msg.lower() or "api key" in error_msg.lower() or "api_key" in error_msg.lower():
                    raise RuntimeError(f"Gemini API initialization failed: {error_msg}\nCheck Railway Variables → GEMINI_API_KEY is correct.")
                # Otherwise, let it fail gracefully when used (might be quota/network issue)
        else:
            print("  [ERROR] No Gemini API key found - cannot initialize LLM")
            raise RuntimeError("GEMINI_API_KEY environment variable not set. Set it in Railway Variables tab.")
    
    def _is_rate_limit_error(self, exc: Exception) -> bool:
        msg = str(exc).lower()
        return ("rate limit" in msg) or ("429" in msg) or ("resource has been exhausted" in msg) or ("quota" in msg)
    
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
        # Allow temporary override for control queries (reduces retries to prevent timeout)
        max_attempts = getattr(self, '_temp_max_attempts', 20)  # Default 20, override for control queries
        while attempts < max_attempts:
            try:
                response = self.client.generate_content(prompt)
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
                if self._is_rate_limit_error(e):
                    # Try to extract retry delay from error message
                    retry_delay = self._extract_retry_delay(e)
                    if retry_delay:
                        wait_time = retry_delay + 1  # Add 1 second buffer
                        print(f"  [RETRY] Quota exceeded, waiting {wait_time:.1f}s (from API) (attempt {attempts+1}/{max_attempts})")
                    else:
                        wait_time = backoff
                        print(f"  [RETRY] Rate limited, backing off {backoff:.1f}s (attempt {attempts+1}/{max_attempts})")
                        # Cap backoff to prevent long connection timeouts
                        max_backoff = 15.0  # Maximum 15s wait to avoid connection drops
                        backoff = min(backoff * 2, max_backoff)
                    
                    import time
                    time.sleep(wait_time)
                    attempts += 1
                    continue
                print(f"  [ERROR] API call failed: {e}")
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
        
        backoff = 1.0
        attempts = 0
        last_err = None
        max_attempts = 20  # Increased for quota errors
        while attempts < max_attempts:
            try:
                response = await self.client.generate_content_async(prompt)
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
                if self._is_rate_limit_error(e):
                    # Try to extract retry delay from error message
                    retry_delay = self._extract_retry_delay(e)
                    if retry_delay:
                        wait_time = retry_delay + 1  # Add 1 second buffer
                        print(f"  [RETRY] Async quota exceeded, waiting {wait_time:.1f}s (from API) (attempt {attempts+1}/{max_attempts})")
                    else:
                        wait_time = backoff
                        print(f"  [RETRY] Async rate limited, backing off {backoff:.1f}s (attempt {attempts+1}/{max_attempts})")
                        max_backoff = 15.0  # Maximum 15s wait to avoid connection drops
                        backoff = min(backoff * 2, max_backoff)
                    
                    import asyncio
                    await asyncio.sleep(wait_time)
                    attempts += 1
                    continue
                print(f"  [ERROR] Async API call failed: {e}")
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
