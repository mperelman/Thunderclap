"""
Document parsing - Extract text from Word documents.
Uses caching to avoid re-parsing unchanged files.
"""
import os
import json
import zipfile
import xml.etree.ElementTree as ET
from docx import Document
from .config import SOURCE_DOCS_DIR, CACHE_DIR


def get_cache_path(docx_filename):
    """Get cache file path for a document."""
    cache_name = f"{docx_filename}.cache.json"
    return os.path.join(CACHE_DIR, cache_name)


def _extract_endnotes(docx_path: str) -> dict:
    """Extract endnotes from a .docx file using the underlying XML."""
    endnotes = {}
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    try:
        with zipfile.ZipFile(docx_path) as zf:
            if 'word/endnotes.xml' not in zf.namelist():
                return {}
            xml_data = zf.read('word/endnotes.xml')
        root = ET.fromstring(xml_data)
        for endnote in root.findall('w:endnote', ns):
            endnote_id = endnote.get(f'{{{ns["w"]}}}id')
            if endnote_id is None:
                continue
            try:
                if int(endnote_id) <= 0:
                    continue
            except ValueError:
                pass
            texts = [t.text for t in endnote.findall('.//w:t', ns) if t.text]
            text = ''.join(texts).strip()
            if text:
                endnotes[endnote_id] = text
    except Exception:
        return {}
    return endnotes


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
    
    # Extract endnotes
    endnotes = _extract_endnotes(docx_path)

    # Extract main text + per-paragraph endnote references
    text_parts = []
    body_paragraphs = []
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    for para in doc.paragraphs:
        para_text = []
        for run in para.runs:
            if run.italic:
                para_text.append(f'<italic>{run.text}</italic>')
            else:
                para_text.append(run.text)
        para_text_joined = ''.join(para_text)
        text_parts.append(para_text_joined)
        endnote_ids = []
        try:
            refs = para._p.findall('.//w:endnoteReference', ns)
            for ref in refs:
                endnote_id = ref.get(f'{{{ns["w"]}}}id')
                if endnote_id:
                    endnote_ids.append(endnote_id)
        except Exception:
            endnote_ids = []
        body_paragraphs.append({
            'text': para_text_joined,
            'endnote_ids': endnote_ids
        })
    
    text = '\n'.join(text_parts)
    
    return {
        'filename': os.path.basename(docx_path),
        'text': text,
        'endnotes': endnotes,
        'body_paragraphs': body_paragraphs,
        'schema_version': 2,
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
            cache_ok = cached.get('schema_version') == 2
            if cached.get('mtime') == os.path.getmtime(docx_path) and cache_ok:
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

