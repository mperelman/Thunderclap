# Deployment Guide

## Quick Deploy

To sync your local changes to git:

```bash
python deploy.py "Your commit message here"
```

Or without a message (uses timestamp):
```bash
python deploy.py
```

## What it does

1. Checks for changes
2. Adds all changes (`git add .`)
3. Commits with your message
4. Pushes to the remote repository

## GitHub Actions

A GitHub Actions workflow (`.github/workflows/deploy.yml`) will run automatically on push to `main` or `master` branches.

## First-time Setup

If this is your first push:

```bash
git add .
git commit -m "Initial commit"
git push -u origin main
```

After that, use `deploy.py` for consistent deployments.

