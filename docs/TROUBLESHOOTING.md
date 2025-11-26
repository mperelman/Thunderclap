# Troubleshooting Links

## Issue: Links Don't Work

### Step 1: Test Locally First

1. **Start your backend server**:
   ```bash
   python server.py
   ```
   Should show: "Server ready!" on http://localhost:8000

2. **Open frontend in browser**:
   - Go to: `http://localhost:8080/index.html` (if using a test server)
   - Or open `index.html` directly in your browser

3. **Test a query** - if this works locally, the issue is deployment

### Step 2: Deploy to GitHub Pages

1. **Push all changes**:
   ```bash
   python deploy.py "Add GitHub Pages support"
   ```

2. **Enable GitHub Pages**:
   - Go to: https://github.com/mperelman/Thunderclap/settings/pages
   - Under "Source", select: **"GitHub Actions"**
   - Click Save

3. **Wait for deployment** (2-3 minutes):
   - Go to: https://github.com/mperelman/Thunderclap/actions
   - Wait for "Deploy to GitHub Pages" workflow to complete (green checkmark)

4. **Access your site**:
   - https://mperelman.github.io/Thunderclap/

### Step 3: Backend API Issue

**Problem**: Frontend loads but queries fail

**Solution**: The frontend needs a backend API. Options:

**Option A: Use ngrok (quick test)**
```bash
# Terminal 1
python server.py

# Terminal 2  
ngrok http 8000
# Copy the https URL (e.g., https://abc123.ngrok.io)

# Then use:
https://mperelman.github.io/Thunderclap/?api=https://abc123.ngrok.io/query
```

**Option B: Deploy backend to Railway**
1. Sign up: https://railway.app
2. New Project → Deploy from GitHub
3. Connect repo: `mperelman/Thunderclap`
4. Set env: `GEMINI_API_KEY=your_key`
5. Get URL: `https://thunderclap-production.up.railway.app`
6. Use: `https://mperelman.github.io/Thunderclap/?api=https://thunderclap-production.up.railway.app/query`

### Common Errors

**404 Not Found**: GitHub Pages not deployed yet - wait for workflow to complete

**CORS Error**: Backend not allowing GitHub Pages origin - already fixed in server.py

**Connection Refused**: Backend not running or wrong URL - check API URL parameter

**"Server is not running"**: Backend API is down - start it or deploy it

