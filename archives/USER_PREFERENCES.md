# Thunderclap AI - User Preferences & Requirements
**Last Updated:** 2025-12-03
**Archive Session:** session_2025-12-03_0226

---

## Core Philosophy

### NO HARDCODED HEURISTICS
- **CRITICAL:** All filtering, classification, and processing MUST use LLM or document-based rules
- NO hardcoded lists of generic words, places, or names
- Exception: Technical constants (file paths, regex patterns for structure) are acceptable
- LLM filtering script: `scripts/filter_terms_with_llm_v2.py`

### API Key Management
- Centralized in `lib/llm_config.py`
- Current model: `gemini-2.5-flash`
- User does not want to enable billing (free tier only)
- Must handle rate limits gracefully with progress bars

---

## Indexing Preferences

### What TO Index

#### 1. **Surnames from Proper Names**
- Extract from multi-word proper names (e.g., "John Smith" → index "Smith")
- BUT: Exclude generic words (bank, trust, co, york, etc.) even if they appear as surnames

#### 2. **Firm Names (Italicized)**
- Pattern: `<italic>FirmName</italic>`
- Multi-word firms: "Morgan Grenfell", "Deutsche Bank"
- Single-word firms: "Morgan", "Lazard", "Paribas"
- BUT: NOT generic words like "Bank", "Trust", "Company" alone

#### 3. **Firm Abbreviation Patterns**
- `<italic>Park</italic> NB` → "Park NB" and "Park National Bank"
- `<italic>Morgan</italic> IHC` → "Morgan IHC"
- `<italic>Commonwealth</italic> PU` → "Commonwealth PU"
- Abbreviations: NB, IHC, PU, SB, HC, TC

#### 4. **Acronyms (3+ characters, all caps)**
- Examples: "SEC", "FRS", "BANK" (World Bank), "NYSE"
- Create patterns for exact token matching: `\bSEC\b`
- Index both uppercase and lowercase variants

#### 5. **Acronym + Location Patterns**
- Pattern: `ACRONYM Location` where location is a valid city/region
- Examples: "FRS New York", "SEC Chicago", "FRS Boston"
- Valid locations: Federal Reserve cities, major financial centers
- **CRITICAL:** This ensures "FRS New York" hyperlinks as one entity, not "FRS" + "New York"

#### 6. **Law Codes with Years**
- Pattern: `(BA|TA|SA|FA|IA|AA|PA|DA|CA|EA|LA)YYYY`
- Examples: "TA1813" → "Treasury Tax Act 1813", "BA1933" → "Banking Act 1933"

#### 7. **Panic Terms**
- Via `lib/panic_indexer.py`
- Pattern: "Panic of YYYY" where YYYY is a 4-digit year
- Examples: "Panic of 1763", "Panic of 1929"

#### 8. **Identity Terms**
- Religious: Jewish, Sephardi, Quaker, Muslim, etc.
- Ethnic: Armenian, Greek, Lebanese, Basque, Hausa, etc.
- Racial: Black, African American
- Gender: female, woman, widow, queen, princess
- Latino/Hispanic: Latino, Hispanic, Mexican, Cuban

#### 9. **Multi-Word Phrases**
- Firm+location: "Rothschild Paris", "Morgan London"
- Full firm names: "First National Bank of Boston"
- Full names: "James Hill", "David David" (if explicitly indexed)

### What NOT to Index

#### **Generic Words (Even if Capitalized)**
- Financial: bank, trust, company, co, corp, capital, credit, finance
- Titles: president, director, governor, chairman, officer, manager
- Family: son, daughter, father, mother, brother, sister, widow
- Places (too generic): York, London, Paris, New York (standalone)
- Descriptors: financial, assets, policy, national, federal, public
- Time: war, wars, century, decade, year, early, late, modern
- Directions: north, south, east, west, central, western, eastern

#### **Special Cases**
- "Bank" standalone: NO (unless part of "Deutsche Bank", "Rothschild Bank", etc.)
- "Morgan" standalone: YES (it's the firm `<italic>Morgan</italic>`, not a person)
- "New York" standalone: NO (too generic)
- "FRS New York": YES (specific entity: Federal Reserve Bank of New York)

---

## Indexing Technical Details

### Capitalization
- **PRESERVE original capitalization** in the index
- Do NOT lowercase everything
- This distinguishes: "BANK" (World Bank) vs "Bank" (proper noun) vs "bank" (generic)
- Implementation: `canonicalize_term()` only removes possessives, not case

### Deduplication
- **CRITICAL:** Remove duplicate chunk IDs before saving
- Issue: Terms appearing multiple times in same chunk were added multiple times
- Example: "Morgan" appeared 3 times in chunk_123 → added chunk_123 three times
- Fix: `save_indices()` deduplicates using `dict.fromkeys(chunks)`

### Term Counts
- Track how many times each term appears across all chunks
- Used for importance/relevance weighting

---

## Hyperlinking Preferences

### Frontend Hyperlinking Rules

#### **Query Subject Exclusion**
- NEVER hyperlink the query subject in its own answer
- Example: Query "Tell me about War Finance Corporation" → DON'T hyperlink "WFC" or "War Finance Corporation"
- Must handle both full names AND acronyms
- Implementation: Extract acronym from multi-word subjects (e.g., "WFC" from "War Finance Corporation")

#### **Longest Match Preference**
- If both "Morgan" and "Morgan Grenfell" are indexed, prefer "Morgan Grenfell"
- If both "Exchange Bank" and "Corn Exchange Bank" are indexed, prefer "Corn Exchange Bank"
- Implementation:
  1. Sort terms by length (longest first)
  2. Find all matches
  3. Remove overlapping matches (keep longest/earliest)
  4. Replace from end to start (so indices don't shift)

#### **Only Hyperlink Meaningful Entities**
- Multi-word terms (e.g., "Bank of Montreal", "Morgan Grenfell")
- Acronyms 3+ chars (e.g., "SEC", "FRS", "WFC")
- Terms with numbers/special chars (e.g., "BA1933", "TA1813")
- "Panic of YYYY" patterns
- NOT: Single generic words, titles, common places

#### **Exclusions**
- Very short terms (≤2 chars): "co", "nb", "of", "in", "to"
- Common short words even if acronyms: "co", "era", "inc", "ltd", "corp"
- Query subject and its acronym

---

## Query Engine Preferences

### Variant Matching
- **CRITICAL:** Match ALL case/plural/singular variants automatically
- Query "Hispanics" → find "Hispanic", "hispanic", "Hispanics", "hispanics"
- Query "Bank" → find "Bank", "bank", "BANK"
- Implementation: For each keyword, check:
  1. Exact match
  2. Lowercase variant
  3. Capitalized variant (Title case)
  4. Plural variant (add/remove 's')
  5. All combinations

### Identity Query Handling
- Detect "Tell me about [identity]" patterns
- Apply special limits to avoid token quota issues
- Examples: "Tell me about Black", "Tell me about women", "Tell me about Hispanics"
- Limit: BROAD_IDENTITY_EARLY_CHUNK_LIMIT = 50 chunks

### Control/Influence Query Handling
- Detect "How did [identity] control/influence/dominate [sector]"
- Apply very strict limits: CONTROL_INFLUENCE_EARLY_CHUNK_LIMIT = 8 chunks
- These are extremely broad and would otherwise timeout

---

## Narrative Generation Preferences

### CRITICAL RULES

#### **1. RELEVANCE ABOVE ALL (TOP PRIORITY)**
- ONLY include information that DIRECTLY involves the query subject
- Do NOT include unrelated entities just because they're in the same document chunk
- Test EVERY sentence: "Does this involve [query subject]?" If NO → DELETE IT
- Example ERROR: Document mentions Lever and African Association → LLM writes "Lever formed African Association" (WRONG if they were separate/competitors)

#### **2. ACCURACY - NEVER FABRICATE (SECOND PRIORITY)**
- ONLY state what documents EXPLICITLY say
- NO inferences, assumptions, or combinations
- Do NOT connect separate entities unless document explicitly connects them
- Better to be incomplete than inaccurate

#### **3. Subject Must Be Active in EVERY Sentence**
- ✓ "Lehman merged with Goldman"
- ✗ "Goldman fused with Lehman"
- ✓ "Lehman partnered with Li Ming and Lazard"
- ✗ "Li Ming partnered with Lehman"

#### **4. No Platitudes or Flowery Language**
- ✗ "dynamic nature of the financial world"
- ✗ "testament to", "journey", "transformative era", "strategically positioned"

### Thunderclap Framework

#### **SOCIOLOGY + PANIC Lenses (IN EVERY SECTION)**
- View history through sociological and panic lenses throughout
- NOT just in opening, but in EVERY time period

#### **Sociology:**
- **COUSINHOODS:** Banking dominated by small intermarried elite families
  - Name SPECIFIC families, NOT ethnic/religious groups as monoliths
  - Examples: Jewish (Mendes, Sassoon, DelBanco, Rothschild, Warburg), Quaker (Barclay, Lloyd, Bevan), Huguenot (Hope, Mallet, Thellusson)
- **KINLINKS ACROSS COUSINHOODS:** Most cousinhoods intermarried extensively
  - Examples: Schroder/Baring kinlinked with London cousinhood; Oppenheim (Jewish) kinlinked with Protestant Cologne
- **MINORITY MIDDLEMEN:** Show exclusion from land/politics/industry → channeled into finance
- **CASTE:** Consider caste within groups (e.g., Kohanim/Katz priestly lineage)
- **CONVERSIONS:** How conversions affected access
- **SEX/GENDER:** Did being a woman change access? Widows?
- **FAMILY:** How did family structures shape opportunities?
- **LAW:** What legal barriers or advantages existed?

#### **PANICS AS FRAMEWORK:**
- Cover ALL Panics in ALL time periods (not just opening)
- For each: What happened? How did identity shape outcome?
- Examples: 1763, 1873, 1893, 1907, 1929, etc.

### Organization & Style

#### **Chronological Organization (CRITICAL)**
- Organize STRICTLY by time periods (e.g., "1770s-1790s", "1800-1815", "1820s-1840s")
- Move forward in time - NEVER jump backwards
- Do NOT organize by topic if it breaks chronology
- Cover ALL time periods documents mention - do NOT skip
- Include periods of decline/transition

#### **Comprehensive Coverage**
- Cover ALL aspects documents discuss (banking, trading, industry, partnerships)
- Include ALL major families as part of the subject
- Provide substantive, complete coverage - not just a narrow slice

#### **Writing Style: Bernanke + Maya Angelou**
- Mix analytical rigor (Bernanke) with humanizing details (Maya Angelou)
- Short paragraphs (3-4 sentences max) that flow together
- NO melodrama, but show people as human beings

#### **Naming Conventions**
- **Institutions:** Use italics (*Hope*, *Lehman*, *Morgan*)
- **People:** Regular text (Henry Hope, Henry Lehman, J.P. Morgan)
- NEVER use "& Co." or "& Company" (causes incorporation/structure issues)
- Be CONSISTENT: "WWI" and "WWII" (not "World War I" then "WWII")
- CLARIFY ambiguous names: "President Carter" not "Carter"

### Related Questions
- Provide 3-5 follow-up questions at end
- Questions should be about topics with enough content for multiple paragraphs
- Include time periods or specific aspects to avoid token limit issues
- Good: "What was Bank of Montreal's role in financing Canadian railway development in the 1880s-1890s?"
- Bad: "Tell me about Bank of Montreal" (too broad)

---

## File Organization

### Keep These Directories
- `lib/` - Core library code
- `scripts/` - Utility scripts (indexing, filtering, etc.)
- `data/` - Index files, chunks, vectordb (.gitignored except indices.json)
- `archives/` - Session archives, documentation
- `.github/` - CI/CD workflows

### Clean Up These
- `temp/` - ALL temporary test files
- Root directory test files: `test_*.py`, `*_results.txt`
- Outdated documentation in temp/
- Old session archives without clear dates

### .gitignore Rules
- `data/` (except `data/indices.json` and `data/filtered_terms.json`)
- `temp/`
- `__pycache__/`
- `.env`
- `*.pyc`
- Editor configs (`.vscode/`, `.idea/`)

---

## Progress Indicators

### CRITICAL: Always Show Progress
- User demands progress bars for ANY long-running process (>30 seconds)
- Use `tqdm` for Python scripts
- Show: current item, total items, percentage, ETA
- Update frequency: Every batch or every 5 items
- Examples:
  - Index building: `Indexing: 95%|#########5| 1950/2044 [05:46<00:16, 5.92it/s]`
  - LLM filtering: `Batch 25/49 (51%)` (update every 5 batches)

---

## API & Rate Limiting

### LLM API Configuration
- **File:** `lib/llm_config.py`
- **Model:** `gemini-2.5-flash`
- **Free Tier Limits:**
  - 15 requests/minute (RPM)
  - 250 requests/day
- **Handling:**
  - Wait 5 seconds between batches (12 requests/minute, safe margin)
  - Implement exponential backoff for rate limit errors
  - Provide clear error messages when quota exceeded
  - Create new client for each batch (workaround for key invalidation)

### Batch Sizes
- **LLM Filtering:** 250 terms per batch (prevents output token limit)
- **Query Processing:** Varies by query type (control/influence: 8, broad identity: 50)

---

## Testing & Deployment

### Git Workflow
- NEVER skip hooks (--no-verify)
- NEVER force push to main
- NEVER commit unless user explicitly asks
- Always check git status before committing

### Railway Deployment
- Backend deploys automatically via GitHub integration
- Manual deploy if needed: `railway up` or dashboard
- Wait 1-2 minutes after push for deployment

### GitHub Pages (Frontend)
- Frontend at: `index.html`
- Caching: User must hard refresh (Ctrl+Shift+R) after updates
- Build ID tracking: Update `BUILD_ID` constant to force cache refresh

---

## Known Issues & Workarounds

### API Quota Exhaustion
- **Issue:** Free tier limited to 250 requests/day
- **Workaround:** Wait 24 hours for reset OR use new API key
- **Not Acceptable:** Heuristic filtering (user wants LLM only)

### ChromaDB UUID Caching
- **Issue:** ChromaDB caches collection UUIDs internally
- **Fix:** Always get fresh collection reference: `client.get_collection(name=COLLECTION_NAME)`

### Windows Line Endings
- **Issue:** Git warns "LF will be replaced by CRLF"
- **Non-Issue:** Cosmetic warning, doesn't affect functionality

---

## Quality Standards

### Code Quality
- Modular: Single responsibility per function/class
- No duplication: Extract common code to utilities
- Clear naming: Descriptive variable/function names
- Comments: Explain WHY, not WHAT
- Type hints: Use where beneficial (not everywhere)

### Documentation
- README for setup/usage
- Docstrings for public functions
- Inline comments for complex logic
- This preferences document for future reference

### Error Handling
- Graceful degradation (don't crash on bad input)
- Clear error messages to user
- Log errors for debugging
- Retry logic for transient failures (API rate limits)

---

## Contact & Support
- Repository: https://github.com/mperelman/Thunderclap
- Railway Backend: [auto-deployed]
- Frontend: GitHub Pages

---

**END OF PREFERENCES DOCUMENT**

