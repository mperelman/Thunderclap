#!/usr/bin/env python3
"""
Debugging Helper Script

Use this script to methodically debug issues.
It guides you through the problem-solving process and documents solutions.
"""

import json
from pathlib import Path
from datetime import datetime

DEBUG_LOG = Path("temp/debug_sessions.json")

def load_sessions():
    """Load previous debug sessions."""
    if DEBUG_LOG.exists():
        with open(DEBUG_LOG) as f:
            return json.load(f)
    return []

def save_session(session):
    """Save a debug session."""
    sessions = load_sessions()
    sessions.append(session)
    with open(DEBUG_LOG, 'w') as f:
        json.dump(sessions, f, indent=2)

def start_debug_session(problem_description):
    """Start a new debugging session."""
    session = {
        "started": datetime.now().isoformat(),
        "problem": problem_description,
        "observations": [],
        "hypotheses": [],
        "tests": [],
        "fixes": [],
        "verified": False,
        "solution": None
    }
    return session

def add_observation(session, observation):
    """Add an observation about the problem."""
    session["observations"].append({
        "timestamp": datetime.now().isoformat(),
        "observation": observation
    })
    print(f"✓ Observation recorded: {observation}")

def add_hypothesis(session, hypothesis, reasoning, test_method):
    """Add a hypothesis to test."""
    session["hypotheses"].append({
        "timestamp": datetime.now().isoformat(),
        "hypothesis": hypothesis,
        "reasoning": reasoning,
        "test_method": test_method,
        "tested": False,
        "result": None
    })
    print(f"✓ Hypothesis recorded: {hypothesis}")

def record_test(session, hypothesis_index, test_script, result, passed):
    """Record test results."""
    if hypothesis_index < len(session["hypotheses"]):
        session["hypotheses"][hypothesis_index]["tested"] = True
        session["hypotheses"][hypothesis_index]["result"] = {
            "test_script": test_script,
            "result": result,
            "passed": passed,
            "timestamp": datetime.now().isoformat()
        }
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} Hypothesis {hypothesis_index + 1}: {session['hypotheses'][hypothesis_index]['hypothesis']}")

def record_fix(session, fix_description, files_changed):
    """Record a fix attempt."""
    session["fixes"].append({
        "timestamp": datetime.now().isoformat(),
        "description": fix_description,
        "files_changed": files_changed,
        "verified": False
    })
    print(f"✓ Fix recorded: {fix_description}")

def verify_fix(session, fix_index, test_script, result, passed):
    """Verify a fix works."""
    if fix_index < len(session["fixes"]):
        session["fixes"][fix_index]["verified"] = True
        session["fixes"][fix_index]["verification"] = {
            "test_script": test_script,
            "result": result,
            "passed": passed,
            "timestamp": datetime.now().isoformat()
        }
        status = "✅ VERIFIED" if passed else "❌ NOT VERIFIED"
        print(f"{status} Fix {fix_index + 1}: {session['fixes'][fix_index]['description']}")

def complete_session(session, solution):
    """Mark session as complete with solution."""
    session["completed"] = datetime.now().isoformat()
    session["verified"] = True
    session["solution"] = solution
    save_session(session)
    print(f"\n✅ Session completed and saved!")
    print(f"Solution: {solution}")

def print_checklist():
    """Print debugging checklist."""
    print("\n" + "="*70)
    print("DEBUGGING CHECKLIST")
    print("="*70)
    print()
    print("Before claiming a fix:")
    print("  [ ] I've observed the actual problem (not assumed)")
    print("  [ ] I've formed a hypothesis about the cause")
    print("  [ ] I've created a test to verify the hypothesis")
    print("  [ ] The test confirms the hypothesis is correct")
    print("  [ ] I've implemented a fix")
    print("  [ ] I've verified the fix works in problem environment")
    print("  [ ] I've measured the improvement (before/after)")
    print("  [ ] I've documented the solution with test results")
    print()

def interactive_debug():
    """Interactive debugging session."""
    print("="*70)
    print("DEBUGGING HELPER")
    print("="*70)
    print()
    
    problem = input("Describe the problem: ")
    session = start_debug_session(problem)
    
    print("\n" + "="*70)
    print("STEP 1: OBSERVE")
    print("="*70)
    print("Record your observations. Type 'done' when finished.")
    while True:
        obs = input("\nObservation: ")
        if obs.lower() == 'done':
            break
        add_observation(session, obs)
    
    print("\n" + "="*70)
    print("STEP 2: HYPOTHESIZE")
    print("="*70)
    print("List possible causes. Type 'done' when finished.")
    while True:
        hyp = input("\nHypothesis: ")
        if hyp.lower() == 'done':
            break
        reasoning = input("  Why this could be the cause: ")
        test_method = input("  How to test: ")
        add_hypothesis(session, hyp, reasoning, test_method)
    
    print("\n" + "="*70)
    print("STEP 3: TEST")
    print("="*70)
    print_checklist()
    
    print("After testing, record results:")
    for i, hyp in enumerate(session["hypotheses"]):
        print(f"\nHypothesis {i+1}: {hyp['hypothesis']}")
        test_script = input("  Test script path: ")
        result = input("  Test result: ")
        passed = input("  Did it pass? (y/n): ").lower() == 'y'
        record_test(session, i, test_script, result, passed)
    
    print("\n" + "="*70)
    print("STEP 4: FIX AND VERIFY")
    print("="*70)
    fix_desc = input("\nFix description: ")
    files = input("Files changed (comma-separated): ").split(',')
    record_fix(session, fix_desc, [f.strip() for f in files])
    
    verify_script = input("Verification test script: ")
    verify_result = input("Verification result: ")
    verify_passed = input("Did verification pass? (y/n): ").lower() == 'y'
    verify_fix(session, 0, verify_script, verify_result, verify_passed)
    
    if verify_passed:
        solution = input("\nSolution summary: ")
        complete_session(session, solution)
    else:
        print("\n⚠️  Fix not verified. Continue debugging or save session?")
        save = input("Save session? (y/n): ").lower() == 'y'
        if save:
            save_session(session)
            print("Session saved. Continue debugging when ready.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--checklist":
        print_checklist()
    else:
        interactive_debug()
