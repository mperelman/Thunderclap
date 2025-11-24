"""Quick test of the query endpoint"""
import requests
import json

url = "http://localhost:8000/query"
data = {
    "question": "tell me about female bankers",
    "max_length": 3000
}

print("Sending query...")
try:
    response = requests.post(url, json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")

