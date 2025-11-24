"""Test if API is properly enabled for this project"""
import os
from dotenv import load_dotenv
load_dotenv(override=True)

key = os.getenv('GEMINI_API_KEY_1')
print(f"Testing key: {key[:20]}...")
print()

try:
    import google.generativeai as genai
    genai.configure(api_key=key)
    
    # Try to list models - this tests if API is enabled
    print("Checking if Generative Language API is enabled...")
    models = genai.list_models()
    
    model_list = list(models)
    print(f"[OK] API is enabled! Found {len(model_list)} models")
    print()
    
    # Try a minimal request
    print("Testing minimal API call...")
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    response = model.generate_content("Say 'test'")
    print(f"[SUCCESS] Response: {response.text}")
    print()
    print("The API key and project are working correctly!")
    print("The quota exhaustion might be hitting a different limit.")
    
except Exception as e:
    error_msg = str(e)
    print(f"[ERROR] {error_msg}")
    
    if "API_KEY_INVALID" in error_msg:
        print("\n[ISSUE] API key is invalid or expired")
    elif "403" in error_msg or "SERVICE_DISABLED" in error_msg:
        print("\n[ISSUE] Generative Language API not enabled for this project")
        print("Enable it at: https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com")
    elif "429" in error_msg or "quota" in error_msg.lower():
        print("\n[ISSUE] Quota exhausted on this project too")
        print("This project has also hit its 200 RPD limit")

