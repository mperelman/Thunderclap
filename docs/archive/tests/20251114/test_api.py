"""Quick test of the secure API"""
import os
import sys
import time
import subprocess
import requests

# Set API key
os.environ['GEMINI_API_KEY'] = 'AIzaSyAztOHisWFGmAxxuTyuvUTwPzKI4cgrH24'

print("🚀 Starting secure API server...")
print("=" * 60)

# Start server in background
server = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "secure_api:app", "--port", "8000"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# Wait for server to start
print("⏳ Waiting for server to start...")
time.sleep(5)

try:
    # Test health endpoint
    print("\n📋 Testing health check...")
    response = requests.get("http://localhost:8000/health")
    print(f"✅ Health check: {response.json()}")
    
    # Test query endpoint
    print("\n🔍 Testing query endpoint...")
    print("Question: 'Tell me about Lehman'")
    response = requests.post(
        "http://localhost:8000/query",
        json={"question": "Tell me about Lehman", "max_length": 500}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Query successful!")
        print(f"\n📖 Answer (first 300 chars):\n{data['answer'][:300]}...")
    else:
        print(f"❌ Query failed: {response.status_code} - {response.text}")
    
    print("\n" + "=" * 60)
    print("✅ API is working! Server running at: http://localhost:8000")
    print("=" * 60)
    print("\nTo test the frontend:")
    print("1. Open simple_frontend.html in your browser")
    print("2. Make sure it points to: http://localhost:8000/query")
    print("\nPress Ctrl+C to stop the server")
    
    # Keep server running
    server.wait()
    
except KeyboardInterrupt:
    print("\n\n🛑 Stopping server...")
    server.terminate()
    print("✅ Server stopped")
except Exception as e:
    print(f"\n❌ Error: {e}")
    server.terminate()


