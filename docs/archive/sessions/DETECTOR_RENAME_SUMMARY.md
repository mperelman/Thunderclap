# Cousinhood Detector → Identity Detector Rename

## Summary

Renamed the "cousinhood detector" to "identity detector" to accurately reflect what it does: detecting broad **identity/attribute** categories (religion, ethnicity, gender, race), NOT actual cousinhoods (small intermarried elite families).

## Key Distinction

- **Cousinhood**: Small intermarried families (actual cousins/in-laws through repeated kinlinks)
  - Example: Rothschild-Warburg cousinhood (kinlinked through marriages)
  
- **Identity/Attribute**: Broad demographic categories that apply to all members
  - Example: All Jewish bankers, all women bankers, all Quakers

The detector finds **identities/attributes**, NOT cousinhoods.

## Changes Made

### 1. Renamed Files
- `lib/cousinhood_detector.py` → `lib/identity_detector.py`
- Class: `CousinoodDetector` → `IdentityDetector`
- Function: `detect_cousinhoods_from_index()` → `detect_identities_from_index()`
- Output: `detected_identities.json` (new file created)

### 2. Expanded Attributes Detected

**Added gender/racial attributes:**
- `female`, `woman`, `women` → normalized to `female`
- `widow`, `widows` → widow bankers
- `black`, `blacks` → Black bankers
- `african`, `african american`, `african-american` → normalized to `african_american`

**Existing religious/ethnic attributes:**
- Jewish (Sephardi, Ashkenazi, Court Jew)
- Christian (Quaker, Huguenot, Mennonite, Calvinist, Presbyterian, Puritan, Boston Brahmin)
- Hindu, Parsee, Armenian, Greek
- Overseas Chinese, Korean Chaebol, Japanese Zaibatsu

### 3. Updated References

**Files updated:**
- `lib/cousinhoods.py` - updated docstring and function comments
- `analyze_attributes.py` - updated import
- `docs/THUNDERCLAP_GUIDE.md` - updated terminology and explanations
- `docs/IDENTITY_DETECTOR.md` - NEW comprehensive documentation

### 4. Terminology Throughout

- "Cousinhood detection" → "Identity/attribute detection"
- "Detected cousinhoods" → "Detected identities/attributes"
- Results dict key: `'cousinhoods'` → `'identities'`

### 5. Maintained Backward Compatibility

- `lib/cousinhoods.py` still loads from `detected_cousinhoods.json` (legacy filename)
- Added note in docstring about filename for backward compatibility
- Data structures remain compatible

## Example Output (NEW)

```
WIDOW (new york, london, boston):
  gomperz              (4 mentions)
  adolphe              (4 mentions)
  morgan               (4 mentions)
  isaac                (3 mentions)

FEMALE (london, paris, boston):
  [women bankers found]

AFRICAN_AMERICAN (new york, boston):
  [Black bankers found]
```

## How to Use

### Run the detector:
```bash
python lib/identity_detector.py
```

### Analyze multi-attribute families:
```bash
python analyze_attributes.py
```

### Integration:
`lib/cousinhoods.py` automatically merges hardcoded + detected identities.

## What Changed in Detection

**No functional changes to detection logic:**
- Same precise regex patterns
- Same Boston Brahmin / Hindu Brahmin disambiguation
- Same multi-attribute support
- Same noise filtering

**Only additions:**
- Added gender/racial identity terms to search list
- Expanded normalization mappings
- Better documentation

## Files Modified

1. **Created:**
   - `lib/identity_detector.py` (new file)
   - `docs/IDENTITY_DETECTOR.md` (new documentation)

2. **Updated:**
   - `lib/cousinhoods.py` (docstrings, comments)
   - `analyze_attributes.py` (import statement)
   - `docs/THUNDERCLAP_GUIDE.md` (terminology, examples)

3. **Deleted:**
   - `lib/cousinhood_detector.py` (replaced by identity_detector.py)

## Benefits

1. **Accurate terminology**: Name now reflects what it actually does
2. **Expanded scope**: Now detects gender/racial attributes, not just religion/ethnicity
3. **Clearer distinction**: Users understand this is NOT detecting actual cousinhoods (kinship networks)
4. **Better foundation**: Prepare for future kinship network analysis (true cousinhood detection)

## Future Work

To detect **actual cousinhoods** (kinship networks):
1. Extract marriage/kinlink statements more robustly
2. Build family relationship graphs
3. Cluster by kinship density
4. Identify cousinhood boundaries (where kinlinks cluster vs. sparse)

This would be a separate **kinship network analyzer**, distinct from the identity detector.

