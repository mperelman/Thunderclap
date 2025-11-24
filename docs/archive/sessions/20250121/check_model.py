import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.llm import LLMAnswerGenerator

os.environ['GEMINI_API_KEY'] = 'AIzaSyC5T1rwS2L0veYeBeLs7kndmZUEzNtLs2g'
llm = LLMAnswerGenerator(api_key='AIzaSyC5T1rwS2L0veYeBeLs7kndmZUEzNtLs2g')

if llm.client:
    # Check the model name
    model_name = getattr(llm.client, '_model_name', None) or str(llm.client)
    print(f"Model being used: {model_name}")
else:
    print("No client initialized")


