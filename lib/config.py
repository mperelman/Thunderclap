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
MIN_CHUNKS_FOR_LLM = 5  # Minimum chunks to send to LLM (ensures comprehensive coverage)
MIN_CHUNKS_FOR_FIRM_QUERY = 50  # Minimum chunks for firm queries (ensures comprehensive coverage)

# LLM settings (optional)
DEFAULT_LLM_MODEL = "gpt-4o-mini"  # OpenAI model
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"  # Fallback label; actual model from lib.llm_config.MODEL_PRIORITY
LLM_TEMPERATURE = 0.3  # Lower = more factual

# Answer generation parameters
MAX_SENTENCES_PER_PARAGRAPH = 3  # Hard limit for paragraph length
MAX_REVIEW_ITERATIONS = 2  # Maximum iterations for answer review/fixing (reduced to prevent timeouts)
BATCH_SIZE = 20  # Process chunks in batches of this size (DEPRECATED - use token-based batching)
BATCH_PAUSE_SECONDS = 5  # Pause between batches to avoid rate limits (reduced from 15 to speed up queries)
CHUNK_RETRIEVAL_BATCH_SIZE = 200  # Batch size for retrieving chunks from database
MAX_ANSWER_LENGTH = 15000  # Maximum answer length in characters (for truncation)
# Maximum time for query processing. 0 = no timeout (for batch/script runs). Set QUERY_TIMEOUT_SECONDS env to override.
QUERY_TIMEOUT_SECONDS = int(os.environ.get("QUERY_TIMEOUT_SECONDS", "420") or "420")

# Token-based batching (more efficient than chunk count)
MAX_TOKENS_PER_MINUTE = 250000  # Max tokens per minute (user limit)
MAX_TOKENS_PER_REQUEST = 200000  # Max tokens per API call (conservative limit under 250k/min)
ESTIMATED_WORDS_PER_CHUNK = 400  # Average words per chunk (from CHUNK_SIZE)
TOKENS_PER_WORD = 1.3  # Rough estimate: 1 word ≈ 1.3 tokens
MAX_WORDS_PER_REQUEST = 150000  # Max words per request (~200K tokens / 1.3)
# Fraction of token budget used per request. RPM (requests/min) is usually the bottleneck; TPM/RPD are under-used. Higher = fewer requests, less RPM pressure, better TPM use. Default 0.7 (was 0.35). Set TOKEN_BUDGET_FRACTION env to override.
try:
    _raw = float(os.environ.get("TOKEN_BUDGET_FRACTION", "0.7") or "0.7")
except (ValueError, TypeError):
    _raw = 0.7
TOKEN_BUDGET_FRACTION = max(0.1, min(1.0, _raw))

# Answer review thresholds
EARLY_STOP_GAP_THRESHOLD = 10  # Years gap threshold for detecting early stopping
SPARSE_RESULTS_THRESHOLD = 5  # Below this, augment with endnotes

# Control/influence query parameters
CONTROL_INFLUENCE_EARLY_CHUNK_LIMIT = 8  # Limit chunks BEFORE augmentation for control/influence queries
CONTROL_INFLUENCE_FINAL_CHUNK_LIMIT = 5  # Final chunk limit AFTER deduplication for control/influence queries
CONTROL_INFLUENCE_MAX_RETRIES = 2  # Reduced retries for control/influence queries (prevents long waits)
CONTROL_INFLUENCE_SLOW_THRESHOLD_SECONDS = 120  # Threshold for warning about slow LLM calls

# Note: Removed BROAD_IDENTITY special-casing - all queries now use standard tiered routing
# Identity queries are filtered for banking/finance relevance, then routed by chunk count


def is_railway() -> bool:
    """Return True when running inside a Railway deployment."""
    return (
        os.getenv('RAILWAY_ENVIRONMENT') is not None
        or os.getenv('RAILWAY_PROJECT_ID') is not None
    )


def safe_load_json(file_path: str, default=None):
    """Load a JSON file, returning *default* if the file is missing or malformed."""
    import json
    if not os.path.exists(file_path):
        return default
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[CONFIG] Warning: could not load {file_path}: {e}")
        return default

