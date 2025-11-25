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

# Install curl for healthcheck + Git LFS + file command + sqlite3 (needed to fetch LFS files and verify DB)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    git-lfs \
    file \
    sqlite3 \
    bc \
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
    echo "=== Checking out main branch (skipping LFS files to avoid quota errors) ===" && \
    GIT_LFS_SKIP_SMUDGE=1 git checkout -f main || \
    (echo "=== Checkout failed, trying without LFS ===" && \
     git config lfs.fetchexclude "*" && \
     git checkout -f main) || \
    (echo "=== Checkout still failed, continuing anyway ===" && true) && \
    echo "=== Resetting to ensure clean state ===" && \
    git reset --hard origin/main 2>/dev/null || true && \
    echo "=== Checking Git LFS status ===" && \
    git lfs version && \
    echo "=== Attempting to fetch LFS files (will continue if quota exceeded) ===" && \
    (git lfs pull origin main 2>&1 || \
     (echo "=== LFS pull failed, trying fetch+checkout ===" && \
      git lfs fetch origin main 2>&1 && \
      git lfs checkout 2>&1) || \
     (echo "=== LFS fetch failed, trying specific files ===" && \
      git lfs checkout data/vectordb/chroma.sqlite3 data/deduplicated_terms/deduplicated_cache.json 2>&1) || \
     echo "=== WARNING: LFS download failed (quota exceeded or network issue) ===" && \
     echo "=== This is OK - download_lfs.sh will download files at runtime ===") && \
    echo "=== Checking if LFS files were downloaded ===" && \
    if [ -f "data/vectordb/chroma.sqlite3" ]; then \
        SIZE=$(stat -f%z data/vectordb/chroma.sqlite3 2>/dev/null || stat -c%s data/vectordb/chroma.sqlite3 2>/dev/null || echo 0); \
        if [ "$SIZE" -gt 1000000 ]; then \
            echo "=== SUCCESS: LFS files downloaded during build ==="; \
        else \
            echo "=== INFO: LFS files are pointer files (will be downloaded at runtime) ==="; \
        fi; \
    else \
        echo "=== INFO: LFS files not found (will be downloaded at runtime) ==="; \
    fi && \
    echo "=== Build complete - download_lfs.sh will handle LFS files at startup ==="

# Verify LFS files (but don't fail build if missing - download_lfs.sh handles it)
RUN echo "=== Checking LFS files status ===" && \
    if [ -f "data/vectordb/chroma.sqlite3" ]; then \
        SIZE=$(stat -f%z data/vectordb/chroma.sqlite3 2>/dev/null || stat -c%s data/vectordb/chroma.sqlite3 2>/dev/null || echo 0); \
        if [ "$SIZE" -gt 1000000 ]; then \
            echo "=== SUCCESS: chroma.sqlite3 downloaded during build ($(echo "scale=2; $SIZE/1024/1024" | bc) MB) ===" && \
            file data/vectordb/chroma.sqlite3; \
        else \
            echo "=== INFO: chroma.sqlite3 is a pointer file (will be downloaded at runtime) ==="; \
        fi; \
    else \
        echo "=== INFO: chroma.sqlite3 not found (will be downloaded at runtime) ==="; \
    fi && \
    if [ -f "data/deduplicated_terms/deduplicated_cache.json" ]; then \
        SIZE=$(stat -f%z data/deduplicated_terms/deduplicated_cache.json 2>/dev/null || stat -c%s data/deduplicated_terms/deduplicated_cache.json 2>/dev/null || echo 0); \
        if [ "$SIZE" -gt 1000000 ]; then \
            echo "=== SUCCESS: deduplicated_cache.json downloaded during build ==="; \
        else \
            echo "=== INFO: deduplicated_cache.json is a pointer file (will be downloaded at runtime) ==="; \
        fi; \
    else \
        echo "=== INFO: deduplicated_cache.json not found (will be downloaded at runtime) ==="; \
    fi && \
    echo "=== Build complete - download_lfs.sh will download LFS files at container startup ==="

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
# Use explicit path and ensure script runs
CMD ["sh", "-c", "echo '=== Starting container ===' && pwd && ls -la download_lfs.sh && chmod +x download_lfs.sh && ./download_lfs.sh && echo '=== Starting server ===' && uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000} --timeout-keep-alive 600"]
