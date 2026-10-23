#!/usr/bin/env bash
set -e
python3 tools/hd-models/tests/test_studio_audit.py
python3 tools/hd-models/tests/test_studio_state.py 2>&1 | tail -3
python3 tools/hd-models/tests/test_recipe.py 2>&1 | tail -3
grep -q "studio/" tools/hd-models/README.md
# the thresholds are unchanged from the job's first commit
root=$(git rev-list --max-parents=0 HEAD | head -1)
for c in DRIFT_WARN DRIFT_FAIL WEIGHTS_FAIL_PCT FLIPPED_WARN_PCT ROOT_OFF_PCT CONFIDENCE_WARN UV_REPEATS TRIANGLES_WARN TEXTURE_MB_WARN; do
  a=$(git show "$root":tools/hd-models/studio/audit.py | grep -E "^.*\b$c\b *=|, $c *=" | head -2)
  b=$(grep -E "^.*\b$c\b *=|, $c *=" tools/hd-models/studio/audit.py | head -2)
  [ "$a" = "$b" ] || { echo "constant $c changed"; exit 1; }
done
# nothing outside the allowed files changed
bad=$( { git diff --name-only "$root"; git ls-files --others --exclude-standard; } | sort -u | grep -v -E '^(tools/hd-models/(studio/audit\.py|README\.md|tests/test_studio_audit\.py|tests/__pycache__/.*|studio/__pycache__/.*|__pycache__/.*)|progress\.md|JOB\.md|verify\.sh|RALPH_DONE|BLOCKED)$' || true)
[ -z "$bad" ] || { echo "files changed outside the allowed set: $bad"; exit 1; }
