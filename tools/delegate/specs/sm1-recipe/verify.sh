#!/usr/bin/env bash
set -e
cd tools/hd-models/tests
python3 -m unittest test_recipe -q
cd ../../..
python3 - <<'PY'
import sys
sys.path.insert(0, "tools/hd-models")
import recipe
assert recipe.SCHEMA == 1
for name in ("RecipeError", "Finding", "parse", "validate", "dumps", "migrate"):
    assert hasattr(recipe, name), name
good = {"schema": 1, "source": {"path": "a.glb"}, "model": {"name": "X", "cards": [1]}}
assert [f for f in recipe.validate(good) if f.level == "error"] == []
bad = dict(good, size={"scale_pct": 100.0})
assert any(f.path == "size.scale_pct" and f.level == "error" for f in recipe.validate(bad))
assert recipe.dumps(good) == recipe.dumps(recipe.parse(recipe.dumps(good)))
PY
echo ok
