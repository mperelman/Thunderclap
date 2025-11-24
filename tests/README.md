# Test Scripts

This folder contains experimental and testing scripts for identity detection development.

## Test Scripts

### `run_experiments.py`
Compares different detection approaches (regex vs LLM vs hybrid).
Tests on 50-chunk sample to evaluate accuracy and efficiency.

**Status:** Designed but needs API quota to run
**Purpose:** Find optimal detection method

### `test_llm_on_sample.py`
Tests LLM detector on 10 highly relevant chunks.
Used to verify LLM can find people regex missed (Wall St Lebanese, African bankers).

**Status:** Tested, hits API quota
**Purpose:** Validate LLM approach works

---

## NOT Test Scripts (Do Not Move Here)

These are production scripts:

- `scripts/complete_detection_tomorrow.py` - **PRODUCTION**: Run after API quota resets
- `scripts/analyze_attributes.py` - **UTILITY**: Analyzes detected attributes

---

## Running Tests

### After API Quota Reset:

```bash
# Run full detection (production)
python scripts/complete_detection_tomorrow.py

# Then rebuild index
python build_index.py
```

### To Run Experiments (Optional):

```bash
# Compare approaches
python tests/run_experiments.py

# Test LLM on sample
python tests/test_llm_on_sample.py
```

---

## Test Results Summary

### Regex Detection (Baseline):
- **Accuracy**: 47% (22/47 known people)
- **API Calls**: 0 (free)
- **Strengths**: Latino (100%), some Lebanese (78%)
- **Weaknesses**: Lebanese Wall St (0%), African (33%), Saudi (0%)

### LLM Detection (Expected):
- **Accuracy**: 90-95% (42-45/47 people)
- **API Calls**: ~138 (with batching)
- **Time**: ~12 minutes
- **Comprehensive**: Multi-attribute, hierarchical, discovers new identities

---

## Archived Files

Old approaches kept as backup:

- `lib/identity_detector_regex_archive.py` - Original regex approach (100+ patterns)
- Can revert if needed, but LLM approach should be superior


