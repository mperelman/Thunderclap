"""
Geographic/Sectoral Processor
==============================
For event queries (panics, wars, crises), organize by geography or sector.
Not by time period since events happen in short timeframes.
Uses async processing with semaphore for rate limiting - no artificial pauses needed.
"""

import asyncio
import re
from typing import List, Tuple, Dict

# Constants
MAX_CONCURRENT_REQUESTS = 10  # Max concurrent API calls (Gemini allows 15 RPM)

# Geographic regions for clustering
GEOGRAPHIES = {
    'United States': r'\b(america|united states|u\.s\.|new york|chicago|boston|wall street|federal reserve|mcadoo|wilson)\b',
    'Britain': r'\b(britain|british|england|london|bank of england|sterling|pound)\b',
    'Germany': r'\b(germany|german|berlin|hamburg|frankfurt|reichsbank|mark)\b',
    'France': r'\b(france|french|paris|banque de france|franc)\b',
    'Russia': r'\b(russia|russian|moscow|saint-petersburg|ruble)\b',
    'Austria-Hungary': r'\b(austria|austrian|habsburg|vienna)\b',
    'Ottoman Empire': r'\b(ottoman|turkey|turkish|constantinople)\b',
    'Asia': r'\b(india|china|japan|asia|bombay|calcutta|shanghai|tokyo)\b',
}


class GeographicProcessor:
    """
    Process event queries by organizing chunks geographically or by sector.
    Better than time periods for events that occur in short timeframes.
    Uses async processing with rate limiting for 3-4x speedup.
    """
    
    def __init__(self, llm_generator, use_async=True):
        """
        Initialize geographic processor.
        
        Args:
            llm_generator: LLM instance
            use_async: If False, uses sequential processing (for FastAPI compatibility)
        """
        self.llm = llm_generator
        self.use_async = use_async
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    
    async def process_by_geography_async(
        self,
        question: str,
        chunks: List[Tuple],
        prompt_builder
    ) -> str:
        """
        Process event queries by geography/sector using async for 3-4x speedup.
        
        Args:
            question: User's question (about an event/crisis)
            chunks: List of (text, metadata) tuples
            prompt_builder: Function to build prompts
        
        Returns:
            Narrative organized by geography/sector
        """
        print("\n" + "="*70)
        print(f"ASYNC GEOGRAPHIC PROCESSING ({len(chunks)} chunks)")
        print("="*70)
        
        # Organize chunks by geography
        print(f"\n[STEP 1] Organizing {len(chunks)} chunks by geography/region...")
        geographic_chunks = self._organize_by_geography(chunks)
        
        # Show organization
        print(f"  Organized into {len(geographic_chunks)} regions:")
        for region, gchunks in geographic_chunks.items():
            print(f"    • {region}: {len(gchunks)} chunks")
        
        # Process all regions concurrently
        print(f"\n[STEP 2] Generating narratives for {len(geographic_chunks)} regions (concurrent)...")
        
        # Create tasks for all regions
        region_tasks = []
        for region, gchunks in geographic_chunks.items():
            print(f"    • Queuing {region} ({len(gchunks)} chunks)...")
            task = self._process_region_async(question, region, gchunks)
            region_tasks.append((region, task))
        
        # Process all regions concurrently (rate-limited by semaphore)
        print(f"  [PROCESSING] Running {len(region_tasks)} regions in parallel...")
        
        # Await all tasks concurrently
        results = await asyncio.gather(*[task for _, task in region_tasks])
        
        # Map results back to regions
        regional_narratives = {}
        for (region, _), narrative in zip(region_tasks, results):
            regional_narratives[region] = narrative
            print(f"    [OK] {region} complete")
        
        # Combine regional narratives
        print(f"\n[STEP 3] Combining {len(regional_narratives)} regional narratives...")
        final_narrative = await self._combine_regional_narratives_async(
            question,
            regional_narratives
        )
        
        print(f"  [OK] Comprehensive narrative complete")
        print("="*70 + "\n")
        
        return final_narrative
    
    def process_by_geography_sequential(
        self,
        question: str,
        chunks: List[Tuple],
        prompt_builder
    ) -> str:
        """
        Process chunks sequentially (no async) for FastAPI compatibility.
        Slower but avoids event loop conflicts.
        
        Args:
            question: User's question (about an event/crisis)
            chunks: List of (text, metadata) tuples
            prompt_builder: Function to build prompts
        
        Returns:
            Narrative organized by geography/sector
        """
        print("\n" + "="*70)
        print(f"SEQUENTIAL GEOGRAPHIC PROCESSING ({len(chunks)} chunks)")
        print("="*70)
        
        # Organize chunks by geography
        print(f"\n[STEP 1] Organizing {len(chunks)} chunks by geography...")
        geographic_chunks = self._organize_by_geography(chunks)
        
        # Show organization
        print(f"  Organized into {len(geographic_chunks)} regions:")
        for region, rchunks in geographic_chunks.items():
            print(f"    • {region}: {len(rchunks)} chunks")
        
        # Process each region sequentially
        print(f"\n[STEP 2] Generating narratives for each region (sequential)...")
        region_narratives = {}
        
        for i, (region, rchunks) in enumerate(geographic_chunks.items(), 1):
            print(f"  [{i}/{len(geographic_chunks)}] Processing {region} ({len(rchunks)} chunks)...")
            
            # Calculate estimated tokens (using config values: 1000 words/chunk, 1.3 tokens/word)
            from lib.config import ESTIMATED_WORDS_PER_CHUNK, TOKENS_PER_WORD
            batch_words = sum(len(chunk[0].split()) for chunk in rchunks)
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
            
            # Use sync generate_answer
            narrative = self.llm.generate_answer(question, rchunks)
            region_narratives[region] = narrative
        
        # Combine regional narratives
        print(f"\n[STEP 3] Combining {len(region_narratives)} regional narratives...")
        
        # Wait before final API call (minimal wait for combining operation)
        import time
        wait_time = 4  # Standard RPM limit
        print(f"  [Rate limit] Waiting {wait_time}s before combining...")
        time.sleep(wait_time)
        
        from lib.prompts import build_merge_prompt
        # Use proper merge prompt with full Thunderclap rules
        merge_prompt = build_merge_prompt(question, list(region_narratives.values()))
        
        final_narrative = self.llm.call_api(merge_prompt)
        
        print(f"  [OK] Comprehensive narrative complete")
        print("="*70 + "\n")
        
        return final_narrative
    
    def process_by_geography(
        self,
        question: str,
        chunks: List[Tuple],
        prompt_builder
    ) -> str:
        """
        Main entry point - uses sequential if use_async=False, otherwise async.
        
        Args:
            question: User's question (about an event/crisis)
            chunks: List of (text, metadata) tuples
            prompt_builder: Function to build prompts
        
        Returns:
            Narrative organized by geography/sector
        """
        # If async disabled, use sequential
        if not self.use_async:
            return self.process_by_geography_sequential(question, chunks, prompt_builder)
        
        # Otherwise use async (with thread handling for FastAPI)
        try:
            loop = asyncio.get_running_loop()
            # We're in an async context - need to run in new loop in thread
            import threading
            
            result = [None]
            exception = [None]
            
            def run_in_thread():
                try:
                    # Create new event loop for this thread
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    result[0] = new_loop.run_until_complete(
                        self.process_by_geography_async(
                            question, chunks, prompt_builder
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
            return asyncio.run(self.process_by_geography_async(
                question, chunks, prompt_builder
            ))
    
    def _organize_by_geography(
        self,
        chunks: List[Tuple]
    ) -> Dict[str, List[Tuple]]:
        """
        Organize chunks by geographic region.
        
        Returns:
            Dict of {region_name: [chunks]}
        """
        geographic_chunks = {name: [] for name in GEOGRAPHIES.keys()}
        geographic_chunks["Other/Global"] = []
        
        for text, metadata in chunks:
            # Try to detect region from chunk text
            region_found = False
            
            for region_name, pattern in GEOGRAPHIES.items():
                if re.search(pattern, text, re.IGNORECASE):
                    geographic_chunks[region_name].append((text, metadata))
                    region_found = True
                    break  # Assign to first matching region
            
            # If no specific region, add to global
            if not region_found:
                geographic_chunks["Other/Global"].append((text, metadata))
        
        # Remove empty regions
        return {k: v for k, v in geographic_chunks.items() if v}
    
    async def _process_region_async(self, question: str, region: str, chunks: list) -> str:
        """
        Process a single region asynchronously.
        
        Args:
            question: User's question
            region: Region name
            chunks: List of (text, metadata) tuples for this region
        
        Returns:
            Narrative for this region
        """
        if len(chunks) > 30:
            # Many chunks - use concurrent batching
            return await self._process_region_batched_async(question, region, chunks)
        else:
            # Few chunks - single API call
            async with self.semaphore:
                return await self.llm.generate_answer_async(question, chunks)
    
    async def _process_region_batched_async(self, question: str, region: str, chunks: list) -> str:
        """
        Process a single region that has many chunks by batching concurrently.
        
        Args:
            question: User's question
            region: Region name
            chunks: List of (text, metadata) tuples for this region
        
        Returns:
            Narrative for this region
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
        
        # Combine batches for this region
        if len(narratives) == 1:
            return narratives[0]
        
        print(f"    Merging {len(narratives)} sub-batches for {region}...")
        
        # Merge sub-batches
        combined_text = "\n\n---\n\n".join(narratives)
        merge_prompt = f"""Combine these {len(narratives)} sections about {question} in {region} into ONE coherent narrative.

{combined_text}

RULES:
- Thematically organize (group by sector/institution, not just list facts)
- Explain causal connections (what triggered what)
- Compare different responses/impacts within this region
- Short paragraphs (3 sentences max)
- Maintain analytical framework

Synthesize:"""
        
        try:
            async with self.semaphore:
                response = await self.llm.client.generate_content_async(merge_prompt)
                return response.text
        except:
            return combined_text
    
    def _process_region_batched(self, question: str, region: str, chunks: list) -> str:
        """Process a single region with many chunks."""
        batch_size = 20
        narratives = []
        total_batches = (len(chunks) + batch_size - 1) // batch_size
        
        print(f"    Batching {len(chunks)} chunks into {total_batches} sub-batches...")
        
        for j in range(0, len(chunks), batch_size):
            batch = chunks[j:j + batch_size]
            batch_num = j // batch_size + 1
            
            print(f"      [{batch_num}/{total_batches}] {len(batch)} chunks...", end='')
            
            # Generate narrative for this batch
            narrative = self.llm.generate_answer(question, batch)
            narratives.append(narrative)
            
            print(" done")
            
            # Pause between batches
            if j + batch_size < len(chunks):
                time.sleep(PAUSE_TIME)
        
        # Combine batches for this region
        if len(narratives) == 1:
            return narratives[0]
        
        print(f"    Merging {len(narratives)} sub-batches for {region}...")
        
        # Merge sub-batches
        combined_text = "\n\n---\n\n".join(narratives)
        merge_prompt = f"""Combine these {len(narratives)} sections about {question} in {region} into ONE coherent narrative.

{combined_text}

RULES:
- Thematically organize (group by sector/institution, not just list facts)
- Explain causal connections (what triggered what)
- Compare different responses/impacts within this region
- Short paragraphs (3 sentences max)
- Maintain analytical framework

Synthesize:"""
        
        try:
            response = self.llm.client.generate_content(merge_prompt)
            return response.text
        except:
            return combined_text
    
    async def _combine_regional_narratives_async(
        self,
        question: str,
        regional_narratives: Dict[str, str]
    ) -> str:
        """
        Combine region-specific narratives into comprehensive narrative asynchronously.
        """
        # Format regional narratives
        sections_text = "\n\n".join([
            f"=== {region} ===\n{narrative}"
            for region, narrative in regional_narratives.items()
        ])
        
        merge_prompt = f"""You have {len(regional_narratives)} region-specific narratives about: {question}

REGIONAL NARRATIVES:
{sections_text}

YOUR TASK: Create ONE comprehensive narrative organized by GEOGRAPHY/REGION.

**CRITICAL INSTRUCTIONS:**

1. GEOGRAPHIC ORGANIZATION:
   - Use region headings: "**United States:**", "**Britain:**", "**Germany:**"
   - Show how event impacted EACH region differently
   - Compare responses: "While US created Fed, Britain closed banks"

2. COMPARATIVE ANALYSIS across regions:
   - CONTRASTING RESPONSES: Different policies in different countries
   - PARALLEL IMPACTS: Similar effects across regions
   - INTERCONNECTIONS: How one region's actions affected others
   - Example: "US closure of Jewish banks contrasted with German war credit banks"

3. THEMATIC SECTIONS within each region:
   - Group by themes (banking response, regulatory changes, war financing)
   - Each section = 2-4 paragraphs on ONE theme

4. PARAGRAPH LENGTH (HARD LIMIT):
   - MAXIMUM 3 sentences per paragraph
   - After 3 sentences, MANDATORY break

5. CULTURAL ANALYSIS:
   - Show how identity/exclusion shaped impacts
   - Compare treatment of different groups (Jewish banks closed vs. others)

6. WRITING STYLE:
   - BERNANKE: Causal analysis
   - MAYA ANGELOU: Humanizing details
   - SUBJECT ACTIVE, NO PLATITUDES

7. END WITH RELATED QUESTIONS (CRITICAL FILTER):
   - 3-5 questions ONLY about topics with SUBSTANTIAL material in the regional narratives
   - Test EACH: "Could I write 3+ paragraphs from what documents ACTUALLY said?"
   - If NO → DELETE
   
   DO NOT SUGGEST:
   ✗ Sociological analysis UNLESS documents explicitly discussed it
   ✗ Entities mentioned only 1-3 times in passing
   ✗ "How did X impact/affect Y?" when docs only state X happened (NO causal analysis without evidence)
   ✗ "Legacy" or "influence" when docs don't discuss legacy/influence
   ✗ "Why" when docs only describe "what"
   
   CRITICAL CHECK for EACH question:
   - Did the narrative I just wrote discuss the answer? If NO → DELETE
   - Does narrative mention topic in only 1-2 sentences? If YES → DELETE
   
   ONLY SUGGEST:
   ✓ Regions/entities with substantive coverage (5+ mentions with detail)
   ✓ Topics where docs provide analysis, not just facts

Synthesize into ONE geographically organized narrative with comparative analysis.
"""
        
        try:
            async with self.semaphore:
                response = await self.llm.client.generate_content_async(merge_prompt)
                return response.text
        except Exception as e:
            print(f"  [ERROR] Failed to merge narratives: {e}")
            # Fallback: concatenate with separators
            return "\n\n---\n\n".join([
                f"**{region}:**\n{narrative}"
                for region, narrative in regional_narratives.items()
            ])
    
    def _combine_regional_narratives(
        self,
        question: str,
        regional_narratives: Dict[str, str]
    ) -> str:
        """
        Combine region-specific narratives into comprehensive narrative.
        """
        # Format regional narratives
        sections_text = "\n\n".join([
            f"=== {region} ===\n{narrative}"
            for region, narrative in regional_narratives.items()
        ])
        
        merge_prompt = f"""You have {len(regional_narratives)} region-specific narratives about: {question}

REGIONAL NARRATIVES:
{sections_text}

YOUR TASK: Create ONE comprehensive narrative organized by GEOGRAPHY/REGION.

**CRITICAL INSTRUCTIONS:**

1. GEOGRAPHIC ORGANIZATION:
   - Use region headings: "**United States:**", "**Britain:**", "**Germany:**"
   - Show how event impacted EACH region differently
   - Compare responses: "While US created Fed, Britain closed banks"

2. COMPARATIVE ANALYSIS across regions:
   - CONTRASTING RESPONSES: Different policies in different countries
   - PARALLEL IMPACTS: Similar effects across regions
   - INTERCONNECTIONS: How one region's actions affected others

3. SHORT PARAGRAPHS (HARD LIMIT):
   - MAXIMUM 3 sentences per paragraph
   - Each region gets 2-3 focused paragraphs
   
4. CULTURAL/LEGAL CONTEXT:
   - Explain WHY regions responded differently (legal systems, banking structures)
   - Show sociological factors if relevant

5. THUNDERCLAP MECHANICS:
   - Institutions italicized: *Federal Reserve*, *Bank of England*
   - People regular: J.P. Morgan, Benjamin Strong
   - NO PLATITUDES

6. END WITH RELATED QUESTIONS (CRITICAL FILTER):
   - ONLY suggest questions about topics with SUBSTANTIAL coverage
   - For EACH question: "Could I write 3+ paragraphs from what docs said?"
   - If NO → DELETE
   
   DO NOT SUGGEST:
   ✗ Impact/causal questions when docs only state facts
   ✗ Entities mentioned <5 times
   ✗ "How did X affect Y?" without evidence
   
   ONLY SUGGEST:
   ✓ Regions/entities with substantive coverage (5+ mentions with detail)
   ✓ Topics where docs provide analysis, not just facts

Synthesize into ONE geographically organized narrative with comparative analysis.
"""
        
        try:
            response = self.llm.client.generate_content(merge_prompt)
            return response.text
        except Exception as e:
            print(f"  [ERROR] Failed to merge narratives: {e}")
            # Fallback: concatenate with separators
            return "\n\n---\n\n".join([
                f"**{region}:**\n{narrative}"
                for region, narrative in regional_narratives.items()
            ])


