# Upload Data Folder to Railway

Railway needs the `data/` folder to work. Here's how to upload it:

## Option 1: Railway CLI (Recommended)

1. **Install Railway CLI:**
   ```bash
   npm install -g @railway/cli
   ```

2. **Login to Railway:**
   ```bash
   railway login
   ```

3. **Link to your project:**
   ```bash
   railway link
   ```
   (Select your Thunderclap project)

4. **Upload data folder:**
   ```bash
   railway up --service web data/
   ```
   
   Or if that doesn't work:
   ```bash
   cd data
   railway up
   ```

## Option 2: Railway Web Interface

1. Go to: https://railway.app
2. Open your Thunderclap project
3. Click on your service (web)
4. Go to **"Volumes"** tab
5. Create a volume (if not exists)
6. Mount it to `/app/data`
7. Use Railway's file upload feature to upload the `data/` folder contents

## Option 3: SSH into Railway Container

1. In Railway dashboard, go to your service
2. Click **"Connect"** or **"Shell"**
3. Create the data directory:
   ```bash
   mkdir -p /app/data/vectordb
   ```
4. Upload files using Railway's file upload or `scp`

## What Files Are Needed

The `data/` folder should contain:
- `data/vectordb/` - ChromaDB database (entire folder)
- `data/indices.json` - Term indices
- `data/endnotes.json` - Endnotes (if exists)
- `data/chunk_to_endnotes.json` - Chunk mapping (if exists)

## Verify Upload

After uploading, check Railway logs:
```bash
railway logs
```

Look for:
```
[OK] Connected to database (X indexed chunks)
```

If you see this, the data folder is correctly uploaded!

