"""
Iterative Period-Based Processing
==================================
For high-volume queries (>100 chunks), organize by time period and process each separately.
Uses async processing with semaphore for rate limiting - no artificial pauses needed.
"""

import asyncio
import re
from typing import List, Tuple, Dict, Optional

# Constants
MAX_CONCURRENT_REQUESTS = 10  # Max concurrent API calls (Gemini allows 15 RPM)

# Time period definitions (flexible boundaries)
TIME_PERIODS = [
    ("Medieval", r'\b(1[0-4]\d{2}|[89]\d{2})\b'),  # 800-1499
    ("16th-17th centuries", r'\b(15\d{2}|16\d{2}|17\d{2})\b'),  # 1500-1799 first pass
    ("18th century", r'\b(17[0-9]\d)\b'),  # 1700-1799
    ("19th century", r'\b(18\d{2})\b'),  # 1800-1899
    ("20th century", r'\b(19\d{2})\b'),  # 1900-1999
    ("21st century", r'\b(20[012]\d)\b'),  # 2000-2029
]


class IterativePeriodProcessor:
    """
    Process high-volume queries by organizing chunks into time periods,
    generating narratives for each period, then combining.
    Uses async processing with rate limiting for 3-4x speedup.
    """
    
    def __init__(self, llm_generator, use_async=True):
        """
        Initialize iterative processor.
        
        Args:
            llm_generator: LLM instance
            use_async: If False, uses sequential processing (for FastAPI compatibility)
        """
        self.llm = llm_generator
        self.use_async = use_async
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    
    async def process_iterative_async(
        self,
        question: str,
        chunks: List[Tuple],
        prompt_builder,
        max_chunks_per_period: int = 50,
        subject_terms: Optional[List[str]] = None,
        subject_phrases: Optional[List[str]] = None
    ) -> str:
        """
        Process chunks iteratively by time period using async for 3-4x speedup.
        
        Args:
            question: User's question
            chunks: List of (text, metadata) tuples
            prompt_builder: Function to build prompts
            max_chunks_per_period: Max chunks to use per period
        
        Returns:
            Comprehensive narrative covering all periods
        """
        print("\n" + "="*70)
        print(f"ASYNC ITERATIVE PROCESSING ({len(chunks)} chunks)")
        print("="*70)
        
        # Organize chunks by time period
        print(f"\n[STEP 1] Organizing {len(chunks)} chunks by time period...")
        period_chunks = self._organize_by_period(
            chunks,
            max_chunks_per_period,
            subject_terms,
            subject_phrases
        )
        
        # Show organization
        print(f"  Organized into {len(period_chunks)} time periods:")
        for period, pchunks in period_chunks.items():
            print(f"    • {period}: {len(pchunks)} chunks")
        
        # Process periods sequentially to avoid bursting rate limits
        print(f"\n[STEP 2] Generating narratives period-by-period (sequential)...")
        
        period_narratives = {}
        for period, pchunks in period_chunks.items():
            print(f"  [START] {period} ({len(pchunks)} chunks)...")
            narrative = await self._process_period_async(question, period, pchunks)
            period_narratives[period] = narrative
            print(f"  [OK] {period} complete")
        
        # Combine period narratives
        print(f"\n[STEP 3] Combining {len(period_narratives)} period narratives...")
        final_narrative = await self._combine_period_narratives_async(
            question, 
            period_narratives
        )
        
        print(f"  [OK] Comprehensive narrative complete")
        print("="*70 + "\n")
        
        return final_narrative
    
    def process_iterative_sequential(
        self,
        question: str,
        chunks: List[Tuple],
        prompt_builder,
        max_chunks_per_period: int = 50,
        subject_terms: Optional[List[str]] = None,
        subject_phrases: Optional[List[str]] = None
    ) -> str:
        """
        Process chunks sequentially (no async) for FastAPI compatibility.
        Slower but avoids event loop conflicts.
        
        Args:
            question: User's question
            chunks: List of (text, metadata) tuples
            prompt_builder: Function to build prompts
            max_chunks_per_period: Max chunks to use per period
        
        Returns:
            Comprehensive narrative covering all periods
        """
        print("\n" + "="*70)
        print(f"SEQUENTIAL PROCESSING ({len(chunks)} chunks)")
        print("="*70)
        
        # Organize chunks by time period
        print(f"\n[STEP 1] Organizing {len(chunks)} chunks by time period...")
        period_chunks = self._organize_by_period(
            chunks,
            max_chunks_per_period,
            subject_terms,
            subject_phrases
        )
        
        # Show organization
        print(f"  Organized into {len(period_chunks)} time periods:")
        for period, pchunks in period_chunks.items():
            print(f"    • {period}: {len(pchunks)} chunks")
        
        # Process each period sequentially
        print(f"\n[STEP 2] Generating narratives for each period (sequential)...")
        period_narratives = {}
        
        for i, (period, pchunks) in enumerate(period_chunks.items(), 1):
            print(f"  [{i}/{len(period_chunks)}] Processing {period} ({len(pchunks)} chunks)...")
            import sys
            sys.stdout.flush()  # Ensure output is visible
            
            # Calculate estimated tokens (using config values: 1000 words/chunk, 1.3 tokens/word)
            from lib.config import ESTIMATED_WORDS_PER_CHUNK, TOKENS_PER_WORD
            batch_words = sum(len(chunk[0].split()) for chunk in pchunks)
            estimated_tokens = int(batch_words * TOKENS_PER_WORD)
            
            # Rate limit: Gemini allows 15 RPM = 4s minimum between requests
            # Use minimal wait to avoid connection timeouts while respecting API limits
            if i > 1:
                import time
                # Minimal wait: 4 seconds (RPM limit), only increase for very large requests
                if estimated_tokens > 200000:  # >200K tokens (rare)
                    wait_time = 6
                else:
                    wait_time = 4  # Standard RPM limit
                
                print(f"    [Rate limit] Waiting {wait_time}s (~{int(estimated_tokens):,} tokens)...")
                time.sleep(wait_time)
            
            # Just use regular generate_answer (sync)
            print(f"    [API] Calling LLM for {period}...")
            sys.stdout.flush()
            narrative = self.llm.generate_answer(question, pchunks)
            print(f"    [OK] {period} narrative complete ({len(narrative)} chars)")
            sys.stdout.flush()
            period_narratives[period] = narrative
        
        # Combine period narratives
        print(f"\n[STEP 3] Combining {len(period_narratives)} period narratives...")
        import sys
        sys.stdout.flush()
        
        # Wait before final API call (minimal wait for combining operation)
        import time
        wait_time = 4  # Standard RPM limit
        print(f"  [Rate limit] Waiting {wait_time}s before combining...")
        sys.stdout.flush()
        time.sleep(wait_time)
        
        # Use sync combine
        sections_text = "\n\n".join([
            f"=== {period} ===\n{narrative}"
            for period, narrative in period_narratives.items()
        ])
        
        from lib.prompts import build_merge_prompt
        # Use proper merge prompt with full Thunderclap rules
        merge_prompt = build_merge_prompt(question, list(period_narratives.values()))
        
        print(f"  [API] Calling LLM to combine narratives...")
        sys.stdout.flush()
        final_narrative = self.llm.call_api(merge_prompt)
        print(f"  [OK] Final narrative complete ({len(final_narrative)} chars)")
        sys.stdout.flush()
        
        print(f"  [OK] Comprehensive narrative complete")
        print("="*70 + "\n")
        
        return final_narrative
    
    def process_iterative(
        self,
        question: str,
        chunks: List[Tuple],
        prompt_builder,
        max_chunks_per_period: int = 50,
        subject_terms: Optional[List[str]] = None,
        subject_phrases: Optional[List[str]] = None
    ) -> str:
        """
        Synchronous wrapper for async process_iterative_async.
        Maintains backwards compatibility while using async internally.
        Handles both sync and async contexts.
        
        Args:
            question: User's question
            chunks: List of (text, metadata) tuples
            prompt_builder: Function to build prompts
            max_chunks_per_period: Max chunks to use per period
        
        Returns:
            Comprehensive narrative covering all periods
        """
        # Check if we're already in an async context
        try:
            loop = asyncio.get_running_loop()
            # We're in an async context - need to run in new loop in thread
            import concurrent.futures
            import threading
            
            result = [None]
            exception = [None]
            
            def run_in_thread():
                try:
                    # Create new event loop for this thread
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    result[0] = new_loop.run_until_complete(
                        self.process_iterative_async(
                    question, chunks, prompt_builder, max_chunks_per_period, subject_terms, subject_phrases
                        )
                    )
                    new_loop.close()
                except Exception as e:
                    exception[0] = e
            
            thread = threading.Thread(target=run_in_thread)
            thread.start()
            thread.join()
            
            if exception[0]:
                raise exception[0]
            return result[0]
            
        except RuntimeError:
            # No running loop - safe to use asyncio.run()
            return asyncio.run(self.process_iterative_async(
                question, chunks, prompt_builder, max_chunks_per_period, subject_terms, subject_phrases
            ))
    
    def organize_periods(
        self,
        chunks: List[Tuple],
        max_per_period: int,
        subject_terms: Optional[List[str]] = None,
        subject_phrases: Optional[List[str]] = None
    ) -> Dict[str, List[Tuple]]:
        return self._organize_by_period(chunks, max_per_period, subject_terms, subject_phrases)

    def _organize_by_period(
        self,
        chunks: List[Tuple],
        max_per_period: int,
        subject_terms: Optional[List[str]] = None,
        subject_phrases: Optional[List[str]] = None
    ) -> Dict[str, List[Tuple]]:
        """
        Organize chunks by time period using regex detection.
        
        Returns:
            Dict of {period_name: [chunks]}
        """
        period_chunks = {name: [] for name, _ in TIME_PERIODS}
        period_chunks["Undated"] = []
        
        for text, metadata in chunks:
            # Try to detect time period from chunk text
            # Find ALL matching periods, then assign to the LATEST one
            # This ensures chunks spanning multiple periods go to the later period
            matching_periods = []
            
            for period_name, pattern in TIME_PERIODS:
                if re.search(pattern, text):
                    matching_periods.append(period_name)
            
            if matching_periods:
                # Assign to the LATEST matching period (last in TIME_PERIODS order)
                # This ensures chunks with years from multiple periods go to the later period
                period_order = ["Medieval", "16th-17th centuries", "18th century", "19th century", "20th century", "21st century"]
                latest_period = max(matching_periods, key=lambda x: period_order.index(x) if x in period_order else -1)
                if len(period_chunks[latest_period]) < max_per_period:
                    period_chunks[latest_period].append((text, metadata))
            else:
                # If no period detected, add to undated (if space)
                if len(period_chunks["Undated"]) < max_per_period:
                    period_chunks["Undated"].append((text, metadata))
        
        # Remove empty periods
        period_chunks = {k: v for k, v in period_chunks.items() if v}
        
        if subject_terms or subject_phrases:
            lowered_terms = [term.lower() for term in (subject_terms or [])]
            lowered_phrases = []
            exact_phrases = []
            if subject_phrases:
                for phrase in subject_phrases:
                    if phrase.isupper():
                        exact_phrases.append(phrase)
                    else:
                        lowered_phrases.append(phrase.lower())
            filtered = {}
            # Prioritize later periods - they're more likely to have relevant content
            period_order = ["Medieval", "16th-17th centuries", "18th century", "19th century", "20th century", "21st century", "Undated"]
            sorted_periods = sorted(period_chunks.keys(), key=lambda x: period_order.index(x) if x in period_order else 999, reverse=True)
            
            for period in sorted_periods:
                plist = period_chunks[period]
                matches = [
                    chunk for chunk in plist
                    if self._chunk_matches(chunk[0], lowered_terms, lowered_phrases, exact_phrases)
                ]
                # Keep period even if no matches - might have relevant content that doesn't explicitly mention subject
                # But prioritize matches if they exist
                if matches:
                    filtered[period] = matches
                elif plist:  # Keep chunks from this period to avoid dropping entire eras
                    # For later periods (20th, 21st century), keep more chunks as they're more likely to be relevant
                    if period in ["20th century", "21st century"]:
                        filtered[period] = plist[:15]  # Keep more from later periods
                    else:
                        filtered[period] = plist[:10]  # Keep more chunks from all periods
            if filtered:
                period_chunks = filtered
    @staticmethod
    def _chunk_matches(
        text: str,
        lowered_terms: List[str],
        lowered_phrases: List[str],
        exact_phrases: List[str]
    ) -> bool:
        text_lower = text.lower()
        if lowered_phrases or exact_phrases:
            for phrase in lowered_phrases:
                if phrase and phrase in text_lower:
                    return True
            for phrase in exact_phrases:
                if re.search(rf'\b{re.escape(phrase)}\b', text):
                    return True
            return False if lowered_terms else False
        if lowered_terms:
            return any(term in text_lower for term in lowered_terms)
        return True
        
        return period_chunks
    
    async def _process_period_async(self, question: str, period: str, chunks: list) -> str:
        """
        Process a single period asynchronously.
        
        Args:
            question: User's question
            period: Period name
            chunks: List of (text, metadata) tuples for this period
        
        Returns:
            Narrative for this period
        """
        if len(chunks) > 30:
            # Many chunks - use concurrent batching
            return await self._process_period_batched_async(question, period, chunks)
        else:
            # Few chunks - single API call
            async with self.semaphore:
                return await self.llm.generate_answer_async(question, chunks)
    
    async def _process_period_batched_async(self, question: str, period: str, chunks: list) -> str:
        """
        Process a single period that has many chunks by batching concurrently.
        
        Args:
            question: User's question
            period: Period name
            chunks: List of (text, metadata) tuples for this period
        
        Returns:
            Narrative for this period
        """
        batch_size = 20
        total_batches = (len(chunks) + batch_size - 1) // batch_size
        
        print(f"    Batching {len(chunks)} chunks into {total_batches} sub-batches (concurrent)...")
        
        # Create all batch tasks
        batch_tasks = []
        for j in range(0, len(chunks), batch_size):
            batch = chunks[j:j + batch_size]
            batch_num = j // batch_size + 1
            
            # Create async task with rate limiting
            async def process_batch_with_limit(b=batch, bn=batch_num):
                async with self.semaphore:
                    print(f"      [{bn}/{total_batches}] Processing {len(b)} chunks...")
                    result = await self.llm.generate_answer_async(question, b)
                    print(f"      [{bn}/{total_batches}] Done")
                    return result
            
            batch_tasks.append(process_batch_with_limit())
        
        # Process all batches concurrently
        narratives = await asyncio.gather(*batch_tasks)
        
        # Combine batches for this period
        if len(narratives) == 1:
            return narratives[0]
        
        print(f"    Merging {len(narratives)} sub-batches for {period}...")
        
        # Merge sub-batches
        combined_text = "\n\n---\n\n".join(narratives)
        merge_prompt = f"""Combine these {len(narratives)} sections about {question} in {period} into ONE coherent narrative.

{combined_text}

RULES:
- Thematically organize (group by region/theme, not just list facts)
- Explain cultural/sociological WHY (exclusion, kinship, legal restrictions)
- Remove redundancies
- Maintain analytical framework
- SHORT PARAGRAPHS (ABSOLUTELY CRITICAL): 
  * MAXIMUM 3-4 sentences per paragraph
  * ONE topic per paragraph
  * If you have 10 sentences, split into 3-4 paragraphs
  * Long paragraphs hide poor organization

Synthesize:"""
        
        try:
            async with self.semaphore:
                response = await self.llm.client.generate_content_async(merge_prompt)
                return response.text
        except:
            return combined_text
    
    async def _combine_period_narratives_async(
        self,
        question: str,
        period_narratives: Dict[str, str]
    ) -> str:
        """
        Combine period-specific narratives into one comprehensive narrative asynchronously.
        """
        
        # Format period narratives
        sections_text = "\n\n".join([
            f"=== {period} ===\n{narrative}"
            for period, narrative in period_narratives.items()
        ])
        
        # List all periods to ensure they're all covered
        # Sort periods chronologically (rough approximation)
        period_order = ["Medieval", "16th-17th centuries", "18th century", "19th century", "20th century", "21st century", "Undated"]
        sorted_periods = sorted(period_narratives.keys(), key=lambda x: period_order.index(x) if x in period_order else 999)
        period_list = ", ".join(sorted_periods)
        
        merge_prompt = f"""You have {len(period_narratives)} period-specific narratives about: {question}

PERIODS PROVIDED (YOU MUST COVER ALL OF THESE IN CHRONOLOGICAL ORDER): {period_list}

PERIOD NARRATIVES:
{sections_text}

YOUR TASK: Create ONE comprehensive narrative that is THEMATICALLY COHERENT with CULTURAL ANALYSIS.

CRITICAL REQUIREMENTS:
1. You MUST cover ALL {len(period_narratives)} periods listed above. Do not skip any period.
2. Move chronologically through all periods from earliest to latest: {period_list}
3. If you mention a later period (e.g., 20th century), you cannot then jump back to an earlier period (e.g., 19th century).
4. Each period should get at least 1-2 paragraphs of coverage.

**CRITICAL INSTRUCTIONS:**

1. STRUCTURE - THEMATIC SECTIONS with multiple focused paragraphs:
   - Use section headings: "**Theme Name:**" (e.g., "**Caste System Under British Rule:**")
   - Each section = 2-4 SHORT paragraphs on ONE coherent theme
   - Don't randomly jump themes - finish one before moving to next
   - Example: "**Colonial Era:**" → 3 paragraphs about EIC, Brahmins, Dalits (all related)

2. COMPARATIVE ANALYSIS - Draw comparisons across groups when relevant:
   - PARALLEL PATTERNS: Multiple groups with same dynamics (endogamy, exclusion, networks)
     Example: "Like Russian Jews, Old Believers practiced endogamy to maintain trust networks"
   - CONTRASTING TREATMENT: Different treatment of similar groups in same era
     Example: "As Russia restricted Jewish rights in 1880, it simultaneously expanded Old Believer freedoms in 1883"
   - COMPETITION/COLLABORATION: Groups competing or partnering in same sectors
     Example: "Bukharan Jewish textile factories rivaled Old Believer counterparts in Moscow"
   - HIERARCHY/RELATIONSHIPS: How groups related to each other
     Example: "Brahmin dominance under *EIC* systematically excluded lower-caste Dalits from finance roles"
   - Draw these comparisons even if groups not mentioned in same sentence - look across all period content
   - Comparisons reveal structural dynamics and power relationships

3. CULTURAL/SOCIOLOGICAL EXPLANATIONS (MOST IMPORTANT):
   - Explain WHY patterns emerged, not just WHAT happened
   - MINORITY MIDDLEMEN: Why were Jews channeled into banking? (land restrictions, exclusion from guilds)
   - LEGAL EXCLUSION: How did laws limit opportunities and push into specific roles?
   - KINSHIP NETWORKS: How did endogamous marriage create trust/capital networks?
   - EXPULSIONS/CONVERSIONS: What drove migrations and identity changes?
   - Apply this lens to EVERY period - don't just list events

4. BUILD NARRATIVE ARC:
   - Show patterns developing ACROSS periods (not isolated snapshots)
   - Example: "This pattern of Court Jews, first seen in Medieval Baghdad, spread to Habsburg Vienna..."
   - Connect causes to effects across time
   - Show how conditions in one era shaped opportunities in the next

4. CHRONOLOGICAL BUT THEMATIC:
   - Use time period headings: "**Medieval Period:**", "**16th-17th Centuries:**"
   - Within each period: Group by geography/theme
   - Example paragraph flow:
     ¶1: "In the Islamic world, Jews served as Court Bankers because..."
     ¶2: "The Abbasids appointed Aaron Amram, who..."
     ¶3: "In Christian Europe, different dynamics emerged..."
     ¶4: "Anschel Oppenheim financed Habsburg Austria because..."

5. BALANCED COVERAGE (MANDATORY):
   - Each period gets roughly equal space (2-4 paragraphs)
   - If one period has 10 facts and another has 2, COMPRESS the heavy one
   - Don't let data-heavy periods dominate
   - YOU MUST INCLUDE ALL PERIODS - do not skip any period listed above
   - Move forward chronologically: earliest period → next period → ... → latest period
   - If you mention a later period, you cannot then jump back to an earlier period

6. COMPARATIVE ANALYSIS - Compare groups when docs discuss them together:
   - If docs mention Old Believers AND Russian Jews, compare their experiences
   - If docs discuss Brahmin AND Dalit, show the contrast
   - Only compare when documents EXPLICITLY discuss groups together
   - Comparisons enrich narrative

7. DEFINE SPECIALIZED TERMS on first use:
   - Dalit (untouchable, lowest Hindu caste, faced severe discrimination, excluded from temples)
   - Brahmin (priestly caste, highest in Hindu hierarchy, scholarly pursuits)
   - Kohanim (Jewish priestly caste, descended from Aaron)
   - Court Jew (banker serving European monarchs, often vulnerable to political shifts)
   - Parsee (Zoroastrians fled Persia to India in 7th century)
   - Old Believers (Russian Orthodox sect, split after 17th century reforms)
   - Always explain hierarchy and social status when relevant

8. PARAGRAPH LENGTH (HARD LIMIT - COUNT EVERY SENTENCE):
   - MAXIMUM 3 sentences per paragraph
   - After 3 sentences, MANDATORY paragraph break
   - Each paragraph within a section explores one subtopic
   - Example format:
     
     **Section Theme:**
     
     Subtopic 1 (3 sentences). Second sentence. Third sentence.
     
     Subtopic 2 starts. Second sentence elaborates. Third connects.
     
   - Never write 5+ sentences without a break

9. WRITING STYLE:
   - BERNANKE: Analytical rigor, causal analysis (explain WHY)
   - MAYA ANGELOU: Humanizing details (fled with movable assets, widow operated from home)
   - NO LIST-LIKE WRITING: Don't just say "X did Y in 1492, Z did W in 1493..."
   - BUILD PARAGRAPHS around themes, not individual facts

10. THUNDERCLAP MECHANICS:
   - SUBJECT ACTIVE: *Rothschild* hired (NOT was hired by)
   - Institutions italicized: *Lehman*, *Hope*
   - People regular: Jacob Schiff
   - NO PLATITUDES

11. END WITH RELATED QUESTIONS (CRITICAL FILTER):
   - Provide 3-5 questions ONLY about topics with SUBSTANTIAL material across the period narratives
   - For EACH question, verify: "Could I write 3+ paragraphs from what the documents ACTUALLY said?"
   - If NO → DELETE that question
   
   DO NOT SUGGEST:
   ✗ Sociological questions (identity impact, barriers) UNLESS documents explicitly analyzed those dynamics
   ✗ Entities only mentioned 1-3 times (passing mentions ≠ sufficient material)
   ✗ "How did X impact/affect Y?" when documents only state X happened (NO causal analysis without evidence)
   ✗ "Legacy" or "influence" questions when documents don't discuss legacy/influence
   ✗ "Why" questions when documents only describe "what" happened
   
   CRITICAL CHECK for EACH question:
   - Did the narrative I just wrote discuss the answer? If NO → DELETE
   - Does narrative mention topic in only 1-2 sentences? If YES → DELETE
   
   ONLY SUGGEST:
   ✓ Entities discussed across multiple periods with substantive detail (5+ mentions)
   ✓ Topics where documents provide analysis, not just facts
   ✓ Specific institutions/events covered in depth across the narrative

Now synthesize into ONE coherent narrative with CULTURAL ANALYSIS and THEMATIC FLOW.
"""
        
        try:
            async with self.semaphore:
                response = await self.llm.client.generate_content_async(merge_prompt)
                return response.text
        except Exception as e:
            print(f"  [ERROR] Failed to merge narratives: {e}")
            # Fallback: concatenate with separators
            return "\n\n---\n\n".join([
                f"**{period}:**\n{narrative}"
                for period, narrative in period_narratives.items()
            ])


def create_iterative_processor(llm_generator):
    """Factory function to create iterative processor."""
    return IterativePeriodProcessor(llm_generator)

