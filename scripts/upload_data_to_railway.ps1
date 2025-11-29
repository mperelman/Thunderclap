# PowerShell script to upload data folder to Railway using Railway CLI

Write-Host "Uploading data folder to Railway..." -ForegroundColor Cyan
Write-Host ""

# Check if Railway CLI is available
try {
    $railwayVersion = npx @railway/cli --version 2>&1
    Write-Host "✅ Railway CLI found: $railwayVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ ERROR: Railway CLI not found!" -ForegroundColor Red
    Write-Host "Install it with: npm install -g @railway/cli" -ForegroundColor Yellow
    exit 1
}

# Check if logged in
try {
    $whoami = npx @railway/cli whoami 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Not logged in. Please run: npx @railway/cli login" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Logged in as: $whoami" -ForegroundColor Green
} catch {
    Write-Host "❌ Not logged in. Please run: npx @railway/cli login" -ForegroundColor Red
    exit 1
}

# Link to project if needed
Write-Host ""
Write-Host "Linking to Railway project..." -ForegroundColor Cyan
npx @railway/cli link
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Link failed or already linked. Continuing..." -ForegroundColor Yellow
}

# Create data directory in Railway volume
Write-Host ""
Write-Host "Creating /app/data directory..." -ForegroundColor Cyan
npx @railway/cli run --service web mkdir -p /app/data/vectordb

# Upload indices.json
Write-Host ""
Write-Host "Uploading indices.json..." -ForegroundColor Cyan
if (Test-Path "data/indices.json") {
    Get-Content "data/indices.json" | npx @railway/cli run --service web sh -c "cat > /app/data/indices.json"
    Write-Host "✅ indices.json uploaded" -ForegroundColor Green
} else {
    Write-Host "⚠️  indices.json not found" -ForegroundColor Yellow
}

# Upload endnotes.json if exists
Write-Host ""
Write-Host "Uploading endnotes.json..." -ForegroundColor Cyan
if (Test-Path "data/endnotes.json") {
    Get-Content "data/endnotes.json" | npx @railway/cli run --service web sh -c "cat > /app/data/endnotes.json"
    Write-Host "✅ endnotes.json uploaded" -ForegroundColor Green
} else {
    Write-Host "⚠️  endnotes.json not found" -ForegroundColor Yellow
}

# Upload chunk_to_endnotes.json if exists
Write-Host ""
Write-Host "Uploading chunk_to_endnotes.json..." -ForegroundColor Cyan
if (Test-Path "data/chunk_to_endnotes.json") {
    Get-Content "data/chunk_to_endnotes.json" | npx @railway/cli run --service web sh -c "cat > /app/data/chunk_to_endnotes.json"
    Write-Host "✅ chunk_to_endnotes.json uploaded" -ForegroundColor Green
} else {
    Write-Host "⚠️  chunk_to_endnotes.json not found" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "✅ Data files uploaded!" -ForegroundColor Green
Write-Host ""
Write-Host "⚠️  NOTE: vectordb/ folder is large and complex." -ForegroundColor Yellow
Write-Host "   You may need to upload it manually via Railway Volumes web interface." -ForegroundColor Yellow
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Go to Railway → Your service → Volumes tab" -ForegroundColor White
Write-Host "2. Ensure a volume is mounted to /app/data" -ForegroundColor White
Write-Host "3. Upload the entire data/vectordb/ folder contents" -ForegroundColor White
Write-Host ""

