# Server Not Running - Error Message Fix
**Date:** 2025-01-21  
**Issue:** "Connection lost" error when server is not running

## Problem

When the server is not running, users see a generic "Connection lost" error message that doesn't clearly indicate the server needs to be started.

## Root Cause

The frontend error handler catches "Failed to fetch" / "NetworkError" but doesn't distinguish between:
1. Server not running (connection refused)
2. Server running but query timeout/error

## Solution

Added server health check in error handler to detect if server is running and show appropriate message.

### Changes Made

**File:** `index.html` (lines 1082-1112)

**Before:**
```javascript
} else if (errorMsg.includes('Failed to fetch') || errorMsg.includes('NetworkError')) {
    errorMsg = '⚠️ Connection lost. The query might be taking too long...';
}
```

**After:**
```javascript
} else if (errorMsg.includes('Failed to fetch') || errorMsg.includes('NetworkError')) {
    // Try to check if server is running (async check)
    const checkServer = async () => {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 2000);
            const healthCheck = await fetch('http://localhost:8000/health', { 
                method: 'GET',
                signal: controller.signal
            });
            clearTimeout(timeoutId);
            if (healthCheck.ok) {
                // Server is running - likely a timeout or processing issue
                return '⚠️ Connection lost. The query might be taking too long...';
            }
        } catch (e) {
            // Server is not running or not accessible
            return '⚠️ Server is not running.\n\n' +
                   'Please start the server by running: python server.py\n\n' +
                   'Then try your query again.';
        }
        return '⚠️ Connection lost. Please check if the server is running: python server.py';
    };
    
    // Show default message immediately, then update when check completes
    errorMsg = '⚠️ Connection lost. Checking server status...';
    checkServer().then(msg => {
        errorMsg = msg;
        document.getElementById('answer').innerHTML = `<p style="white-space: pre-line; line-height: 1.8;">${errorMsg}</p>`;
    });
}
```

## Expected Behavior

### Before Fix
- ❌ Generic "Connection lost" message
- ❌ No indication server needs to be started
- ❌ User confusion about what to do

### After Fix
- ✅ Checks if server is running
- ✅ Shows clear message: "Server is not running. Please start the server by running: python server.py"
- ✅ Provides actionable instructions

## Testing

1. **Server Not Running:**
   - Stop server
   - Try a query
   - Should see: "⚠️ Server is not running. Please start the server by running: python server.py"

2. **Server Running but Query Fails:**
   - Start server
   - Try a query that fails
   - Should see: "⚠️ Connection lost. The query might be taking too long..."

## Related Files

- `index.html` - Error handling with server health check
- `server.py` - Server health endpoint (`/health`)

