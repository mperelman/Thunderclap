# Chunk Size History

## Original Configuration (Archived)

### From `docs/archive/ARCHITECTURE.md` (line 103):
```python
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
```

### From `docs/archive/sessions/ARCHITECTURE_REVIEW.md` (line 66):
```python
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
```

### From `docs/archive/PREFERENCES_SUMMARY.md` (line 155):
- **Database**: 1,509 chunks (500-word chunks, 100-word overlap)

### From `docs/archive/sessions/CODEBASE_REVIEW.md` (line 21):
```python
# Old chunking code:
for i in range(0, len(words), 500):
    chunk = ' '.join(words[i:i+500])
```

---

## Current Configuration

### From `lib/config.py` (line 22):
```python
CHUNK_SIZE = 1000  # words
CHUNK_OVERLAP = 200  # words
```

---

## Change Summary

**Original:** 500 words per chunk, 100-word overlap  
**Current:** 1000 words per chunk, 200-word overlap  

**Change:** Chunks were **DOUBLED** from 500 to 1000 words

---

## Impact

1. **Database was built with 1000-word chunks**
   - Changing config won't affect existing chunks
   - Need to rebuild index to use smaller chunks

2. **Current database has ~761 chunks** (from query output)
   - If originally 1,509 chunks at 500 words
   - Doubling to 1000 words would halve the count
   - Makes sense: ~1,509 → ~755 chunks

3. **Why the change?**
   - Larger chunks = fewer chunks total
   - Fewer API calls needed
   - More context per chunk
   - But: Less granular retrieval

---

## To Revert to 500-Word Chunks

1. Change `lib/config.py`:
   ```python
   CHUNK_SIZE = 500
   CHUNK_OVERLAP = 100
   ```

2. Rebuild index:
   ```bash
   python build_index.py
   ```

3. Update `ESTIMATED_WORDS_PER_CHUNK` in config:
   ```python
   ESTIMATED_WORDS_PER_CHUNK = 500  # Match CHUNK_SIZE
   ```

---

**Conclusion:** Chunks were **increased** from 500 to 1000 words, not decreased. The database reflects this change.

