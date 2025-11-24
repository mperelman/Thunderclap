# GitHub Pages Setup

## Accessing frontend.html via GitHub Pages

Once GitHub Pages is enabled, your frontend will be accessible at:
**https://mperelman.github.io/Thunderclap/frontend.html**

## Setup Steps

1. **Enable GitHub Pages** (if not already enabled):
   - Go to your repository: https://github.com/mperelman/Thunderclap
   - Settings → Pages
   - Source: "GitHub Actions"
   - Save

2. **The workflow will deploy automatically** when you push to `main` branch

3. **Access the frontend**:
   - After deployment: https://mperelman.github.io/Thunderclap/frontend.html
   - Or use: https://mperelman.github.io/Thunderclap/ (if index.html exists)

## API Configuration

The frontend needs to connect to your backend API server. You have two options:

### Option 1: Use URL Parameter (Recommended)
Add `?api=YOUR_SERVER_URL` to the GitHub Pages URL:
```
https://mperelman.github.io/Thunderclap/frontend.html?api=https://your-server.com
```

### Option 2: Local Development
For local development, the frontend defaults to `http://localhost:8000/query`

## Notes

- The frontend is static HTML/JS - it needs a running backend server
- GitHub Pages only hosts the frontend, not the Python backend
- You'll need to deploy your backend separately (e.g., Heroku, Railway, Render, etc.)
- Or run the backend locally and use the frontend from GitHub Pages with `?api=http://localhost:8000`

