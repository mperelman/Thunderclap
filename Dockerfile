# Optimized multi-stage Dockerfile for Railway
# Removes sentence-transformers and other indexing-only packages

# Stage 1: Build dependencies
FROM python:3.11-slim as builder

WORKDIR /app

# Install minimal build dependencies + Git LFS (needed to fetch LFS-tracked files)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    git \
    git-lfs \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && git lfs install

# Copy minimal runtime requirements (excludes sentence-transformers, openai, python-docx)
COPY requirements.txt .

# Install Python dependencies (no cache)
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime (ultra-minimal)
FROM python:3.11-slim

WORKDIR /app

# Install curl for healthcheck + Git LFS (needed to fetch LFS files)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    git-lfs \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && git lfs install

# Copy only installed packages from builder
COPY --from=builder /root/.local /root/.local

# Copy only runtime code
COPY server.py .
COPY lib/ ./lib/
COPY public/ ./public/
# Copy entire repo context (Railway clones the repo)
# .git/ and data/ are now included (removed from .dockerignore)
COPY . .

# Debug: Check what we have before LFS pull
RUN echo "=== Checking Git LFS status ===" && \
    git lfs version && \
    git lfs ls-files | head -5 && \
    echo "=== Checking data folder ===" && \
    ls -la data/ 2>/dev/null | head -10 || echo "data/ folder not found" && \
    echo "=== Checking for LFS pointer files ===" && \
    file data/vectordb/chroma.sqlite3 2>/dev/null || echo "chroma.sqlite3 not found" && \
    file data/deduplicated_terms/deduplicated_cache.json 2>/dev/null || echo "deduplicated_cache.json not found"

# Fetch LFS files to replace pointers with actual files
RUN echo "=== Fetching LFS files ===" && \
    git lfs pull || \
    (echo "=== LFS pull failed, trying fetch+checkout ===" && \
     git lfs fetch --all && \
     git lfs checkout) || \
    (echo "=== ERROR: Could not fetch LFS files ===" && \
     echo "Checking what we have:" && \
     ls -lh data/vectordb/chroma.sqlite3 2>/dev/null || echo "chroma.sqlite3 missing" && \
     exit 1)

# Verify LFS files were fetched (fail build if missing)
RUN echo "=== Verifying LFS files after fetch ===" && \
    if [ ! -f data/vectordb/chroma.sqlite3 ] || [ ! -s data/vectordb/chroma.sqlite3 ]; then \
        echo "ERROR: chroma.sqlite3 is missing or empty!" && \
        ls -lh data/vectordb/ 2>/dev/null || echo "vectordb folder missing" && \
        exit 1; \
    fi && \
    if [ ! -f data/deduplicated_terms/deduplicated_cache.json ] || [ ! -s data/deduplicated_terms/deduplicated_cache.json ]; then \
        echo "ERROR: deduplicated_cache.json is missing or empty!" && \
        exit 1; \
    fi && \
    echo "=== Verifying file types ===" && \
    file data/vectordb/chroma.sqlite3 && \
    file data/deduplicated_terms/deduplicated_cache.json && \
    echo "=== File sizes ===" && \
    ls -lh data/vectordb/chroma.sqlite3 && \
    ls -lh data/deduplicated_terms/deduplicated_cache.json && \
    echo "=== LFS files verified successfully ==="

# Environment
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE $PORT

# Health check (removed requests dependency - use curl instead)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:$PORT/health || exit 1

# Run server with explicit timeout settings to prevent Railway proxy timeout
# Railway's proxy likely times out at 60s, so we set uvicorn to 600s (10 min)
CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000} --timeout-keep-alive 600"]
