# Quick Start Guide

## Starting the Server

The Thunderclap AI server must be running before you can make queries.

### Step 1: Start the Server

Open a terminal/command prompt and run:

```bash
python server.py
```

You should see:
```
============================================================
Starting Thunderclap AI Server
============================================================
Server: http://localhost:8000
Press Ctrl+C to stop
============================================================
```

### Step 2: Open the Frontend

Open `index.html` in your web browser (double-click the file or open it via File → Open).

### Step 3: Make Queries

Enter your question in the input box and click "Ask Thunderclap".

## Troubleshooting

### "Connection lost" Error

If you see "Connection lost" or "Server is not running":
1. Check if the server is running (you should see the server output in your terminal)
2. If not, start it with: `python server.py`
3. Refresh the browser page to reload the frontend

### Server Won't Start

**Error: "GEMINI_API_KEY environment variable not set!"**
- Set your API key: `$env:GEMINI_API_KEY='your-api-key'` (PowerShell) or `export GEMINI_API_KEY='your-api-key'` (bash)

**Error: "Could not find collection"**
- Build the index first: `python build_index.py`

### Queries Timing Out

- Large queries can take 30-90 seconds
- Very complex queries may take 2-5 minutes
- If queries consistently timeout, try simplifying your question

## Server Status

Check if server is running:
- Visit: http://localhost:8000/health (should return `{"status": "ok"}`)
- Visit: http://localhost:8000/status (shows recent requests and traces)

## Stopping the Server

Press `Ctrl+C` in the terminal where the server is running.

