# Optimized Dockerfile for Railway deployment
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (excludes data/ via .dockerignore)
COPY . .

# Expose port
EXPOSE $PORT

# Run server
CMD uvicorn server:app --host 0.0.0.0 --port $PORT

