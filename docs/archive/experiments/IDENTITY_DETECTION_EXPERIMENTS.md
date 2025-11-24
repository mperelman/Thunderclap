# Identity Detection Experiments

## Goal
Find the most accurate and efficient method for detecting banking family identities within free tier limits.

## Constraints
- Free tier: 15 RPM, 1M TPM, **200 RPD**
- 1515 total chunks
- Must be completable without paid tier

---

## Experiment Design

### **Test Sample: 50 Chunks (representative)**
- 20 chunks with Latino/Hispanic content
- 10 chunks with Lebanese content
- 10 chunks with African/Muslim content
- 10 chunks with Jewish/European content

**Ground truth: Manual verification of 47 known people**

---

## **Experiment 1: Pure Regex (BASELINE)**
**Status:** Already tested

**Results:**
- Accuracy: 47% (22/47 people found)
- API calls: 0
- Time: <1 minute
- Pros: Free, fast
- Cons: Hardcoding, brittle, false negatives

**Known gaps:**
- 0/7 Lebanese Wall Street
- 0/2 Saudi/Gulf
- 6/9 African missing

---

## **Experiment 2: LLM - Individual Chunks**
**Method:** 1 chunk = 1 API call, comprehensive prompt

**Setup:**
```python
# Comprehensive Option A prompt
# Detects: religion, ethnicity, race, gender, geography, conversion, ancestry
```

**Test on 50 chunks:**
- API calls: 50
- Tokens: ~50K input
- Time: ~5 minutes (with rate limit)

**Metrics to measure:**
- Accuracy: How many of 47 people found?
- Precision: False positives?
- Recall: False negatives?
- Multi-attribute capture: Does it catch Chavez's sephardi + basque + latino?

---

## **Experiment 3: LLM - Small Batches (5 chunks)**
**Method:** 5 chunks = 1 API call

**Test on 50 chunks:**
- API calls: 10
- Tokens: ~40K input
- Time: ~1 minute

**Hypothesis:** 5× more efficient, but might lose accuracy?

---

## **Experiment 4: LLM - Medium Batches (10 chunks)**
**Test on 50 chunks:**
- API calls: 5
- Tokens: ~30K input
- Time: ~30 seconds

**Hypothesis:** 10× more efficient, but more accuracy loss?

---

## **Experiment 5: LLM - Large Batches (20 chunks)**
**Test on 50 chunks:**
- API calls: 2-3
- Tokens: ~25K input
- Time: ~15 seconds

**Hypothesis:** 20× more efficient, but significant accuracy loss?

---

## **Experiment 6: Hybrid - Regex + LLM Validation**
**Method:** 
1. Regex finds candidates (fast, 47% accurate)
2. LLM validates ONLY false negatives (the 25 missing people)

**Test on 50 chunks:**
- Run regex: 0 API calls, finds ~24 people
- LLM processes only chunks with missing people: ~15 API calls
- Total: 15 API calls vs 50 (70% reduction)

**Hypothesis:** Best of both worlds - speed + accuracy?

---

## **Experiment 7: Two-Stage LLM**
**Stage 1:** Quick scan (simple prompt, large batches)
- "Does this chunk mention Lebanese/Black/Muslim bankers? Yes/No"
- Filter to relevant chunks only

**Stage 2:** Detailed extraction (comprehensive prompt, small batches)
- Only process chunks flagged in Stage 1

**Test on 50 chunks:**
- Stage 1: 5 API calls (10 chunks each, simple yes/no)
- Stage 2: ~15 API calls (only relevant chunks, detailed)
- Total: 20 API calls vs 50 (60% reduction)

---

## **Experiment 8: Stratified Sampling**
**Method:**
1. Process 10% random sample (150 chunks)
2. Validate accuracy manually
3. If >90% accurate → scale to all 1515
4. If <90% → refine prompt and retest

**Benefits:**
- Validates approach before full run
- Saves API calls if prompt needs refinement
- Can test multiple strategies cheaply

---

## **Experiment 9: Identity-Specific Optimization**
**Method:** Different strategies for different identities

- **Jewish/Quaker/Huguenot**: Regex (works well, 90%+)
- **Lebanese/African/Muslim**: LLM (regex only 0-30%)
- **Latino/Hispanic**: Regex (works well, 100%)

**Test on 50 chunks:**
- Regex handles 60% of identities: 0 API calls
- LLM handles remaining 40%: ~20 API calls
- Total: 20 API calls vs 50 (60% reduction)

---

## **Evaluation Metrics**

For each experiment, measure:

1. **Accuracy**: % of 47 known people found
2. **Precision**: False positives (noise)
3. **API Efficiency**: Calls needed for all 1515 chunks
4. **Days to Complete**: Given 200 RPD limit
5. **Maintainability**: How hard to update?
6. **Scalability**: Works when documents grow?

---

## **Recommended Testing Order**

1. **Experiment 8** (Sampling) - Test each approach on 50 chunks first
2. **Experiment 6** (Hybrid) - Likely best balance
3. **Experiment 3** (Small batch) - If hybrid doesn't work
4. **Experiment 7** (Two-stage) - If we need more efficiency

---

## **Success Criteria**

**Minimum acceptable:**
- Accuracy: >85% (40/47 people)
- False positives: <10%
- Completable in <3 days on free tier

**Ideal:**
- Accuracy: >95% (45/47 people)
- False positives: <5%
- Completable in <2 days

---

## **Next Steps**

1. Run Experiment 8 (sample 50 chunks)
2. Test multiple approaches
3. Compare results
4. Choose winner
5. Scale to full 1515 chunks


