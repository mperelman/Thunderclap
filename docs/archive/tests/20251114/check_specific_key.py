"""Check if specific key exists"""
import os
from dotenv import load_dotenv

load_dotenv()

target_key = "AIzaSyBwFhYh5ri6tBvFPtpuFgV1SzyEbObt1lo"

# Check all possible locations
found = False

# Check main key
main_key = os.getenv('GEMINI_API_KEY')
if main_key == target_key:
    print(f"YES - Found as GEMINI_API_KEY")
    found = True

# Check numbered keys
if not found:
    for i in range(1, 20):
        key = os.getenv(f'GEMINI_API_KEY_{i}')
        if key == target_key:
            print(f"YES - Found as GEMINI_API_KEY_{i}")
            found = True
            break

if not found:
    print("NO - This key is NOT in the .env file")

