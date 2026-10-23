# Job sm1-recipe

## Goal
`tools/hd-models/recipe.py`: a pure-Python reader and validator for `recipe.json` schema v1 (SM1 slice 1 of the studio plan), with unit tests. It validates and returns findings as data; it does not convert anything and does not call `native_convert`.

## Read first
- notes/studio/recipe-schema.md (whole file, 101 lines): the keys and their meaning.
- tools/hd-models/native_spec.py:10-29: constants to import, not copy: ACTS, MAX_SHOTS, MAX_STRIKES, REGISTRY_CARDS, LOOK_KEYS, TEXTURE_MAX.
- tools/hd-models/tests/test_native_tools.py:1-30: test style (unittest, sys.path set up).

## You may change
- tools/hd-models/recipe.py (new)
- tools/hd-models/tests/test_recipe.py (new)
- progress.md (tick items, add Result/Failed lines only)

## You must not touch
Everything else.

## Rules for validate(recipe) -> list[Finding]
Findings have level "error" or "warn", a dotted `path` (e.g. `size.scale_pct`) and a short message. Unknown keys inside a known section are "warn". A missing optional section is fine. Wrong type is an "error".
- R1 top level: `schema` must equal SCHEMA; `source` and `model` are required objects; known sections are `source, model, meta, audit, rig, mat, size, acts, look, shots, pkg, acks, runs, studio`; unknown top-level key = warn.
- R2 `source`: `path` non-empty string (required); `sha256` string of 64 lowercase hex (optional, error if malformed); `skin` string; `meshes` list of strings.
- R3 `model`: `category` matches C1..C8 (error otherwise, optional key); `name` non-empty string; `cards` list of ints, each a positive int, at most REGISTRY_CARDS entries (native_spec.py); `card_overrides` object whose values may hold integer `scale` (10..1000) and `offset` (list of 3 ints).
- R4 `meta`: `author`, `license`, `url`, `attribution` are strings; warn if `license` is missing.
- R5 `rig`: `profile` in {auto, ue, mixamo, generic}; `root`, `strike` strings; `feet` list of strings; `follow` list of strings matching `BONE=SOURCE` or `BONE=SOURCE@FRACTION` (FRACTION a number).
- R6 `mat`: `atlas` int 64..8192; `no_pbr` bool; `normal_strength` number; `flip_green` bool.
- R7 `size`: `mode` in {scale, extent, root_height, height}; `value` positive number, required when `mode` is set; `origin_height` number; `center` bool; `scale_pct` int 10..1000 (a float or a bool is an error, even 100.0); `origin_offset` / `ground_offset` are ints.
- R8 `acts`: keys must be in {idle, enter, attack, hit, destroyed, win, guard}; `attack2` is an error whose message says it is dropped; each act is an object; `source` is a string or an object with `procedural`; `loop`, `close_loop`, `mirror`, `root_motion` bool; `speed` positive number; `strike` list of 1..4 ints, only allowed on `attack` (error on other acts).
- R9 `look`: keys limited to LOOK_KEYS plus `tint`; `tint` is a warn "not in the engine"; values numbers.
- R10 `shots`: list of at most 8 objects; each has `act` (valid act name) and integer `from`, `to` with 0 <= from <= to; the other keys may be numbers/strings; unknown keys warn.
- R11 `acks`: list of objects with string `check` and a `value` key.

## Constraints
- Python 3.12 in this Linux shell; standard library only (no numpy needed). No new dependencies. Match the style of native_spec.py (docstring at the top, short functions, no classes beyond Finding and RecipeError).
- Tests are plain unittest, runnable with `cd tools/hd-models/tests && python3 -m unittest test_recipe -q`.

## Acceptance
`bash verify.sh` exits 0.
