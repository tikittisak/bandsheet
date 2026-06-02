#!/bin/bash
# push.sh — Bandsheet Auto Push to GitHub
# Claude รันสคริปต์นี้หลัง edit ไฟล์เพื่อ push อัตโนมัติ
# Usage:
#   bash push.sh [commit message]
#   bash push.sh --dry-run

set -e
BAND_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$BAND_ROOT"

DRY_RUN=0
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=1
  shift
fi

MSG="${1:-auto: update bandsheets $(date '+%Y-%m-%d %H:%M')}"

echo "=== Bandsheet Push ==="
echo "Root: $BAND_ROOT"
if [[ "$DRY_RUN" == "1" ]]; then
  echo "Mode: dry-run"
fi

# Step 1: Update all band indexes
echo ""
echo "1. Updating indexes..."
python3 "$BAND_ROOT/update_index.py"

# Step 2: Show current changes
echo ""
echo "2. Current changes..."
git status --short

if [[ "$DRY_RUN" == "1" ]]; then
  echo ""
  echo "Dry-run complete. No files were staged, committed, or pushed."
  exit 0
fi

# Step 3: Git add all changes
echo ""
echo "3. Staging changes..."
git add -A
git status --short

# Step 4: Check if anything to commit
if git diff --cached --quiet; then
  echo "Nothing to commit — already up to date."
  exit 0
fi

# Step 5: Commit
echo ""
echo "4. Committing: $MSG"
git commit -m "$MSG"

# Step 6: Push
echo ""
echo "5. Pushing to GitHub..."
git push origin main

echo ""
echo "=== Done! Pushed to github.com/tikittisak/bandsheet ==="
