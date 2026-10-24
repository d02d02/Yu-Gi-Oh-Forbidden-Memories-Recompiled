#!/usr/bin/env bash
set -e
python tools/hd-models/tests/test_studio_stream.py 2>&1 | tail -3
python tools/hd-models/stream_demo.py --selftest | tail -3
root=$(git rev-list --max-parents=0 HEAD | head -1)
git diff --quiet "$root" -- tools/pc/yfm_control.py || { echo "yfm_control.py must not change"; exit 1; }
