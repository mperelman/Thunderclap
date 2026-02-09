"""
Parallel Batch Processor - Centralized parallel LLM processing
===============================================================
Handles all parallel batch processing with key rotation and rate limiting.
This is the SINGLE source of truth for parallel batch processing logic.
"""
import asyncio
from typing import List, Tuple, Callable, Optional

# Constants
MAX_CONCURRENT_REQUESTS = 10  # Max concurrent API calls (Gemini allows 15 RPM)
DEFAULT_BATCH_SIZE = 20  # Default chunks per batch
DEFAULT_BATCH_DELAY = 0.5  # Delay between concurrent batches (seconds)


async def process_batches_parallel(
    question: str,
    chunks: List[Tuple],
    llm_generator,
    semaphore: asyncio.Semaphore,
    batch_size: int = DEFAULT_BATCH_SIZE,
    batch_delay: float = DEFAULT_BATCH_DELAY,
    context_name: str = "batch"
) -> str:
    """
    Process chunks in parallel batches with automatic key rotation.
    
    This is the centralized function for all parallel batch processing.
    Each batch automatically gets a different API key via the key manager.
    
    Args:
        question: User's question
        chunks: List of (text, metadata) tuples to process
        llm_generator: LLMAnswerGenerator instance (has key manager)
        semaphore: Asyncio semaphore for rate limiting
        batch_size: Number of chunks per batch (default: 20)
        batch_delay: Delay between concurrent batches in seconds (default: 0.5)
        context_name: Name for logging context (e.g., "period", "region")
    
    Returns:
        Combined narrative from all batches
    """
    if not chunks:
        return ""
    
    total_batches = (len(chunks) + batch_size - 1) // batch_size
    
    if total_batches == 1:
        # Single batch - no need for parallel processing
        return await llm_generator.generate_answer_async(question, chunks)
    
    print(f"    Batching {len(chunks)} chunks into {total_batches} sub-batches (concurrent)...")
    
    # Create all batch tasks
    batch_tasks = _create_batch_tasks(
        question=question,
        chunks=chunks,
        batch_size=batch_size,
        total_batches=total_batches,
        llm_generator=llm_generator,
        semaphore=semaphore,
        batch_delay=batch_delay,
        context_name=context_name
    )
    
    # Process all batches concurrently
    narratives = await asyncio.gather(*batch_tasks)
    
    # Combine batches
    if len(narratives) == 1:
        return narratives[0]
    
    return await _merge_batch_narratives(narratives, question, context_name, llm_generator)


def _create_batch_tasks(
    question: str,
    chunks: List[Tuple],
    batch_size: int,
    total_batches: int,
    llm_generator,
    semaphore: asyncio.Semaphore,
    batch_delay: float,
    context_name: str
) -> List:
    """
    Create async tasks for processing batches in parallel.
    
    Args:
        question: User's question
        chunks: List of chunks to process
        batch_size: Chunks per batch
        total_batches: Total number of batches
        llm_generator: LLMAnswerGenerator instance
        semaphore: Rate limiting semaphore
        batch_delay: Delay between batches
        context_name: Context for logging
    
    Returns:
        List of async task coroutines
    """
    batch_tasks = []
    
    for j in range(0, len(chunks), batch_size):
        batch = chunks[j:j + batch_size]
        batch_num = j // batch_size + 1
        
        # Create async task with rate limiting
        # Each batch automatically gets a different key via key manager rotation
        async def process_batch_with_limit(b=batch, bn=batch_num):
            async with semaphore:
                print(f"      [{bn}/{total_batches}] Processing {len(b)} chunks...")
                # Add small delay between batches to respect rate limits
                if bn > 1:
                    await asyncio.sleep(batch_delay)
                result = await llm_generator.generate_answer_async(question, b)
                print(f"      [{bn}/{total_batches}] Done")
                return result
        
        batch_tasks.append(process_batch_with_limit())
    
    return batch_tasks


async def _merge_batch_narratives(
    narratives: List[str],
    question: str,
    context_name: str,
    llm_generator
) -> str:
    """
    Merge multiple batch narratives into a single coherent narrative via LLM.
    
    Args:
        narratives: List of narrative strings from batches
        question: Original question
        context_name: Context name for merge prompt
        llm_generator: LLMAnswerGenerator instance for API call
    
    Returns:
        Merged narrative string
    """
    if len(narratives) == 1:
        return narratives[0]
    
    print(f"    Merging {len(narratives)} sub-batches for {context_name}...")
    
    combined_text = "\n\n---\n\n".join(narratives)
    merge_prompt = f"""Combine these {len(narratives)} sections about {question} in {context_name} into ONE coherent narrative.

{combined_text}

Instructions:
- Remove duplicate information
- Maintain chronological flow
- Ensure smooth transitions between sections
- Keep all important details
- Write as a single, unified narrative

Combined narrative:"""
    
    return await llm_generator.call_api_async(merge_prompt)
