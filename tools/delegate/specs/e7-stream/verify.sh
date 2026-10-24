#!/usr/bin/env bash
set -e
python tools/hd-models/tests/test_studio_stream.py 2>&1 | tail -3
python tools/hd-models/stream_demo.py --selftest | tail -3
git diff --quiet HEAD~0 -- tools/pc/yfm_control.py || { echo "yfm_control.py must not change"; exit 1; }
