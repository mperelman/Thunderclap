# HTTP upload script for ChromaDB database
# Much faster than SSH pipes!

param(
    [string]$ServiceUrl = "https://web-production-c4223.up.railway.app",
    [string]$SourceFile = "data\vectordb\chroma.sqlite3"
)

# Change to script's parent directory (project root)
$scriptDir = Split-Path $MyInvocation.MyCommand.Path
$projectRoot = Split-Path $scriptDir -Parent
Set-Location $projectRoot
Write-Host "Working directory: $projectRoot" -ForegroundColor Gray
Write-Host ""

# Resolve source file path relative to project root
$SourceFile = Join-Path $projectRoot $SourceFile
if (-not (Test-Path $SourceFile)) {
    Write-Host "ERROR: Source file not found: $SourceFile" -ForegroundColor Red
    exit 1
}

$fileSize = (Get-Item $SourceFile).Length
$fileSizeMB = [math]::Round($fileSize / 1MB, 2)

Write-Host "`n=== HTTP DATABASE UPLOAD ===" -ForegroundColor Cyan
Write-Host "File: $SourceFile" -ForegroundColor White
Write-Host "Size: $fileSizeMB MB" -ForegroundColor White
Write-Host "Target: $ServiceUrl/admin/upload-database" -ForegroundColor White
Write-Host ""

# Read file as bytes
Write-Host "Reading file..." -ForegroundColor Cyan
$fileBytes = [System.IO.File]::ReadAllBytes($SourceFile)

# Create multipart form data
Write-Host "Preparing upload..." -ForegroundColor Cyan
$boundary = [System.Guid]::NewGuid().ToString()
$LF = "`r`n"

$bodyLines = @(
    "--$boundary",
    "Content-Disposition: form-data; name=`"file`"; filename=`"chroma.sqlite3`"",
    "Content-Type: application/octet-stream",
    "",
    [System.Text.Encoding]::GetEncoding("iso-8859-1").GetString($fileBytes),
    "--$boundary--"
)
$body = $bodyLines -join $LF
$bodyBytes = [System.Text.Encoding]::GetEncoding("iso-8859-1").GetBytes($body)

Write-Host "Uploading $fileSizeMB MB (this will take 2-5 minutes)..." -ForegroundColor Yellow
Write-Host "Progress: " -NoNewline -ForegroundColor Cyan

try {
    $response = Invoke-WebRequest -Uri "$ServiceUrl/admin/upload-database" `
        -Method POST `
        -ContentType "multipart/form-data; boundary=$boundary" `
        -Body $bodyBytes `
        -TimeoutSec 600 `
        -UseBasicParsing
    
    if ($response.StatusCode -eq 200) {
        Write-Host "`n✅ SUCCESS!" -ForegroundColor Green
        $result = $response.Content | ConvertFrom-Json
        Write-Host "  $($result.message)" -ForegroundColor Green
        Write-Host "  Path: $($result.path)" -ForegroundColor Gray
        Write-Host "  Size: $([math]::Round($result.size_bytes / 1MB, 2)) MB" -ForegroundColor Gray
    } else {
        Write-Host "`n✗ Upload failed: HTTP $($response.StatusCode)" -ForegroundColor Red
        Write-Host $response.Content -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "`n✗ Upload failed: $_" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "Response: $responseBody" -ForegroundColor Red
    }
    exit 1
}
