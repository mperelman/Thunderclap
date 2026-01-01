# Thunderclap AI Server Startup Script
cd C:\Users\perel\OneDrive\Apps\thunderclap-ai
$env:GEMINI_API_KEY='AIzaSyBlqE1F2G_L5l2Lg81gyt0UWcME_K3inFo'
Write-Host "Starting Thunderclap AI Server..." -ForegroundColor Green
Write-Host "API Key: $($env:GEMINI_API_KEY.Substring(0,20))..." -ForegroundColor Gray
python server.py
