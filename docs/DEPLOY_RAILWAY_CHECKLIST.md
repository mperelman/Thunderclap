# Why "Redeploy" Doesn't Change Anything

**Railway "Redeploy" rebuilds the SAME commit.** It does NOT pull new code from GitHub.

So if you click "Redeploy" 3 times, you're running the same old code 3 times.

---

## To get the Cunliffe fix (or any code change) on Railway

### 1. Commit your changes locally

```bash
git status
git add lib/query_engine.py server.py
git commit -m "Cunliffe: sanitizer and body-check"
```

### 2. Push to the branch Railway uses

Railway is usually connected to **main** or **master**. Push there:

```bash
git push origin main
```

(Or `git push origin master` if that's your default branch.)

### 3. Let Railway deploy the new commit

- If Railway is connected to GitHub, it will **auto-deploy** when you push.
- Wait for the new deployment to finish (Railway dashboard → Deployments).
- Do **not** click "Redeploy" on an old deployment — that rebuilds the old commit. Use the **new** deployment that was created by your push.

### 4. Confirm the new code is running

**Option A – Startup logs**

After the new deploy, open Railway → your service → **View Logs**. Look at the **startup** lines. You should see:

```
[STARTUP] CUNLIFFE_SANITIZER=body-check-v2 (answer sanitizer loaded)
```

If you see `CUNLIFFE_SANITIZER=missing` or no such line, the new code is not in the build.

**Option B – Health endpoint**

Open in a browser:

**https://web-production-c4223.up.railway.app/health**

You should see something like:

```json
{"status":"ok","sanitizer":"body-check-v2"}
```

If you see `"sanitizer":"missing"` or no `sanitizer` key, the running app is still old code.

---

## If you don't use Git from this machine

- Make sure the repo Railway deploys from (**mperelman/Thunderclap** on GitHub) has your latest code.
- If you only edit in Cursor and never push, Railway never sees your changes.
- Commit and push from this repo (the one that has `lib/query_engine.py` and `server.py`) to the GitHub repo and branch that Railway is watching.

---

## Summary

| Action | Effect |
|--------|--------|
| Click "Redeploy" in Railway | Rebuilds **same** commit — no new code |
| Push to GitHub (main/master) | New commit → Railway can auto-deploy **new** code |
| Check startup log for `CUNLIFFE_SANITIZER=body-check-v2` | Confirms new build is running |
| Check GET /health for `"sanitizer":"body-check-v2"` | Confirms new code is running |
