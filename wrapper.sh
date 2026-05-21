#!/bin/sh
export PYTHONPATH="/app/lib/bbs-groove/src:${PYTHONPATH:-}"
exec python3 /app/lib/bbs-groove/src/bbs_groove/groove.py "$@"
