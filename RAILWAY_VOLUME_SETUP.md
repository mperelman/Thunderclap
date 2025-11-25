# Railway Volume Setup - Fix "No space left on device"

## The Problem
Railway's container filesystem is running out of space when downloading LFS files (~197MB). Error: `No space left on device`

## Solution: Use Railway Volumes

Railway Volumes provide persistent storage that doesn't count against container disk limits.

### Step 1: Create Volume in Railway
1. Go to Railway dashboard → your service
2. Click "Volumes" tab
3. Click "Create Volume"
4. Name: `thunderclap-data`
5. Size: 1GB (or larger)
6. Click "Create"

### Step 2: Mount Volume to Service
1. Still in Volumes tab
2. Click the volume you just created
3. Click "Mount" or "Attach to Service"
4. Mount path: `/app/data`
5. Click "Mount"

### Step 3: Redeploy
Railway will automatically redeploy. The data folder will now be on persistent storage with more space.

## Alternative: Clean Up Container (Temporary Fix)
The startup script now cleans up aggressively, but this is a temporary workaround. Railway Volumes are the proper solution.

