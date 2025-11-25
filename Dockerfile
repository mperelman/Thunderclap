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

# Install curl for healthcheck + Git LFS + file command (needed to fetch LFS files)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    git-lfs \
    file \
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
# Note: .git/ is NOT included in Docker build context, so we'll initialize git
COPY . .

# Initialize git repository and fetch LFS files from remote
# Railway clones the repo, so we can fetch LFS files directly from GitHub
RUN echo "=== Initializing git repository ===" && \
    git init && \
    git config user.name "Railway Build" && \
    git config user.email "build@railway.app" && \
    git remote add origin https://github.com/mperelman/Thunderclap.git && \
    echo "=== Fetching git refs from remote ===" && \
    git fetch origin main:main && \
    echo "=== Checking out main branch (will overwrite existing files) ===" && \
    git checkout -f main && \
    echo "=== Resetting to ensure clean state ===" && \
    git reset --hard origin/main && \
    echo "=== Checking Git LFS status ===" && \
    git lfs version && \
    echo "=== Checking LFS pointer files after checkout ===" && \
    file data/vectordb/chroma.sqlite3 2>/dev/null && \
    ls -lh data/vectordb/chroma.sqlite3 && \
    echo "=== Fetching LFS files from remote (using pull) ===" && \
    git lfs pull origin main || \
    (echo "=== Pull failed, trying fetch+checkout ===" && \
     git lfs fetch origin main && \
     echo "=== Checking LFS objects after fetch ===" && \
     git lfs ls-files | head -5 && \
     echo "=== Running LFS checkout ===" && \
     git lfs checkout) || \
    (echo "=== Trying to checkout specific files ===" && \
     git lfs checkout data/vectordb/chroma.sqlite3 data/deduplicated_terms/deduplicated_cache.json) && \
    echo "=== Verifying files after checkout ===" && \
    file data/vectordb/chroma.sqlite3 && \
    ls -lh data/vectordb/chroma.sqlite3 && \
    if [ ! -s data/vectordb/chroma.sqlite3 ] || [ $(stat -f%z data/vectordb/chroma.sqlite3 2>/dev/null || stat -c%s data/vectordb/chroma.sqlite3 2>/dev/null || echo 0) -lt 1000000 ]; then \
        echo "ERROR: chroma.sqlite3 is still a pointer file or too small!" && \
        echo "File type:" && \
        file data/vectordb/chroma.sqlite3 && \
        echo "File size:" && \
        ls -lh data/vectordb/chroma.sqlite3 && \
        echo "LFS status:" && \
        git lfs ls-files data/vectordb/chroma.sqlite3 && \
        exit 1; \
    fi && \
    echo "=== LFS files verified successfully ==="

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

# Copy LFS download script
COPY download_lfs.sh .
RUN chmod +x download_lfs.sh

# Run server with explicit timeout settings to prevent Railway proxy timeout
# Railway's proxy likely times out at 60s, so we set uvicorn to 600s (10 min)
# First try to download LFS files if needed, then start server
CMD ["sh", "-c", "./download_lfs.sh && uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000} --timeout-keep-alive 600"]
