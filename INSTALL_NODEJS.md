# Install Node.js (Required for Railway CLI)

## Step 1: Download Node.js

1. Go to: https://nodejs.org/
2. Click the **"LTS"** button (Long Term Support version)
3. Download the Windows installer (.msi file)
4. Run the installer
5. Click "Next" through all the prompts (default settings are fine)
6. Click "Install"
7. Wait for it to finish
8. **Restart PowerShell** (close and reopen it)

## Step 2: Verify Installation

**Open PowerShell again and run:**
```powershell
node --version
npm --version
```

**Should show version numbers** (like v20.x.x and 10.x.x)

## Step 3: Install Railway CLI

**Now run:**
```powershell
npm install -g @railway/cli
```

**Wait for it to finish** (1-2 minutes)

**Verify:**
```powershell
railway --version
```

Then continue with the upload steps!

