"""List models that support Batch API"""
import sys
sys.path.insert(0, '.')

from google import genai
from lib.api_key_manager import APIKeyManager

km = APIKeyManager()
client = genai.Client(api_key=km.get_current_key())

print("Listing models that support Batch API...\n")

try:
    models = client.models.list()
    
    batch_models = []
    for model in models:
        if hasattr(model, 'supported_generation_methods'):
            if 'generateContent' in model.supported_generation_methods:
                batch_models.append(model.name)
    
    print("Models supporting batch generation:")
    for model in batch_models:
        print(f"  - {model}")
    
    if not batch_models:
        print("  No batch models found")
        print("\n  All available models:")
        for model in models:
            print(f"    - {model.name}")

except Exception as e:
    print(f"Error: {e}")


