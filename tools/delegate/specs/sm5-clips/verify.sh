#!/usr/bin/env bash
set -e
python3 tools/hd-models/tests/test_studio_clips.py
python3 tools/hd-models/tests/test_studio_timemap.py 2>&1 | tail -3
python3 tools/hd-models/tests/test_studio_look.py 2>&1 | tail -3
python3 tools/hd-models/tests/test_studio_runs.py 2>&1 | tail -3
python3 tools/hd-models/tests/test_studio_package.py 2>&1 | tail -3
python3 tools/hd-models/tests/test_studio_audit.py 2>&1 | tail -3
root=$(git rev-list --max-parents=0 HEAD | head -1)
for f in tools/hd-models/studio/state.py tools/hd-models/studio/audit.py tools/hd-models/recipe.py; do
  git diff --quiet "$root" -- "$f" || { echo "$f must not change"; exit 1; }
done
