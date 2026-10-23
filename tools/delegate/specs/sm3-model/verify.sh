#!/usr/bin/env bash
set -e
python3 tools/hd-models/tests/test_studio_view.py
python3 tools/hd-models/tests/test_studio_audit.py
python3 tools/hd-models/tests/test_studio_state.py 2>&1 | tail -3
python3 tools/hd-models/tests/test_recipe.py 2>&1 | tail -3
grep -q "studio/session.py" tools/hd-models/README.md
root=$(git rev-list --max-parents=0 HEAD | head -1)
# given modules are unchanged
for f in tools/hd-models/studio/state.py tools/hd-models/studio/audit.py tools/hd-models/recipe.py; do
  git diff --quiet "$root" -- "$f" || { echo "$f must not change"; exit 1; }
done
bad=$( { git diff --name-only "$root"; git ls-files --others --exclude-standard; } | sort -u | grep -v -E '^(tools/hd-models/(studio/(rail|knobs|checkrows|session|run_audit)\.py|README\.md|tests/test_studio_view\.py|tests/__pycache__/.*|studio/__pycache__/.*|__pycache__/.*)|progress\.md|JOB\.md|verify\.sh|RALPH_DONE|BLOCKED)$' || true)
[ -z "$bad" ] || { echo "files changed outside the allowed set: $bad"; exit 1; }
