# Job sm1-recipe: tools/hd-models/recipe.py reader/validator for recipe.json v1, with unit tests

Read JOB.md first (goal, files to read, limits, acceptance). One item per iteration; the check is the line under the item.

## Status
Not started.

## Items
- [ ] Create `tools/hd-models/recipe.py` with `SCHEMA = 1`, `class RecipeError(ValueError)`, `Finding` (namedtuple: level "error"|"warn", path, message), and `parse(text) -> dict` (json.loads; a non-object, or `schema` missing / not an int, raises RecipeError). Create `tools/hd-models/tests/test_recipe.py` (unittest) with tests for these.
  check: cd tools/hd-models/tests && python3 -m unittest test_recipe -q
- [ ] `validate(recipe) -> list[Finding]` for top level, `source`, `model`, `meta` per JOB.md rules R1-R4. One test per rule.
  check: cd tools/hd-models/tests && python3 -m unittest test_recipe -q
- [ ] `validate` for `rig`, `mat`, `size` per rules R5-R7. One test per rule.
  check: cd tools/hd-models/tests && python3 -m unittest test_recipe -q
- [ ] `validate` for `acts`, `look`, `shots`, `acks` per rules R8-R11. One test per rule.
  check: cd tools/hd-models/tests && python3 -m unittest test_recipe -q
- [ ] `dumps(recipe) -> str` (sorted keys, indent 2, trailing newline, ensure_ascii False) and `migrate(recipe) -> dict` (schema 1 returns a copy; a higher schema raises RecipeError naming the version needed; lower than 1 raises). Tests: dumps is idempotent through parse, byte-identical on two calls, migrate cases.
  check: cd tools/hd-models/tests && python3 -m unittest test_recipe -q
- [ ] Test that the abridged dragon example from `notes/studio/recipe-schema.md` (copy it into the test as a dict, replace the "…" values with strings) validates with zero errors.
  check: bash verify.sh
