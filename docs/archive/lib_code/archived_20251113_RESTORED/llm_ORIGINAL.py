"""
LLM Answer Generation - Simple API wrapper.
No prompt logic - just handles API calls to Gemini/OpenAI.
"""
import os


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
                self.client = genai.GenerativeModel('gemini-2.0-flash')
                print("  [OK] Gemini API configured (2.0 Flash, 15 RPM / 1M TPM / 200 RPD)")
            except Exception as e:
                print(f"  [ERROR] Gemini setup failed: {e}")
                self.client = None
        else:
            print("  [WARNING] No Gemini API key found")
    
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
        
        try:
            response = self.client.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"  [ERROR] API call failed: {e}")
            raise
