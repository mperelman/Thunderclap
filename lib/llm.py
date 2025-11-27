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
        self.api_key = api_key or os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        self.client = None
        
        # Try Gemini first
        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
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
                print("  [OK] Gemini API configured (2.5 Flash, 15 RPM / 1M TPM / 200 RPD)")
            except Exception as e:
                print(f"  [ERROR] Gemini setup failed: {e}")
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
    
    def _is_actual_quota_exhaustion(self, exc: Exception) -> bool:
        """Check if this is actual quota exhaustion (not just rate limiting)."""
        msg = str(exc).lower()
        # Actual quota exhaustion has specific indicators
        return (
            ("quota" in msg and "exhausted" in msg) or
            "resource has been exhausted" in msg or
            ("quota" in msg and "limit" in msg and ("daily" in msg or "per day" in msg))
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
        max_quota_retries = 3  # Only retry quota errors 3 times max
        
        while attempts < max_attempts:
            # Check total timeout
            elapsed = time.time() - start_time
            if elapsed > max_total_time:
                raise Exception(f"API call timed out after {elapsed:.1f}s (max {max_total_time}s). Quota may be exhausted.")
            
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
                error_msg = str(e)
                print(f"  [ERROR] API call failed: {error_msg}")
                
                if self._is_rate_limit_error(e):
                    quota_error_count += 1
                    # Fail fast if we've hit quota errors too many times
                    if quota_error_count > max_quota_retries:
                        # Distinguish between actual quota exhaustion vs temporary rate limiting
                        if self._is_actual_quota_exhaustion(e):
                            raise Exception(f"API quota exhausted after {quota_error_count} failures. Please try again later or check your API quota limits.")
                        else:
                            # This is likely a temporary rate limit, not quota exhaustion
                            # Log the actual error for debugging
                            print(f"  [DEBUG] Rate limit error details: {error_msg}")
                            raise Exception(f"Rate limit errors persisted after {quota_error_count} failures ({max_quota_retries} retries). The API may be temporarily rate-limited. Please wait 30-60 seconds and try again.")
                    
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
        max_quota_retries = 3  # Only retry quota errors 3 times max
        
        while attempts < max_attempts:
            # Check total timeout
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > max_total_time:
                raise Exception(f"Async API call timed out after {elapsed:.1f}s (max {max_total_time}s). Quota may be exhausted.")
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
                    quota_error_count += 1
                    # Fail fast if we've hit quota errors too many times
                    if quota_error_count > max_quota_retries:
                        # Distinguish between actual quota exhaustion vs temporary rate limiting
                        if self._is_actual_quota_exhaustion(e):
                            raise Exception(f"API quota exhausted after {quota_error_count} attempts. Please try again later or check your API quota limits.")
                        else:
                            # This is likely a temporary rate limit, not quota exhaustion
                            raise Exception(f"Rate limit errors persisted after {quota_error_count} retry attempts. The API may be temporarily rate-limited. Please wait 30-60 seconds and try again.")
                    
                    # Try to extract retry delay from error message
                    retry_delay = self._extract_retry_delay(e)
                    if retry_delay:
                        wait_time = retry_delay + 1  # Add 1 second buffer
                        print(f"  [RETRY] Async quota exceeded, waiting {wait_time:.1f}s (from API) (attempt {quota_error_count}/{max_quota_retries})")
                    else:
                        wait_time = backoff
                        print(f"  [RETRY] Async rate limited, backing off {backoff:.1f}s (attempt {quota_error_count}/{max_quota_retries})")
                        backoff = min(backoff * 2, 60.0)  # Cap at 60 seconds
                    
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
