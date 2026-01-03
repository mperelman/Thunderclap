"""
Index Builder - Builds indices from documents with smart term grouping.
"""
import json
import re
from tqdm import tqdm
from .config import INDICES_FILE, MIN_TERM_FREQUENCY, CHUNK_SIZE, CHUNK_OVERLAP, DATA_DIR
from .acronyms import ACRONYM_TERMS, ACRONYM_EXPANSIONS
from .term_utils import canonicalize_term, strip_tags
from .constants import (
    LAW_YEAR_PREFIX_EXPANSIONS, 
    STOP_WORDS, 
    GENERIC_WORDS_TO_EXCLUDE,
    GENERIC_NOT_SURNAMES,
    COMMON_FIRST_NAMES,
    GENERIC_PHRASES_TO_EXCLUDE
)
from .text_utils import split_into_sentences, extract_phrases
import os
import time
from collections import defaultdict


def split_into_chunks(text: str, chunk_size: int = None, overlap: int = None) -> list:
    """
    Split text into overlapping chunks.
    
    Args:
        text: Text to split
        chunk_size: Words per chunk (defaults to CHUNK_SIZE from config)
        overlap: Overlapping words between chunks (defaults to CHUNK_OVERLAP from config)
    
    Returns:
        List of chunk strings
    """
    chunk_size = chunk_size or CHUNK_SIZE
    overlap = overlap or CHUNK_OVERLAP
    
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    
    return chunks


# Term groupings - Hierarchical structure (general to specific)
# Principle: All Quakers are Protestant, All Sephardim are Jewish (but not vice versa)
# Documents use both general ("Jewish Sassoon") and specific ("Sephardi Sassoon") - both valid
# Note: Kinlinks muddle separation - families can have multiple identities and act as bridges
TERM_GROUPS = {
    # Christian hierarchy (general -> specific)
    'christian': ['christian', 'christians', 'gentile', 'gentiles'],  # Most general
    'protestant': ['protestant', 'protestants'],  # General Protestant (includes specific below)
    'calvinist': ['calvinist', 'calvinists'],  # Specific: Reformed tradition
    'presbyterian': ['presbyterian', 'presbyterians'],  # Specific: Scotland/Ireland (Protestant)
    'quaker': ['quaker', 'quakers'],  # Specific: British colonies/West Indies/Pennsylvania
    'huguenot': ['huguenot', 'huguenots'],  # Specific: spread from France
    'mennonite': ['mennonite', 'mennonites'],  # Specific: Holland/Dutch/Amsterdam
    'puritan': ['puritan', 'puritans'],  # Specific: New England
    'boston brahmin': ['boston brahmin', 'boston brahmins'],  # Very specific: Puritan elite subset
    'knickerbocker': ['knickerbocker', 'knickerbockers'],  # Specific: New York Protestant elite
    'catholic': ['catholic', 'catholics'],  # Includes Irish Catholic (separate from Presbyterian Irish)
    'catholic irish': ['catholic irish', 'irish catholic'],  # Specific: Irish Catholics
    'orthodox': ['orthodox', 'eastern orthodox', 'greek orthodox'],  # Eastern Orthodox
    
    # Jewish hierarchy (general -> specific)
    'jewish': ['jew', 'jews', 'jewish'],  # General (includes all Jewish subgroups)
    'sephardi': ['sephardi', 'sephardim', 'sephardic'],  # Specific: Spain/Portugal diaspora
    'ashkenazi': ['ashkenazi', 'ashkenazim', 'ashkenazic'],  # Specific: Poland/Germany
    'court jew': ['court jew', 'court jews'],  # Specific: political elite
    
    # Other religious/ethnic groups
    'muslim': ['muslim', 'muslims', 'islam', 'islamic', 'sunni', 'shia', 'shiite'],
    'palestinian': ['palestinian', 'palestine'],  # Palestinian identity (often diaspora)
    'parsee': ['parsee', 'parsees', 'parsi', 'parsis', 'zoroastrian', 'zoroastrians'],
    'hindu': ['hindu', 'hindus', 'bania', 'banias', 'kayastha', 'kayasthas', 
              'kshatriya', 'vaishya', 'maratha', 'marathas', 'seth', 'seths', 
              'savakar', 'savakars', 'jain', 'jains'],
    'brahmin': ['brahmin', 'brahmins'],  # Ambiguous: Hindu caste OR Boston Brahmin elite
    'greek': ['greek', 'greeks'],
    'armenian': ['armenian', 'armenians'],
    'lebanese': ['lebanese', 'lebanon', 'maronite', 'maronites', 'phoenician'],  # Lebanese banking families
    
    # Asian banking families (can be Christian, Buddhist, or other - context determines)
    'overseas chinese': ['overseas chinese', 'sino-thai', 'chinese thai'],
    'chaebol': ['chaebol', 'chaebols'],  # Korean family conglomerates
    'zaibatsu': ['zaibatsu'],  # Japanese family conglomerates
    
    # Racial/ethnic groups
    'black': ['black', 'blacks', 'african american', 'african americans',
              'hausa', 'yoruba', 'igbo', 'fulani', 'akan', 'zulu',  # African ethnic groups
              'nigerian', 'ghanaian', 'kenyan', 'south african'],
    'women': ['woman', 'women', 'female', 'queen', 'princess', 'lady'],  # Include royal titles
    
    # LGBTQ+ identities (keyword-based, not individual tagging - see docs/archive/LGBT_LATINO_APPROACH.md)
    'gay': ['gay', 'gays', 'homosexual', 'homosexuals', 'homosexuality'],
    'lgbt': ['lgbt', 'lgbtq', 'lgbtq+', 'lesbian', 'lesbians', 'bisexual', 'bisexuals', 
             'queer', 'transgender', 'trans', 'lavender marriage', 'lavender marriages'],
    
    # Indigenous/Native American/Pre-colonial Americas
    'native american': ['native american', 'american indian', 'indigenous', 'tribal', 
                        'lumbee', 'cherokee', 'navajo', 'sioux', 'apache'],
    'mesoamerican': ['mesoamerican', 'maya', 'aztec', 'inca', 'olmec', 
                     'zapotec', 'mixtec', 'toltec'],  # Pre-colonial civilizations
    'mestizo': ['mestizo', 'mestizos', 'mixed-race'],  # Colonial mixed-race merchants
    
    # Wars
    'wwi': ['wwi', 'world war i', 'first world war'],
    'wwii': ['wwii', 'world war ii', 'second world war'],
}

ACRONYM_PATTERNS = {
    term: re.compile(rf'\b{re.escape(term)}\b')
    for term in ACRONYM_TERMS
}

def extract_acronyms_from_documents(chunks):
    """
    Extract acronym definitions from documents dynamically.
    Looks for patterns like:
    - "SEC (Securities and Exchange Commission)" - Acronym (Full Name)
    - "Securities and Exchange Commission (SEC)" - Full Name (Acronym)
    - "SEC, or Securities and Exchange Commission" - Acronym, or Full Name
    - "XXX ("X")" - Full term/phrase with quoted acronym in parentheses
    
    Returns:
        dict: {acronym: full_name} mapping
    """
    acronym_map = {}
    # Pattern 1: Acronym (Full Name) - e.g., "SEC (Securities and Exchange Commission)"
    pattern1 = re.compile(r'\b([A-Z]{2,})\s*\(([^)]{5,50}?)\)', re.IGNORECASE)
    # Pattern 2: Full Name (Acronym) - e.g., "Securities and Exchange Commission (SEC)"
    pattern2 = re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){2,})\s*\(([A-Z]{2,})\)', re.IGNORECASE)
    # Pattern 3: Acronym, or Full Name - e.g., "SEC, or Securities and Exchange Commission"
    pattern3 = re.compile(r'\b([A-Z]{2,})\s*,\s*or\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', re.IGNORECASE)
    # Pattern 4: Full term/phrase ("Acronym") - e.g., "XXX ("X")" - quoted acronym in parentheses
    # Handle both regular quotes and special quote characters (curly quotes that may appear as � or �)
    pattern4 = re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*\(["\u201C\u201D\u2018\u2019\u00AB\u00BB]([A-Z]{2,})["\u201C\u201D\u2018\u2019\u00AB\u00BB]\)', re.IGNORECASE)
    
    for chunk in chunks:
        visible = strip_tags(chunk)
        
        # Pattern 1: Acronym (Full Name)
        for match in pattern1.finditer(visible):
            acronym = match.group(1).upper()
            full_name = match.group(2).strip()
            # Skip if it looks like Pattern 4 (quoted acronym) - Pattern 4 will handle it
            if full_name.startswith('"') and full_name.endswith('"'):
                continue
            # Validate: acronym should be 2-10 chars, full name should be reasonable length
            if 2 <= len(acronym) <= 10 and 5 <= len(full_name) <= 100:
                # Only add if not already found or if this is a better match
                if acronym not in acronym_map or len(full_name) < len(acronym_map[acronym]):
                    acronym_map[acronym] = full_name
        
        # Pattern 2: Full Name (Acronym)
        for match in pattern2.finditer(visible):
            full_name = match.group(1).strip()
            acronym = match.group(2).upper()
            if 2 <= len(acronym) <= 10 and 5 <= len(full_name) <= 100:
                if acronym not in acronym_map or len(full_name) < len(acronym_map[acronym]):
                    acronym_map[acronym] = full_name
        
        # Pattern 3: Acronym, or Full Name
        for match in pattern3.finditer(visible):
            acronym = match.group(1).upper()
            full_name = match.group(2).strip()
            if 2 <= len(acronym) <= 10 and 5 <= len(full_name) <= 100:
                if acronym not in acronym_map or len(full_name) < len(acronym_map[acronym]):
                    acronym_map[acronym] = full_name
        
        # Pattern 4: Full term/phrase ("Acronym") - e.g., "XXX ("X")"
        for match in pattern4.finditer(visible):
            full_name = match.group(1).strip()
            acronym = match.group(2).upper()  # Already extracted without quotes
            if 2 <= len(acronym) <= 10 and 5 <= len(full_name) <= 100:
                if acronym not in acronym_map or len(full_name) < len(acronym_map[acronym]):
                    acronym_map[acronym] = full_name
    
    return acronym_map

def deduplicate_chunks(chunks, chunk_ids, chunk_metadatas):
    """
    Deduplicate overlapping chunks before indexing.
    Merges overlapping chunks within the same document to create unions.
    
    Args:
        chunks: List of chunk texts
        chunk_ids: List of chunk IDs
        chunk_metadatas: List of chunk metadata dicts (must have 'filename' key)
    
    Returns:
        Tuple of (deduplicated_chunks, deduplicated_chunk_ids, deduplicated_chunk_metadatas, id_mapping)
        where id_mapping maps old chunk IDs to new merged chunk IDs
    """
    if not chunks:
        return chunks, chunk_ids, chunk_metadatas, {}
    
    print("Deduplicating overlapping chunks...")
    
    # Group chunks by document (filename)
    chunks_by_doc = defaultdict(list)
    for i, (chunk_id, chunk_text, metadata) in enumerate(zip(chunk_ids, chunks, chunk_metadatas)):
        filename = metadata.get('filename', 'unknown') if metadata else 'unknown'
        chunks_by_doc[filename].append((i, chunk_id, chunk_text, metadata))
    
    # Process each document
    deduplicated_chunks = []
    deduplicated_chunk_ids = []
    deduplicated_chunk_metadatas = []
    id_mapping = {}  # old_id -> new_id
    
    total_original = len(chunks)
    total_merged = 0
    
    # Use shared split_into_sentences from text_utils.py
    
    def merge_overlapping_chunks(chunk1: str, chunk2: str, overlap_threshold: int = None) -> tuple:
        """Merge two overlapping chunks into a union, removing duplicate sentences. Returns (merged_text, did_merge)."""
        overlap_threshold = overlap_threshold or CHUNK_OVERLAP
        
        # FIRST: Check for actual duplicate content (sentence-level)
        # This catches real duplicates, not just expected overlaps
        sentences1 = split_into_sentences(chunk1)
        sentences2 = split_into_sentences(chunk2)
        normalized1 = {s.lower().strip(): s for s in sentences1}
        normalized2 = {s.lower().strip(): s for s in sentences2}
        duplicates = set(normalized1.keys()) & set(normalized2.keys())
        
        # If chunks share significant duplicate sentences (>30% overlap), merge them
        if duplicates:
            overlap_ratio = len(duplicates) / max(len(normalized1), len(normalized2)) if max(len(normalized1), len(normalized2)) > 0 else 0
            
            # Only merge if >30% sentence overlap (actual duplication)
            if overlap_ratio > 0.3:
                # Merge: keep all unique sentences
                merged_sentences = []
                seen = set()
                for s in sentences1:
                    normalized = s.lower().strip()
                    if normalized not in seen:
                        merged_sentences.append(s)
                        seen.add(normalized)
                for s in sentences2:
                    normalized = s.lower().strip()
                    if normalized not in seen:
                        merged_sentences.append(s)
                        seen.add(normalized)
                
                merged = " ".join(merged_sentences)
                return (merged, True)
        
        # SECOND: Check for boundary overlap (sequential chunks)
        # But only merge if there's MORE than expected overlap (actual duplication)
        words1 = chunk1.split()
        words2 = chunk2.split()
        
        # Case 1: End of chunk1 overlaps with start of chunk2
        if len(words1) >= overlap_threshold and len(words2) >= overlap_threshold:
            end_words1 = words1[-overlap_threshold:]
            start_words2 = words2[:overlap_threshold]
            
            if end_words1 == start_words2:
                # Check if overlap is MORE than expected (duplicate content beyond boundary)
                # Calculate sentence overlap ratio
                overlap_ratio = len(duplicates) / max(len(normalized1), len(normalized2)) if max(len(normalized1), len(normalized2)) > 0 else 0
                
                # If chunks share >50% content, merge them
                if overlap_ratio > 0.5:
                    merged_sentences = []
                    seen = set()
                    for s in sentences1:
                        normalized = s.lower().strip()
                        if normalized not in seen:
                            merged_sentences.append(s)
                            seen.add(normalized)
                    for s in sentences2:
                        normalized = s.lower().strip()
                        if normalized not in seen:
                            merged_sentences.append(s)
                            seen.add(normalized)
                    
                    merged = " ".join(merged_sentences)
                    return (merged, True)
        
        # Case 2: Start of chunk1 overlaps with end of chunk2 (reverse order)
        if len(words1) >= overlap_threshold and len(words2) >= overlap_threshold:
            start_words1 = words1[:overlap_threshold]
            end_words2 = words2[-overlap_threshold:]
            
            if start_words1 == end_words2:
                # Merge with sentence-level deduplication
                sentences1 = split_into_sentences(chunk1)
                sentences2 = split_into_sentences(chunk2)
                normalized1 = {s.lower().strip(): s for s in sentences1}
                normalized2 = {s.lower().strip(): s for s in sentences2}
                
                # Merge: keep all unique sentences (chunk2 first, then chunk1)
                merged_sentences = []
                seen = set()
                for s in sentences2:
                    normalized = s.lower().strip()
                    if normalized not in seen:
                        merged_sentences.append(s)
                        seen.add(normalized)
                for s in sentences1:
                    normalized = s.lower().strip()
                    if normalized not in seen:
                        merged_sentences.append(s)
                        seen.add(normalized)
                
                merged = " ".join(merged_sentences)
                return (merged, True)
        
        # Case 3: Partial boundary overlap - check for smaller overlaps
        min_overlap = max(50, overlap_threshold // 2)
        for n in range(overlap_threshold, min_overlap - 1, -10):
            if len(words1) < n or len(words2) < n:
                continue
            
            end_words1 = words1[-n:]
            start_words2 = words2[:n]
            
            if end_words1 == start_words2:
                # Merge with sentence-level deduplication
                sentences1 = split_into_sentences(chunk1)
                sentences2 = split_into_sentences(chunk2)
                normalized1 = {s.lower().strip(): s for s in sentences1}
                normalized2 = {s.lower().strip(): s for s in sentences2}
                
                merged_sentences = []
                seen = set()
                for s in sentences1:
                    normalized = s.lower().strip()
                    if normalized not in seen:
                        merged_sentences.append(s)
                        seen.add(normalized)
                for s in sentences2:
                    normalized = s.lower().strip()
                    if normalized not in seen:
                        merged_sentences.append(s)
                        seen.add(normalized)
                
                merged = " ".join(merged_sentences)
                return (merged, True)
        
        # Case 4: One chunk completely contained in another (rare)
        if chunk2.lower().strip() in chunk1.lower() and len(chunk2) < len(chunk1):
            return (chunk1, True)
        
        if chunk1.lower().strip() in chunk2.lower() and len(chunk1) < len(chunk2):
            return (chunk2, True)
        
        return (None, False)
    
    for filename, doc_chunks in tqdm(chunks_by_doc.items(), desc="Deduplicating"):
        # Sort chunks by their original order (preserve document order)
        doc_chunks_sorted = sorted(doc_chunks, key=lambda x: x[0])
        
        # Process chunks sequentially, merging ONLY adjacent/overlapping chunks
        merged_doc_chunks = []
        used_indices = set()
        
        i = 0
        while i < len(doc_chunks_sorted):
            if i in used_indices:
                i += 1
                continue
            
            orig_idx, chunk_id, chunk_text, metadata = doc_chunks_sorted[i]
            
            # Try to merge with NEXT chunk only (adjacent merging)
            # LIMIT: Only merge a few chunks at a time to prevent creating massive chunks
            merged_text = chunk_text
            merged_indices = {i}
            merged_id = chunk_id
            j = i + 1
            max_merge_count = 3  # Maximum number of chunks to merge together
            
            # Only merge with immediately adjacent chunks that overlap
            while j < len(doc_chunks_sorted) and len(merged_indices) < max_merge_count:
                if j in used_indices:
                    j += 1
                    continue
                
                orig_idx2, chunk_id2, chunk_text2, metadata2 = doc_chunks_sorted[j]
                
                # Check for overlap (only merges if there's boundary overlap)
                merged_result, did_merge = merge_overlapping_chunks(merged_text, chunk_text2)
                
                if did_merge:
                    # CRITICAL: Don't merge chunks that just have the expected overlap from chunking
                    # Only merge if there's ACTUAL duplicate content beyond the expected overlap
                    words1 = merged_text.split()
                    words2 = chunk_text2.split()
                    overlap_threshold = CHUNK_OVERLAP
                    
                    # Check if this is just the expected overlap from chunking (normal sequential chunks)
                    if len(words1) >= overlap_threshold and len(words2) >= overlap_threshold:
                        end_words1 = words1[-overlap_threshold:]
                        start_words2 = words2[:overlap_threshold]
                        if end_words1 == start_words2:
                            # This is just the expected overlap from chunking - DON'T merge
                            # These are normal sequential chunks, not duplicates
                            break
                    
                    # Check for actual duplicate content (more than expected overlap)
                    # If chunks share >50% of their content, they're likely duplicates
                    sentences1 = split_into_sentences(merged_text)
                    sentences2 = split_into_sentences(chunk_text2)
                    normalized1 = {s.lower().strip() for s in sentences1}
                    normalized2 = {s.lower().strip() for s in sentences2}
                    overlap_ratio = len(normalized1 & normalized2) / max(len(normalized1), len(normalized2)) if max(len(normalized1), len(normalized2)) > 0 else 0
                    
                    # Only merge if >50% sentence overlap (actual duplication, not just boundary overlap)
                    if overlap_ratio < 0.5:
                        break  # Not enough duplicate content
                    
                    merged_text = merged_result
                    merged_indices.add(j)
                    used_indices.add(j)
                    id_mapping[chunk_id2] = merged_id
                    total_merged += 1
                    j += 1  # Continue to next chunk
                else:
                    # No boundary overlap - stop merging
                    break
            
            if len(merged_indices) > 1:
                print(f"    Merged {len(merged_indices)} chunks from {filename}")
            
            merged_doc_chunks.append((merged_id, merged_text, metadata))
            used_indices.add(i)
            i = j  # Move to next unmerged chunk
        
        # Add merged chunks to output
        for chunk_id, chunk_text, metadata in merged_doc_chunks:
            deduplicated_chunks.append(chunk_text)
            deduplicated_chunk_ids.append(chunk_id)
            deduplicated_chunk_metadatas.append(metadata)
    
    reduction = total_original - len(deduplicated_chunks)
    print(f"[OK] Deduplicated: {total_original} -> {len(deduplicated_chunks)} chunks ({reduction} merged, {100*reduction/total_original:.1f}% reduction)\n")
    
    return deduplicated_chunks, deduplicated_chunk_ids, deduplicated_chunk_metadatas, id_mapping


def filter_terms_with_llm(term_counts, term_to_chunks, all_acronyms, batch_size=500):
    """
    Filter indexed terms using LLM to remove generic/common terms.
    This replaces hardcoded exclusion lists with intelligent LLM-based filtering.
    
    Args:
        term_counts: Dict of {term: count}
        term_to_chunks: Dict of {term: [chunk_ids]}
        all_acronyms: Dict of acronyms to keep (auto-kept without LLM)
        batch_size: Number of terms to process per LLM call
    
    Returns:
        Tuple of (filtered_term_counts, filtered_term_to_chunks)
    """
    try:
        from .llm import LLMAnswerGenerator
    except ImportError:
        print("  [WARN] LLM module not available, skipping LLM filtering")
        return term_counts, term_to_chunks
    
    terms = list(term_counts.keys())
    if not terms:
        return term_counts, term_to_chunks
    
    print(f"  Total terms to filter: {len(terms)}")
    
    # Test LLM initialization
    try:
        test_llm = LLMAnswerGenerator()
        if not test_llm.client:
            print("  [WARN] LLM initialization failed, skipping LLM filtering")
            return term_counts, term_to_chunks
    except Exception as e:
        print(f"  [WARN] LLM initialization failed: {e}, skipping LLM filtering")
        return term_counts, term_to_chunks
    
    # OPTIMIZATION: Pre-filter using hardcoded lists BEFORE sending to LLM
    # This reduces API calls significantly
    from .constants import GENERIC_WORDS_TO_EXCLUDE, GENERIC_PHRASES_TO_EXCLUDE
    
    # Pre-filter: Remove terms that are definitely generic (no LLM needed)
    pre_filtered_terms = []
    pre_removed = 0
    for term in terms:
        term_lower = term.lower()
        # Keep if NOT in exclusion lists
        if term_lower not in GENERIC_WORDS_TO_EXCLUDE and term_lower not in GENERIC_PHRASES_TO_EXCLUDE:
            pre_filtered_terms.append(term)
        else:
            pre_removed += 1
    
    print(f"  Pre-filtered: {pre_removed:,} generic terms removed (no LLM needed)")
    print(f"  Remaining terms to LLM filter: {len(pre_filtered_terms):,}")
    
    filtered_terms = []
    num_batches = (len(pre_filtered_terms) + batch_size - 1) // batch_size
    
    print(f"  Processing {num_batches} batches of {batch_size} terms each")
    print(f"  Rate limit: 15 requests/minute (4 seconds between batches)")
    print()
    
    # Create progress bar with proper configuration
    # Always show progress bar - it will adapt to terminal or show as text if redirected
    import sys
    progress_bar = tqdm(
        range(0, len(terms), batch_size), 
        desc="LLM Filtering", 
        unit="batch", 
        dynamic_ncols=True,
        mininterval=0.1,  # Update frequently
        maxinterval=1.0,  # But not too frequently
        file=sys.stdout  # Explicitly use stdout
    )
    
    for i in range(0, len(pre_filtered_terms), batch_size):
        batch = pre_filtered_terms[i:i+batch_size]
        batch_num = i//batch_size + 1
        
        # Pre-filter: Keep ALL acronyms (3+ caps) without sending to LLM
        acronyms_in_batch = [t for t in batch if t.isupper() and len(t) >= 3]
        non_acronyms = [t for t in batch if not (t.isupper() and len(t) >= 3)]
        
        # Add acronyms directly to filtered list (don't send to LLM)
        filtered_terms.extend(acronyms_in_batch)
        
        # If entire batch is acronyms, skip LLM call
        if not non_acronyms:
            progress_bar.set_postfix({
                'status': f'{len(acronyms_in_batch)} acronyms auto-kept',
                'total_kept': len(filtered_terms)
            })
            progress_bar.update(1)
            continue
        
        # Wait BEFORE making request (except first batch) to respect 15 RPM limit
        if i > 0:
            time.sleep(4)  # 4 seconds = 15 requests/minute (optimized)
        
        # Create a FRESH LLM client for each batch
        try:
            llm = LLMAnswerGenerator()
            
            # OPTIMIZED: Shorter, more focused prompt
            # OPTIMIZED: Limit to 400 terms per batch to avoid token limits
            terms_to_send = non_acronyms[:400]
            
            prompt = f"""Filter terms for hyperlinking. Return JSON array of terms to KEEP.

KEEP: Multi-word entities, rare surnames (Rothschild/Sassoon), identity terms (Jewish/Quaker), law codes (BA1933).
EXCLUDE: Common first names, family words, generic titles, common places, function words.

Terms: {json.dumps(terms_to_send)}

Output: JSON array only, no explanations."""
            
            response_text = llm.call_api(prompt).strip()
            
            # Extract JSON from response
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()
            
            kept_terms = json.loads(response_text)
            filtered_terms.extend(kept_terms)
            
            # Update progress bar
            kept_pct = (len(kept_terms) / len(batch)) * 100
            removed_count = len(batch) - len(kept_terms)
            progress_bar.set_postfix({
                'kept': f'{len(kept_terms)}/{len(batch)} ({kept_pct:.0f}%)',
                'removed': removed_count,
                'total_kept': len(filtered_terms)
            })
            progress_bar.update(1)  # Explicitly update progress
        
        except Exception as e:
            error_msg = str(e)
            # Check if it's a quota/rate limit error
            is_quota_error = '429' in error_msg or 'quota' in error_msg.lower() or 'rate limit' in error_msg.lower()
            
            if is_quota_error:
                # Quota exceeded - skip remaining batches gracefully
                print(f"\n  [WARN] API quota exceeded. Skipping remaining {num_batches - batch_num} batches.")
                print(f"  [INFO] Keeping {len(filtered_terms):,} terms filtered so far.")
                print(f"  [INFO] {len(pre_filtered_terms) - len(filtered_terms):,} terms not filtered (will use hardcoded filters)")
                # Add remaining terms that weren't filtered (they'll be filtered by hardcoded lists later)
                remaining_terms = pre_filtered_terms[i:]
                filtered_terms.extend([t for t in remaining_terms if t.isupper() and len(t) >= 3])  # Keep acronyms
                break  # Stop processing, don't retry
            else:
                # Other error - keep this batch and continue
                progress_bar.set_postfix({
                    'status': 'ERROR - keeping batch',
                    'total_kept': len(filtered_terms)
                })
                filtered_terms.extend(batch)
                progress_bar.update(1)
                time.sleep(10)  # Wait after error, but shorter
    
    # Close progress bar
    progress_bar.close()
    
    # Create filtered dictionaries
    filtered_term_set = set(filtered_terms)
    filtered_term_counts = {t: c for t, c in term_counts.items() if t in filtered_term_set}
    filtered_term_to_chunks = {t: ids for t, ids in term_to_chunks.items() if t in filtered_term_set}
    
    removed = len(term_counts) - len(filtered_term_counts)
    total_removed = pre_removed + removed
    print(f"  [OK] LLM filtering complete: {len(filtered_term_counts):,} terms kept, {total_removed:,} removed ({100*total_removed/len(term_counts):.1f}%)")
    print(f"       ({pre_removed:,} pre-filtered + {removed:,} LLM-filtered)")
    
    # Save filtered terms list for server.py to use
    try:
        filtered_terms_file = os.path.join(DATA_DIR, 'filtered_terms.json')
        with open(filtered_terms_file, 'w', encoding='utf-8') as f:
            json.dump(sorted(filtered_term_set), f, indent=2, ensure_ascii=False)
        print(f"  [OK] Saved filtered terms to {filtered_terms_file}")
    except Exception as e:
        print(f"  [WARN] Could not save filtered terms: {e}")
    
    return filtered_term_counts, filtered_term_to_chunks


def _index_significant_words_from_firm(firm_term: str, term_counts: dict, term_to_chunks: dict, chunk_id: str, generic_words: set):
    """
    Index significant words from a firm name separately.
    For example: "Chase NB" → also index "Chase"
                 "Goldman Sachs" → also index "Goldman" and "Sachs"
                 "Crédit Lyonnais" → also index "Crédit" and "Lyonnais"
    
    Args:
        firm_term: The complete firm name (e.g., "Chase NB", "Goldman Sachs")
        term_counts: Dictionary of term counts
        term_to_chunks: Dictionary mapping terms to chunk IDs
        chunk_id: Current chunk ID
        generic_words: Set of generic words to skip (from GENERIC_FIRM_WORDS)
    """
    from .constants import GENERIC_WORDS_TO_EXCLUDE
    
    # Split firm name into words
    words = firm_term.split()
    
    # For each word, check if it's significant and index it separately
    for word in words:
        word_lower = word.lower()
        
        # Skip if:
        # 1. Too short (< 4 characters)
        # 2. Generic firm word (bank, trust, nb, etc.)
        # 3. Generic word from exclusion list
        # 4. Common location words (unless it's a significant part of the name)
        if len(word) < 4:
            continue
        if word_lower in generic_words:
            continue
        if word_lower in GENERIC_WORDS_TO_EXCLUDE:
            continue
        
        # Index the word (preserve original capitalization)
        word_term = canonicalize_term(word)
        if word_term and word_term != firm_term:  # Don't duplicate if it's the same
            term_counts[word_term] = term_counts.get(word_term, 0) + 1
            if word_term not in term_to_chunks:
                term_to_chunks[word_term] = []
            term_to_chunks[word_term].append(chunk_id)


def build_indices(chunks, chunk_ids):
    # Define GENERIC_FIRM_WORDS at the top of the function (used throughout)
    GENERIC_FIRM_WORDS = {
        'bank', 'banks', 'trust', 'trusts', 'company', 'companies', 'co', 'corp', 'corporation',
        'inc', 'incorporated', 'ltd', 'limited', 'group', 'holding', 'holdings',
        'partners', 'partnership', 'associates', 'brothers', 'sons', 'son',
        'york', 'london', 'paris', 'berlin', 'vienna', 'amsterdam', 'brussels', 'geneva',
        'america', 'american', 'british', 'french', 'german', 'swiss', 'italian',
        'national', 'federal', 'state', 'central', 'commercial', 'investment', 'merchant',
        'private', 'public', 'royal', 'imperial', 'first', 'second', 'third', 'fourth',
        'savings', 'loan', 'credit', 'finance', 'financial', 'capital', 'equity',
        'securities', 'asset', 'assets', 'management', 'services', 'solutions'
    }
    """
    Build term→chunk_id indices with smart term grouping.
    """
    term_counts = {}
    term_to_chunks = {}
    entity_cooccurrence = {}
    chunk_entities = {}
    name_changes = {}
    
    print("Building indices...")
    
    # First pass: Extract acronyms from documents dynamically
    print("  Extracting acronyms from documents...")
    extracted_acronyms = extract_acronyms_from_documents(chunks)
    # Merge with hardcoded acronyms (hardcoded takes precedence if conflict)
    all_acronyms = {**extracted_acronyms, **ACRONYM_EXPANSIONS}
    print(f"  Found {len(extracted_acronyms)} acronyms in documents")
    if len(extracted_acronyms) > 0:
        print(f"  Sample extracted acronyms: {list(extracted_acronyms.items())[:5]}")
    print(f"  Total acronyms (including hardcoded): {len(all_acronyms)}")
    
    # Build patterns for all acronyms (extracted + hardcoded)
    all_acronym_patterns = {
        term: re.compile(rf'\b{re.escape(term)}\b')
        for term in all_acronyms.keys()
    }
    
    for chunk_id, chunk in tqdm(zip(chunk_ids, chunks), total=len(chunks), desc="Indexing"):
        chunk_lower = chunk.lower()
        chunk_entity_list = []
        
        # Detect name changes
        name_change_patterns = [
            r'([A-Z][a-z]+)\s+(?:changed|anglicized).*?name.*?to\s+([A-Z][a-z]+)',
            r'([A-Z][a-z]+).*?formerly.*?([A-Z][a-z]+)',
        ]
        for pattern in name_change_patterns:
            matches = re.findall(pattern, chunk)
            for old_name, new_name in matches:
                old_lower = old_name.lower()
                new_lower = new_name.lower()
                if 'née' not in chunk_lower and 'nee' not in chunk_lower:
                    if old_lower not in name_changes:
                        name_changes[old_lower] = set()
                    name_changes[old_lower].add(new_lower)
        
        # CRITICAL CHANGE: Only index IMPORTANT banking family surnames, not all surnames
        # Focus on key banking families from cousinhoods, not every person mentioned
        # Important banking family surnames (from cousinhoods and key banking history)
        IMPORTANT_BANKING_SURNAMES = {
            # Jewish banking families
            'rothschild', 'warburg', 'kuhn', 'loeb', 'schiff', 'seligman', 'lazard', 'goldschmidt',
            'mendes', 'sassoon', 'delbanco', 'oppenheim', 'wertheimer', 'goldman', 'sachs',
            'lehman', 'katz', 'katzenellenbogen', 'cohen', 'kagan', 'abrabanel', 'seneor',
            # Quaker banking families
            'barclay', 'bevan', 'tritton', 'lloyd',
            # Huguenot banking families
            'hope', 'mallet', 'thellusson',
            # Puritan/Boston Brahmin
            'morgan', 'cabot', 'lowell', 'forbes', 'perkins', 'higginson',
            # Knickerbocker (New York elite)
            'rensselaer', 'schuyler', 'schaack', 'roosevelt', 'livingston',
            # Protestant Cologne
            'stein', 'schaaffhausen',
            # Gentile British
            'baring', 'grenfell',
            # Armenian banking families
            'balian', 'dadian', 'gulbenkian',
            # Black banking families
            'brimmer', 'lewis', 'raines', 'ferguson', 'jordan', 'ogunlesi', 'cole', 'johnson',
            'parsons', 'wright', 'walker', 'perry', 'church', 'gaston', 'weston', 'turner',
            'dibble', 'vaughan',
            # Other important banking families
            'chase', 'rockefeller', 'vanderbilt', 'harriman', 'hill', 'gould', 'frick',
            'mellon', 'du pont', 'ford', 'astor', 'guggenheim'
        }
        
        # Extract surnames from proper names, but ONLY index if they're important banking families
        proper_names = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b', chunk)
        
        for full_name in proper_names:
            parts = full_name.split()
            surname_raw = parts[-1]  # Keep original capitalization
            surname = canonicalize_term(surname_raw)
            surname_lower = surname.lower()
            
            # CRITICAL: Only index if surname is an important banking family
            if surname_lower not in IMPORTANT_BANKING_SURNAMES:
                continue
            
            # Index surname (preserving capitalization)
            for target in filter(None, {surname_raw, surname}):
                term_counts[target] = term_counts.get(target, 0) + 1
                if target not in term_to_chunks:
                    term_to_chunks[target] = []
                term_to_chunks[target].append(chunk_id)
            chunk_entity_list.append(surname or surname_raw)
            
            # REMOVED: No longer indexing middle names (maiden names) - not needed for hyperlinking
        
        # Index identity terms directly from text (Jewish, female, widow, Black, etc.)
        # These are important searchable terms even without identity detector
        identity_terms = [
            # Religious
            r'\b(jewish|jew|jews|sephardi|sephardim|ashkenazi|ashkenazim|court\s+jew|court\s+jews|kohanim|katz)\b',
            r'\b(quaker|quakers|huguenot|huguenots|mennonite|mennonites|puritan|puritans|calvinist|presbyterian)\b',
            r'\b(muslim|muslims|islam|islamic|sunni|shia|shiite|alawite|druze|ismaili)\b',
            r'\b(maronite|maronites|coptic|greek\s+orthodox|orthodox)\b',
            r'\b(parsee|parsees|zoroastrian|hindu|brahmin|bania)\b',
            # Ethnic
            r'\b(armenian|armenians|greek|greeks|lebanese|syrian|syrians|palestinian|palestinians)\b',
            r'\b(basque|basques|hausa|yoruba|igbo|fulani|akan|zulu)\b',
            r'\b(scottish|scots|irish|welsh)\b',
            # Racial
            r'\b(black|african\s+american|african-american)\b',
            # Gender
            r'\b(female|woman|women|widow|widows|queen|princess|lady|heiress)\b',
            # Latino/Hispanic
            r'\b(latino|latina|latinos|latinas|hispanic|hispanics|mexican|cuban|puerto\s+rican)\b',
        ]
        
        visible = strip_tags(chunk)
        for pattern in identity_terms:
            matches = re.finditer(pattern, visible, re.IGNORECASE)
            for match in matches:
                # Preserve case but normalize spaces to underscores
                identity_term = match.group(1).replace(' ', '_')
                canonical = canonicalize_term(identity_term)
                target = canonical if canonical else identity_term
                term_counts[target] = term_counts.get(target, 0) + 1
                if target not in term_to_chunks:
                    term_to_chunks[target] = []
                term_to_chunks[target].append(chunk_id)
                # Also index with spaces (for natural search)
                space_version = target.replace('_', ' ')
                if space_version != target:
                    term_counts[space_version] = term_counts.get(space_version, 0) + 1
                    if space_version not in term_to_chunks:
                        term_to_chunks[space_version] = []
                    term_to_chunks[space_version].append(chunk_id)
        
        # Index firm names (italicized)
        # Pattern 1: Complete firm name in single <italic> tag: <italic>FirmName</italic>
        # Pattern 2a: <italic>First</italic> NB <italic>of</italic> <italic>Chicago</italic> (of italicized - most common)
        # Pattern 2b: <italic>First</italic> NB of <italic>Philadelphia</italic> (of not italicized)
        # Pattern 2c: <italic>First NB of Boston</italic> (entire phrase italicized)
        firm_pattern = re.compile(r'<italic>([^<]+?)</italic>', re.IGNORECASE)
        
        # Pattern 2a: <italic>Word</italic> NB <italic>of</italic> <italic>Location</italic> (of italicized - most common)
        # Pattern 2b: <italic>Word</italic> NB of <italic>Location</italic> (of not italicized)
        # Pattern 2c: <italic>Word</italic> NB (standalone, no location) - e.g., <italic>Park</italic> NB
        # Pattern 2d: <italic>Word</italic> IHC (Investment Holding Company)
        # Pattern 2e: <italic>Word</italic> PU (Public Utility)
        # Include possessive forms: <italic>First</italic> NB <italic>of</italic> <italic>Boston</italic>'s -> "first nb of boston"
        nb_pattern_italic_a = re.compile(r'<italic>([A-Z][a-z]+)</italic>\s+NB\s+<italic>of</italic>\s+<italic>([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)</italic>(?:\'s)?', re.IGNORECASE)
        nb_pattern_italic_b = re.compile(r'<italic>([A-Z][a-z]+)</italic>\s+NB\s+of\s+<italic>([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)</italic>(?:\'s)?', re.IGNORECASE)
        nb_pattern_standalone = re.compile(r'<italic>([A-Z][a-z]+)</italic>\s+(NB|IHC|PU|SB|HC|TC)(?:\'s)?(?=\s|[,.]|$)', re.IGNORECASE)  # Standalone abbreviations
        
        for pattern in [nb_pattern_italic_a, nb_pattern_italic_b]:
            for match in pattern.finditer(chunk):
                first_part = match.group(1).strip()
                location_part = match.group(2).strip()
                if len(first_part) < 50 and len(location_part) < 50:
                    # Canonicalize (preserves case)
                    first_term = canonicalize_term(first_part)
                    location_term = canonicalize_term(location_part)
                    
                    # CRITICAL: Index BOTH the firm name alone AND the complete firm name with location
                    # This allows "First National Bank" queries AND "First National Bank of Cleveland" queries
                    
                    # Index firm name alone (e.g., "First NB", "First National Bank")
                    firm_name = f"{first_term} NB"
                    term_counts[firm_name] = term_counts.get(firm_name, 0) + 1
                    if firm_name not in term_to_chunks:
                        term_to_chunks[firm_name] = []
                    term_to_chunks[firm_name].append(chunk_id)
                    
                    # CRITICAL: Also index significant words from the firm name separately
                    # This allows "First" queries to find "First NB", etc.
                    _index_significant_words_from_firm(firm_name, term_counts, term_to_chunks, chunk_id, GENERIC_FIRM_WORDS)
                    
                    # Also index expanded version: "First National Bank"
                    expanded_name = f"{first_term} National Bank"
                    term_counts[expanded_name] = term_counts.get(expanded_name, 0) + 1
                    if expanded_name not in term_to_chunks:
                        term_to_chunks[expanded_name] = []
                    term_to_chunks[expanded_name].append(chunk_id)
                    
                    # CRITICAL: Also index significant words from the expanded name
                    _index_significant_words_from_firm(expanded_name, term_counts, term_to_chunks, chunk_id, GENERIC_FIRM_WORDS)
                    
                    # CRITICAL: Also index the COMPLETE firm name with location (e.g., "First NB of Cleveland", "First National Bank of Cleveland")
                    # This prevents splitting "First National Bank of Cleveland" into separate parts
                    complete_firm_nb = f"{first_term} NB of {location_term}"
                    term_counts[complete_firm_nb] = term_counts.get(complete_firm_nb, 0) + 1
                    if complete_firm_nb not in term_to_chunks:
                        term_to_chunks[complete_firm_nb] = []
                    term_to_chunks[complete_firm_nb].append(chunk_id)
                    
                    complete_firm_expanded = f"{first_term} National Bank of {location_term}"
                    term_counts[complete_firm_expanded] = term_counts.get(complete_firm_expanded, 0) + 1
                    if complete_firm_expanded not in term_to_chunks:
                        term_to_chunks[complete_firm_expanded] = []
                    term_to_chunks[complete_firm_expanded].append(chunk_id)
        
        # Pattern 2c: Standalone abbreviations: <italic>Park</italic> NB, <italic>Morgan</italic> IHC, etc.
        for match in nb_pattern_standalone.finditer(chunk):
            firm_name = match.group(1).strip()
            abbrev = match.group(2).strip().upper()
            
            # Create full term: "Park NB", "Morgan IHC", etc.
            full_term = f"{canonicalize_term(firm_name)} {abbrev}"
            term_counts[full_term] = term_counts.get(full_term, 0) + 1
            if full_term not in term_to_chunks:
                term_to_chunks[full_term] = []
            term_to_chunks[full_term].append(chunk_id)
            
            # CRITICAL: Also index significant words from the firm name separately
            # This allows "Park" queries to find "Park NB", "Morgan" to find "Morgan IHC", etc.
            _index_significant_words_from_firm(full_term, term_counts, term_to_chunks, chunk_id, GENERIC_FIRM_WORDS)
            
            # Also create expanded version for NB
            if abbrev == 'NB':
                expanded = f"{canonicalize_term(firm_name)} National Bank"
                term_counts[expanded] = term_counts.get(expanded, 0) + 1
                if expanded not in term_to_chunks:
                    term_to_chunks[expanded] = []
                term_to_chunks[expanded].append(chunk_id)
                
                # CRITICAL: Also index significant words from the expanded name
                _index_significant_words_from_firm(expanded, term_counts, term_to_chunks, chunk_id, GENERIC_FIRM_WORDS)
        
        # Pattern 3: Firm name in plain text (no italics): "First NB of Boston", "Second NB of New York", etc.
        # These appear in regular text and should be indexed as phrases
        # Include possessive forms: "First NB of Boston's" -> "first nb of boston"
        # Use strip_tags to get plain text, then search for the pattern
        visible_text = strip_tags(chunk)
        # CRITICAL FIX: The pattern was capturing "Boston in" instead of just "Boston"
        # The issue: The location group was too greedy and capturing following words
        # Fix: Use a lookahead to ensure we stop at word boundary before lowercase words, punctuation, or end of string
        # The pattern now explicitly stops before: lowercase words, numbers, punctuation, or end of string
        nb_pattern_plain = re.compile(r'\b([A-Z][a-z]+)\s+NB\s+of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*?)(?:\'s)?(?=\s+[a-z]|\s+\d|\s*[.,;:!?)]|\s*$|\b)', re.IGNORECASE)
        
        # Pattern 3b: Firm names with "Bank of [Location]" - e.g., "Reinach Bank of Paris", "Deutsche Bank of London"
        # CRITICAL: This captures complete firm names to prevent splitting "Bank of Paris" separately
        bank_of_pattern = re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*?)\s+Bank\s+of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*?)(?:\'s)?(?=\s+[a-z]|\s+\d|\s*[.,;:!?)]|\s*$|\b)', re.IGNORECASE)
        for match in nb_pattern_plain.finditer(visible_text):
            first_part = match.group(1).strip()
            location_part = match.group(2).strip()
            if len(first_part) < 50 and len(location_part) < 50:
                # Canonicalize (now preserves case: "Paribas" stays "Paribas")
                first_term = canonicalize_term(first_part)
                location_term = canonicalize_term(location_part)
                
                # CRITICAL: Index BOTH the firm name alone AND the complete firm name with location
                # This allows "First National Bank" queries AND "First National Bank of Cleveland" queries
                
                # Index firm name alone (e.g., "First NB", "First National Bank")
                firm_name = f"{first_term} NB"
                term_counts[firm_name] = term_counts.get(firm_name, 0) + 1
                if firm_name not in term_to_chunks:
                    term_to_chunks[firm_name] = []
                term_to_chunks[firm_name].append(chunk_id)
                
                # CRITICAL: Also index significant words from the firm name separately
                # This allows "First" queries to find "First NB", etc.
                _index_significant_words_from_firm(firm_name, term_counts, term_to_chunks, chunk_id, GENERIC_FIRM_WORDS)
                
                # Also index expanded version: "First National Bank"
                expanded_name = f"{first_term} National Bank"
                term_counts[expanded_name] = term_counts.get(expanded_name, 0) + 1
                if expanded_name not in term_to_chunks:
                    term_to_chunks[expanded_name] = []
                term_to_chunks[expanded_name].append(chunk_id)
                
                # CRITICAL: Also index significant words from the expanded name
                _index_significant_words_from_firm(expanded_name, term_counts, term_to_chunks, chunk_id, GENERIC_FIRM_WORDS)
                
                # CRITICAL: Also index the COMPLETE firm name with location (e.g., "First NB of Cleveland", "First National Bank of Cleveland")
                # This prevents splitting "First National Bank of Cleveland" into separate parts
                complete_firm_nb = f"{first_term} NB of {location_term}"
                term_counts[complete_firm_nb] = term_counts.get(complete_firm_nb, 0) + 1
                if complete_firm_nb not in term_to_chunks:
                    term_to_chunks[complete_firm_nb] = []
                    term_to_chunks[complete_firm_nb].append(chunk_id)
                
                complete_firm_expanded = f"{first_term} National Bank of {location_term}"
                term_counts[complete_firm_expanded] = term_counts.get(complete_firm_expanded, 0) + 1
                if complete_firm_expanded not in term_to_chunks:
                    term_to_chunks[complete_firm_expanded] = []
                    term_to_chunks[complete_firm_expanded].append(chunk_id)
        
        # Pattern 3b: Index "Name Bank of Location" as complete firm names (e.g., "Reinach Bank of Paris")
        for match in bank_of_pattern.finditer(visible_text):
            firm_name_part = match.group(1).strip()
            location_part = match.group(2).strip()
            if len(firm_name_part) < 50 and len(location_part) < 50:
                # Skip if firm_name_part is generic (e.g., "First", "Second", "National")
                if firm_name_part.lower() in ['first', 'second', 'third', 'national', 'federal', 'state', 'central', 'commercial', 'investment', 'merchant', 'private', 'public', 'royal', 'imperial']:
                    continue
                # Index complete firm name: "Reinach Bank of Paris"
                complete_firm = f"{canonicalize_term(firm_name_part)} Bank of {canonicalize_term(location_part)}"
                term_counts[complete_firm] = term_counts.get(complete_firm, 0) + 1
                if complete_firm not in term_to_chunks:
                    term_to_chunks[complete_firm] = []
                term_to_chunks[complete_firm].append(chunk_id)
                
                # CRITICAL: Also index significant words from the firm name separately
                # This allows "Reinach" queries to find "Reinach Bank of Paris", etc.
                _index_significant_words_from_firm(complete_firm, term_counts, term_to_chunks, chunk_id, GENERIC_FIRM_WORDS)
        
        # Pattern 1: Standard firm names in <italic> tags
        # CRITICAL: Only index multi-word italicized terms or non-generic single words
        # Generic words like "Bank", "Trust", "Co" should NOT be indexed standalone
        GENERIC_FIRM_WORDS = {
            'bank', 'banks', 'trust', 'trusts', 'company', 'companies', 'co', 'corp', 'corporation',
            'inc', 'incorporated', 'ltd', 'limited', 'group', 'holding', 'holdings',
            'partners', 'partnership', 'associates', 'brothers', 'sons', 'son',
            'york', 'london', 'paris', 'berlin', 'vienna', 'amsterdam', 'brussels', 'geneva',
            'america', 'american', 'british', 'french', 'german', 'swiss', 'italian',
            'national', 'international', 'federal', 'state', 'central', 'commercial',
            'investment', 'merchant', 'private', 'public', 'royal', 'imperial',
            'exchange', 'credit', 'finance', 'capital', 'securities', 'assets'
        }
        
        for match in firm_pattern.finditer(chunk):
            firm = match.group(1).strip()
            if len(firm) < 100:
                # Canonicalize (now preserves case)
                firm_term = canonicalize_term(firm)
                
                # CRITICAL: Skip malformed terms (punctuation, fragments)
                # Skip if:
                # 1. Empty or just whitespace
                # 2. Starts with punctuation (e.g., ", and", ". Siemens", "& Trust")
                # 3. Ends with punctuation (e.g., "Chase,", "Baring.", "British &")
                # 4. Is just punctuation (e.g., "&", ",", ".")
                # 5. Is a single character
                if not firm_term or len(firm_term) <= 1:
                    continue
                if firm_term[0] in ',.;:!?&-—–()[]{}"\'/\\|':
                    continue
                if firm_term[-1] in ',.;:!?&-—–"\'/\\|':  # Allow trailing ) ] } for valid phrases
                    continue
                if all(c in ',.;:!?&-—–()[]{}"\'/\\| ' for c in firm_term):
                    continue
                
                # CRITICAL: Skip standalone generic words
                # Only index if:
                # 1. Multi-word (e.g., "Morgan Grenfell", "Deutsche Bank")
                # 2. Single word but NOT generic (e.g., "Paribas" OK, "Bank" NOT OK)
                is_multi_word = ' ' in firm_term
                is_generic = firm_term.lower() in GENERIC_FIRM_WORDS
                
                # CRITICAL: Also check if it's a generic word from GENERIC_WORDS_TO_EXCLUDE
                # This prevents "bank", "director", "president" from being indexed standalone
                if firm_term.lower() in GENERIC_WORDS_TO_EXCLUDE:
                    continue
                
                # CRITICAL: Check if it's a generic phrase
                if firm_term.lower() in GENERIC_PHRASES_TO_EXCLUDE:
                    continue
                
                if is_generic and not is_multi_word:
                    # Skip standalone generic words like "Bank", "Trust", "Co"
                    continue
                
                # Index the firm name itself (with capitalization preserved)
                term_counts[firm_term] = term_counts.get(firm_term, 0) + 1
                if firm_term not in term_to_chunks:
                    term_to_chunks[firm_term] = []
                term_to_chunks[firm_term].append(chunk_id)
                
                # Also index expanded version if firm contains "NB" abbreviation
                # This allows "First National Bank of Boston" queries to match "First NB of Boston" entries
                # Expand "NB" to "National Bank" for better matching
                firm_lower_check = firm_term.lower()
                if ' nb ' in firm_lower_check or ' nb of ' in firm_lower_check or firm_lower_check.endswith(' nb'):
                    firm_expanded = re.sub(r'\bNB\b', 'National Bank', firm_term, flags=re.IGNORECASE)
                    if firm_expanded != firm_term and firm_expanded:
                        term_counts[firm_expanded] = term_counts.get(firm_expanded, 0) + 1
                        if firm_expanded not in term_to_chunks:
                            term_to_chunks[firm_expanded] = []
                        term_to_chunks[firm_expanded].append(chunk_id)
                
                # CRITICAL: Also index firm + location if the firm name includes a location
                # This allows "Warburg New York" to be indexed as a complete unit
                # Check if firm_term contains location-like words (cities, regions)
                # But only if it's a multi-word term (single word firms don't need location)
                if is_multi_word and len(firm_term.split()) >= 2:
                    # Index the complete firm name including location
                    # This handles cases like "Warburg New York", "Hamburg Chamber of Commerce"
                    # The complete term is already indexed above, so this is just a note
                    pass
        
        # Index acronyms (exact token) and their exact spelled-out names (dictionary) for ALL acronyms
        visible = strip_tags(chunk)
        visible_lower = visible.lower()
        # OPTIMIZATION: Pre-check if acronym term appears in text before running expensive regex
        # This reduces 1.6M regex searches to only ~few thousand
        # Use all_acronym_patterns (extracted + hardcoded) instead of ACRONYM_PATTERNS
        for term, pattern in all_acronym_patterns.items():
            # Fast pre-check: only run regex if term appears in text (case-insensitive)
            # This skips 99%+ of patterns immediately
            term_lower = term.lower()
            if term_lower not in visible_lower:
                continue
            
            # Exact token match for the acronym (e.g., \bSEC\b) - only runs if term found
            if pattern.search(visible):
                term_counts[term] = term_counts.get(term, 0) + 1
                term_to_chunks.setdefault(term, []).append(chunk_id)
                # Also index lowercase alias
                term_lc = term.lower()
                term_counts[term_lc] = term_counts.get(term_lc, 0) + 1
                term_to_chunks.setdefault(term_lc, []).append(chunk_id)
                
                # CRITICAL: Also index acronym + location patterns (e.g., "FRS New York", "SEC Chicago")
                # These are specific entities: FRS New York = Federal Reserve Bank of New York
                # Pattern: ACRONYM followed by a capitalized place name
                # NOTE: Only index if location is part of a specific entity (Federal Reserve cities, major financial centers)
                acronym_location_pattern = re.compile(rf"\b{re.escape(term)}\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b")
                for match in acronym_location_pattern.finditer(visible):
                    location = match.group(1).strip()
                    # Only index if location is a Federal Reserve city or major financial center
                    # These are specific banking entities, not generic place names
                    valid_locations = {
                        'new york', 'boston', 'chicago', 'philadelphia', 'cleveland', 'richmond',
                        'atlanta', 'st louis', 'minneapolis', 'kansas city', 'dallas', 'san francisco',
                        'london', 'paris', 'vienna', 'berlin', 'amsterdam', 'brussels', 'zurich',
                        'geneva', 'frankfurt', 'milan', 'madrid', 'lisbon', 'stockholm', 'copenhagen',
                        'tokyo', 'hong kong', 'singapore', 'shanghai', 'beijing', 'mumbai', 'dubai'
                    }
                    if location.lower() in valid_locations:
                        # Index as specific entity: "FRS New York" = Federal Reserve Bank of New York
                        full_term = f"{term} {location}"
                        term_counts[full_term] = term_counts.get(full_term, 0) + 1
                        term_to_chunks.setdefault(full_term, []).append(chunk_id)
        # Use all_acronyms (extracted + hardcoded) instead of ACRONYM_EXPANSIONS
        # OPTIMIZATION: Pre-check if full name appears in text before running expensive regex
        for term, full_name in all_acronyms.items():
            if not full_name:
                continue
            # Fast pre-check: only run regex if full name appears in text (case-insensitive)
            full_name_lower = full_name.lower()
            if full_name_lower not in visible_lower:
                continue
            full_pat = re.compile(rf"\b{re.escape(full_name)}\b", re.IGNORECASE)
            amp_pat = None
            if " and " in full_name.lower():
                amp_pat = re.compile(rf"\b{re.escape(full_name.replace('and', '&'))}\b", re.IGNORECASE)
            if full_pat.search(visible) or (amp_pat and amp_pat.search(visible)):
                term_counts[term] = term_counts.get(term, 0) + 1
                term_to_chunks.setdefault(term, []).append(chunk_id)
                term_lc = term.lower()
                term_counts[term_lc] = term_counts.get(term_lc, 0) + 1
                term_to_chunks.setdefault(term_lc, []).append(chunk_id)

        # Index law codes like TA1813 / BA1933 with explicit 4-digit years
        # 1) Index the literal token (e.g., TA1813) in both cases
        # 2) Expand to full phrase with 4-digit year (e.g., "Treasury Tax Act 1813")
        # Note: Only 4-digit years are supported (e.g., TA1813, not TA13)
        law_matches = re.findall(r"\b(BHCA|BA|TA|SA|FA|IA|AA|PA|DA|CA|EA|LA)(\d{4})\b", visible)
        if law_matches:
            for prefix, year_token in law_matches:
                literal = f"{prefix}{year_token}"
                # Index literal (both cases)
                for alias in (literal, literal.lower()):
                    term_counts[alias] = term_counts.get(alias, 0) + 1
                    term_to_chunks.setdefault(alias, []).append(chunk_id)
                # Build full phrase
                full_base = LAW_YEAR_PREFIX_EXPANSIONS.get(prefix)
                if full_base:
                    full_year = int(year_token)
                    full_phrase = f"{full_base} {full_year}"
                    # Index exact full phrase (both cases)
                    for alias in (full_phrase, full_phrase.lower()):
                        term_counts[alias] = term_counts.get(alias, 0) + 1
                        term_to_chunks.setdefault(alias, []).append(chunk_id)
        
        # Don't index every word - only index specific entities:
        # - Surnames (already indexed above)
        # - Firm names (already indexed above)
        # - Acronyms (already indexed above)
        # - Law codes (already indexed above)
        # - Panics (indexed separately via panic_indexer)
        
        # Store entities for co-occurrence
        if chunk_entity_list:
            chunk_entities[chunk_id] = chunk_entity_list
    
    # Build entity associations
    print("Building associations...")
    entity_associations = {}
    
    # 1. Co-occurrence associations (entities appearing together in chunks)
    # Enhanced: Also check if single words appear near multi-word phrases that contain them
    print("  Building co-occurrence associations...")
    for chunk_id, entities in chunk_entities.items():
        unique = list(set(entities))
        for i, e1 in enumerate(unique):
            if e1 not in entity_cooccurrence:
                entity_cooccurrence[e1] = {}
            for e2 in unique[i+1:]:
                entity_cooccurrence[e1][e2] = entity_cooccurrence[e1].get(e2, 0) + 1
                if e2 not in entity_cooccurrence:
                    entity_cooccurrence[e2] = {}
                entity_cooccurrence[e2][e1] = entity_cooccurrence[e2].get(e1, 0) + 1
    
    # Enhanced: Check for word-phrase proximity associations
    # If a single word appears near a multi-word phrase that contains it, associate them
    # Only if they appear together in multiple chunks (not just once)
    print("  Building word-phrase proximity associations...")
    word_phrase_cooccurrence = {}
    
    # Get chunk text for proximity checking
    chunk_text_map = {chunk_id: chunk for chunk_id, chunk in zip(chunk_ids, chunks)}
    
    for chunk_id, chunk_text in chunk_text_map.items():
        chunk_lower = chunk_text.lower()
        # Get all terms that appear in this chunk
        chunk_terms = []
        for term in term_to_chunks.keys():
            if chunk_id in term_to_chunks[term]:
                chunk_terms.append(term)
        
        # Check for word-phrase pairs where word is part of phrase
        for term1 in chunk_terms:
            words1 = term1.split()
            # term1 is a single word
            if len(words1) == 1:
                word1 = words1[0].lower()
                # Look for multi-word phrases that contain this word
                for term2 in chunk_terms:
                    if term1 == term2:
                        continue
                    words2 = term2.split()
                    # term2 is a multi-word phrase
                    if len(words2) > 1:
                        # Check if term2 contains word1
                        term2_lower = term2.lower()
                        if word1 in term2_lower:
                            # Check proximity: are they within 50 words of each other?
                            # Find positions of both terms in the chunk
                            word1_pattern = re.compile(rf'\b{re.escape(word1)}\b', re.IGNORECASE)
                            term2_pattern = re.compile(rf'\b{re.escape(term2)}\b', re.IGNORECASE)
                            
                            word1_matches = list(word1_pattern.finditer(chunk_text))
                            term2_matches = list(term2_pattern.finditer(chunk_text))
                            
                            # Check if any word1 match is within 50 words of any term2 match
                            for w_match in word1_matches:
                                w_pos = w_match.start()
                                w_word_count = len(chunk_text[:w_pos].split())
                                for t_match in term2_matches:
                                    t_pos = t_match.start()
                                    t_word_count = len(chunk_text[:t_pos].split())
                                    word_distance = abs(w_word_count - t_word_count)
                                    if word_distance <= 50:  # Within 50 words
                                        # Found proximity - count this co-occurrence
                                        key = (term1, term2)
                                        if key not in word_phrase_cooccurrence:
                                            word_phrase_cooccurrence[key] = 0
                                        word_phrase_cooccurrence[key] += 1
                                        break
                                else:
                                    continue
                                break
    
    # Merge word-phrase proximity associations into entity_cooccurrence
    # Only include if they co-occur in at least 2 chunks (to avoid spurious matches)
    proximity_count = 0
    for (word, phrase), count in word_phrase_cooccurrence.items():
        if count >= 2:  # Must appear together in at least 2 chunks
            if word not in entity_cooccurrence:
                entity_cooccurrence[word] = {}
            entity_cooccurrence[word][phrase] = entity_cooccurrence[word].get(phrase, 0) + count
            if phrase not in entity_cooccurrence:
                entity_cooccurrence[phrase] = {}
            entity_cooccurrence[phrase][word] = entity_cooccurrence[phrase].get(word, 0) + count
            proximity_count += 1
    
    print(f"  [OK] Created {proximity_count} word-phrase proximity associations (>=2 co-occurrences)")
    
    # Filter by frequency (must happen before firm associations to get filtered terms)
    term_counts_filtered = {
        t: c for t, c in term_counts.items()
        if c >= MIN_TERM_FREQUENCY or t in all_acronyms.keys()
    }
    
    # CRITICAL: Final filter - remove any generic words that slipped through
    # This ensures generic words are NEVER in the index (they should have been filtered earlier)
    # Use centralized constant from constants.py
    def should_exclude_term(term):
        """Check if term should be excluded (word or phrase)."""
        term_lower = term.lower()
        # Check single words
        if term_lower in GENERIC_WORDS_TO_EXCLUDE:
            return True
        # Check multi-word phrases
        if term_lower in GENERIC_PHRASES_TO_EXCLUDE:
            return True
        return False
    
    # First pass: hardcoded exclusion (fast, catches obvious cases)
    term_counts_filtered = {t: c for t, c in term_counts_filtered.items() if not should_exclude_term(t)}
    term_to_chunks_filtered = {t: ids for t, ids in term_to_chunks.items() if t in term_counts_filtered and not should_exclude_term(t)}
    
    # Second pass: LLM-based filtering (removes generic terms that hardcoded list missed)
    print("\n" + "="*80)
    print("FILTERING TERMS WITH LLM (removing generic/common terms)")
    print("="*80)
    term_counts_filtered, term_to_chunks_filtered = filter_terms_with_llm(
        term_counts_filtered, term_to_chunks_filtered, all_acronyms
    )
    print("="*80 + "\n")
    
    # Apply term grouping - merge related terms
    # CRITICAL: Collect chunks from ALL variants (both filtered and unfiltered) to create union
    # Then set ALL variants to point to the same merged chunks
    # NOTE: This merges CHUNK IDs only (fast set operations). Text deduplication happens
    #       AFTER this step in create_deduplicated_term_files() which processes the merged chunks.
    print("Applying term grouping...")
    for main_term, variants in TERM_GROUPS.items():
        all_chunks = set()
        # Collect chunks from ALL variants - check both filtered and unfiltered sets
        for variant in variants:
            # Check filtered set first (most up-to-date)
            if variant in term_to_chunks_filtered:
                all_chunks.update(term_to_chunks_filtered[variant])
            # Also check unfiltered set - variants might be filtered out but should still be merged
            if variant in term_to_chunks:
                all_chunks.update(term_to_chunks[variant])
        
        # CRITICAL: Also check underscore versions (from identity detector)
        # Identity detector uses underscores (e.g., "court_jew") but TERM_GROUPS uses spaces
        # Merge underscore versions with space versions
        main_term_underscore = main_term.replace(' ', '_')
        if main_term_underscore in term_to_chunks_filtered:
            all_chunks.update(term_to_chunks_filtered[main_term_underscore])
        if main_term_underscore in term_to_chunks:
            all_chunks.update(term_to_chunks[main_term_underscore])
        
        # Also check underscore versions of variants
        for variant in variants:
            variant_underscore = variant.replace(' ', '_')
            if variant_underscore in term_to_chunks_filtered:
                all_chunks.update(term_to_chunks_filtered[variant_underscore])
            if variant_underscore in term_to_chunks:
                all_chunks.update(term_to_chunks[variant_underscore])
        
        if all_chunks:
            merged_chunks_list = list(all_chunks)
            # Store under main term
            term_to_chunks_filtered[main_term] = merged_chunks_list
            # Also keep ALL variants pointing to same chunks for backward compatibility
            # This ensures queries for "blacks" or "jews" get the same results as "black" or "jewish"
            for variant in variants:
                term_to_chunks_filtered[variant] = merged_chunks_list.copy()
            # Also store underscore version pointing to same chunks
            term_to_chunks_filtered[main_term_underscore] = merged_chunks_list.copy()
    
    # Top associations
    for entity, cooccur in entity_cooccurrence.items():
        if entity in term_counts_filtered:
            top = sorted(cooccur.items(), key=lambda x: x[1], reverse=True)[:10]
            entity_associations[entity] = [e for e, c in top if c >= 3]
    
    # Convert name_changes sets to lists
    name_changes_serializable = {k: list(v) for k, v in name_changes.items()}
    
    print(f"[OK] Indexed {len(term_counts_filtered)} terms")
    print(f"[OK] Created {sum(len(ids) for ids in term_to_chunks_filtered.values())} mappings")
    print(f"[OK] Applied {len(TERM_GROUPS)} term groups")
    print(f"[OK] Detected {len(name_changes_serializable)} name changes")
    
    return {
        'term_index': term_counts_filtered,
        'term_to_chunks': term_to_chunks_filtered,
        'entity_associations': entity_associations,
        'name_changes': name_changes_serializable,
        'version': '2.0'
    }


def create_deduplicated_term_files(indices, all_chunks, chunk_ids, min_chunks=25):
    """
    Create preprocessed deduplicated text files for meaningful indexed terms with many chunks.
    Only processes terms with >min_chunks chunks and filters out stop words.
    
    IMPORTANT: This function runs AFTER TERM_GROUPS has merged chunk IDs. It takes the
    already-merged indices and deduplicates the TEXT content (sentence/phrase level).
    
    Flow:
    1. TERM_GROUPS merges chunk IDs (fast set operations) → indices.json
    2. This function deduplicates TEXT content (expensive text analysis) → cache.json
    
    Args:
        indices: Dictionary with 'term_to_chunks' mapping (already TERM_GROUPS merged)
        all_chunks: List of all chunk texts
        chunk_ids: List of all chunk IDs
        min_chunks: Minimum number of chunks required to create a deduplicated file (default: 25)
    
    Returns:
        Number of files created
    """
    import os
    from .config import DATA_DIR
    
    # Stop words and common words to skip
    # Use centralized STOP_WORDS from constants.py
    # Extended with domain-specific terms
    EXTENDED_STOP_WORDS = STOP_WORDS | {'year', 'years', 'became', 'married'}
    
    # Load identity terms to prioritize
    try:
        from .identity_terms import IDENTITY_TERMS_SET
        identity_terms_set = IDENTITY_TERMS_SET
    except:
        identity_terms_set = set()
    
    print(f"Creating deduplicated text files for meaningful terms with >{min_chunks} chunks...")
    
    # Create directory for deduplicated term files
    dedup_dir = os.path.join(DATA_DIR, 'deduplicated_terms')
    os.makedirs(dedup_dir, exist_ok=True)
    
    # Create chunk lookup
    chunk_dict = {cid: chunk for cid, chunk in zip(chunk_ids, all_chunks)}
    
    # Filter terms: only process meaningful terms with >min_chunks chunks
    term_to_chunks = indices.get('term_to_chunks', {})
    meaningful_terms = {}
    
    for term, chunk_list in term_to_chunks.items():
        term_lower = term.lower()
        
        # Skip stop words
        if term_lower in EXTENDED_STOP_WORDS:
            continue
        
        # Skip single-letter terms
        if len(term) <= 1:
            continue
        
        # Skip common verbs/adjectives
        if term_lower in ['bank', 'banks', 'family', 'families', 'daughter', 'son', 'children']:
            continue
        
        # Only process terms with >min_chunks chunks
        if len(chunk_list) <= min_chunks:
            continue
        
        # Prioritize: proper nouns (capitalized), identity terms, firm names (contain "nb" or "bank")
        is_proper_noun = term[0].isupper() if term else False
        is_identity_term = term_lower in identity_terms_set
        is_firm_name = 'nb' in term_lower or 'bank' in term_lower or 'co' in term_lower
        
        # Only process if it's a proper noun, identity term, or firm name
        if is_proper_noun or is_identity_term or is_firm_name:
            meaningful_terms[term] = chunk_list
    
    print(f"  Found {len(meaningful_terms)} meaningful terms with >{min_chunks} chunks (out of {len(term_to_chunks)} total)")
    
    # Since there are only a few hundred meaningful terms, we can do in-memory deduplication
    # Store deduplicated chunks in a cache dictionary
    deduplicated_cache = {}
    
    # Use shared split_into_sentences from text_utils.py
    # Note: extract_phrases logic is kept local here as it has specific behavior
    def extract_phrases_local(text: str, min_words: int = 5) -> list:
        """Extract meaningful phrases from text (sentences and longer sub-phrases)."""
        sentences = split_into_sentences(text)  # From text_utils
        phrases = []
        
        for sentence in sentences:
            # Add full sentence
            words = sentence.split()
            if len(words) >= min_words:
                phrases.append(sentence.lower().strip())
            
            # Extract longer sub-phrases from sentences (5+ words)
            # This catches phrases like "The bank merged with Goldman in 1920" within longer sentences
            for i in range(len(words) - min_words + 1):
                for j in range(i + min_words, len(words) + 1):
                    phrase = " ".join(words[i:j])
                    if len(phrase.split()) >= min_words:
                        phrases.append(phrase.lower().strip())
        
        return phrases
    
    def merge_overlapping_chunks(chunk1: str, chunk2: str) -> tuple:
        """Merge two overlapping chunks, removing duplicate sentences and longer phrases. Returns (merged_text, did_merge)."""
        # First: Check for duplicate sentences (exact matches)
        sentences1 = split_into_sentences(chunk1)
        sentences2 = split_into_sentences(chunk2)
        normalized_sentences1 = {s.lower().strip(): s for s in sentences1}
        normalized_sentences2 = {s.lower().strip(): s for s in sentences2}
        duplicate_sentences = set(normalized_sentences1.keys()) & set(normalized_sentences2.keys())
        
        # Second: Check for duplicate longer phrases (5+ words) within sentences
        # This catches cases where the same phrase appears in different sentences
        phrases1 = extract_phrases_local(chunk1, min_words=5)
        phrases2 = extract_phrases_local(chunk2, min_words=5)
        duplicate_phrases = set(phrases1) & set(phrases2)
        
        # Filter duplicate phrases: only keep longer ones (7+ words) to avoid false matches
        # Short phrases (3-6 words) might change meaning in different contexts
        meaningful_duplicate_phrases = {p for p in duplicate_phrases if len(p.split()) >= 7}
        
        # Calculate overlap: sentences + meaningful phrases
        total_overlap = len(duplicate_sentences) + len(meaningful_duplicate_phrases)
        total_content = max(len(normalized_sentences1), len(normalized_sentences2))
        
        # If chunks share significant overlap (>30% sentences OR meaningful phrases), merge them
        sentence_overlap_ratio = len(duplicate_sentences) / total_content if total_content > 0 else 0
        has_meaningful_overlap = len(duplicate_sentences) > 0 or len(meaningful_duplicate_phrases) > 0
        
        if has_meaningful_overlap and (sentence_overlap_ratio > 0.3 or len(meaningful_duplicate_phrases) > 0):
            # Merge: keep all unique sentences, removing duplicates
            merged_sentences = []
            seen_sentences = set()
            
            # Add sentences from chunk1
            for s in sentences1:
                normalized = s.lower().strip()
                if normalized not in seen_sentences:
                    merged_sentences.append(s)
                    seen_sentences.add(normalized)
            
            # Add sentences from chunk2 that aren't duplicates
            for s in sentences2:
                normalized = s.lower().strip()
                if normalized not in seen_sentences:
                    merged_sentences.append(s)
                    seen_sentences.add(normalized)
            
            merged = " ".join(merged_sentences)
            return (merged, True)
        
        return (None, False)
    
    # Process each meaningful term independently - create deduplicated text file
    files_created = 0
    
    for term, chunk_id_list in tqdm(meaningful_terms.items(), desc="Creating term files"):
        if not chunk_id_list:
            continue
        
        # Get chunks for this term
        term_chunks = [chunk_dict.get(cid, "") for cid in chunk_id_list if cid in chunk_dict and chunk_dict.get(cid, "")]
        
        if not term_chunks:
            continue
        
        # Deduplicate chunks for this term
        deduplicated_text = deduplicate_chunks_for_term(term_chunks)
        
        # Store in cache (keyed by term)
        deduplicated_cache[term] = deduplicated_text
        files_created += 1  # Count terms processed (not individual files, but cache entries)
        
        # Note: Individual .txt files are no longer created - only JSON cache is used
        # This saves disk space and improves performance (33K+ files avoided)
    
    # Save cache to JSON for fast loading at query time
    cache_file = os.path.join(dedup_dir, 'deduplicated_cache.json')
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(deduplicated_cache, f, indent=2)
        print(f"  [OK] Saved deduplication cache to {cache_file}")
    except Exception as e:
        print(f"  [WARN] Could not save cache: {e}")
    
    print(f"[OK] Created {files_created} deduplicated term files in {dedup_dir}\n")
    
    return files_created


def deduplicate_chunks_for_term(chunks: list) -> str:
    """
    Deduplicate chunks for a single term using sentence and phrase-level deduplication.
    
    Args:
        chunks: List of chunk text strings
    
    Returns:
        Deduplicated text (all chunks merged, duplicates removed)
    """
    import re
    
    # Use shared split_into_sentences from text_utils.py
    
    def extract_phrases_local(text: str, min_words: int = 5) -> list:
        """Extract meaningful phrases from text."""
        sentences = split_into_sentences(text)  # From text_utils
        phrases = []
        for sentence in sentences:
            words = sentence.split()
            if len(words) >= min_words:
                phrases.append(sentence.lower().strip())
            # Extract longer sub-phrases (5+ words)
            for i in range(len(words) - min_words + 1):
                for j in range(i + min_words, len(words) + 1):
                    phrase = " ".join(words[i:j])
                    if len(phrase.split()) >= min_words:
                        phrases.append(phrase.lower().strip())
        return phrases
    
    # Collect all sentences from all chunks
    all_sentences = []
    seen_sentences = set()
    seen_phrases_7plus = set()  # Track 7+ word phrases
    
    for chunk in chunks:
        if not chunk.strip():
            continue
        
        sentences = split_into_sentences(chunk)
        
        for sentence in sentences:
            normalized = sentence.lower().strip()
            
            # Skip duplicate sentences
            if normalized in seen_sentences:
                continue
            
            # Check if sentence contains a duplicate longer phrase (7+ words)
            words = sentence.split()
            if len(words) >= 7:
                if normalized in seen_phrases_7plus:
                    continue  # Skip - it's a duplicate longer phrase
                seen_phrases_7plus.add(normalized)
            
            all_sentences.append(sentence)
            seen_sentences.add(normalized)
    
    # Join all unique sentences
    return " ".join(all_sentences)


def save_indices(indices):
    """Save indices to disk, deduplicating chunk lists first."""
    # CRITICAL: Deduplicate chunk IDs for each term
    # Many terms appear multiple times in the same chunk, causing duplicate chunk IDs
    term_to_chunks = indices.get('term_to_chunks', {})
    total_before = sum(len(chunks) for chunks in term_to_chunks.values())
    duplicates_removed = 0
    
    for term, chunks in term_to_chunks.items():
        if len(chunks) != len(set(chunks)):
            unique_chunks = list(dict.fromkeys(chunks))  # Preserves order, removes duplicates
            duplicates_removed += len(chunks) - len(unique_chunks)
            term_to_chunks[term] = unique_chunks
    
    total_after = sum(len(chunks) for chunks in term_to_chunks.values())
    
    if duplicates_removed > 0:
        print(f"  [DEDUP] Removed {duplicates_removed:,} duplicate chunk references ({total_before:,} -> {total_after:,})")
    
    with open(INDICES_FILE, 'w', encoding='utf-8') as f:
        json.dump(indices, f, indent=2)
    print(f"[OK] Saved indices to {INDICES_FILE}")


def expand_with_hierarchy(term_to_chunks, detected_identities):
    """
    Expand detected identities using hierarchy (specific -> general).
    
    Example: If chunk has "alawite" identity, also index under "muslim" and "levantine".
    This allows both specific searches ("alawite bankers") and general ("muslim bankers").
    """
    from lib.identity_hierarchy import get_parent_categories
    
    if not detected_identities or 'identities' not in detected_identities:
        print("  [SKIP] No detected identities for hierarchy expansion")
        return term_to_chunks
    
    print("Expanding identities with hierarchy (specific -> general)...")
    expansions = 0
    
    for specific_identity, data in detected_identities.get('identities', {}).items():
        # Get parent categories
        parents = get_parent_categories(specific_identity)
        
        if parents:
            # Get all chunks with this specific identity
            specific_lower = specific_identity.lower().replace('_', ' ')
            specific_chunks = set(term_to_chunks.get(specific_lower, []))
            
            # Add these chunks to parent categories
            for parent in parents:
                parent_lower = parent.lower()
                if parent_lower not in term_to_chunks:
                    term_to_chunks[parent_lower] = []
                
                existing = set(term_to_chunks[parent_lower])
                for chunk_id in specific_chunks:
                    if chunk_id not in existing:
                        term_to_chunks[parent_lower].append(chunk_id)
                        existing.add(chunk_id)
                        expansions += 1
    
    print(f"  [OK] Added {expansions} hierarchical links (specific->general)")
    return term_to_chunks


def augment_indices_with_identities(term_to_chunks, detected_identities):
    """
    Enhance term_to_chunks by adding identity metadata from detector.
    
    Example: If "parsons" appears in chunk_123 and detector says Parsons is Black,
    then chunk_123 is also added to term_to_chunks["black"].
    
    This makes searching "black bankers" also find chunks about Parsons/McGuire/Lewis
    even if those chunks don't explicitly mention race.
    
    Args:
        term_to_chunks: dict {term -> [chunk_ids]}
        detected_identities: dict from identity_detector
    
    Returns:
        Enhanced term_to_chunks with identity metadata
    """
    if not detected_identities or 'identities' not in detected_identities:
        print("  [SKIP] No detected identities to augment index")
        return term_to_chunks
    
    print("Augmenting index with identity metadata...")
    augmentation_count = 0
    
    for identity, data in detected_identities.get('identities', {}).items():
        # Handle both "families" (hereditary) and "individuals" (LGBT, Latino)
        names = data.get('families', []) or data.get('individuals', [])
        identity_lower = identity.lower()
        
        # Initialize identity term in index if not present
        if identity_lower not in term_to_chunks:
            term_to_chunks[identity_lower] = []
        
        existing_chunks = set(term_to_chunks[identity_lower])
        
        # For each name with this identity (family or individual)
        for name in names:
            name_lower = name.lower()
            
            # Find all chunks containing this surname
            if name_lower in term_to_chunks:
                name_chunks = term_to_chunks[name_lower]
                
                # Add these chunks to the identity term (avoid duplicates)
                for chunk_id in name_chunks:
                    if chunk_id not in existing_chunks:
                        term_to_chunks[identity_lower].append(chunk_id)
                        existing_chunks.add(chunk_id)
                        augmentation_count += 1
    
            print(f"  [OK] Added {augmentation_count} identity→chunk links")
    
    # Step 2: Expand with hierarchy (specific -> general)
    term_to_chunks = expand_with_hierarchy(term_to_chunks, detected_identities)
    
    return term_to_chunks


def build_endnote_mappings(documents, chunks, chunk_ids):
    """
    Build mappings between body chunks and their linked endnotes.
    
    Args:
        documents: List of document dicts with body_paragraphs and endnotes
        chunks: List of chunked body text
        chunk_ids: List of chunk IDs
        
    Returns:
        dict with:
            - all_endnotes: dict {doc:id -> text}
            - chunk_to_endnotes: dict {chunk_id -> [endnote_ids]}
    """
    import os
    from .config import DATA_DIR
    
    print("Building endnote mappings...")
    
    all_endnotes = {}
    chunk_to_endnotes = {}
    
    # Collect all endnotes with doc-prefixed IDs
    for doc in documents:
        if 'body_paragraphs' not in doc:
            continue
        doc_name = doc['filename'].replace('.docx', '')
        for endnote_id, endnote_text in doc['endnotes'].items():
            prefixed_id = f"{doc_name}:{endnote_id}"
            all_endnotes[prefixed_id] = endnote_text
    
    # Map chunks to endnotes
    for doc in documents:
        if 'body_paragraphs' not in doc:
            continue
        doc_name = doc['filename'].replace('.docx', '')
        doc_text = ' '.join(p['text'] for p in doc['body_paragraphs'])
        
        # For each chunk, find which document paragraphs it contains
        chunk_start = 0
        for chunk_id, chunk_text in zip(chunk_ids, chunks):
            # Find this chunk in the document
            chunk_idx = doc_text.find(chunk_text[:100])  # Use first 100 chars as match
            
            if chunk_idx >= 0:
                # Find which paragraphs overlap with this chunk
                para_start = 0
                chunk_endnote_ids = []
                
                for para in doc['body_paragraphs']:
                    para_end = para_start + len(para['text'])
                    
                    # If paragraph overlaps with chunk, add its endnotes
                    if para_start <= chunk_idx + len(chunk_text) and para_end >= chunk_idx:
                        for endnote_id in para['endnote_ids']:
                            prefixed_id = f"{doc_name}:{endnote_id}"
                            chunk_endnote_ids.append(prefixed_id)
                    
                    para_start = para_end + 1  # +1 for newline
                
                if chunk_endnote_ids:
                    chunk_to_endnotes[chunk_id] = list(set(chunk_endnote_ids))  # Deduplicate
    
    print(f"[OK] Collected {len(all_endnotes)} endnotes")
    print(f"[OK] Mapped {len(chunk_to_endnotes)} chunks to endnotes")
    
    # Save to separate files
    endnotes_file = os.path.join(DATA_DIR, 'endnotes.json')
    mappings_file = os.path.join(DATA_DIR, 'chunk_to_endnotes.json')
    
    with open(endnotes_file, 'w', encoding='utf-8') as f:
        json.dump(all_endnotes, f, indent=2)
    print(f"[OK] Saved endnotes to {endnotes_file}")
    
    with open(mappings_file, 'w', encoding='utf-8') as f:
        json.dump(chunk_to_endnotes, f, indent=2)
    print(f"[OK] Saved mappings to {mappings_file}")
    
    return {
        'all_endnotes': all_endnotes,
        'chunk_to_endnotes': chunk_to_endnotes
    }


