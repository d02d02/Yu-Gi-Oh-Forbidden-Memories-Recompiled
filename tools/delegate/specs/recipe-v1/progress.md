# Job recipe-v1: tools/hd-models/recipe.py, the studio's recipe reader and validator, with tests

Read JOB.md first. One item per iteration. Run the check under the item; tick only if it passes.
Tests: tools/hd-models/tests/test_recipe.py (unittest). Run a group with `python3 tools/hd-models/tests/test_recipe.py -k <Name>`.

## Status
Not started.

## Items
- [ ] 1. Create tools/hd-models/recipe.py (SCHEMA=1, RecipeError, load, canonical_json) and tests class TestLoad
  check: python3 tools/hd-models/tests/test_recipe.py -k TestLoad
- [ ] 2. recipe.validate(): top level, source, model, meta rules; tests class TestValidateBasic
  check: python3 tools/hd-models/tests/test_recipe.py -k TestValidateBasic
- [ ] 3. recipe.validate(): size, rig, mat rules; tests class TestValidateStages
  check: python3 tools/hd-models/tests/test_recipe.py -k TestValidateStages
- [ ] 4. recipe.validate(): acts, look, shots, acks rules; tests class TestValidateActs
  check: python3 tools/hd-models/tests/test_recipe.py -k TestValidateActs
- [ ] 5. recipe.convert_args(): mapping to native_convert's options; tests class TestConvertArgs
  check: python3 tools/hd-models/tests/test_recipe.py -k TestConvertArgs
- [ ] 6. recipe.model_json_members() and fixture tools/hd-models/tests/fixtures/recipe_dragon.json; tests class TestModelJson
  check: python3 tools/hd-models/tests/test_recipe.py -k TestModelJson
- [ ] 7. Add a short "recipe.py" section to tools/hd-models/README.md
  check: grep -q "recipe.py" tools/hd-models/README.md
