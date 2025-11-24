"""Test if query.ask works"""
import os

os.environ['GEMINI_API_KEY'] = 'AIzaSyAztOHisWFGmAxxuTyuvUTwPzKI4cgrH24'

try:
    from query import ask
    print("✅ Import successful")
    
    print("\n🔍 Testing ask function...")
    result = ask("Tell me about Lehman", use_llm=True)
    print(f"✅ Query successful! ({len(result)} chars)")
    print(f"\nFirst 200 chars:\n{result[:200]}...")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()


