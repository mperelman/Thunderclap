# Check Railway Logs for Current Error

## The Issue

You're getting "API Key not found" errors. The server trace you showed is from **old requests**. We need to check the **CURRENT** Railway logs to see what's happening now.

## How to Check Railway Logs

1. **Go to Railway**: https://railway.app
2. **Open your Thunderclap service**
3. **Click "View Logs"** or **"Deployments"** → **"View Logs"**
4. **Look for the MOST RECENT entries** (scroll to bottom)

## What to Look For

### Good Signs ✅
```
[OK] Gemini API configured (2.5 Flash, 15 RPM / 1M TPM / 200 RPD)
Connecting to document database...
[OK] Connected to database (X indexed chunks)
```

### Bad Signs ❌
```
[ERROR] Gemini setup failed: ...
[WARNING] No Gemini API key found
ERROR: GEMINI_API_KEY environment variable not set!
```

## Verify API Key is Set

1. In Railway dashboard, go to **Variables** tab
2. **Check if `GEMINI_API_KEY` exists**
3. **Value should be**: `YOUR_API_KEY_HERE` (get from https://aistudio.google.com/apikey)
4. **Make sure**:
   - No spaces before/after
   - No quotes around it
   - Exact match

## Common Issues

**Issue 1: Key not set**
- Railway Variables tab → Add `GEMINI_API_KEY`
- Value: `YOUR_API_KEY_HERE` (get from https://aistudio.google.com/apikey)
- Save

**Issue 2: Key has extra characters**
- Copy-paste exactly: `YOUR_API_KEY_HERE` (no spaces, no quotes)
- No spaces, no quotes

**Issue 3: Railway hasn't restarted**
- After updating variable, Railway should auto-restart
- If not, manually restart: Settings → Restart

**Issue 4: Key not activated at Google**
- Go to: https://makersuite.google.com/app/apikey
- Verify key exists and is active
- Make sure Gemini API is enabled

## Next Steps

1. **Check CURRENT Railway logs** (not old server trace)
2. **Share what you see** - especially any `[ERROR]` or `[WARNING]` messages
3. **Verify API key is set** in Railway Variables
4. **Test again** after verifying

The server trace you showed is from old requests. We need to see what Railway logs show RIGHT NOW.




