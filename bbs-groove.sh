#!/bin/sh
# Lance BBS Groove depuis les sources locales
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export PYTHONPATH="$SCRIPT_DIR/src:${PYTHONPATH:-}"
exec python3 "$SCRIPT_DIR/src/bbs_groove/groove.py" "$@"
