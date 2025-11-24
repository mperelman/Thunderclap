# Thunderclap Framework - Embedded in Code

This document explains how the Thunderclap analytical framework is memorialized in the codebase.

## Core Principle

Thunderclap traces financial history through **SOCIOLOGICAL and PANIC lenses IN EVERY SECTION** (not just the opening), not just chronology.

## CRITICAL: Framework Must Be Maintained Throughout

**Common Error**: Narratives mention identity and panics in the opening paragraph, then abandon the framework and become pure chronology in later sections.

**Correct Approach**: EVERY time period section must maintain sociological + panic analysis:
- 17th Century section → analyze identity's impact in that era
- Early 19th Century section → analyze identity's impact + cover Panics of that era
- Post-WWI section → analyze identity's impact + regulatory changes of that era

**Example of Dropping Framework (BAD):**
```
Opening: "Hope was a Huguenot family..."
Later: "In 1820, Hope financed X. In 1830, Hope expanded to Y."  ← Pure chronology, no analysis
```

**Example of Maintaining Framework (GOOD):**
```
Opening: "Hope, a Huguenot family, leveraged Protestant networks..."
Later: "During Panic of 1825, Hope's Huguenot connections to Labouchere enabled X..."  ← Continues analysis
```

## Where It's Embedded

### 1. Main LLM Prompt (`lib/llm.py`, lines 112-146)

Every narrative generation uses this prompt structure:

**THUNDERCLAP FRAMEWORK (CRITICAL - VIEW HISTORY THROUGH THESE LENSES):**

1. **SOCIOLOGICAL LENS - Identity Shapes Opportunities (MAINTAIN THROUGHOUT):**
   - Analyze through MULTIPLE dimensions: religion/race/class, sex/gender, family structure, and law
   - State identity explicitly (Jewish, Quaker, Protestant, Black, women, widows, etc)
   - ANALYZE (not just mention) how these dimensions created BARRIERS or ADVANTAGES in EVERY time period
   - **Sex/Gender**: Did being a woman change access? Did widows operate differently? Were daughters excluded?
   - **Family**: How did family structures (inheritance, primogeniture, marriage patterns) shape opportunities?
   - **Law**: What legal barriers or advantages existed? (e.g., women barred from exchanges, religious tests for office)
   - In EACH section: Show HOW these dimensions shaped opportunities/barriers for that era
   - Base analysis on what documents actually say, don't invent sociological explanations

2. **FINANCIAL PANICS AS ORGANIZING FRAMEWORK (COVER ALL PANICS):**
   - Structure narrative around the Panics documents mention affecting the subject
   - For EACH Panic in EACH time period: What happened? How did identity shape outcome (if docs say)?
   - BAD: Mention Panic of 1763 in opening, then ignore Panic of 1873, 1893, 1907, 1929 in later sections
   - Don't just narrate chronology - connect each Panic to sociology if documents do

3. **FAMILY/SOCIAL NETWORKS AS SOCIAL CAPITAL (IN EVERY ERA):**
   - Show marriages/connections the documents mention in each time period
   - Explain significance based on what documents say these connections enabled
   - Use documents as source, don't speculate about significance

4. **REGULATORY CHANGES AS STRUCTURAL SHIFTS (WHEN RELEVANT):**
   - Show how regulations changed who could access opportunities
   - Connect to identity when documents indicate

5. **NAMING CONVENTIONS (CRITICAL):**
   - **Institutions**: Use italics (*Hope*, *Lehman*, *Morgan*)
   - **People**: Regular text (Henry Hope, Henry Lehman, J.P. Morgan)
   - **NEVER** use "& Co." or "& Company" - causes incorporation/structure issues

6. **WRITING STYLE (Bernanke + Maya Angelou):**
   - Mix analytical rigor (Bernanke) with humanizing details (Maya Angelou)
   - Include events/details that humanize people (e.g., "fled to London with movable assets", "worked from home as widow", "daughter excluded from partnership")
   - NO melodrama, but show people as human beings navigating real constraints
   - Balance factual economic analysis with moments that reveal individual experiences

### 2. Batch Combining Prompt (`lib/query_engine.py`, lines 253-295)

When combining multiple narrative sections:

**THUNDERCLAP FRAMEWORK - View history through SOCIOLOGICAL + PANIC lenses IN EVERY SECTION:**

- **SOCIOLOGY**: Analyze (not just mention) how identity shaped opportunities/barriers in EVERY time period - don't abandon after opening
- **PANICS**: Cover ALL Panics mentioned in sections - Panic of 1763, 1873, 1893, 1907, 1929, etc. Connect each to identity if docs do
- **NETWORKS**: Show how connections created access or exclusion in each era
- **REGULATIONS**: How did they change who could access opportunities?
- **NAMING**: Use italics for institutions (*Hope* for bank), regular for people (Henry Hope). NEVER "& Co." or "& Company"

This prompt explicitly instructs the LLM to:
1. Unify into ONE narrative (not separate sections)
2. Maintain framework THROUGHOUT all time periods
3. Cover ALL panics mentioned across sources
4. Use correct naming conventions

### 3. AI Assistant Instructions (`.cursorrules`, lines 51-68)

Ensures AI assistants maintain framework:

**View history through SOCIOLOGICAL + PANIC lenses (not just chronological):**

✓ SOCIOLOGY: Analyze how identity shaped opportunities (BASED ON DOCUMENTS)
  - State identity explicitly + explain its impact using what documents say
  - Don't invent sociological explanations - use what documents actually say

✓ PANICS AS FRAMEWORK: Structure around crises (COVER ALL DOCS MENTION)
  - Cover ALL Panics documents mention affecting subject
  - For each: What happened? How did identity shape outcome (if docs say so)?
  - Base connections on documents, don't invent theories

✓ NETWORKS: How did marriages/connections create access or exclusion?
✓ REGULATIONS: How did they change who could access opportunities?

## Examples of Framework in Action

### Good Analysis (Document-Based, Framework Maintained Throughout)
- ✓ "*Hope*, a Huguenot institution, leveraged Protestant networks to access Bank of England capital in 1693"
- ✓ "During Panic of 1825, *Hope* partnered with *Baring* to stabilize markets. Their shared Protestant identity enabled rapid coordination with BOE"
- ✓ "In the post-WWI era, Gentile banks forced out Jewish competitors. Only *Lippmann Rosenthal* maintained position alongside Gentile *Hope*"
- ✓ "Henry Hope fled to London in 1794 with his movable assets when French armies occupied Holland" (humanizing detail)
- ✓ "Amsterdam barred women from the exchange. Johanna Borski, as a widow, worked from home through a single broker" (sex/gender + law dimensions)
- ✓ "Primogeniture excluded younger sons from partnerships. They entered colonial trade instead" (family structure dimension)

### Bad Analysis (Invented or Framework Dropped)
- ✗ "Hope & Co. was Jewish" (wrong - they were Huguenot, AND uses "& Co.")
- ✗ "Hope was Huguenot" in opening, then pure chronology: "In 1825 Hope financed X. In 1830 Hope expanded to Y." (drops framework)
- ✗ "Panic of 1825 occurred" (no detail about impact on subject)
- ✗ Making up sociological connections not in documents

### Naming Convention Examples
- ✓ "*Hope* partnered with *Baring* in 1813"
- ✓ "Henry Hope fled to London"
- ✓ "*Lehman* merged with Goldman"
- ✗ "Hope & Co. partnered with Baring & Co." (never use "& Co.")
- ✗ "Hope partnered with Henry Baring" (institution vs person - should be "*Hope* partnered with *Baring*")

## Key Principles

1. **Document-Grounded**: All analysis must be based on what documents actually say - no invented theories or speculation
2. **Analytical, Not Descriptive**: Don't just mention identity/panics - explain how they mattered
3. **Multi-Dimensional Sociology**: Analyze through religion/race/class, sex/gender, family structure, and law
4. **Comprehensive**: Cover ALL panics documents mention (1763, 1825, 1837, 1873, 1893, 1907, 1929, etc.), not just one
5. **Maintained Throughout**: Apply sociological + panic framework in EVERY time period section, not just the opening paragraph
6. **Humanizing Without Melodrama**: Include details that show people navigating real constraints (Bernanke rigor + Maya Angelou storytelling)
7. **Naming Consistency**: Institutions in italics (*Hope*), people regular (Henry Hope), NEVER "& Co."
8. **Subject Active**: Every sentence must have subject as active voice

## Result

Every query returns a narrative that:
- Analyzes identity through **multiple dimensions** (religion/race/class, sex/gender, family, law) **in EVERY time period section**
- Structures around financial crises (covers ALL panics documents mention)
- Connects identity dimensions to crisis outcomes when documents do
- Shows family networks and structures as social capital in each era
- Explains regulatory and legal impacts when relevant
- Includes **humanizing details** that show people navigating real constraints (Bernanke rigor + Maya Angelou storytelling)
- Uses italics for institutions (*Hope*), regular text for people (Henry Hope)
- Never uses "& Co." or "& Company"
- Keeps subject active in every sentence
- NO melodrama, but reveals individual experiences
- Ends with 3-5 Related Questions
- All grounded in actual document content - no invented theories

**Most Critical**: The sociological + panic framework is maintained THROUGHOUT all sections, not abandoned after the opening.


