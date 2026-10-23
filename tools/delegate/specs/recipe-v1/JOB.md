# Job recipe-v1

## Goal
`tools/hd-models/recipe.py`: pure Python (stdlib only), reads and checks a studio `recipe.json` and turns it into the arguments
the existing converter takes and the members the package's `model.json` holds. No GUI, no engine, no disc. The recipe's keys are
defined in `notes/studio/recipe-schema.md` (read it completely first; the table "Keys by section" is the contract).

## Read first
- notes/studio/recipe-schema.md (whole file)
- tools/hd-models/native_spec.py lines 1-40 (the limits: ACTS, MAX_SHOTS, SHOT_RANGES, MAX_STRIKES, REGISTRY_CARDS, LOOK_KEYS, TEXTURE_MAX, MAX_SIDE). Import them with `import native_spec as spec`; never copy the numbers.
- tools/hd-models/native_convert.py lines 735-760 (the argparse options; their `dest` names are the keys convert_args returns)
- tools/hd-models/tests/test_native_tools.py lines 1-30 (how tests here import modules and are written: unittest, `sys.path.insert(0, str(HERE.parent))`)

## You may change
tools/hd-models/recipe.py (new), tools/hd-models/tests/test_recipe.py (new), tools/hd-models/tests/fixtures/recipe_dragon.json (new),
tools/hd-models/README.md (one section added). progress.md: only tick items and add Result/Failed lines.

## Do not touch
Everything else, in particular native_convert.py, native_check.py, native_spec.py, any C file.

## The API (exact names)
```
SCHEMA = 1
class RecipeError(ValueError)
def load(source) -> dict            # source: dict, or a path (str or Path) to a JSON file. Returns a deep copy.
                                    # RecipeError when: not a JSON object; "schema" missing or not an int; schema < 1;
                                    # schema > SCHEMA (message contains "newer studio"); the file is not valid JSON.
def canonical_json(recipe) -> str   # json.dumps(..., sort_keys=True, indent=2, ensure_ascii=False) + "\n";
                                    # a float with a whole value (3.0) is written as an int (3). Nothing else changes.
def validate(recipe) -> list[dict]  # findings: {"path": "size.mode", "level": "error" or "warn", "message": str}; [] when clean
def convert_args(recipe) -> dict    # keys are native_convert option dests (see below); only keys that the recipe sets
def model_json_members(recipe) -> dict   # members of model.json that the recipe sets (see below)
```

## validate() rules (error unless it says warn)
Top level: recipe must contain "source" (object with "path": non-empty str) and "model" (object with "category" in C1..C8).
Unknown top-level key: warn. Known: schema, studio, source, model, meta, audit, rig, mat, size, acts, look, shots, pkg, acks, runs, timing.
- source: path str; sha256 optional str of 64 hex chars (else error); skin optional str; meshes optional list of str.
- model: name optional non-empty str; cards optional list of ints >= 1, at most spec.REGISTRY_CARDS, no duplicates.
- meta: author, license, url optional str; license missing or empty: warn "licence is empty".
- size: mode in scale, extent, root_height, height; value number > 0 when mode is set (mode and value come together, else error);
  origin_height number >= 0; scale_pct int in 10..500; offset list of 3 ints; center bool.
- rig: profile in auto, ue, mixamo, generic; root non-empty str; follow list of str, each matching `^[^=@\s]+=[^=@\s]+(@[0-9.]+)?$`; feet list of str.
- mat: atlas int, a power of two, 64..spec.MAX_SIDE (warn above spec.TEXTURE_MAX); no_pbr bool.
- acts: keys only from spec.ACTS (anything else: error, message lists the valid names). Each act is an object. "source" is a str
  (a clip name) or an object with exactly one key "procedural" (str). "strike" list of ints >= 0, at most spec.MAX_STRIKES, allowed
  only on "attack" (on another act: warn). "root_motion" in remove, keep. "loop", "close_loop", "mirror" bool. "speed" number > 0.
- look: keys only from spec.LOOK_KEYS (else error); values numbers.
- shots: list, at most spec.MAX_SHOTS. Each is an object with "act" in spec.ACTS and ints for from, to, yaw, pitch, distance, height,
  ease within spec.SHOT_RANGES (missing optional members are fine except act, from, to); from < to; "other" bool.
- acks: list of objects with "check" (non-empty str) and "value" (any).
Each finding names the exact path, e.g. "shots[1].yaw", "acts.attack.strike", "size.scale_pct".

## convert_args() mapping (returns only what the recipe sets)
- size.mode/value: exactly one of `scale`, `extent`, `root_height`, `height` = value (the mode names are the dests).
- size.origin_height -> origin_height; size.center == False -> no_center True.
- rig.profile -> rig; rig.root -> root; rig.follow -> follow (the list as is).
- mat.atlas -> texture_max; mat.no_pbr True -> no_pbr True.
- meta.author -> author; meta.license -> license; model.name -> name.
- Any act with root_motion "keep" -> keep_root_motion True.
- clips: if any act has a str source, `clips` = comma-joined, de-duplicated clip names in spec.ACTS order.
Every returned key must be in this set of valid dests, and a test asserts that:
{clips, clips_from, rig, root, root_height, origin_height, height, extent, scale, texture_max, follow, no_center, keep_root_motion, no_pbr, name, author, license}

## model_json_members() mapping (only what is set)
- clips: {act: clip name} for acts whose source is a str. strike: {"attack": [ints]} from acts.attack.strike.
- scale: size.scale_pct. offset: size.offset. look: the look object. shots: the shots list (as is).
- author, license: from meta. source: meta.url.

## Constraints
- Python 3.12, standard library only in recipe.py (the tests may use unittest, tempfile, json, copy).
- Deterministic: never depend on dict insertion order for output; canonical_json sorts keys.
- Match the style of native_spec.py and native_check.py (module docstring, short comments saying why).
- Every rule above gets a test that fails without it (one valid and one invalid case at least). Group them in the named test classes.
- The test file ends with `if __name__ == "__main__": unittest.main()`.

## Acceptance
`bash verify.sh` exits 0.
