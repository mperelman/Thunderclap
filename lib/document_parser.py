"""
Document parsing - Extract text from Word documents.
Uses caching to avoid re-parsing unchanged files.
"""
import os
import json
from docx import Document
from .config import SOURCE_DOCS_DIR, CACHE_DIR


def get_cache_path(docx_filename):
    """Get cache file path for a document."""
    cache_name = f"{docx_filename}.cache.json"
    return os.path.join(CACHE_DIR, cache_name)


def parse_document(docx_path):
    """
    Parse a Word document and extract text with italic markup.
    
    Returns:
        dict with:
            - filename: str
            - text: str (with <italic>...</italic> tags)
            - endnotes: dict {id: text}
    """
    doc = Document(docx_path)
    
    # Extract main text
    text_parts = []
    for para in doc.paragraphs:
        para_text = []
        for run in para.runs:
            if run.italic:
                para_text.append(f'<italic>{run.text}</italic>')
            else:
                para_text.append(run.text)
        text_parts.append(''.join(para_text))
    
    text = '\n'.join(text_parts)
    
    # Extract endnotes (simplified - adapt to your document structure)
    endnotes = {}
    
    return {
        'filename': os.path.basename(docx_path),
        'text': text,
        'endnotes': endnotes,
        'mtime': os.path.getmtime(docx_path)
    }


def load_all_documents(use_cache=True):
    """
    Load all .docx files from source_documents directory.
    Uses cache if available and files haven't changed.
    
    Returns:
        list of document dicts
    """
    os.makedirs(CACHE_DIR, exist_ok=True)
    
    docx_files = [f for f in os.listdir(SOURCE_DOCS_DIR) 
                  if f.endswith('.docx') and not f.startswith('~')]
    
    documents = []
    for docx_file in docx_files:
        docx_path = os.path.join(SOURCE_DOCS_DIR, docx_file)
        cache_path = get_cache_path(docx_file)
        
        # Check cache
        if use_cache and os.path.exists(cache_path):
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached = json.load(f)
            
            # Use cache if file hasn't changed
            if cached.get('mtime') == os.path.getmtime(docx_path):
                print(f"[CACHE] Using cache for {docx_file}")
                documents.append(cached)
                continue
        
        # Parse document
        print(f"Parsing {docx_file}...")
        doc_data = parse_document(docx_path)
        
        # Save to cache
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(doc_data, f, indent=2)
        
        documents.append(doc_data)
    
    return documents

