"""Restart server and test query."""
import subprocess
import sys
import os
import time
import requests

# Stop all Python processes
print("Stopping all Python processes...")
try:
    subprocess.run(["taskkill", "/F", "/IM", "python.exe"], 
                   capture_output=True, check=False)
    time.sleep(2)
except:
    pass

# Clear caches
print("Clearing Python caches...")
for root, dirs, files in os.walk('.'):
    # Remove __pycache__ directories
    if '__pycache__' in dirs:
        cache_dir = os.path.join(root, '__pycache__')
        try:
            import shutil
            shutil.rmtree(cache_dir)
            print(f"  Removed {cache_dir}")
        except:
            pass
    # Remove .pyc files
    for file in files:
        if file.endswith('.pyc'):
            try:
                os.remove(os.path.join(root, file))
            except:
                pass

print("Starting server...")
# Start server in background
env = os.environ.copy()
env['GEMINI_API_KEY'] = 'AIzaSyCGPsVN5zK8nWGRc6gNuniim4mJ16kNWZM'
server_process = subprocess.Popen(
    [sys.executable, "server.py"],
    env=env,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

# Wait for server to start
print("Waiting for server to start...")
time.sleep(12)

# Test the query
print("\nTesting query: 'Tell me about Rothschild Vienna'")
try:
    response = requests.post(
        "http://localhost:8000/query",
        json={"question": "Tell me about Rothschild Vienna", "max_length": 15000},
        timeout=180
    )
    if response.status_code == 200:
        print("[OK] Query successful!")
        result = response.json()
        answer = result.get('answer', '')
        print(f"\nAnswer length: {len(answer)} characters")
        print(f"First 500 chars:\n{answer[:500]}...")
    else:
        print(f"[ERROR] Query failed with status {response.status_code}")
        print(f"Error: {response.text}")
except Exception as e:
    print(f"[ERROR] Error: {e}")

# Stop server
print("\nStopping server...")
try:
    server_process.terminate()
    server_process.wait(timeout=5)
except:
    server_process.kill()

print("Done!")

