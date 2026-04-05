"""
Centralized LLM Configuration – **source of truth** for model list and RPM (README points here).

Uses a FIXED model list only (no list_models call). Text-out models only: 2.5 Flash, 2.5 Flash Lite,
3 Flash. 2.5 Flash TTS is not supported for generateContent in the standard API (404).

Note: Gemini 2.0 Flash and 2.0 Flash Lite are retired June 1, 2026; this project uses 2.5/3 only.

Rate limits (per key per model); delay before reusing same (key, model) = 60/RPM seconds:
  Model                    RPM   TPM     RPD
  Gemini 2.5 Flash         5    250 K   20
  Gemini 2.5 Flash Lite   10   250 K   20
  Gemini 3 Flash           10  250 K   20

Enforcement of delay and 429 handling: lib.llm_executor.
"""
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# API Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
GEMINI_MODEL = 'gemini-pro'

# Fixed list of model IDs that support text output (generateContent). Do NOT use list_models().
# Order: 2.5 Flash, 2.5 Flash Lite, 3 Flash (aligned with Austria).
MODEL_PRIORITY = [
    'gemini-2.5-flash',        # Gemini 2.5 Flash
    'gemini-2.5-flash-lite',   # Gemini 2.5 Flash Lite
    'gemini-3-flash-preview',   # Gemini 3 Flash
]

# Limit is per key per model (RPM = requests per minute). Delay between same (key, model) = 60/RPM.
MODEL_RPM = {
    'gemini-2.5-flash': 5,
    'gemini-2.5-flash-lite': 10,
    'gemini-3-flash-preview': 10,
}

# Generation configuration
GENERATION_CONFIG = {
    "temperature": 0.2,
    "top_p": 0.3,
    "top_k": 1,
    "max_output_tokens": 16384,
    "candidate_count": 1,
}

def get_llm_client(api_key=None, model_index=0):
    """
    Get a configured Gemini LLM client using a FIXED model list (no list_models).
    model_index rotates on 429 (next model in MODEL_PRIORITY). Per-key-per-model RPM is enforced in llm_executor.
    """
    key = api_key or GEMINI_API_KEY
    if not key:
        raise Exception("No API key found. Set GEMINI_API_KEY environment variable.")
    key = key.strip()
    if not key.startswith('AIza'):
        raise Exception(f"Invalid API key format. Key should start with 'AIza'. Got: {key[:10]}...")

    genai.configure(api_key=key)
    idx = max(0, int(model_index)) % len(MODEL_PRIORITY)
    model_name = MODEL_PRIORITY[idx]
    if idx > 0:
        print(f"  [DEBUG] Using model #{idx + 1}: {model_name} (rotated from 429)")
    client = genai.GenerativeModel(
        model_name=model_name,
        generation_config=GENERATION_CONFIG,
    )
    print(f"  [OK] Gemini API configured ({model_name}), key length: {len(key)}")
    return client

