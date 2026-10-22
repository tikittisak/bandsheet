#!/bin/bash
# push.sh — Bandsheet Auto Push to GitHub
# Claude รันสคริปต์นี้หลัง edit ไฟล์เพื่อ push อัตโนมัติ
# Usage:
#   bash push.sh [commit message] [--allow-content songs/name.html ...]
#   bash push.sh --dry-run [--allow-content songs/name.html ...]

set -e
BAND_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$BAND_ROOT"

DRY_RUN=0
MSG=""
CONTENT_GUARD_ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --allow-content)
      if [[ $# -lt 2 ]]; then
        echo "ERROR: --allow-content requires songs/<name>.html" >&2
        exit 2
      fi
      CONTENT_GUARD_ARGS+=("--allow" "$2")
      shift 2
      ;;
    *)
      if [[ -n "$MSG" ]]; then
        echo "ERROR: unexpected argument: $1" >&2
        exit 2
      fi
      MSG="$1"
      shift
      ;;
  esac
done
MSG="${MSG:-auto: update bandsheets $(date '+%Y-%m-%d %H:%M')}"

echo "=== Bandsheet Push ==="
echo "Root: $BAND_ROOT"
if [[ "$DRY_RUN" == "1" ]]; then
  echo "Mode: dry-run"
fi

# Step 1: Update all band indexes
echo ""
echo "1. Updating indexes..."
python3 "$BAND_ROOT/update_index.py"

# Step 2: Refuse silent lyric/chord/section drift. Intentional content edits
# must name each exact song path on the command line.
echo ""
echo "2. Checking protected song content..."
python3 "$BAND_ROOT/content_guard.py" "${CONTENT_GUARD_ARGS[@]}"

# Step 3: Show current changes
echo ""
echo "3. Current changes..."
git status --short

if [[ "$DRY_RUN" == "1" ]]; then
  echo ""
  echo "Dry-run complete. No files were staged, committed, or pushed."
  exit 0
fi

# Step 4: Git add all changes
echo ""
echo "4. Staging changes..."
git add -A
git status --short

# Step 5: Check if anything to commit
if git diff --cached --quiet; then
  echo "Nothing to commit — already up to date."
  exit 0
fi

# Step 6: Commit
echo ""
echo "5. Committing: $MSG"
git commit -m "$MSG"

# Step 7: Push
echo ""
echo "6. Pushing to GitHub..."
git push origin main

echo ""
echo "=== Done! Pushed to github.com/tikittisak/bandsheet ==="
