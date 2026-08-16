#!/bin/bash
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

python3 validate_bandsheet.py --report "_work/reports/bandsheet-change-report-$(date +%F).md"
bash push.sh --dry-run
