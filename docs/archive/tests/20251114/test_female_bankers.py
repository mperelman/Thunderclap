"""Test female bankers query specifically"""
import requests
import time

url = "http://localhost:8000/query"
data = {"question": "tell me about female bankers", "max_length": 3000}

print("Testing: 'tell me about female bankers'")
print("This will take 2-3 minutes (1101 chunks)...")
print("Waiting...")

start = time.time()
try:
    response = requests.post(url, json=data, timeout=300)  # 5 min timeout
    elapsed = time.time() - start
    print(f"\nStatus: {response.status_code}")
    print(f"Time: {elapsed:.1f} seconds")
    if response.status_code == 200:
        answer = response.json()['answer']
        print(f"Answer length: {len(answer)} characters")
        print(f"\nFirst 500 chars:\n{answer[:500]}")
    else:
        print(f"Error: {response.text}")
except requests.exceptions.Timeout:
    print("Request timed out after 5 minutes")
except Exception as e:
    print(f"Error: {e}")

