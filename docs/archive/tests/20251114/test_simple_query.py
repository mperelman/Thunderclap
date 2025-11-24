"""Test with simplest possible query"""
import requests

url = "http://localhost:8000/query"
data = {"question": "tell me about Hope", "max_length": 3000}

print("Testing simple query: 'tell me about Hope'")
response = requests.post(url, json=data)
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:500]}")

