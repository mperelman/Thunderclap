"""
Index Builder - Builds indices from documents with smart term grouping.
"""
import json
import re
from tqdm import tqdm
from .config import INDICES_FILE, MIN_TERM_FREQUENCY, CHUNK_SIZE, CHUNK_OVERLAP, DATA_DIR
import os


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

def build_indices(chunks, chunk_ids):
    """
    Build term→chunk_id indices with smart term grouping.
    """
    term_counts = {}
    term_to_chunks = {}
    entity_cooccurrence = {}
    chunk_entities = {}
    name_changes = {}
    
    print("Building indices...")
    
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
        
        # Extract surnames
        proper_names = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b', chunk)
        for full_name in proper_names:
            parts = full_name.split()
            surname = parts[-1].lower()
            
            term_counts[surname] = term_counts.get(surname, 0) + 1
            if surname not in term_to_chunks:
                term_to_chunks[surname] = []
            term_to_chunks[surname].append(chunk_id)
            chunk_entity_list.append(surname)
        
        # Index firm names
        firms = re.findall(r'<italic>(.*?)</italic>', chunk)
        for firm in firms:
            if len(firm) < 100:
                firm_lower = firm.lower()
                term_counts[firm_lower] = term_counts.get(firm_lower, 0) + 1
                if firm_lower not in term_to_chunks:
                    term_to_chunks[firm_lower] = []
                term_to_chunks[firm_lower].append(chunk_id)
        
        # Index all significant words (for geographies, events, identities)
        words = re.findall(r'\b[a-z]{4,}\b', chunk_lower)
        for word in words:
            term_counts[word] = term_counts.get(word, 0) + 1
            if word not in term_to_chunks:
                term_to_chunks[word] = []
            term_to_chunks[word].append(chunk_id)
        
        # Store entities for co-occurrence
        if chunk_entity_list:
            chunk_entities[chunk_id] = chunk_entity_list
    
    # Build entity associations
    print("Building associations...")
    entity_associations = {}
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
    
    # Filter by frequency
    term_counts_filtered = {t: c for t, c in term_counts.items() if c >= MIN_TERM_FREQUENCY}
    term_to_chunks_filtered = {t: ids for t, ids in term_to_chunks.items() if t in term_counts_filtered}
    
    # Apply term grouping - merge related terms
    print("Applying term grouping...")
    for main_term, variants in TERM_GROUPS.items():
        all_chunks = set()
        for variant in variants:
            if variant in term_to_chunks_filtered:
                all_chunks.update(term_to_chunks_filtered[variant])
        
        if all_chunks:
            # Store under main term
            term_to_chunks_filtered[main_term] = list(all_chunks)
            # Also keep variants pointing to same chunks for backward compatibility
            for variant in variants:
                term_to_chunks_filtered[variant] = list(all_chunks)
    
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


def save_indices(indices):
    """Save indices to disk."""
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
        doc_name = doc['filename'].replace('.docx', '')
        for endnote_id, endnote_text in doc['endnotes'].items():
            prefixed_id = f"{doc_name}:{endnote_id}"
            all_endnotes[prefixed_id] = endnote_text
    
    # Map chunks to endnotes
    for doc in documents:
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


