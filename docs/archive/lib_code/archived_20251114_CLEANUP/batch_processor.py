"""
Batch Processor - Handles rate limiting and batching for LLM requests.
Manages API quotas and batch processing strategy.
"""

import time
from typing import List, Tuple
from .config import (
    BATCH_SIZE_SMALL, BATCH_SIZE_MEDIUM, BATCH_SIZE_LARGE,
    PAUSE_TIME_SMALL, PAUSE_TIME_MEDIUM, PAUSE_TIME_LARGE,
    DAILY_QUOTA_WARNING_THRESHOLD
)


class BatchProcessor:
    """
    Manages batch processing of chunks for LLM narrative generation.
    Handles rate limiting, quota warnings, and adaptive batch sizing.
    """
    
    def __init__(self, llm_generator):
        """
        Initialize batch processor.
        
        Args:
            llm_generator: LLMAnswerGenerator instance to use for API calls
        """
        self.llm = llm_generator
    
    def process_in_batches(
        self,
        question: str,
        chunks: List[Tuple],
        prompt_builder
    ) -> str:
        """
        Process chunks in batches with rate limiting.
        
        Args:
            question: User's question
            chunks: List of (chunk_text, metadata) tuples
            prompt_builder: Function that builds prompt from question, chunks, batch_context
        
        Returns:
            Generated narrative (single batch) or merged narrative (multiple batches)
        """
        # Single batch - no need for merging
        if len(chunks) <= BATCH_SIZE_SMALL:
            prompt = prompt_builder(question, chunks, "")
            return self.llm.call_api(prompt)
        
        # Multiple batches - process and merge
        return self._process_multiple_batches(question, chunks, prompt_builder)
    
    def _process_multiple_batches(
        self,
        question: str,
        chunks: List[Tuple],
        prompt_builder
    ) -> str:
        """Process chunks in multiple batches and merge results."""
        # Calculate batch parameters
        batch_size, pause_time = self._calculate_batch_params(len(chunks))
        total_batches = (len(chunks) + batch_size - 1) // batch_size
        
        # Show progress info
        self._show_batch_info(len(chunks), total_batches, batch_size, pause_time)
        
        # Check quota warning
        self._check_quota_warning(total_batches)
        
        # Process each batch
        narratives = []
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            print(f"  [BATCH {batch_num}/{total_batches}] Processing {len(batch)} chunks...")
            
            # Build prompt with batch context
            batch_context = f" (This is batch {batch_num} of {total_batches} - focus on the content in these documents, will be merged later)"
            prompt = prompt_builder(question, batch, batch_context)
            
            # Generate narrative for this batch
            narrative = self.llm.call_api(prompt)
            narratives.append(narrative)
            
            # Pause between batches (except after last batch)
            if i + batch_size < len(chunks):
                print(f"  [WAIT] Pausing {pause_time} seconds to avoid rate limit...")
                time.sleep(pause_time)
        
        # Merge all narratives
        print(f"  [COMBINE] Merging {len(narratives)} narrative sections...")
        return self._merge_narratives(question, narratives)
    
    def _calculate_batch_params(self, total_chunks: int) -> Tuple[int, int]:
        """
        Calculate optimal batch size and pause time based on query size.
        
        Gemini 2.0 Flash limits:
        - 15 RPM (requests per minute)
        - 1,000,000 TPM (tokens per minute)
        - 50-200 RPD (requests per day, depending on model)
        
        Args:
            total_chunks: Total number of chunks to process
        
        Returns:
            Tuple of (batch_size, pause_time_seconds)
        """
        if total_chunks < 50:
            return BATCH_SIZE_SMALL, PAUSE_TIME_SMALL
        elif total_chunks < 200:
            return BATCH_SIZE_MEDIUM, PAUSE_TIME_MEDIUM
        else:
            return BATCH_SIZE_LARGE, PAUSE_TIME_LARGE
    
    def _show_batch_info(
        self,
        total_chunks: int,
        total_batches: int,
        batch_size: int,
        pause_time: int
    ):
        """Display batch processing information."""
        estimated_time = total_batches * pause_time
        print(f"  [INFO] Processing {total_chunks} chunks in {total_batches} batches")
        print(f"  [INFO] Batch size: {batch_size} chunks, Pause: {pause_time}sec")
        print(f"  [INFO] Estimated time: ~{estimated_time//60} min {estimated_time%60} sec")
        print(f"  [INFO] Rate: ~10 req/min (well under 15 RPM limit)")
    
    def _check_quota_warning(self, total_batches: int):
        """Warn if query might exceed daily quota."""
        if total_batches > DAILY_QUOTA_WARNING_THRESHOLD:
            print(f"  [WARNING] This query requires {total_batches} API requests")
            print(f"  [WARNING] May exceed daily quota (50 RPD for exp models, 200 for standard)")
            print(f"  [TIP] Try a more specific query or wait for quota reset")
    
    def _merge_narratives(self, question: str, narratives: List[str]) -> str:
        """
        Merge multiple narrative sections into one coherent narrative.
        
        Args:
            question: Original user question
            narratives: List of narrative strings to merge
        
        Returns:
            Merged narrative string
        """
        if len(narratives) == 1:
            return narratives[0]
        
        # Import here to avoid circular dependency
        from .prompts import build_merge_prompt
        
        # Build merge prompt
        merge_prompt = build_merge_prompt(question, narratives)
        
        # Call LLM to merge
        try:
            return self.llm.call_api(merge_prompt)
        except Exception as e:
            print(f"  [WARNING] Merge failed: {e}")
            # Fallback: just concatenate
            return "\n\n---\n\n".join(narratives)



