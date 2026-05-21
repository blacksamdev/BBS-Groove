#!/bin/bash

set -e

export PYTHONUNBUFFERED=1
export PYTHONPATH=/usr/local/lib/bbs-groove/src

exec python3 -m bbs_groove.groove "$@"
