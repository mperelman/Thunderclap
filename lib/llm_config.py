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
GEMINI_MODEL = 'gemini-1.5-flash'  # The model that works with your API key

# Generation configuration
GENERATION_CONFIG = {
    "temperature": 0.2,
    "top_p": 0.3,
    "top_k": 1,
    "max_output_tokens": 16384,
    "candidate_count": 1,
}

def get_llm_client():
    """
    Get a configured Gemini LLM client.
    
    Returns:
        genai.GenerativeModel: Configured Gemini model
    
    Raises:
        Exception: If API key is not set or model initialization fails
    """
    if not GEMINI_API_KEY:
        raise Exception("No API key found. Set GEMINI_API_KEY environment variable.")
    
    genai.configure(api_key=GEMINI_API_KEY)
    
    client = genai.GenerativeModel(
        model_name=GEMINI_MODEL,
        generation_config=GENERATION_CONFIG,
    )
    
    print(f"  [OK] Gemini API configured ({GEMINI_MODEL})")
    return client

