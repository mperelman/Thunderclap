"""
LLM Executor – single responsibility: run one prompt with retries and key rotation.

This module is the **source of truth** for LLM/async behavior (README only points here).

Behavior (LLM/async):
- **Per-call timeout**: API_CALL_TIMEOUT_SEC (default 120s; GEMINI_API_CALL_TIMEOUT=0 for no timeout).
- **Per-key-per-model rate limit**: Before reusing the same (key, model) we wait 60/RPM seconds
  (RPM in lib.llm_config.MODEL_RPM: 2.5 Flash 5, 2.5 Flash Lite 10, 3 Flash 10).
- **Key rotation**: MIN_DELAY_SAME_KEY_SEC (15s) minimum between reusing the same key.
- **429 handling**: RPM -> rotate to next key and model, wait then retry. Daily quota exhausted ->
  mark key exhausted, try next key. Token quota -> treat as exhausted. We use _extract_retry_delay()
  when present; else 10s minimum wait.
- **Other HTTP**: 400 -> re-raise (no retry). 403 -> mark key exhausted, rotate. 404 -> invalidate
  client, try next key. 503 -> retry after 5–60s, same key.
- **Event loop**: get_llm_client via run_in_executor so list_models doesn't block; API call via
  asyncio.wait_for so we don't block the loop. LLM_PINPOINT=1 logs where we are (client vs API).

Modular layout:
- lib.api_key_manager: key provider (rotation, rate limits)
- lib.llm_config: client factory (get_llm_client, MODEL_PRIORITY, MODEL_RPM)
- lib.llm_executor: request execution (this module)
- lib.llm: facade (LLMAnswerGenerator composes the above)

No prompt building, no answer generation. Used by llm.LLMAnswerGenerator.
"""
import asyncio
import os
import re
import time
from typing import Optional, Callable, Any, Dict, Tuple

# Minimum seconds before reusing the same key (so we rotate across keys with breaks)
# 15s => ~4 RPM per key; under 2.5 Flash (5 RPM) and 2.5 Flash Lite (10 RPM)
MIN_DELAY_SAME_KEY_SEC = 15.0
# Per-call timeout (seconds). 0 = no timeout (wait until API responds or fails). Set via GEMINI_API_CALL_TIMEOUT.
_API_CALL_TIMEOUT_ENV = os.environ.get("GEMINI_API_CALL_TIMEOUT", "120") or "120"
API_CALL_TIMEOUT_SEC = int(_API_CALL_TIMEOUT_ENV) if _API_CALL_TIMEOUT_ENV.isdigit() else 120

# Per-key-per-model rate limit: delay = 60/RPM before reusing same (key, model) — from Austria
def _delay_sec_for_model(model_name: str) -> float:
    from lib.llm_config import MODEL_RPM
    return 60.0 / MODEL_RPM.get(model_name, 5)


def _is_rate_limit_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return (
        "rate limit" in msg or "429" in msg or "resource has been exhausted" in msg
        or ("quota" in msg and ("exceeded" in msg or "exhausted" in msg or "limit" in msg))
        or "too many requests" in msg
    )


def _is_key_expired_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return (
        "api key expired" in msg or "api key invalid" in msg or "api_key_invalid" in msg
        or ("api key" in msg and ("expired" in msg or "invalid" in msg))
        or ("key" in msg and "expired" in msg)
        or ("key" in msg and "invalid" in msg and "api" in msg)
    )


def _is_token_quota_error(exc: Exception) -> bool:
    """True only for token-specific limits (TPM). Generic 429 'check your plan and billing' is RPM, not token quota."""
    msg = str(exc).lower()
    if "check your plan and billing" in msg or "plan and billing details" in msg:
        return False  # generic 429 text -> treat as RPM, not token quota
    return (
        "input_token" in msg
        or "output_token" in msg
        or "token_count" in msg
        or ("token" in msg and ("tokens per" in msg or "token limit" in msg or "token quota" in msg))
    )


def _is_key_leaked_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return "leaked" in msg or "compromised" in msg or "exposed" in msg


def _is_http_error(exc: Exception, code: int) -> bool:
    msg = str(exc)
    return str(code) in msg or f"{code}" in msg


def _is_400_bad_request(exc: Exception) -> bool:
    return _is_http_error(exc, 400) or "bad request" in str(exc).lower()


def _is_403_forbidden(exc: Exception) -> bool:
    return _is_http_error(exc, 403) or "403" in str(exc) or "forbidden" in str(exc).lower()


def _is_404_not_found(exc: Exception) -> bool:
    return _is_http_error(exc, 404) or "404" in str(exc) or "not found" in str(exc).lower()


def _is_503_unavailable(exc: Exception) -> bool:
    return _is_http_error(exc, 503) or "503" in str(exc) or "service unavailable" in str(exc).lower() or "unavailable" in str(exc).lower()


def _is_actual_quota_exhaustion(exc: Exception) -> bool:
    """Treat only as daily/quota exhaustion when message explicitly says so. Generic 429
    ('check your plan and billing') is usually RPM rate limit - we wait and retry same key."""
    msg = str(exc).lower()
    return (
        ("quota" in msg and "exhausted" in msg and ("daily" in msg or "per day" in msg))
        or ("resource has been exhausted" in msg and "daily" in msg)
        or "rpd" in msg  # requests per day
    )


def _extract_retry_delay(exc: Exception) -> Optional[float]:
    match = re.search(r"retry in (\d+\.?\d*)s", str(exc), re.I)
    if match:
        return float(match.group(1))
    match = re.search(r"seconds[:\s]+(\d+\.?\d*)", str(exc), re.I)
    if match:
        return float(match.group(1))
    return None


def _raise_keys_exhausted(total: int, single_key: bool, error_msg: str, kind: str = "expired/invalid") -> None:
    if single_key:
        raise Exception(
            f"API key {kind}. Only 1 key was found. "
            "Set GEMINI_API_KEY and/or GEMINI_API_KEY_1, GEMINI_API_KEY_2, etc. for rotation.\n\n"
            f"Error: {error_msg[:200]}"
        )
    raise Exception(f"All {total} API keys are {kind}. Add new keys (GEMINI_API_KEY, GEMINI_API_KEY_1, etc.).")


class LLMExecutor:
    """
    Executes a single prompt with retries and optional key rotation.
    Reuses client when key unchanged; only gets new client when key rotates or first use.
    """

    def __init__(
        self,
        key_provider=None,
        single_key: Optional[str] = None,
        client_factory: Optional[Callable[[str], Any]] = None,
        max_attempts: int = 20,
        max_total_time: float = 300.0,
        max_quota_retries: int = 5,
    ):
        self.key_provider = key_provider
        self.single_key = (single_key or "").strip() if single_key else None
        self.client_factory = client_factory
        self.max_attempts = max_attempts
        self.max_total_time = max_total_time
        self.max_quota_retries = max_quota_retries
        self._client = None
        self._client_key: Optional[str] = None
        self._retry_same_key: Optional[str] = None  # When set, use this key for next attempt (retry same key after 429)
        self._model_index: int = 0  # Rotate models on 429 (passed to client_factory)
        self._last_used: Dict[Tuple[str, str], float] = {}  # (key_str, model_name) -> timestamp; per-key-per-model RPM (from Austria)

    def _get_key(self, delay_seconds: float = 5.0) -> Optional[str]:
        if self._retry_same_key is not None:
            key = self._retry_same_key
            self._retry_same_key = None
            return key
        if self.key_provider:
            return self.key_provider.get_next_key(delay_seconds=delay_seconds)
        return self.single_key

    def _get_client(self, key_str: str):
        if not self.client_factory:
            raise RuntimeError("No client_factory set on LLMExecutor")
        # Include model_index so we can rotate models on 429
        model_index = getattr(self, "_model_index", 0)
        if not self._client or self._client_key != key_str:
            try:
                self._client = self.client_factory(key_str, model_index)
            except TypeError:
                self._client = self.client_factory(key_str)
            self._client_key = key_str
        return self._client

    def _invalidate_client(self) -> None:
        self._client = None
        self._client_key = None

    async def execute_async(self, prompt: str, max_attempts_override: Optional[int] = None) -> str:
        max_attempts = max_attempts_override if max_attempts_override is not None else self.max_attempts
        attempts = 0
        last_err = None
        quota_error_count = 0
        start = time.time()
        import sys
        sys.stdout.flush()

        while attempts < max_attempts:
            if self.max_total_time > 0 and time.time() - start > self.max_total_time:
                raise Exception(
                    f"API call timed out after {self.max_total_time:.0f}s. Quota may be exhausted."
                )
            current_key = None
            try:
                # Different keys with breaks: require MIN_DELAY_SAME_KEY_SEC before reusing a key
                delay = MIN_DELAY_SAME_KEY_SEC
                current_key = self._get_key(delay_seconds=delay)
                if not current_key:
                    if self.key_provider:
                        if self.key_provider.get_available_count() == 0:
                            raise Exception(
                                "All API keys exhausted. Add new keys or wait for quotas to reset."
                            )
                        wait = MIN_DELAY_SAME_KEY_SEC
                        print(f"  [WAIT] All keys in cooldown, waiting {wait:.0f}s before next key...")
                        await asyncio.sleep(wait)
                        current_key = self._get_key(delay_seconds=0)
                    if not current_key:
                        raise Exception("No API key available.")
                key_str = current_key.strip()
                # Per-key-per-model rate limit (from Austria): wait 60/RPM before reusing same (key, model)
                from lib.llm_config import MODEL_PRIORITY, MODEL_RPM
                model_index = getattr(self, "_model_index", 0)
                model_name = MODEL_PRIORITY[model_index % len(MODEL_PRIORITY)]
                delay_sec = _delay_sec_for_model(model_name)
                now = time.time()
                last = self._last_used.get((key_str, model_name), 0)
                wait = max(0.0, last + delay_sec - now)
                if wait > 0:
                    await asyncio.sleep(wait)
                self._last_used[(key_str, model_name)] = time.time()
                _pinpoint = os.environ.get("LLM_PINPOINT") in ("1", "true", "yes")
                if attempts == 0:
                    print(f"  [API] Making request with key {key_str[:20]}...")
                    sys.stdout.flush()
                elif attempts > 0:
                    print(f"  [RETRY] Attempt {attempts + 1}/{max_attempts} with key {key_str[:20]}...")
                    sys.stdout.flush()
                if _pinpoint:
                    print("  [PINPOINT] get_client_start (run_in_executor)...")
                    sys.stdout.flush()
                # Get client in thread so list_models() doesn't block the event loop
                loop = asyncio.get_event_loop()
                client = await loop.run_in_executor(None, lambda: self._get_client(key_str))
                if _pinpoint:
                    print("  [PINPOINT] get_client_done")
                    sys.stdout.flush()
                if _pinpoint:
                    print(f"  [PINPOINT] api_call_start (wait_for {API_CALL_TIMEOUT_SEC or '∞'}s)...")
                    sys.stdout.flush()
                # Per-call timeout: 0 = no timeout (wait until API responds or fails)
                if API_CALL_TIMEOUT_SEC and API_CALL_TIMEOUT_SEC > 0:
                    response = await asyncio.wait_for(
                        client.generate_content_async(prompt),
                        timeout=API_CALL_TIMEOUT_SEC,
                    )
                else:
                    response = await client.generate_content_async(prompt)
                if _pinpoint:
                    print("  [PINPOINT] api_call_done")
                    sys.stdout.flush()
                print(f"  [API] Response received")
                sys.stdout.flush()
                if self.key_provider and current_key:
                    self.key_provider.reset_key_errors(current_key)
                self._model_index = 0  # Success: next call tries preferred model first
                if not response.candidates or len(response.candidates) == 0:
                    raise Exception("Empty response")
                c = response.candidates[0]
                if hasattr(c, "finish_reason"):
                    if c.finish_reason == 3:
                        raise Exception("Response blocked by safety filter.")
                    if c.finish_reason == 4:
                        raise Exception("Response blocked by recitation filter.")
                # Extract text: response.text can raise if candidate has no valid Part (e.g. finish_reason=1 but empty)
                try:
                    return response.text or ""
                except Exception as text_err:
                    err_str = str(text_err).lower()
                    if "part" in err_str or "finish_reason" in err_str or "valid" in err_str:
                        # Candidate has no content parts - extract manually or treat as empty
                        out = []
                        if hasattr(c, "content") and c.content and hasattr(c.content, "parts"):
                            for part in getattr(c.content, "parts", []) or []:
                                if hasattr(part, "text") and part.text:
                                    out.append(part.text)
                        if not out and hasattr(c, "parts"):
                            for part in getattr(c, "parts", []) or []:
                                if hasattr(part, "text") and part.text:
                                    out.append(part.text)
                        if out:
                            return "".join(out)
                        # No parts: treat as empty response so caller can fall back (retry / no-info handling)
                        print(f"  [API] Response has no content parts (finish_reason may be 1); treating as empty")
                        sys.stdout.flush()
                        return ""
                    raise
            except Exception as e:
                last_err = e
                error_msg = str(e)
                print(f"  [ERROR] Async API call failed: {error_msg[:150]}")
                sys.stdout.flush()

                if _is_key_expired_error(e):
                    if self.key_provider and current_key:
                        self.key_provider.mark_key_exhausted(current_key)
                        next_key = self.key_provider.get_next_key(delay_seconds=0)
                        if next_key and next_key.strip() != (current_key or "").strip():
                            self._invalidate_client()
                            attempts += 1
                            continue
                        if self.key_provider.get_available_count() == 0:
                            _raise_keys_exhausted(
                                len(self.key_provider.keys), False, error_msg, "expired or invalid"
                            )
                        await asyncio.sleep(1)
                        attempts += 1
                        continue
                    _raise_keys_exhausted(1, True, error_msg, "expired or invalid")

                if _is_key_leaked_error(e):
                    if self.key_provider and current_key:
                        self.key_provider.mark_key_exhausted(current_key)
                        next_key = self.key_provider.get_next_key(delay_seconds=0)
                        if next_key and next_key.strip() != (current_key or "").strip():
                            self._invalidate_client()
                            attempts += 1
                            continue
                        if self.key_provider.get_available_count() == 0:
                            _raise_keys_exhausted(
                                len(self.key_provider.keys), False, error_msg, "leaked or invalid"
                            )
                        await asyncio.sleep(1)
                        attempts += 1
                        continue
                    _raise_keys_exhausted(1, True, error_msg, "leaked")

                if _is_403_forbidden(e):
                    if self.key_provider and current_key:
                        print(f"  [403] Forbidden for key {current_key[:20]}..., marking exhausted")
                        sys.stdout.flush()
                        self.key_provider.mark_key_exhausted(current_key)
                        next_key = self.key_provider.get_next_key(delay_seconds=0)
                        if next_key and next_key.strip() != (current_key or "").strip():
                            self._invalidate_client()
                            attempts += 1
                            continue
                    raise

                if isinstance(e, asyncio.TimeoutError):
                    print(f"  [TIMEOUT] API call did not respond within {API_CALL_TIMEOUT_SEC or 120:.0f}s, retrying...")
                    sys.stdout.flush()
                    await asyncio.sleep(5)
                    attempts += 1
                    continue

                # Check 429/rate limit BEFORE 404 so we don't mis-classify (429 body can contain "404")
                if _is_rate_limit_error(e):
                    if self.key_provider and current_key:
                        # Only mark exhausted / rotate if it's actual daily quota exhaustion; else retry same key after wait
                        _actual = _is_actual_quota_exhaustion(e)
                        _token = _is_token_quota_error(e)
                        if os.environ.get("LLM_DEBUG_429"):
                            _msg = str(e).lower()
                            print(f"  [429] actual_quota={_actual} token_quota={_token} msg_len={len(_msg)}")
                            sys.stdout.flush()
                        if _actual:
                            print(f"  [QUOTA] Daily quota exhausted for key {current_key[:20]}..., marking exhausted")
                            sys.stdout.flush()
                            self.key_provider.mark_key_exhausted(current_key)
                            next_key = self.key_provider.get_next_key(delay_seconds=0)
                            if next_key and next_key.strip() != (current_key or "").strip():
                                self._invalidate_client()
                                attempts += 1
                                continue
                            if self.key_provider.get_available_count() == 0:
                                raise Exception("All API keys have exhausted their daily quota. Please wait for quotas to reset or add new keys.")
                        elif _token:
                            self.key_provider.mark_key_exhausted(current_key)
                        else:
                            # RPM: rotate to next key and next model (don't exhaust key; use different key/model)
                            self.key_provider.mark_key_error(current_key)
                            self._model_index = getattr(self, "_model_index", 0) + 1
                            self._invalidate_client()
                            print(f"  [429] Rotating to next key and model (model_index={self._model_index})...")
                            sys.stdout.flush()
                            await asyncio.sleep(MIN_DELAY_SAME_KEY_SEC)
                            attempts += 1
                            continue
                    quota_error_count += 1
                    if quota_error_count > self.max_quota_retries:
                        if _is_token_quota_error(e):
                            raise Exception(
                                "Token quota exceeded. Wait 1–2 minutes or simplify the query."
                            )
                        if _is_actual_quota_exhaustion(e) and self.key_provider and current_key:
                            self.key_provider.mark_key_exhausted(current_key)
                        raise Exception(
                            f"Rate limit / quota errors after {self.max_quota_retries} retries. Try again later."
                        )
                    # RPM cooldown: wait then retry (with next key from rotation)
                    wait_time = _extract_retry_delay(e)
                    if wait_time is not None and wait_time > 60:
                        pass
                    elif wait_time is not None:
                        wait_time = max(wait_time + 1, 10)  # at least 10s before next attempt
                    else:
                        wait_time = 10
                    print(f"  [WAIT] Rate limit (RPM) - waiting {wait_time:.0f}s then next key/model (retry {quota_error_count}/{self.max_quota_retries})...")
                    sys.stdout.flush()
                    await asyncio.sleep(wait_time)
                    attempts += 1
                    continue

                if _is_404_not_found(e):
                    self._invalidate_client()
                    if self.key_provider and current_key:
                        print(f"  [404] Model not found for key {current_key[:20]}..., trying next key")
                        sys.stdout.flush()
                        next_key = self.key_provider.get_next_key(delay_seconds=0)
                        if next_key and next_key.strip() != (current_key or "").strip():
                            attempts += 1
                            continue
                    raise

                if _is_400_bad_request(e):
                    print(f"  [400] Bad request (check prompt/params), not retrying.")
                    sys.stdout.flush()
                    raise

                if _is_503_unavailable(e):
                    wait_503 = _extract_retry_delay(e) or 10
                    wait_503 = min(max(wait_503, 5), 60)
                    print(f"  [503] Service unavailable - waiting {wait_503:.0f}s before retry...")
                    sys.stdout.flush()
                    await asyncio.sleep(wait_503)
                    attempts += 1
                    continue

                raise
        raise last_err or Exception("API call failed after retries.")

    def execute_sync(self, prompt: str, max_attempts_override: Optional[int] = None) -> str:
        """Synchronous wrapper: run async executor in new event loop."""
        try:
            # Check if there's a running loop
            asyncio.get_running_loop()
            # There's a running loop - need to run in thread
            import threading
            import queue
            result_queue = queue.Queue()

            def run():
                try:
                    result = asyncio.run(self.execute_async(prompt, max_attempts_override))
                    result_queue.put(('success', result))
                except Exception as e:
                    result_queue.put(('error', e))

            t = threading.Thread(target=run, daemon=False)
            t.start()
            join_timeout = (self.max_total_time + 10) if self.max_total_time > 0 else None
            t.join(timeout=join_timeout)

            if join_timeout is not None and t.is_alive():
                raise Exception(f"execute_sync timed out after {self.max_total_time + 10}s")
            
            if not result_queue.empty():
                status, value = result_queue.get()
                if status == 'error':
                    raise value
                return value
            else:
                raise Exception("Thread completed but no result available")
        except RuntimeError:
            # No running loop - safe to use asyncio.run()
            return asyncio.run(self.execute_async(prompt, max_attempts_override))
