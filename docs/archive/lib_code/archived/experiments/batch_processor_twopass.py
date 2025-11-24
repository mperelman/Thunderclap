"""
Two-Pass Batch Processor
=========================
Pass 1: Extract structured data from chunks (parallelizable)
Pass 2: Synthesize into coherent narrative with full Thunderclap framework
"""

import time
from typing import List, Tuple
from .config import BATCH_SIZE_SMALL, PAUSE_TIME_SMALL
from .prompts_twopass import build_extraction_prompt, build_synthesis_prompt, parse_extraction_json


class TwoPassBatchProcessor:
    """
    Two-pass processing for high-quality narratives:
    1. Extract structured data from all chunks
    2. Synthesize into coherent narrative
    """
    
    def __init__(self, llm_generator):
        """
        Initialize two-pass processor.
        
        Args:
            llm_generator: LLMAnswerGenerator instance
        """
        self.llm = llm_generator
    
    def process_two_pass(
        self,
        question: str,
        chunks: List[Tuple]
    ) -> str:
        """
        Process chunks using two-pass approach.
        
        Args:
            question: User's question
            chunks: List of (chunk_text, metadata) tuples
        
        Returns:
            Generated narrative following full Thunderclap framework
        """
        print("\n" + "="*70)
        print("TWO-PASS NARRATIVE GENERATION")
        print("="*70)
        
        # PASS 1: Extract structured data
        print("\n[PASS 1] Extracting structured data from chunks...")
        extracted_data = self._extract_structured_data(question, chunks)
        
        if not extracted_data:
            print("  [ERROR] No data extracted from chunks")
            return "Unable to generate narrative - no relevant data found."
        
        # Count relevant chunks
        relevant_count = sum(1 for d in extracted_data.values() if d.get('relevant', False))
        print(f"  [OK] Extracted data from {relevant_count}/{len(chunks)} relevant chunks")
        
        # PASS 2: Synthesize narrative
        print("\n[PASS 2] Synthesizing narrative with Thunderclap framework...")
        narrative = self._synthesize_narrative(question, extracted_data)
        
        print("  [OK] Narrative generation complete")
        print("="*70 + "\n")
        
        return narrative
    
    def _extract_structured_data(
        self,
        question: str,
        chunks: List[Tuple]
    ) -> dict:
        """
        Pass 1: Extract structured data from chunks.
        
        Processes in batches to handle many chunks efficiently.
        """
        all_extracted = {}
        
        # Process in batches (keep smaller to avoid JSON truncation)
        batch_size = 15  # Reduced to ensure complete JSON responses
        total_batches = (len(chunks) + batch_size - 1) // batch_size
        
        if total_batches > 1:
            print(f"  Processing {len(chunks)} chunks in {total_batches} extraction batches...")
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            if total_batches > 1:
                print(f"    [EXTRACT {batch_num}/{total_batches}] Processing {len(batch)} chunks...")
            
            # Build extraction prompt
            prompt = build_extraction_prompt(question, batch)
            
            # Call LLM
            response = self.llm.call_api(prompt)
            
            # Parse JSON response
            batch_data = parse_extraction_json(response)
            
            # Validate batch_data is a dict before updating
            if isinstance(batch_data, dict):
                all_extracted.update(batch_data)
            else:
                print(f"    [ERROR] Invalid JSON format in batch {batch_num}, skipping...")
            
            # Pause between batches (except last)
            if i + batch_size < len(chunks) and total_batches > 1:
                print(f"    [WAIT] Pausing {PAUSE_TIME_SMALL} seconds...")
                time.sleep(PAUSE_TIME_SMALL)
        
        return all_extracted
    
    def _synthesize_narrative(
        self,
        question: str,
        extracted_data: dict
    ) -> str:
        """
        Pass 2: Synthesize extracted data into coherent narrative.
        
        Uses full Thunderclap framework for high-quality output.
        """
        # Build synthesis prompt with all extracted data
        prompt = build_synthesis_prompt(question, extracted_data)
        
        # Call LLM for final synthesis
        narrative = self.llm.call_api(prompt)
        
        return narrative


def create_two_pass_processor(llm_generator):
    """Factory function to create two-pass processor."""
    return TwoPassBatchProcessor(llm_generator)

