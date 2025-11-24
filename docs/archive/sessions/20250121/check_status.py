"""Check server status and debug traces."""
import sys
import requests
import json

try:
    r = requests.get('http://localhost:8000/debug/last?n=50', timeout=5)
    traces = r.json()
    print(f"Total traces: {len(traces)}")
    print("\nLast 20 events:")
    for i, t in enumerate(traces[-20:], 1):
        event = t.get('event', 'unknown')
        msg = str(t.get('message', ''))[:150]
        print(f"{i}. {event}: {msg}")
except Exception as e:
    print(f"Error: {e}")

