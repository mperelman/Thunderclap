# Railway Volume Setup - Fix "No space left on device"

## The Problem
Railway's container filesystem is running out of space when downloading LFS files (~197MB). Error: `No space left on device`

**Root Cause**: The volume exists but is NOT mounted at `/app/data`. The app writes to `/app/data/vectordb/` which is on the container filesystem (limited space), not the volume.

## Solution: Mount Railway Volume at `/app/data`

Railway Volumes provide persistent storage that doesn't count against container disk limits.

### Step 1: Increase Volume Size (or Create New)

**If volume already exists (99% full):**
1. Go to Railway dashboard → your service
2. Click "Volumes" tab
3. Find your volume (`web-volume` or similar)
4. Click on it → "Settings" or "Edit"
5. Increase size to **at least 1GB** (2GB recommended)
6. Save changes

**OR create new larger volume:**
1. Go to Railway dashboard → your service
2. Click "Volumes" tab
3. Click "New Volume" or "Create Volume"
4. Name: `thunderclap-data`
5. Size: **1GB minimum** (2GB recommended for safety)
6. Click "Create"

### Step 2: Mount Volume at `/app/data` (CRITICAL)
1. Still in Volumes tab
2. Find the volume you just created
3. Click "Mount" or "Attach" button
4. **Mount path MUST be**: `/app/data` (exactly this path, no trailing slash)
5. Click "Mount" or "Save"

**IMPORTANT**: The mount path must be `/app/data` because the app writes to `data/vectordb/` relative to `/app/`.

### Step 3: Verify Mount
After mounting, Railway will redeploy. Check the deployment logs for:
```
SUCCESS: /app/data is mounted on a volume (persistent storage)
```

If you see:
```
WARNING: Railway volume detected but NOT mounted at /app/data
```
Then the volume is mounted at the wrong path. Unmount it and remount at `/app/data`.

### Step 4: Test
After redeploy, the startup script will download LFS files to the volume (which has more space). The "No space left on device" error should be resolved.

## Troubleshooting

**"No space left on device" persists:**
- Verify volume is mounted: Check logs for volume mount message
- Verify mount path: Must be `/app/data`, not `/data` or `/app/data/`
- Check volume size: Should be at least 1GB
- Unmount and remount: Sometimes remounting fixes issues

**Volume already exists but wrong path:**
- Unmount the volume from current path
- Remount at `/app/data`

