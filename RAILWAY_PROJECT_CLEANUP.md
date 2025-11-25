# Railway Project Cleanup Guide

You have two Railway projects. Let's figure out which one to use and clean up.

## Step 1: Identify Which Project You're Using

Your Railway URL is: `web-production-c4223.up.railway.app`

**To find which project this belongs to:**

1. Go to: https://railway.app
2. Click on **"ample-stillness"** project
3. Click on the **web** service
4. Go to **"Settings"** tab
5. Look at the **"Domains"** section
6. Check if it shows: `web-production-c4223.up.railway.app`
7. Repeat for **"innovative-freedom"** project

**The one with `web-production-c4223.up.railway.app` is the one you're using.**

## Step 2: Delete the Unused Project

**To delete a Railway project:**

1. Go to: https://railway.app
2. Click on the project you want to delete (probably "ample-stillness")
3. Click on **"Settings"** (gear icon in left sidebar)
4. Scroll to the bottom
5. Click **"Delete Project"**
6. Type the project name to confirm
7. Click **"Delete"**

⚠️ **WARNING:** This permanently deletes the project and all its services. Make sure you're deleting the RIGHT one!

## Step 3: Rename Project (Optional)

**To rename "innovative-freedom" to "thunderclap":**

1. Go to: https://railway.app
2. Click on **"innovative-freedom"** project
3. Click on **"Settings"** tab
4. Find **"Project Name"** field
5. Change it to: `thunderclap`
6. Click **"Save"**

## Step 4: Verify You're Using the Right Project

After cleanup, verify:

1. Your Railway URL should still be: `web-production-c4223.up.railway.app`
2. The project name should be what you want (e.g., "thunderclap")
3. The frontend should still work (it's hardcoded to use that URL)

## Quick Check: Which Project Has Your Data?

**Check Railway logs to see which project is active:**

1. Go to Railway dashboard
2. Click on **"innovative-freedom"** → **web** service → **"Deployments"** tab
3. Click on latest deployment → **"View Logs"**
4. Look for: `[OK] Connected to database` or `Database not initialized`

If you see "Database not initialized" in innovative-freedom, that's the one you need to upload data to.

If you see "Connected to database" in ample-stillness, that one has your data (but you're not using it).

## Recommendation

**Use "innovative-freedom"** (the one you've been updating) and:
1. Delete "ample-stillness" (the old one)
2. Rename "innovative-freedom" to "thunderclap" (optional, for clarity)
3. Upload data folder to "innovative-freedom" (or "thunderclap" if renamed)

