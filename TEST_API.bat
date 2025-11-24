@echo off
REM ============================================================
REM Test the Thunderclap AI API
REM ============================================================

echo.
echo ============================================================
echo       Testing Thunderclap AI API
echo ============================================================
echo.
echo Make sure the server is running (START_SERVER.bat)!
echo.
pause

echo.
echo [1/3] Testing health check...
curl http://localhost:8000/health
echo.
echo.

echo [2/3] Testing API info endpoint...
curl http://localhost:8000/
echo.
echo.

echo [3/3] Testing query endpoint with sample question...
echo Question: "Tell me about Lehman"
echo.
curl -X POST http://localhost:8000/query -H "Content-Type: application/json" -d "{\"question\": \"Tell me about Lehman\", \"max_length\": 800}"
echo.
echo.

echo ============================================================
echo       Test Complete!
echo ============================================================
echo.
echo If all tests passed, you can:
echo   1. Open simple_frontend.html in your browser
echo   2. Try asking questions about banking history
echo.
pause




