import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.llm import LLMAnswerGenerator

os.environ['GEMINI_API_KEY'] = 'REVOKED_KEY_REMOVED'  # REMOVED: Exposed key revoked
llm = LLMAnswerGenerator(api_key='REVOKED_KEY_REMOVED')  # REMOVED: Exposed key revoked

if llm.client:
    # Check the model name
    model_name = getattr(llm.client, '_model_name', None) or str(llm.client)
    print(f"Model being used: {model_name}")
else:
    print("No client initialized")


