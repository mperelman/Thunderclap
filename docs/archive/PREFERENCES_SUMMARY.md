# User Preferences - Quick Reference

## 0. ACCURACY ABOVE ALL ELSE (NEVER VIOLATE)

**LLMs can fabricate connections - you MUST prevent this:**

- ONLY state what documents EXPLICITLY say - no inferences or assumptions
- Do NOT connect separate entities mentioned near each other unless document explicitly connects them
- If document says "X founded Y" and separately "Z founded W", keep them SEPARATE - do NOT write "X and Z formed their companies"
- NEVER fabricate relationships between different people or institutions
- Better to be incomplete than inaccurate

**Example of GRAVE ERROR:**
- Document: "William Lever founded Lever in 1885. By 1889 nine traders merged to form African Association."
- LLM ERROR: "William Lever formed his African Association" (COMPLETELY FALSE - they were separate entities!)
- CORRECT: State them separately - Lever founded his company, nine traders (not including Lever) formed African Association

---

## MOST CRITICAL: Thunderclap Framework Must Be Maintained THROUGHOUT

**Common Error**: Mentioning identity and panics in the opening, then dropping the framework in later sections.

**Correct**: Apply sociological + panic analysis in EVERY time period section.

---

## 1. Naming Conventions (CRITICAL)

- **Institutions**: Use italics → *Hope*, *Lehman*, *Morgan*, *Baring*
- **People**: Regular text → Henry Hope, Henry Lehman, J.P. Morgan
- **NEVER** use "& Co." or "& Company" (causes incorporation/structure issues)
- Be consistent: "WWI"/"WWII" always (not "World War I" then "WWII")
- Clarify ambiguous names: "President Carter" not just "Carter"

---

## 2. Thunderclap Framework (Maintain in EVERY Section)

### SOCIOLOGY - In EVERY Time Period:

**COUSINHOODS AND MINORITY MIDDLEMEN (Critical Framing):**
- Banking dominated by **COUSINHOODS** (small intermarried elite families), NOT entire populations
- Examples across groups:
  * Jewish: *Rothschild*, *Warburg*, *Kuhn Loeb*, *Seligman*, *Lazard*
  * Quaker: *Barclay*, *Lloyd*, *Bevan*, *Tritton*
  * Huguenot: *Hope*, *Mallet*, *Thellusson*
  * Boston Brahmins (Gentile US): Cabot, Lowell, Forbes
  * Protestant Cologne cousinhood: Oppenheim, Stein, Schaaffhausen
  * Parsees (India): Tata, Wadia, Petit
  * Armenians (Ottoman): Balian, Dadian, Gulbenkian
- Name SPECIFIC families, NOT ethnic/religious groups as monoliths
- **MINORITY MIDDLEMEN** pattern: excluded from land/politics/industry → channeled into finance
- Show **KINLINKS** (kinship networks), explain **EXCLUSION** from other venues
- Consider **CASTE** within groups (e.g., Kohanim/Katz priestly lineage among Jews)
- Consider **CONVERSIONS** and how they affected access

**Multi-Dimensional Analysis:**
- Analyze through MULTIPLE dimensions: religion/race/class, sex/gender, family structure, law
- State identity explicitly (Jewish, Quaker, Protestant, Black, women, widows, etc.)
- ANALYZE (not just mention) how these dimensions shaped opportunities/barriers for that era
- **Sex/Gender**: Did being a woman change access? Did widows operate differently? Were daughters excluded?
- **Family**: How did family structures (inheritance, primogeniture, marriage patterns) shape opportunities?
- **Law**: What legal barriers or advantages existed? (women barred from exchanges, religious tests for office)
- Base analysis on what DOCUMENTS say - don't invent theories
- BAD: "Hope was Huguenot" in opening → then pure chronology later
- GOOD: Opening mentions Huguenot → Each section shows how it mattered in that era

### PANICS - Cover ALL Documents Mention:
- Structure around ALL Panics: 1763, 1825, 1837, 1873, 1893, 1907, 1929, etc.
- For EACH Panic: What happened? How did identity shape outcome (if docs say)?
- BAD: Mention Panic of 1763 in opening → ignore 1825, 1873, 1907 in later sections
- GOOD: Cover each Panic when chronologically relevant, connect to identity if docs do

### NETWORKS - In Each Era:
- Show marriages/connections documents mention in each time period
- Explain significance based on what documents say these enabled
- Don't just list - analyze what they meant for access/exclusion

### REGULATIONS - When Relevant:
- How did regulations change who could access opportunities?
- Connect to identity when documents do

---

## 3. Writing Style: Bernanke + Maya Angelou

- **Mix analytical rigor (Bernanke) with humanizing details (Maya Angelou)**
- Include events/details that humanize people:
  - ✓ "Henry Hope fled to London with movable assets in 1794"
  - ✓ "As a widow barred from the exchange, Johanna Borski worked from home"
  - ✓ "The daughter was excluded from the partnership despite her father's role"
- **NO melodrama**, but show people as human beings navigating real constraints
- Balance factual economic analysis with moments that reveal individual experiences
- Show people making decisions, facing barriers, adapting to circumstances

---

## 4. Subject Must Be Active (Every Sentence)

- ✓ "*Lehman* merged with Goldman in 1906"
- ✗ "Goldman fused with *Lehman*"
- ✓ "*Lehman* partnered with Li Ming and *Lazard*"
- ✗ "Li Ming partnered with *Lehman*"

---

## 4. Only Include Directly Relevant Information

- If mentioning another entity/event, explain its connection to subject
- Don't include tangential facts just because they're in a chunk
- Example: "SA40 forced Atlas to split" is irrelevant unless you explain Lehman's role

---

## 5. NO Platitudes or Flowery Language

Never use:
- "dynamic nature of the financial world"
- "testament to"
- "journey"
- "transformative era"
- "strategically positioned"

---

## 6. Short, Focused Paragraphs

- ONE clear topic per paragraph (max 3-4 sentences)
- NEVER mix unrelated topics (banking + government work)
- NEVER span decades in one paragraph
- BAD: "Founded in 1930s. After WWII expanded. By 1960s opened European offices."
- GOOD: Three separate paragraphs for founding, post-WWII expansion, and 1960s Europe

---

## 7. High-Level Narrative Organization

- Organize by time periods with clear headings
- Focus on key events and transitions
- Don't list every marriage unless directly relevant
- Show cause and effect

---

## 8. End with Related Questions

- 3-5 specific follow-up questions
- Focus on details that explore what was mentioned in the narrative

---

## System Info

- **Database**: 1,509 chunks (500-word chunks, 100-word overlap)
- **Terms**: 23,504 indexed (names, places, events, identities)
- **Term Grouping**: jew/jews/jewish, quaker/quakers, muslim/islam return same results
- **Processing**: Takes ALL chunks from index, batches 20-30 chunks with 6-sec pauses
- **API**: Gemini 2.0 Flash (15 RPM, 50 RPD for exp model)

---

## Where Preferences Are Embedded

1. **`lib/llm.py`** (lines 112-146) - Main narrative generation prompt
2. **`lib/query_engine.py`** (lines 253-291) - Batch combination prompt
3. **`.cursorrules`** - AI assistant instructions
4. **`README.md`** - User documentation
5. **`THUNDERCLAP_FRAMEWORK.md`** - Technical details and examples

---

## API Key

```powershell
$env:GEMINI_API_KEY='AIzaSyBlqE1F2G_L5l2Lg81gyt0UWcME_K3inFo'
```

---

**Remember**: The framework must be maintained THROUGHOUT all sections, not just mentioned in the opening!

