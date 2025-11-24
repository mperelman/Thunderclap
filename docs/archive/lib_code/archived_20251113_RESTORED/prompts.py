"""
Centralized prompt templates for Thunderclap AI.
All narrative rules, frameworks, and instructions in ONE place.
"""
# Identity formatting functions removed - no longer needed

# Generate examples once (DRY principle)
identity_EXAMPLES = ""  # Removed
KINLINK_EXAMPLES = ""  # Removed

# ============================================================================
# CRITICAL RULES (TOP PRIORITY - NEVER VIOLATE)
# ============================================================================

CRITICAL_RELEVANCE_AND_ACCURACY = """
RULE #1: RELEVANCE ABOVE ALL (MOST CRITICAL - FILTER EVERYTHING)
- ONLY include information that DIRECTLY involves the query subject
- Do NOT include information just because it appears in the same document chunk
- Test for EVERY sentence: "Does this sentence involve the query subject?" If NO → DELETE IT

WHAT COUNTS AS "DIRECTLY INVOLVES":
✓ Historical context that explains the subject (e.g., "Parsees fled Persia in 7th century" when query is about Parsees)
✓ Partnerships/marriages/transactions involving the subject (e.g., "Jardine partnered with Parsee Cowasjee")
✓ Trading/commercial activities of the subject (not just banking - include trade, industry if docs mention)
✓ All major families that are part of the subject group (e.g., Tata, Wadia for Parsees)
✗ Standalone information about completely different entities that appeared in same chunks

SOCIOLOGICAL PATTERNS (caste, identitys, rabbinates):
- ONLY include when the query subject is directly part of that pattern
- For specific entity queries → Only include patterns the subject participated in
- For general pattern queries → Then discuss patterns across multiple entities

RULE #2: ACCURACY - NEVER FABRICATE
- ONLY state what documents EXPLICITLY say - no inferences, assumptions, or combinations
- Do NOT connect separate entities mentioned near each other unless document explicitly connects them
- If document says "X founded Y" then separately "Z founded W", keep them SEPARATE
- NEVER fabricate relationships between different people or institutions
- Do NOT mention panics/laws unless documents explicitly link them to the subject
- Better to be incomplete than inaccurate
"""

# ============================================================================
# THUNDERCLAP FRAMEWORK - SOCIOLOGY
# ============================================================================

# Build sociology framework dynamically with identity data
THUNDERCLAP_SOCIOLOGY_FRAMEWORK = f"""
SOCIOLOGICAL LENS - Identity Shapes Opportunities (MAINTAIN THROUGHOUT):

CRITICAL FRAMING - identityS AND MINORITY MIDDLEMEN:
- Banking dominated by identityS (small intermarried elite families), NOT entire populations
- Examples across identitys:
{identity_EXAMPLES}
- Name SPECIFIC families, NOT ethnic/religious groups as monoliths
- KINLINKS ACROSS identityS (FUNDAMENTAL): Most identitys kinlinked extensively outside their grouping
{KINLINK_EXAMPLES}
  * Sephardim later kinlinked with Ashkenazim
- MINORITY MIDDLEMEN: Show exclusion from land/politics/industry → channeled into finance
- KINLINKS: Explain marriages/kinship networks and what they enabled (within and across groups)
- CASTE: Consider caste within groups (e.g., Kohanim/Katz priestly lineage among Jews) if documents mention
- CONVERSIONS: How did conversions (forced/strategic/genuine) affect access if documents mention

CRITICAL: For questions about group influence/control in banking:
- ANSWER THE SPECIFIC QUESTION: Base on what documents say about that group, time, and place
- ANALYZE NARROWLY: If control existed, explain how narrowly defined (which families? what time/place?)
- PROVIDE CONTEXT: Compare with other groups in similar contexts
- EXPLAIN DYNAMICS: What factors shaped this (exclusion from other venues, legal access, networks)?
- Documents may show: Some groups/families dominated certain times/places - state this if true, with context

ANALYZE THROUGH MULTIPLE DIMENSIONS (based on what documents say):
- Religion/race/class: What group? What access/barriers?
- Sex/gender: Did being a woman change access? Widows? Daughters?
- Family: How did inheritance, marriage patterns shape opportunities?
- Law: What legal barriers or advantages? (e.g., women barred from exchanges, religious tests)
- Exclusion: What venues were closed? Where did this channel people?

CRITICAL: Maintain sociological analysis THROUGHOUT all time periods - don't abandon after opening paragraph.
"""

# ============================================================================
# THUNDERCLAP FRAMEWORK - PANICS
# ============================================================================

THUNDERCLAP_PANIC_FRAMEWORK = """
PANICS AS ORGANIZING FRAMEWORK (MAINTAIN THROUGHOUT):
- Cover EVERY Panic documents mention (1763, 1825, 1837, 1873, 1893, 1907, 1929, etc.)
- For each: What happened? How did identity shape outcome (if docs say so)?
- BAD: "Panic of 1825 occurred" then move on
- GOOD: "During Panic of 1825, [subject] [specific actions from docs]. [Identity analysis if docs support]"
- Don't invent connections - base on documents
"""

# ============================================================================
# THUNDERCLAP FRAMEWORK - NETWORKS & REGULATIONS
# ============================================================================

THUNDERCLAP_NETWORKS_REGULATIONS = """
NETWORKS (MAINTAIN THROUGHOUT):
- Show specific marriages/partnerships and what they enabled (based on docs)
- Don't just list - explain significance

REGULATIONS (WHEN RELEVANT):
- How did rules change access to opportunities?
- Connect to identity if documents support it
"""

# ============================================================================
# NAMING CONVENTIONS
# ============================================================================

NAMING_CONVENTIONS = """
NAMING CONVENTIONS (CRITICAL):
- Institutions: Use italics (*Hope*, *Lehman*, *Morgan*)
- People: Regular text (Henry Hope, Henry Lehman, J.P. Morgan)
- NEVER use "& Co." or "& Company" - causes incorporation/structure issues
- Be CONSISTENT: "WWI" and "WWII" (not "World War I" then "WWII")
- CLARIFY ambiguous names: "President Carter" not "Carter"
"""

# ============================================================================
# WRITING STYLE
# ============================================================================

WRITING_STYLE = """
WRITING STYLE: Mix Bernanke (analytical rigor, economic precision) + Maya Angelou (humanizing details, storytelling)
- Include events that humanize people (e.g., "fled to London with movable assets", "worked from home as widow", "daughter excluded from partnership")
- NO melodrama, but show people as human beings navigating constraints
- Balance factual analysis with moments that reveal individual experiences
"""

# ============================================================================
# OTHER RULES
# ============================================================================

NARRATIVE_STRUCTURE_RULES = """
NARRATIVE STRUCTURE:
1. RELEVANCE FILTER - STAY ON TOPIC:
   - Every sentence must be about the query subject or directly involve them
   - Do NOT include information about other entities just because they're in the same chunk
   - Ask yourself: "Does this sentence involve [query subject]?" If NO → DELETE IT

2. SUBJECT MUST BE ACTIVE IN EVERY SENTENCE:
   ✓ "*Lehman* merged with Goldman"
   ✗ "Goldman merged with *Lehman*"

3. CLEAR CHRONOLOGICAL ORGANIZATION (CRITICAL):
   - Organize STRICTLY by time periods (e.g., "1770s-1790s", "1800-1815", "1820s-1840s", "Post-1850")
   - Move forward in time - NEVER jump backwards
   - CRITICAL: Do NOT organize by topic if it breaks chronology (e.g., no "Factors" section after covering later centuries)
   - Within each period, group related events together (banking, panics, legal changes, networks)
   - Connect time periods with transitions
   - For EACH period, cover what documents mention
   - ONLY include panics/laws if documents explicitly link them to the subject
   - BAD: 1770s → 1920s → 1783 → 1798 (jumping backwards after 1920s)
   - BAD: Covering 1957 then adding a "Factors" section mentioning 1783
   - GOOD: 1770s-1790s → 1800-1815 → 1820s-1840s → 1850-1900 → 1900-1960 (flows forward)

4. CONNECT PARAGRAPHS - BUILD A NARRATIVE:
   - Each paragraph should flow into the next
   - Use transitions to show relationships between events
   - Don't just list disconnected facts
   - Show how earlier events shaped later ones
   - BAD: Isolated statements with no connections
   - GOOD: "This expansion laid the groundwork for...", "Building on these connections...", "During this period..."

5. SHORT, FOCUSED PARAGRAPHS:
   - Each paragraph = ONE CLEAR TOPIC (max 3-4 sentences)
   - NEVER mix unrelated topics in one paragraph
   - But ensure paragraphs connect to form a coherent whole

6. NO PLATITUDES OR FLOWERY LANGUAGE:
   ✗ "dynamic nature of the financial world"
   ✗ "testament to"
   ✗ "journey"
   ✗ "transformative era"
   ✗ "strategically positioned"

7. COMPREHENSIVE COVERAGE (CRITICAL):
   - Address the question fully - don't provide sparse, incomplete answers
   - Cover ALL time periods documents mention (e.g., if docs mention 7th century, 1815, 1840s, cover all three)
   - Do NOT skip time periods - if documents cover 1790s and 1991, you MUST cover 1800-1900 if present
   - Include periods of decline or transition - these are still important historical context
   - Cover ALL aspects documents discuss (banking, trading, industry, politics, panics, legal changes, networks, partnerships)
   - Include ALL major families/entities documents mention as part of the subject
   - Don't be overly restrictive in filtering - if documents discuss the subject in a context, include it
   - ONLY exclude information if it's about completely different, unconnected entities
   - Provide substantive, complete coverage - not just a narrow slice

8. END WITH RELATED QUESTIONS:
   - Provide 3-5 follow-up questions based on entities/topics mentioned in the documents you just read
   - Questions should explore topics that had enough content to generate a substantive narrative
   - Good question types: other families/entities mentioned, broader topics/themes, related places/periods
   - Bad question types: hyper-specific details that only had 1 sentence in the documents
   - Test: "Could I write multiple paragraphs answering this from the documents?" If yes → good question
"""

# ============================================================================
# BATCH PROMPT BUILDER
# ============================================================================

def build_batch_prompt(question: str, chunks: list, batch_context: str = "") -> str:
    """
    Build a prompt for processing a single batch of chunks.
    
    Args:
        question: User's question
        chunks: List of (chunk_text, metadata) tuples
        batch_context: Optional context about batch number
    
    Returns:
        Complete prompt string
    """
    # Prepare context from chunks
    context_parts = []
    for i, (chunk, metadata) in enumerate(chunks, 1):
        source = metadata.get('filename', 'Unknown')
        context_parts.append(f"[Source {i}: {source}]\n{chunk}\n")
    
    context = "\n---\n".join(context_parts)
    
    prompt = f"""Write a factual overview about {question} based ONLY on the provided documents.

Historical Documents:
{context}

{CRITICAL_RELEVANCE_AND_ACCURACY}

NARRATIVE RULES:

{NARRATIVE_STRUCTURE_RULES}

THUNDERCLAP FRAMEWORK (CRITICAL - VIEW HISTORY THROUGH THESE LENSES):

Thunderclap traces financial history through SOCIOLOGICAL and PANIC lenses. EVERY section/time period must maintain this analytical framework - don't abandon it after the opening:

{THUNDERCLAP_SOCIOLOGY_FRAMEWORK}

{THUNDERCLAP_PANIC_FRAMEWORK}

{THUNDERCLAP_NETWORKS_REGULATIONS}

{NAMING_CONVENTIONS}

{WRITING_STYLE}

CRITICAL: Address the question comprehensively using information explicitly stated in the documents above.
- Cover ALL time periods present in the documents (don't skip centuries)
- Include ALL major events/families/entities mentioned in the documents
- Don't provide sparse summaries - extract and present the substantive content from the documents{batch_context}

Answer:"""
    
    return prompt

# ============================================================================
# MERGE PROMPT BUILDER
# ============================================================================

def build_merge_prompt(question: str, narratives: list) -> str:
    """
    Build a prompt for merging multiple narrative sections.
    
    Args:
        question: User's original question
        narratives: List of narrative strings to merge
    
    Returns:
        Complete merge prompt string
    """
    sections_text = "\n".join([
        f"=== Section {i+1} ===\n{narrative}\n"
        for i, narrative in enumerate(narratives)
    ])
    
    prompt = f"""You have {len(narratives)} partial narratives about {question}. Merge them into ONE unified, coherent narrative.

SECTIONS TO MERGE:
{sections_text}

YOUR TASK: Create ONE complete narrative (not separate sections). Deduplicate information, organize chronologically by time period, and maintain analytical framework THROUGHOUT.

{CRITICAL_RELEVANCE_AND_ACCURACY}

CRITICAL: FILTER FOR RELEVANCE WHILE MERGING
- As you merge, REMOVE any information that doesn't directly involve the query subject
- If sections mention unrelated entities, SKIP those paragraphs entirely
- Test each paragraph: "Does this involve the query subject?" If NO → DELETE IT

CRITICAL MERGE INSTRUCTIONS:

1. ORGANIZE CHRONOLOGICALLY - BUILD A COHERENT NARRATIVE:
   - Do NOT keep as separate sections with headers like "Section 1", "Section 2"
   - Organize STRICTLY by time periods (e.g., "1770s-1790s", "1800-1815", "1820s-1840s", "Post-1850")
   - Move forward in time - NEVER jump backwards
   - CRITICAL: If you mention 1957, you CANNOT then mention 1783 - that's jumping backwards
   - Do NOT organize by topic if it breaks chronology (e.g., no "Factors" section that jumps back in time)
   - Within each period, group related events together (banking, panics, legal changes, networks)
   - Cover what documents mention for each period
   - ONLY include panics/laws if documents explicitly link them to the subject
   - Merge overlapping information (same events/people mentioned multiple times)
   - Connect paragraphs with transitions showing how events relate
   - Keep subject active in every sentence

2. BUILD CONNECTIONS - DON'T JUST LIST FACTS:
   - Show how earlier events shaped later ones
   - Use transitions: "Building on these connections...", "This expansion enabled...", "During this period..."
   - Don't write isolated statements with no flow
   - Create a narrative arc, not a disconnected list
   - Avoid repetition - don't mention the same fact twice in different sections

3. COMPREHENSIVE COVERAGE (CRITICAL):
   - Address the question fully with substantive detail
   - Cover ALL time periods mentioned in the sections (7th century, Mughal period, 1815, 1840s, 1850s, 1870s, 1900s, etc.)
   - Do NOT skip time periods - if sections cover 1790s and 1991, you MUST include 1800-1900 content if present
   - Include periods of decline or transition - these are important historical context
   - Cover ALL aspects mentioned (banking, trading, industry, partnerships, historical context)
   - Include ALL major families/entities mentioned as part of the subject
   - Don't be overly restrictive - if sections discuss the subject in a context, include it
   - Don't provide sparse, scattered statements - provide complete coverage

4. MAINTAIN THUNDERCLAP FRAMEWORK IN EVERY TIME PERIOD (CRITICAL):
   
   {THUNDERCLAP_SOCIOLOGY_FRAMEWORK}
   
   {THUNDERCLAP_PANIC_FRAMEWORK}
   
   {THUNDERCLAP_NETWORKS_REGULATIONS}

5. SHORT FOCUSED PARAGRAPHS THAT CONNECT:
   - ONE clear topic per paragraph (3-4 sentences max)
   - Never mix unrelated topics in one paragraph
   - But ensure paragraphs flow together into a coherent narrative

6. {NAMING_CONVENTIONS}

7. {WRITING_STYLE}
   
8. OTHER:
   - NO platitudes or flowery language
   - Consistent: "WWI"/"WWII" always
   - Clarify ambiguous names: "President Carter" not just "Carter"
   - End with "Related Questions:" (3-5 follow-ups)

9. RELATED QUESTIONS (CRITICAL - Make them useful):
   - Generate 3-5 questions based on entities/topics that appeared in the narrative sections
   - Questions should be about topics with enough content for a substantive narrative (multiple paragraphs)
   - Good question types: other families/entities mentioned, broader topics/themes, related places/periods
   - Bad question types: hyper-specific details that only had 1 sentence
   - Test each question: "Could I write multiple paragraphs from the documents?" If yes → include it

REMEMBER: The goal is ONE coherent narrative that maintains sociological + panic analysis THROUGHOUT all time periods, not just the opening.

CRITICAL FINAL CHECK:
- Did you cover ALL time periods mentioned in the sections? (If sections mention 1790s, 1829, 1847, 1862, 1894, ALL must appear)
- Did you skip any centuries? (e.g., jumping from 1790s to 1991 skips 1800-1990)
- Did you include ALL major families/entities from the sections?
- Is the narrative substantive and complete, not sparse?

Answer:"""
    
    return prompt

