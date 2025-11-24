"""Run debugger with automatic retry on quota errors."""
import sys
import os
import time
import re
import requests
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from temp.review_api_answer import review_api_answer

def run_with_retry(question, max_retries=10):
    """Run query with automatic retry on quota errors."""
    for attempt in range(max_retries):
        try:
            print(f"Attempt {attempt + 1}/{max_retries}...")
            result = review_api_answer(question)
            if result is None:
                # API error, check if we should retry
                continue
            results, answer = result
            return results, answer
        except Exception as e:
            error_str = str(e)
            # Check if it's a quota error from the review function
            if "429" in error_str or "quota" in error_str.lower():
                # Extract retry delay from error message
                retry_match = re.search(r'retry in (\d+\.?\d*)s', error_str)
                if retry_match:
                    wait_time = float(retry_match.group(1))
                    print(f"Quota exceeded. Waiting {wait_time:.1f} seconds before retry...")
                    time.sleep(wait_time + 1)  # Add 1 second buffer
                else:
                    # Default wait time
                    wait_time = 30
                    print(f"Quota exceeded. Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
            else:
                # Other error, don't retry
                print(f"Error: {e}")
                raise
    
    # Check if we have a saved answer to review
    print("\nAll retries exhausted. Checking for saved answer...")
    if os.path.exists("temp/last_answer.txt"):
        print("Found saved answer, reviewing it...")
        result = review_api_answer(use_saved=True)
        if result:
            return result
    raise Exception(f"Failed after {max_retries} attempts and no saved answer found")

if __name__ == "__main__":
    question = "Tell me about Vienna Rothschild banking"
    try:
        results, answer = run_with_retry(question)
        print("\n✓ Debugger completed successfully!")
    except Exception as e:
        print(f"\n✗ Debugger failed: {e}")

