warning: in the working copy of 'server.py', LF will be replaced by CRLF the next time Git touches it
[1mdiff --git a/server.py b/server.py[m
[1mindex b7a2cb5..ded9ebc 100644[m
[1m--- a/server.py[m
[1m+++ b/server.py[m
[36m@@ -223,6 +223,24 @@[m [mdef get_status():[m
         "trace_count": len(TRACE_BUFFER)[m
     }[m
 [m
[32m+[m[32m@app.get("/terms")[m
[32m+[m[32mdef get_indexed_terms():[m
[32m+[m[32m    """Get list of indexed terms for hyperlinking in responses."""[m
[32m+[m[32m    from lib.config import INDICES_FILE[m
[32m+[m[32m    try:[m
[32m+[m[32m        if os.path.exists(INDICES_FILE):[m
[32m+[m[32m            with open(INDICES_FILE, 'r', encoding='utf-8') as f:[m
[32m+[m[32m                data = json.load(f)[m
[32m+[m[32m            terms = list(data.get('term_to_chunks', {}).keys())[m
[32m+[m[32m            # Filter out very short terms and common words[m
[32m+[m[32m            filtered_terms = [t for t in terms if len(t) > 3 and t.lower() not in ['the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use']][m
[32m+[m[32m            return {"terms": filtered_terms}[m
[32m+[m[32m        else:[m
[32m+[m[32m            return {"terms": []}[m
[32m+[m[32m    except Exception as e:[m
[32m+[m[32m        print(f"[ERROR] Failed to load indexed terms: {e}")[m
[32m+[m[32m        return {"terms": []}[m
[32m+[m
 if __name__ == "__main__":[m
     import uvicorn[m
     print("="*60)[m
