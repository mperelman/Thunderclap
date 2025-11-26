# Railway 405 Method Not Allowed Fix

## The Problem

Railway logs show:
```
INFO:     100.64.0.3:43758 - "GET /query HTTP/1.1" 405 Method Not Allowed
```

The `/query` endpoint requires **POST** requests, but a **GET** request is being made.

## Possible Causes

### 1. Frontend URL Configuration Issue

The frontend might be using the wrong URL. Check:

**Current frontend code:**
```javascript
const API_URL = (() => {
    const urlParams = new URLSearchParams(window.location.search);
    const apiParam = urlParams.get('api');
    if (apiParam) return apiParam;
    // ...
    return 'http://localhost:8000/query';
})();
```

**If using Railway, the frontend should be:**
```html
https://mperelman.github.io/Thunderclap/?api=https://web-production-c4223.up.railway.app/query
```

**Note:** The `?api=` parameter should point to `/query` endpoint, not just the base URL.

### 2. CORS Preflight Issue

The browser might be making an OPTIONS preflight request that's being logged as GET.

**Check browser console (F12):**
- Look for CORS errors
- Check Network tab for OPTIONS requests

### 3. Direct Browser Access

Someone might be accessing the Railway URL directly in a browser, which makes a GET request.

## The Fix

I've added a GET handler that returns a helpful error message:

```python
@app.get("/query")
async def query_get():
    """Handle GET requests to /query with helpful error message."""
    return JSONResponse(
        status_code=405,
        content={
            "error": "Method Not Allowed",
            "message": "The /query endpoint requires a POST request with JSON body.",
            ...
        }
    )
```

## How to Test

1. **Check frontend URL:**
   - Open frontend: `https://mperelman.github.io/Thunderclap/?api=https://web-production-c4223.up.railway.app/query`
   - Open browser console (F12)
   - Make a query
   - Check Network tab - should see **POST** request

2. **Check Railway logs:**
   - After making a query, check logs
   - Should see: `POST /query HTTP/1.1" 200 OK` (or 503 if data missing)

## Next Steps

1. **Verify frontend URL** - Make sure `?api=` parameter points to `/query` endpoint
2. **Check browser console** - Look for CORS errors or network issues
3. **Test query** - Make a query and check Railway logs for POST request

The GET handler is now in place, so GET requests will return a helpful error instead of crashing.





