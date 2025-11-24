import requests
import json

try:
    print("Testing Adani query...")
    r = requests.post('http://localhost:8000/query', 
                     json={'question': 'tell me about adani', 'max_length': 15000}, 
                     timeout=120)
    print(f'Status: {r.status_code}')
    if r.status_code == 200:
        data = r.json()
        print(f'Answer length: {len(data["answer"])}')
        print(f'First 200 chars: {data["answer"][:200]}')
    else:
        print(f'Error response: {r.text}')
except Exception as e:
    print(f'Exception: {e}')
    import traceback
    traceback.print_exc()



