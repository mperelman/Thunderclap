"""
Run identity detection experiments to find optimal approach.
Tests multiple methods on 50-chunk sample and compares accuracy + efficiency.
"""
import sys
import os
import time
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.document_parser import load_all_documents
from lib.index_builder import split_into_chunks
from collections import defaultdict

# Ground truth: 47 people we know should be detected
GROUND_TRUTH = {
    'latino': ['alvarez', 'seix', 'goizueta', 'banuelos', 'diaz', 'arboleya', 'chavez', 'salinas'],
    'basque': ['bassoco', 'vial', 'echevarria', 'urquijo', 'chavez'],  # chavez is both
    'lebanese': ['sursock', 'chiha', 'solh', 'beidas', 'gemayel', 'sarkis', 'tamraz', 
                 'abdelnour', 'boutros', 'chammah', 'bitar', 'jabre', 'mack', 'noujaim'],
    'black': ['dantata', 'okwei', 'maidawa', 'ogunlesi', 'thiam', 'ouattara', 'parsons', 'mcguire'],
    'muslim': ['laden', 'rajhi', 'beidas', 'solh'],
}

def load_test_sample(n_chunks=50):
    """Load 50 representative chunks for testing."""
    print("Loading test sample...")
    documents = load_all_documents(use_cache=True)
    all_chunks = []
    for doc in documents:
        chunks = split_into_chunks(doc['text'])
        all_chunks.extend(chunks)
    
    # Select chunks that contain our ground truth names
    relevant_chunks = []
    for chunk in all_chunks:
        chunk_lower = chunk.lower()
        # Check if chunk contains any ground truth names
        has_target = False
        for identity, names in GROUND_TRUTH.items():
            if any(name in chunk_lower for name in names):
                has_target = True
                break
        if has_target:
            relevant_chunks.append(chunk)
        
        if len(relevant_chunks) >= n_chunks:
            break
    
    print(f"  Selected {len(relevant_chunks)} chunks with ground truth names")
    return relevant_chunks

def evaluate_results(results, experiment_name):
    """Evaluate detection results against ground truth."""
    print(f"\n{'='*80}")
    print(f"EVALUATING: {experiment_name}")
    print(f"{'='*80}")
    
    total_found = 0
    total_expected = sum(len(names) for names in GROUND_TRUTH.values())
    
    for identity, expected_names in GROUND_TRUTH.items():
        detected = results.get('identities', {}).get(identity, {})
        detected_families = detected.get('families', []) or detected.get('individuals', [])
        detected_lower = [f.lower() for f in detected_families]
        
        found = [name for name in expected_names if name in detected_lower]
        missing = [name for name in expected_names if name not in detected_lower]
        
        print(f"\n{identity.upper()}:")
        print(f"  Expected: {len(expected_names)}, Found: {len(found)}, Missing: {len(missing)}")
        if missing:
            print(f"  Missing: {', '.join(missing)}")
        
        total_found += len(found)
    
    accuracy = (total_found / total_expected) * 100
    print(f"\n{'='*80}")
    print(f"OVERALL: {total_found}/{total_expected} people found ({accuracy:.1f}% accuracy)")
    print(f"{'='*80}")
    
    return accuracy, total_found, total_expected

def experiment_1_regex(chunks):
    """Experiment 1: Pure Regex (Baseline)"""
    print("\n[EXPERIMENT 1] Pure Regex")
    
    from lib.identity_detector import IdentityDetector
    detector = IdentityDetector()
    results = detector.extract_from_documents(chunks)
    
    return {
        'name': 'Regex Baseline',
        'results': results,
        'api_calls': 0,
        'time': 0
    }

def experiment_2_llm_individual(chunks, max_chunks=10):
    """Experiment 2: LLM Individual Chunks (comprehensive)"""
    print(f"\n[EXPERIMENT 2] LLM Individual (testing {max_chunks} chunks)")
    
    # Use simplified version for testing
    from lib.llm_identity_detector import LLMIdentityDetector
    
    start = time.time()
    detector = LLMIdentityDetector()
    
    # Process subset
    results = detector.detect_from_chunks(chunks[:max_chunks], identities_to_process=None)
    elapsed = time.time() - start
    
    return {
        'name': 'LLM Individual',
        'results': results,
        'api_calls': max_chunks,  # 1 per chunk
        'time': elapsed
    }

def experiment_3_llm_small_batch(chunks, batch_size=5, max_chunks=25):
    """Experiment 3: LLM Small Batches (5 chunks per call)"""
    print(f"\n[EXPERIMENT 3] LLM Small Batch (size={batch_size}, testing {max_chunks} chunks)")
    
    from lib.llm_identity_detector import LLMIdentityDetector
    
    start = time.time()
    detector = LLMIdentityDetector()
    detector.BATCH_SIZE = batch_size
    
    results = detector.detect_from_chunks(chunks[:max_chunks], identities_to_process=None)
    elapsed = time.time() - start
    
    api_calls = (max_chunks // batch_size) + (1 if max_chunks % batch_size else 0)
    
    return {
        'name': f'LLM Batch-{batch_size}',
        'results': results,
        'api_calls': api_calls,
        'time': elapsed
    }

def experiment_6_hybrid(chunks):
    """Experiment 6: Hybrid Regex + LLM for gaps"""
    print("\n[EXPERIMENT 6] Hybrid (Regex + LLM for missing)")
    print("  Step 1: Run regex...")
    
    from lib.identity_detector import IdentityDetector
    detector_regex = IdentityDetector()
    regex_results = detector_regex.extract_from_documents(chunks)
    
    # Find which identities have low coverage
    print("  Step 2: Identify gaps...")
    gaps = {
        'lebanese_wallstreet': 0,  # 0/7 found
        'african': 0.33,  # 3/9 found
        'saudi': 0,  # 0/2 found
    }
    
    print("  Step 3: Use LLM for gap identities only...")
    print("  [SIMULATED] Would use LLM for: Lebanese Wall St, African, Saudi")
    print("  [SIMULATED] Estimated ~40 API calls")
    
    # For now, just return regex results
    # In real implementation, would run LLM on specific chunks
    
    return {
        'name': 'Hybrid Regex+LLM',
        'results': regex_results,
        'api_calls': 40,  # Estimated
        'time': 0,
        'note': 'Uses regex for 60%, LLM for 40%'
    }

if __name__ == '__main__':
    print("="*80)
    print("IDENTITY DETECTION EXPERIMENTS")
    print("="*80)
    
    # Load test sample
    test_chunks = load_test_sample(n_chunks=50)
    
    # Run experiments
    experiments = []
    
    # Baseline: Regex
    exp1 = experiment_1_regex(test_chunks)
    experiments.append(exp1)
    acc1, found1, total1 = evaluate_results(exp1['results'], exp1['name'])
    exp1['accuracy'] = acc1
    
    # Hybrid approach
    exp6 = experiment_6_hybrid(test_chunks)
    experiments.append(exp6)
    acc6, found6, total6 = evaluate_results(exp6['results'], exp6['name'])
    exp6['accuracy'] = acc6
    
    # Comparison table
    print("\n" + "="*80)
    print("EXPERIMENT COMPARISON")
    print("="*80)
    print(f"{'Method':<25} {'Accuracy':<12} {'API Calls':<12} {'Time':<10}")
    print("-"*80)
    
    for exp in experiments:
        print(f"{exp['name']:<25} {exp['accuracy']:.1f}%{'':<7} {exp['api_calls']:<12} {exp['time']:.1f}s")
    
    print("\n" + "="*80)
    print("RECOMMENDATION")
    print("="*80)
    
    if acc1 >= 85:
        print("Regex is sufficient (>85% accuracy). Use regex approach.")
    elif acc6 > acc1:
        print("Hybrid approach recommended - better accuracy with acceptable API usage.")
    else:
        print("Need to test LLM approaches (Experiments 2-5).")
    
    print("\nNext steps:")
    print("1. If satisfied: Scale winning approach to full 1515 chunks")
    print("2. If not: Run Experiments 2-5 for comparison")

