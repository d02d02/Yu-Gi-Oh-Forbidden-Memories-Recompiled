#!/usr/bin/env bash
set -e
python3 tools/hd-models/tests/test_recipe.py
python3 tools/hd-models/tests/test_native_tools.py 2>&1 | tail -3
test -f tools/hd-models/tests/fixtures/recipe_dragon.json
grep -q "recipe.py" tools/hd-models/README.md
# nothing outside the allowed files changed since the clone's first (shallow root) commit, committed or not
root=$(git rev-list --max-parents=0 HEAD | head -1)
bad=$( { git diff --name-only "$root"; git ls-files --others --exclude-standard; } | sort -u | grep -v -E '^(tools/hd-models/(recipe\.py|README\.md|tests/test_recipe\.py|tests/fixtures/recipe_dragon\.json|tests/__pycache__/.*|__pycache__/.*)|progress\.md|JOB\.md|verify\.sh)$' || true)
[ -z "$bad" ] || { echo "files changed outside the allowed set: $bad"; exit 1; }
