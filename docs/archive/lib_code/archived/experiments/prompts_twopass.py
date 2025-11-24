"""
Two-Pass Narrative Generation
==============================
Pass 1: Extract structured data from chunks
Pass 2: Synthesize into coherent narrative with full Thunderclap framework
"""

from .prompts import CRITICAL_RELEVANCE_AND_ACCURACY, THUNDERCLAP_SOCIOLOGY_FRAMEWORK, THUNDERCLAP_PANIC_FRAMEWORK

# ============================================================================
# PASS 1: EXTRACTION PROMPT
# ============================================================================

def build_extraction_prompt(question: str, chunks: list) -> str:
    """
    Pass 1: Extract structured data from chunks.
    Returns JSON with people, dates, events, identities, etc.
    """
    chunks_text = "\n\n".join([
        f"--- CHUNK {i+1} ---\n{text}"
        for i, (text, meta) in enumerate(chunks)
    ])
    
    return f"""You are extracting structured information from historical banking documents.

QUERY: {question}

YOUR TASK: For EACH chunk, extract ANY relevant content (broad interpretation):

Extract WHATEVER IS PRESENT (not all fields required):
1. TIME_PERIOD: Specific years/decades (e.g., "1780-1790", "1850s", "18th century")
2. CONTENT_TYPE: What this chunk provides ("person_biography", "legal_context", "crisis_background", "institutional_info", "general_context")
3. SUMMARY: 1-2 sentence summary of what this chunk says about the query subject
4. PEOPLE: Specific individuals mentioned (if any)
5. INSTITUTIONS: Organizations mentioned (if any)
6. EVENTS: Specific actions/transactions (if any)
7. IDENTITIES: Attributes mentioned (if any)
8. LOCATIONS: Places mentioned (if any)

EXTRACTION PHILOSOPHY - BE PERMISSIVE:
- Extract if chunk has ANY relevance to query (even tangential)
- Context chunks are VALUABLE (legal restrictions, economic conditions, historical background)
- Not every chunk needs people/events - general information counts!
- For "jewish bankers" query, include:
  ✓ Specific Jewish banker activities
  ✓ General conditions affecting Jewish bankers
  ✓ Legal/regulatory context
  ✓ Financial crises they experienced
  ✓ Institutional/geographic context
- When in doubt, EXTRACT - Pass 2 will filter during synthesis

DOCUMENT CHUNKS:
{chunks_text}

RESPOND WITH JSON (one object per chunk, include ONLY fields that are present):
{{
  "chunk_1": {{
    "relevant": true,
    "time_period": "1780-1790",
    "content_type": "person_biography",
    "summary": "Rothschild funded Austrian campaigns with Oppenheim cousin",
    "people": ["Rothschild (Mayer)", "Oppenheim (Nehm)"],
    "events": ["funded Austrian campaigns against France"],
    "identities": ["Jewish", "Court Jew"],
    "locations": ["Frankfurt", "Vienna"]
  }},
  "chunk_2": {{
    "relevant": true,
    "time_period": "1787-1791",
    "content_type": "legal_context",
    "summary": "France eased guild restrictions on Jews, extended citizenship to Sephardi then Ashkenazi",
    "locations": ["France", "Alsace", "Lorraine"]
  }},
  "chunk_3": {{
    "relevant": true,
    "time_period": "1789",
    "content_type": "crisis_background",
    "summary": "French Revolution created political instability affecting banking",
    "events": ["French Revolution began"],
    "locations": ["France"]
  }},
  ...
}}

Extract from ALL chunks with ANY connection. Only mark relevant=false if COMPLETELY unrelated to query.
"""


# ============================================================================
# PASS 2: SYNTHESIS PROMPT
# ============================================================================

def build_synthesis_prompt(question: str, extracted_data: dict) -> str:
    """
    Pass 2: Synthesize extracted data into narrative following full Thunderclap framework.
    """
    # Organize data by time period
    time_periods = {}
    all_people = set()
    all_identities = set()
    all_crises = set()
    
    for chunk_id, data in extracted_data.items():
        # Skip if data is None or not relevant
        if not data or not data.get('relevant', False):
            continue
            
        period = data.get('time_period', 'Unknown')
        if period not in time_periods:
            time_periods[period] = []
        time_periods[period].append(data)
        
        # Safely update sets (handle None values)
        people = data.get('people', [])
        if people:
            all_people.update(people)
        
        identities = data.get('identities', [])
        if identities:
            all_identities.update(identities)
        
        crises = data.get('crises', [])
        if crises:
            all_crises.update(crises)
    
    # Format extracted data for synthesis
    data_summary = []
    for period in sorted(time_periods.keys()):
        data_summary.append(f"\n**{period}:**")
        period_data = time_periods[period]
        
        # Aggregate events
        events = []
        for d in period_data:
            events.extend(d.get('events', []))
        
        for event in events:
            data_summary.append(f"  • {event}")
    
    data_text = "\n".join(data_summary)
    
    return f"""You are a banking historian creating a narrative about: {question}

EXTRACTED DATA FROM {len(extracted_data)} CHUNKS:
{data_text}

IDENTITIES PRESENT: {', '.join(sorted(all_identities))}
CRISES MENTIONED: {', '.join(sorted(all_crises))}

YOUR TASK: Create ONE complete narrative following the Thunderclap Framework.

NOTE ON EXTRACTED DATA:
- Pass 1 extraction was PERMISSIVE - includes direct mentions, context, and background
- YOU must filter during synthesis - only include information directly involving query subject
- YOU must balance coverage - don't let one time period dominate just because it has more data
- YOU choose what to expand vs. compress for coherent narrative

{CRITICAL_RELEVANCE_AND_ACCURACY}

============================================================================
THUNDERCLAP FRAMEWORK (APPLY TO EVERY SECTION)
============================================================================

**WRITING STYLE - Bernanke + Maya Angelou:**
- ANALYTICAL RIGOR (Bernanke): Factual precision, causal analysis, economic logic
- HUMANIZING DETAILS (Maya Angelou): Individual experiences, human moments (fled with movable assets, widow operated from home)
- BALANCE: Facts + humanity, NO melodrama
- NO PLATITUDES: Never "dynamic nature", "testament to", "transformative era", "strategically positioned"

**STRUCTURE - Chronological with Balanced Coverage:**
1. STRICT TIME PERIODS (e.g., "1770s-1790s", "1800-1815", "1820s-1840s")
   - Move FORWARD in time, NEVER jump backwards
   - Cover ALL periods in extracted data with EVEN detail
   - If 18th century has 20 events and 19th has 5, BALANCE the narrative length

2. SHORT PARAGRAPHS (3-4 sentences max)
   - ONE topic per paragraph
   - NEVER mix topics or span decades in one paragraph
   - Connect paragraphs with transitions

3. SUBJECT ALWAYS ACTIVE
   - "*Lehman* merged with Goldman" ✓
   - "Goldman merged with *Lehman*" ✗

{THUNDERCLAP_SOCIOLOGY_FRAMEWORK}

{THUNDERCLAP_PANIC_FRAMEWORK}

**NAMING CONVENTIONS:**
- Institutions: Italics (*Hope*, *Lehman*, *Morgan*)
- People: Regular (Henry Hope, Henry Lehman, J.P. Morgan)
- NEVER "& Co." or "& Company"
- Consistency: "WWI" and "WWII" (not "World War I" then "WWII")

**END WITH RELATED QUESTIONS:**
Generate 3-5 specific follow-up questions about:
- Other entities/topics mentioned in documents
- Broader themes with enough content for multiple paragraphs
- Related places/periods

============================================================================
CRITICAL EDITORIAL DECISIONS
============================================================================

1. BALANCE COVERAGE ACROSS TIME PERIODS
   - If data is heavy in one period (18th century), compress details
   - If data is light in another (19th century), expand what's there
   - Aim for even narrative flow, not proportional to source material

2. PRIORITIZE QUALITY OVER QUANTITY
   - Better: Coherent narrative of 5 well-developed periods
   - Worse: Scattered mentions of 20 disconnected events

3. MAINTAIN FRAMEWORK THROUGHOUT
   - Every section needs sociology + panic lens (if relevant)
   - Don't drop analytical framework after first paragraph
   - Consistent voice and structure from start to finish

Now create the narrative following ALL the rules above.
"""


# ============================================================================
# HELPER FUNCTION
# ============================================================================

def parse_extraction_json(llm_response: str) -> dict:
    """Parse JSON from LLM extraction response."""
    import json
    import re
    
    # Try to extract JSON from response
    # LLMs sometimes wrap in markdown code blocks
    json_match = re.search(r'```json\s*(.*?)\s*```', llm_response, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        # Try to find JSON object directly
        json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            return {}
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"  [WARNING] Failed to parse extraction JSON: {e}")
        print(f"  [DEBUG] Attempting to salvage partial data...")
        
        # Try to salvage partial JSON by fixing common issues
        try:
            # Remove trailing commas before closing braces/brackets
            json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
            return json.loads(json_str)
        except:
            print(f"  [ERROR] Could not salvage JSON, returning empty dict")
            return {}

