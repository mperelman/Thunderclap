"""Auto-retry debugger that keeps trying until it succeeds."""
import sys
import os
import time
import re
import subprocess
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def extract_retry_delay(error_text):
    """Extract retry delay from error message."""
    match = re.search(r'retry in (\d+\.?\d*)s', error_text)
    if match:
        return float(match.group(1))
    return 30  # Default

def run_debugger():
    """Run debugger with automatic retries."""
    question = "Tell me about Vienna Rothschild banking"
    max_attempts = 100
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        print(f"\n{'='*70}")
        print(f"Attempt {attempt}/{max_attempts}")
        print(f"{'='*70}\n")
        
        try:
            # Run the review script
            result = subprocess.run(
                [sys.executable, "temp/review_api_answer.py", question],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            output = result.stdout + result.stderr
            
            # Check if it succeeded
            if result.returncode == 0 and "ANSWER REVIEW REPORT" in output:
                print(output)
                print("\n✓ Debugger completed successfully!")
                return True
            
            # Check for quota error
            if "429" in output or "quota" in output.lower():
                wait_time = extract_retry_delay(output)
                print(f"Quota exceeded. Waiting {wait_time:.1f} seconds...")
                time.sleep(wait_time + 2)
            else:
                # Other error, print and wait a bit
                print(output)
                print("Error occurred. Waiting 10 seconds before retry...")
                time.sleep(10)
                
        except subprocess.TimeoutExpired:
            print("Query timed out. Retrying...")
            time.sleep(5)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)
    
    print(f"\n✗ Failed after {max_attempts} attempts")
    return False

if __name__ == "__main__":
    run_debugger()


