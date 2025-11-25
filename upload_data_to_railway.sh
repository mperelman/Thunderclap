#!/bin/bash
# Script to upload data folder to Railway using Railway CLI

echo "Uploading data folder to Railway..."
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "ERROR: Railway CLI not found!"
    echo "Install it with: npm install -g @railway/cli"
    exit 1
fi

# Check if logged in
if ! railway whoami &> /dev/null; then
    echo "Logging in to Railway..."
    railway login
fi

# Link to project if needed
echo "Linking to Railway project..."
railway link

# Create data directory in Railway volume
echo "Creating /app/data directory..."
railway run --service web mkdir -p /app/data/vectordb

# Upload indices.json
echo "Uploading indices.json..."
railway run --service web sh -c "cat > /app/data/indices.json" < data/indices.json

# Upload endnotes.json if exists
if [ -f "data/endnotes.json" ]; then
    echo "Uploading endnotes.json..."
    railway run --service web sh -c "cat > /app/data/endnotes.json" < data/endnotes.json
fi

# Upload chunk_to_endnotes.json if exists
if [ -f "data/chunk_to_endnotes.json" ]; then
    echo "Uploading chunk_to_endnotes.json..."
    railway run --service web sh -c "cat > /app/data/chunk_to_endnotes.json" < data/chunk_to_endnotes.json
fi

echo ""
echo "✅ Data files uploaded!"
echo ""
echo "⚠️  NOTE: vectordb/ folder is large and complex."
echo "   You may need to upload it manually via Railway Volumes web interface."
echo ""
echo "Next steps:"
echo "1. Go to Railway → Your service → Volumes tab"
echo "2. Create a volume mounted to /app/data"
echo "3. Upload the entire data/vectordb/ folder contents"
echo ""

