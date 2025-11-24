"""
Search Engine - Handles document retrieval via keyword and vector search.
Pure search logic, no LLM interaction.
"""

import json
import os
import chromadb
from typing import List, Dict, Optional, Set
from .config import VECTORDB_DIR, INDICES_FILE, COLLECTION_NAME, DATA_DIR


class SearchEngine:
    """
    Handles document search and retrieval.
    Separated from query orchestration and LLM interaction.
    """
    
    def __init__(self):
        """Initialize search engine with indices and vector database."""
        # Connect to ChromaDB
        self.chroma_client = chromadb.PersistentClient(path=VECTORDB_DIR)
        try:
            self.collection = self.chroma_client.get_collection(name=COLLECTION_NAME)
        except Exception as e:
            print(f"  [ERROR] Could not find collection '{COLLECTION_NAME}'")
            print(f"    Run: python build_index.py")
            raise
        
        # Load pre-built indices
        self._load_indices()
        
        # Load endnotes and mappings
        self._load_endnotes()
    
    def _load_indices(self):
        """Load term-to-chunk mappings from disk."""
        if not os.path.exists(INDICES_FILE):
            raise FileNotFoundError(f"Indices not found: {INDICES_FILE}. Run: python build_index.py")
        
        with open(INDICES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.term_to_chunks = data['term_to_chunks']
            self.entity_associations = data.get('entity_associations', {})
            self.name_changes = data.get('name_changes', {})
    
    def _load_endnotes(self):
        """Load endnotes and chunk-to-endnote mappings."""
        endnotes_file = os.path.join(DATA_DIR, 'endnotes.json')
        mappings_file = os.path.join(DATA_DIR, 'chunk_to_endnotes.json')
        
        if os.path.exists(endnotes_file) and os.path.exists(mappings_file):
            with open(endnotes_file, 'r', encoding='utf-8') as f:
                self.endnotes = json.load(f)
            
            with open(mappings_file, 'r', encoding='utf-8') as f:
                self.chunk_to_endnotes = json.load(f)
        else:
            self.endnotes = {}
            self.chunk_to_endnotes = {}
    
    def keyword_search(self, query: str, max_results: int = 50) -> Set[str]:
        """
        Perform keyword-based search using term indices with automatic expansion.
        Uses entity_associations and name_changes to find related entities dynamically.
        
        Args:
            query: Search query (single term or phrase)
            max_results: Maximum number of chunk IDs to return
        
        Returns:
            Set of matching chunk IDs
        """
        terms = query.lower().split()
        all_chunk_ids = set()
        expanded_terms = set(terms)
        
        # Expand query using name changes (e.g., "warburg" -> also search "delbanco")
        for term in terms:
            # Forward: old_name -> new_names
            if term in self.name_changes:
                expanded_terms.update(self.name_changes[term])
            # Reverse: new_name -> old_names
            for old_name, new_names in self.name_changes.items():
                if term in new_names:
                    expanded_terms.add(old_name)
        
        # Expand query using entity associations (dynamic, not hardcoded)
        for term in terms:
            if term in self.entity_associations:
                # Add associated entities (e.g., "hindu" -> "tagore", "dutt", etc.)
                associated = self.entity_associations[term][:5]  # Top 5 associations
                expanded_terms.update([a.lower() for a in associated])
        
        # Search for all terms (original + name variants + associated)
        for term in expanded_terms:
            if term in self.term_to_chunks:
                chunk_ids = self.term_to_chunks[term]
                all_chunk_ids.update(chunk_ids[:max_results])
        
        return all_chunk_ids
    
    def vector_search(self, query: str, n_results: int = 50) -> Dict:
        """
        Perform semantic search using vector embeddings.
        
        Args:
            query: Search query
            n_results: Number of results to return
        
        Returns:
            Dictionary with 'ids', 'documents', 'metadatas'
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        return {
            'ids': results['ids'][0] if results['ids'] else [],
            'documents': results['documents'][0] if results['documents'] else [],
            'metadatas': results['metadatas'][0] if results['metadatas'] else []
        }
    
    def fetch_chunks_by_ids(self, chunk_ids: List[str]) -> Dict:
        """
        Fetch specific chunks by their IDs.
        
        Args:
            chunk_ids: List of chunk IDs to fetch
        
        Returns:
            Dictionary with 'documents' and 'metadatas'
        """
        if not chunk_ids:
            return {'documents': [], 'metadatas': []}
        
        results = self.collection.get(ids=chunk_ids)
        
        # Ensure metadatas is a list, not None, and has same length as documents
        documents = results.get('documents', [])
        metadatas = results.get('metadatas', [])
        
        # If metadatas is None or wrong length, create empty dicts
        if not metadatas or len(metadatas) != len(documents):
            metadatas = [{} for _ in documents]
        
        return {
            'documents': documents,
            'metadatas': metadatas
        }
    
    def fetch_linked_endnotes(self, chunk_ids: List[str]) -> tuple[List[str], int]:
        """
        Fetch endnotes linked to given body chunks.
        
        Args:
            chunk_ids: List of body chunk IDs
        
        Returns:
            Tuple of (endnote_texts, total_endnote_count)
        """
        if not self.endnotes or not self.chunk_to_endnotes:
            return [], 0
        
        # Collect all unique endnote IDs linked to these chunks
        endnote_ids = set()
        for chunk_id in chunk_ids:
            if chunk_id in self.chunk_to_endnotes:
                endnote_ids.update(self.chunk_to_endnotes[chunk_id])
        
        # Fetch endnote texts
        endnote_texts = []
        for endnote_id in sorted(endnote_ids):
            if endnote_id in self.endnotes:
                endnote_texts.append(self.endnotes[endnote_id])
        
        return endnote_texts, len(endnote_ids)
    
    def get_stats(self) -> Dict:
        """Get search engine statistics."""
        return {
            'total_chunks': self.collection.count(),
            'indexed_terms': len(self.term_to_chunks),
            'entity_associations': len(self.entity_associations),
            'total_endnotes': len(self.endnotes),
            'chunks_with_endnotes': len(self.chunk_to_endnotes)
        }

