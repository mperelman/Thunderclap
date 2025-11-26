#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deployment script to sync local changes to git repository.
Usage: python deploy.py [commit_message]
"""
import subprocess
import sys
import os
from datetime import datetime

# Fix Windows encoding issues
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def run_command(cmd, check=True):
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.CalledProcessError as e:
        return e.stdout.strip(), e.stderr.strip(), e.returncode

def main():
    # Get commit message from args or use default
    if len(sys.argv) > 1:
        commit_message = sys.argv[1]
    else:
        commit_message = f"Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    print("🔄 Starting deployment...")
    
    # Check git status
    stdout, stderr, code = run_command("git status --porcelain", check=False)
    if not stdout:
        print("✅ No changes to commit")
        return
    
    print(f"📝 Changes detected:\n{stdout}\n")
    
    # Add all changes
    print("➕ Adding changes...")
    stdout, stderr, code = run_command("git add .")
    if code != 0:
        print(f"❌ Error adding files: {stderr}")
        return
    
    # Commit
    print(f"💾 Committing: {commit_message}")
    stdout, stderr, code = run_command(f'git commit -m "{commit_message}"')
    if code != 0:
        if "nothing to commit" in stderr.lower():
            print("✅ Nothing to commit")
            return
        print(f"❌ Error committing: {stderr}")
        return
    
    # Get current branch
    stdout, stderr, code = run_command("git branch --show-current")
    if code != 0:
        print(f"❌ Error getting branch: {stderr}")
        return
    branch = stdout.strip() or "main"
    
    # Push to remote
    print(f"🚀 Pushing to origin/{branch}...")
    stdout, stderr, code = run_command(f"git push -u origin {branch}")
    if code != 0:
        print(f"❌ Error pushing: {stderr}")
        print("\n💡 Tip: If this is your first push, you may need to set upstream:")
        print(f"   git push -u origin {branch}")
        return
    
    print("✅ Deployment complete!")
    print(f"   Committed: {commit_message}")
    print(f"   Pushed to: origin/{branch}")

if __name__ == "__main__":
    main()

