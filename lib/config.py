"""
Configuration - All paths and parameters in ONE place.
"""
import os

# Base directories
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_DOCS_DIR = os.path.join(ROOT_DIR, 'source_documents')
DATA_DIR = os.path.join(ROOT_DIR, 'data')
LIB_DIR = os.path.join(ROOT_DIR, 'lib')
TEMP_DIR = os.path.join(ROOT_DIR, 'temp')

# Data subdirectories
CACHE_DIR = os.path.join(DATA_DIR, 'cache')
VECTORDB_DIR = os.path.join(DATA_DIR, 'vectordb')
INDICES_FILE = os.path.join(DATA_DIR, 'indices.json')

# ChromaDB collection name
COLLECTION_NAME = "historical_documents"

# Indexing parameters
CHUNK_SIZE = 400  # words
CHUNK_OVERLAP = 100  # words
MIN_TERM_FREQUENCY = 2  # minimum occurrences to index a term
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'  # SentenceTransformers model

# Query parameters  
DEFAULT_TOP_K = 10  # Default number of results
MAX_CONTEXT_CHUNKS = 15  # Max chunks to use for LLM context

# LLM settings (optional)
DEFAULT_LLM_MODEL = "gpt-4o-mini"  # OpenAI model
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"  # Gemini model
LLM_TEMPERATURE = 0.3  # Lower = more factual

# Answer generation parameters
MAX_SENTENCES_PER_PARAGRAPH = 3  # Hard limit for paragraph length
MAX_REVIEW_ITERATIONS = 2  # Maximum iterations for answer review/fixing (reduced to prevent timeouts)
BATCH_SIZE = 20  # Process chunks in batches of this size (DEPRECATED - use token-based batching)
BATCH_PAUSE_SECONDS = 5  # Pause between batches to avoid rate limits (reduced from 15 to speed up queries)
CHUNK_RETRIEVAL_BATCH_SIZE = 200  # Batch size for retrieving chunks from database
MAX_ANSWER_LENGTH = 15000  # Maximum answer length in characters (for truncation)
QUERY_TIMEOUT_SECONDS = 420  # Maximum time for query processing (7 minutes, leaving buffer for frontend timeout)

# Token-based batching (more efficient than chunk count)
MAX_TOKENS_PER_MINUTE = 250000  # Max tokens per minute (user limit)
MAX_TOKENS_PER_REQUEST = 200000  # Max tokens per API call (conservative limit under 250k/min)
ESTIMATED_WORDS_PER_CHUNK = 400  # Average words per chunk (from CHUNK_SIZE)
TOKENS_PER_WORD = 1.3  # Rough estimate: 1 word ≈ 1.3 tokens
MAX_WORDS_PER_REQUEST = 150000  # Max words per request (~200K tokens / 1.3)

# Answer review thresholds
EARLY_STOP_GAP_THRESHOLD = 10  # Years gap threshold for detecting early stopping
SPARSE_RESULTS_THRESHOLD = 10  # Below this, augment with endnotes

# Control/influence query parameters
CONTROL_INFLUENCE_EARLY_CHUNK_LIMIT = 8  # Limit chunks BEFORE augmentation for control/influence queries
CONTROL_INFLUENCE_FINAL_CHUNK_LIMIT = 5  # Final chunk limit AFTER deduplication for control/influence queries
CONTROL_INFLUENCE_MAX_RETRIES = 2  # Reduced retries for control/influence queries (prevents long waits)
CONTROL_INFLUENCE_SLOW_THRESHOLD_SECONDS = 120  # Threshold for warning about slow LLM calls

# Note: Removed BROAD_IDENTITY special-casing - all queries now use standard tiered routing
# Identity queries are filtered for banking/finance relevance, then routed by chunk count

