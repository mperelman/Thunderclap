"""
Centralized LLM Configuration
All LLM-related scripts should import from this module to ensure consistency.
"""
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# API Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
GEMINI_MODEL = 'gemini-pro'  # Use gemini-pro (most widely supported, works with all API versions)

# Generation configuration
GENERATION_CONFIG = {
    "temperature": 0.2,
    "top_p": 0.3,
    "top_k": 1,
    "max_output_tokens": 16384,
    "candidate_count": 1,
}

def get_llm_client(api_key=None):
    """
    Get a configured Gemini LLM client.
    
    Args:
        api_key: Optional API key. If not provided, uses GEMINI_API_KEY from env/.env
    
    Returns:
        genai.GenerativeModel: Configured Gemini model
    
    Raises:
        Exception: If API key is not set or model initialization fails
    """
    # Use provided key, or fall back to env/.env
    key = api_key or GEMINI_API_KEY
    if not key:
        raise Exception("No API key found. Set GEMINI_API_KEY environment variable.")
    
    # Strip whitespace and validate key format
    key = key.strip()
    if not key.startswith('AIza'):
        raise Exception(f"Invalid API key format. Key should start with 'AIza'. Got: {key[:10]}...")
    
    # Configure globally - this is required for GenerativeModel to work
    # The configure() method stores the key internally
    print(f"  [DEBUG] Configuring genai with key: {key[:20]}... (length: {len(key)})")
    genai.configure(api_key=key)
    
    # Try multiple model names in order of preference
    # Start with most basic/compatible model first
    model_names = ['gemini-pro', 'models/gemini-pro', 'gemini-1.5-pro', 'models/gemini-1.5-pro']
    
    last_error = None
    for model_name in model_names:
        try:
            print(f"  [DEBUG] Trying model: {model_name}")
            # Create client - it will use the globally configured key
            # IMPORTANT: The client must be created AFTER configure() is called
            client = genai.GenerativeModel(
                model_name=model_name,
                generation_config=GENERATION_CONFIG,
            )
            print(f"  [OK] Gemini API configured ({model_name}), key: {key[:20]}...")
            return client
        except Exception as e:
            last_error = e
            print(f"  [DEBUG] Model {model_name} failed: {e}")
            continue
    
    # If all models failed, raise the last error
    raise Exception(f"Failed to create Gemini client with any model. Last error: {last_error}")

