# Identity Index Integration - Design Proposal

## Problem

Currently, the identity detector and search index are **disconnected**:

1. **Index Builder** (`lib/index_builder.py`): 
   - Extracts surnames, firms, words from documents
   - Creates `term_to_chunks` mapping
   - Saves to `data/indices.json`
   - **Does NOT use identity detector results**

2. **Identity Detector** (`lib/identity_detector.py`):
   - Finds which families have which identities (Black, Jewish, Quaker, etc.)
   - Saves to `data/detected_cousinhoods.json`
   - **Not integrated into search index**

3. **Search** (`lib/search_engine.py`):
   - Searches for "black bankers" 
   - Only finds chunks with word "black" explicitly
   - **Misses chunks about Parsons/McGuire/Lewis that don't mention race**

## Solution: Augment Index with Identity Metadata

After standard indexing, enhance the index by linking family surnames to their detected identities.

### Example

**Detector finds:** 
```json
{
  "black": {
    "families": ["parsons", "mcguire", "lewis", "raines", "brimmer", ...]
  }
}
```

**Index enhancement:**
```python
# For each chunk containing "parsons":
#   Add "black" to that chunk's searchable terms
# Result: Searching "black" now also finds chunks about Parsons
```

### Implementation

**Option 1: Augment at Index Build Time**

In `build_index.py`, after building standard indices:

```python
def augment_indices_with_identities(term_to_chunks, detected_identities):
    """
    Enhance term_to_chunks by adding identity terms to family chunks.
    
    Example:
        If "parsons" appears in chunk_123
        And detector says parsons is Black
        Then add chunk_123 to term_to_chunks["black"]
    """
    for identity, data in detected_identities.get('identities', {}).items():
        families = data.get('families', [])
        
        # For each family with this identity
        for family in families:
            family_lower = family.lower()
            
            # Find all chunks containing this family
            if family_lower in term_to_chunks:
                family_chunks = term_to_chunks[family_lower]
                
                # Add these chunks to the identity term
                if identity not in term_to_chunks:
                    term_to_chunks[identity] = []
                
                # Add chunks (avoid duplicates)
                existing = set(term_to_chunks[identity])
                for chunk_id in family_chunks:
                    if chunk_id not in existing:
                        term_to_chunks[identity].append(chunk_id)
    
    return term_to_chunks
```

**Option 2: Augment at Search Time**

In `lib/search_engine.py`, when searching for identity terms:

```python
def search_with_identity_expansion(self, query):
    """Expand identity queries to include known family surnames."""
    # Load detected identities
    identities = load_detected_cousinhoods()
    
    # If query contains identity term, add family surnames
    expanded_queries = [query]
    for identity in ['black', 'jewish', 'quaker', ...]:
        if identity in query.lower():
            families = identities['identities'][identity]['families']
            expanded_queries.extend(families)
    
    # Search for all expanded queries
    ...
```

## Recommendation

**Use Option 1** (augment at build time):

### Pros
- ✅ No search-time overhead
- ✅ Works with existing search engine
- ✅ Transparent to users
- ✅ Identities cached in index file

### Cons
- ❌ Requires rebuilding index when detector improves
- ❌ Slightly larger index file

### Workflow

```bash
# Build index WITH identity metadata
python build_index.py

# This should:
# 1. Build standard indices (existing)
# 2. Run identity detector (new)
# 3. Augment indices with identity metadata (new)
# 4. Save enhanced indices (existing)
```

## Benefits

1. **Better Recall**: Searching "black bankers" finds:
   - Chunks explicitly mentioning "Black" ✓ (current)
   - Chunks about Parsons/McGuire/Lewis ✓ (NEW!)

2. **Works for ALL Identities**: 
   - "jewish bankers" → Rothschild, Warburg, Lazard
   - "quaker bankers" → Barclay, Lloyd
   - "women bankers" → Detected female names

3. **Maintains Accuracy**:
   - Only links families detected by precise regex patterns
   - No false positives from proximity matching

## Implementation Checklist

- [ ] Add `augment_indices_with_identities()` to `lib/index_builder.py`
- [ ] Modify `build_index.py` to:
  - [ ] Run identity detector after indexing
  - [ ] Call augment function
  - [ ] Save enhanced indices
- [ ] Add `--skip-identity-augmentation` flag for speed (optional)
- [ ] Update README to explain identity-enhanced search
- [ ] Test: Search "black bankers" should find Parsons chunks

