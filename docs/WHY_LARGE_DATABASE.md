# Why is the Database So Large?

## You're NOT Loading an LLM Model

**Important**: We're **NOT** loading an LLM model locally. We use **Google's Gemini API** (cloud-based). No local model files.

## What IS Taking Up Space: ChromaDB Vector Database

The **177MB file** (`chroma.sqlite3`) is a **vector database** (ChromaDB) that stores:

### What's Inside:
1. **1,509 document chunks** (from your Word docs)
2. **Embeddings** (384-dimensional vectors) for each chunk (~1KB each)
3. **Full text** of each chunk (~400 words = ~2KB each)
4. **Metadata** (filename, chunk ID, etc.)
5. **Index structures** (for fast similarity search)

### Size Breakdown:
- **Embeddings**: 1,509 chunks × ~1KB = ~1.5MB
- **Text**: 1,509 chunks × ~2KB = ~3MB
- **Metadata**: ~1MB
- **SQLite overhead + indexes**: ~170MB (SQLite stores data efficiently but indexes add overhead)

**Total: ~177MB**

## Why So Large?

ChromaDB uses SQLite with HNSW (Hierarchical Navigable Small World) indexes for fast similarity search. These indexes are large but necessary for:
- Finding relevant chunks quickly
- Semantic search (finding chunks by meaning, not just keywords)

## Can We Make It Smaller?

**Not easily.** The size comes from:
1. **Number of chunks** (1,509) - fixed by your documents
2. **Chunk size** (400 words) - needed for context
3. **Index structures** - needed for fast search

**Options:**
- Reduce chunk size → worse search quality
- Reduce number of chunks → lose document coverage
- Remove indexes → much slower queries

## Bottom Line

The 177MB database is **normal** for 1,509 document chunks with vector search. It's not an LLM model - it's your indexed documents ready for semantic search.

**Solution**: Just increase Railway volume to 1GB (plenty of room for 177MB + overhead).



