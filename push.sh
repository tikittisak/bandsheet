#!/bin/bash
# push.sh — Bandsheet Auto Push to GitHub
# Claude รันสคริปต์นี้หลัง edit ไฟล์เพื่อ push อัตโนมัติ
# Usage: bash push.sh [commit message]

set -e
BAND_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$BAND_ROOT"

MSG="${1:-auto: update bandsheets $(date '+%Y-%m-%d %H:%M')}"

echo "=== Bandsheet Push ==="
echo "Root: $BAND_ROOT"

# Step 1: Update all band indexes
echo ""
echo "1. Updating indexes..."
python3 "$BAND_ROOT/update_index.py"

# Step 2: Git add all changes
echo ""
echo "2. Staging changes..."
git add -A
git status --short

# Step 3: Check if anything to commit
if git diff --cached --quiet; then
  echo "Nothing to commit — already up to date."
  exit 0
fi

# Step 4: Commit
echo ""
echo "3. Committing: $MSG"
git commit -m "$MSG"

# Step 5: Push
echo ""
echo "4. Pushing to GitHub..."
git push origin main

echo ""
echo "=== Done! Pushed to github.com/tikittisak/bandsheet ==="
