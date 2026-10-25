#!/usr/bin/env bash
set -e
python3 tools/hd-models/tests/test_studio_corpus.py
python3 tools/hd-models/studio/corpus.py --check
for t in audit report build clips; do python3 tools/hd-models/tests/test_studio_$t.py 2>&1 | tail -3; done
root=$(git rev-list --max-parents=0 HEAD | head -1)
for f in tools/hd-models/studio/audit.py tools/hd-models/studio/state.py tools/hd-models/recipe.py tools/hd-models/tests/synthetic_gltf.py; do
  git diff --quiet "$root" -- "$f" || { echo "$f must not change"; exit 1; }
done
