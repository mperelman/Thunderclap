# Optimized multi-stage Dockerfile for Railway
# Removes sentence-transformers and other indexing-only packages

# Stage 1: Build dependencies
FROM python:3.11-slim as builder

WORKDIR /app

# Install minimal build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy minimal runtime requirements (excludes sentence-transformers, openai, python-docx)
COPY requirements.txt .

# Install Python dependencies (no cache)
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime (ultra-minimal)
FROM python:3.11-slim

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy only installed packages from builder
COPY --from=builder /root/.local /root/.local

# Copy only runtime code
COPY server.py .
COPY lib/ ./lib/
COPY public/ ./public/
# Copy data folder (for Railway deployment - includes ChromaDB and indices)
COPY data/ ./data/

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
