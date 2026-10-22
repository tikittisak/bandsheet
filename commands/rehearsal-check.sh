#!/bin/bash
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ $# -ne 1 ]]; then
  echo "Usage: bash commands/rehearsal-check.sh playlists/<band>/<playlist>.json" >&2
  exit 2
fi

PLAYLIST="$1"
NAME="$(basename "$PLAYLIST" .json)"
python3 rehearsal_check.py "$PLAYLIST" \
  --report "_work/reports/${NAME}-rehearsal-readiness-$(date +%F).md"
