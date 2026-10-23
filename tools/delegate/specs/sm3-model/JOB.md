# Job sm3-model

## Goal
Five small UI-free modules under `tools/hd-models/studio/` that hold everything the Model Studio's Tk tab will show for stages
S0-S3, so the tab itself stays a thin skin and everything is testable headless: `rail.py`, `knobs.py`, `checkrows.py`,
`session.py`, `run_audit.py`. Tests: `tools/hd-models/tests/test_studio_view.py` (one class per item). Pure Python 3.12, stdlib
`unittest`, numpy exists, NO tkinter anywhere in this job. The modules are plain data in, plain data out (dicts, lists, strings).

## Facts and excerpts (pasted: do NOT re-read state.py, audit.py or recipe.py in full; open a function only if you need its detail)

### Running things
From the repo root: `python3 tools/hd-models/tests/test_studio_view.py -k TestRail` (unittest, `-k` filters by class name).
Test file header (as `test_studio_state.py` / `test_studio_audit.py`):
```python
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
from studio import state, audit, rail, knobs, checkrows, session
import synthetic_gltf
```
`synthetic_gltf.write(path)` writes a small rigged glb (6 bones, 5 clips, 2 materials, no licence/category in the recipe).
`tests/test_studio_audit.py` has a `variant(tmp_dir, mutate)` helper that edits the glb JSON; copy what you need, do not import from it.

### state.Studio (studio/state.py, given, do not change)
`Studio(recipe=None)`; `.recipe` dict; `.state(stage)` -> "todo"|"pass"|"warn"|"fail"|"stale"; `.states()`; `.unacknowledged(stage)`;
`.can_build() -> (ok, reasons)`; `.set_findings(stage, findings, inputs=None)`; `.unchanged(stage, inputs)`; `.reopen(stage, inputs)` -> True when
the checks must run (a stale stage whose inputs equal the last run's returns False and becomes current); `.acknowledge(check_id, value)`;
`.edit(path, value)` (value None removes the key; returns the stages marked stale; one undo entry); `.reset_stage(stage)`; `.change_category(c)`;
`.undo()`, `.redo()` (both return the stages marked); `.save(path)` (atomic, .bak; sets save_state "saved"|"error"); `.save_state` "saved"|"unsaved"|"error";
`.report()`. Module level: `STAGES` S0..S9, `GROUPS` = (("Prepare",(S0..S3)),("Fit",(S4,S5,S6)),("Judge",(S7,S8)),("Ship",(S9,))), `DEPENDENTS`,
`stage_of_path(path)` (source/model/meta -> S0, audit -> S1, rig -> S2, mat -> S3, size -> S4, ...), `get_path`, `set_path`.
A finding: `{"id": "S1.weights", "level": "info"|"warn"|"fail", "message", "fix", "value"?, ...extra}`.

### audit.py (given, do not change)
`audit.load_model(path) -> Model` (raises `audit.AuditError`); `audit.audit_stage(stage, model, recipe=None, clips_from=None) -> {"findings": [...], "data": {...}}`
for "S0".."S3"; `audit.audit_all(path, recipe=None, clips_from=None)`; `audit.apply_to_studio(studio, results, inputs=None)`.
`audit.detect_category(model) -> {"category", "confidence", "evidence"}`. The recipe keys each stage reads: S0 `meta.license`, `meta.author`, `model.category`,
`source.skin`; S1 none of the knobs yet; S2 `rig.profile`, `rig.root`, `rig.humanoid`, `rig.extras`, `model.category`; S3 `mat.*`.

### recipe.py (given)
`recipe.SCHEMA` = 1; `recipe.load(dict_or_path)`; `recipe.validate(recipe) -> [{"path","level": "error"|"warn","message"}]`; `recipe.canonical_json(recipe)`.
A new recipe is `{"schema": 1, "source": {"path": <glb path relative to the recipe file>, "sha256": <hex of the glb>}}`.

### Rail (item 1) - what the Tk rail shows
Groups in order with their stage ids: Prepare S0-S3, Fit S4-S6, Judge S7-S8, Ship S9 (use `state.GROUPS`). Nine entries: S1 and S2 are ONE entry
"Skeleton" whose ids are ("S1","S2") and whose state is the worse of the two (order worst to best: fail, warn, stale, todo, pass). Names and subtitles:
S0 "Intake"/"triage", Skeleton "Skeleton"/"audit and rig", S3 "Materials"/"textures", S4 "Size"/"placement", S5 "Clips"/"acts", S6 "Timing"/"strikes", S7 "Look"/"light",
S8 "Validate"/"in game", S9 "Package"/"build". State glyphs: pass "ok", warn "!", fail "x", stale "o" (hollow), todo ".".
`rail(studio) -> list` of dicts: `{"kind": "group", "label"}` and `{"kind": "stage", "ids": ("S0",), "name", "subtitle", "state", "glyph"}` in display order.
`next_stage(stage)` -> the next stage id in `state.STAGES` or None. `footer(studio, stage) -> {"previous": id|None, "next": id|None, "next_label", "next_enabled": bool, "next_reason": str}`:
Next is enabled only when the CURRENT stage's state is "pass" (looking is free, Next is gated); the reason says why not ("S1 has 2 warnings to acknowledge", "S1 is fail", "S1 was never run", "S1 is stale").
`next_label` is verb-first and names the target: "Continue to S1 Skeleton", the last stage S9 reads "Build package". At S9 `next` is None.

### Knobs (item 2) - the tables of S0-S3 (control: select|text|toggle|number|list|chips|readonly)
S0: model.category select C1-C8 (auto: detected) | source.path readonly | meta.author text | meta.license text | meta.url text | meta.attribution toggle (auto: on when the licence text contains BY) | source.skin select (only if several; auto: the skin with most bound vertices) | source.meshes list | model.cards chips (auto: empty)
S1: audit.fix_axes toggle (auto on) | audit.bone_limit select merge/drop/fail (auto merge) | audit.merge list | audit.smooth_passes number (auto 0) | audit.normalise toggle (auto on) | audit.drop_parts list | audit.mirror select none/x (auto none)
S2: rig.profile select auto/ue/mixamo/generic (auto: auto) | rig.root text (bone name; auto: pelvis for a biped) | rig.humanoid map | rig.feet list | rig.strike text | rig.extras list | rig.follow list
S3: mat.atlas select 512/1024/2048 (auto: smallest that keeps texel density) | mat.items list | mat.normal_strength number (auto 1.0) | mat.no_pbr toggle
A knob dict: `{"path", "stage", "label", "control", "choices": [...]|None, "unit": str|None, "auto": str (the auto value, shown as a hint), "help": str}`.
Labels are visible text with the unit in it ("Weight smoothing (passes)", "Atlas size (px)"). `knobs.knobs(stage)` -> list in table order; `knobs.knob(path)` -> dict or None;
`value(recipe, path)` -> the recipe value or None (use `state.get_path`); `is_changed(recipe, path)` -> True when the key is present (it then shows the dot and "back to auto");
`back_to_auto(studio, path)` -> `studio.edit(path, None)`. The knob's `stage` must equal `state.stage_of_path(path)`; a test asserts it for all.
A second test takes one valid sample value per knob (you choose them; the validators are `recipe._validate_*`, read only the one you need) and asserts `recipe.validate` returns no "error" finding for a recipe holding it.

### Check rows (item 3)
`check_rows(studio, stage) -> {"rows": [...], "summary": {"fail": n, "warn": n, "acked": n, "info": n}}`. A row: `{"id", "level", "chip", "message", "fix", "value", "acknowledged": bool, "fix_target": path|None}`.
`chip` is "fail", "warn", "acked" (a warn with a matching ack in the recipe) or "info" (shown as pass). Order: fail, warn, acked, then info; ties keep the finding order.
When there are more than four info findings they are replaced by one row `{"id": "info*", "level": "info", "chip": "info", "message": "N checks passed", "collapsed": [ids]}`.
`fix_target` per check id (None for any id not listed): S0.licence meta.license | S0.attribution meta.author | S0.category model.category | S0.category-confidence model.category | S0.skins source.skin |
S1.bones audit.bone_limit | S1.weights audit.smooth_passes | S1.merge audit.merge | S1.scale audit.fix_axes | S1.normals audit.fix_axes | S2.map rig.humanoid | S2.root-side rig.root | S2.extras-weights rig.extras | S3.atlas mat.atlas | S3.memory mat.atlas.

### Session (items 4 and 5) - the object the Tk tab drives
`Session.open(glb_path, recipe_path=None) -> Session`: if `recipe_path` exists, `recipe.load` it; else a new recipe (see recipe.py above; the glb path stored relative to the recipe file when a recipe_path is given, else absolute). `.studio` (a `state.Studio`), `.glb`, `.recipe_path`.
The model is parsed once (`audit.load_model`) and cached; a changed `source.sha256` (the file on disk differs from the recipe's) reloads it and marks every stage stale. A glb that does not open gives `S0.load` fail through `audit.audit_all` and no cached model.
`stage_inputs(stage) -> dict`: for S0..S3 the recipe sections the stage reads (`source`, `model`, `meta` for S0; plus `audit` for S1; `rig`, `model.category` for S2; `mat` for S3) as plain data, plus `"sha256"`. Equal dicts mean "nothing the stage reads changed".
`run_stage(stage) -> list of findings`: `audit.audit_stage(stage, model, studio.recipe)`, stored with `studio.set_findings(stage, findings, stage_inputs(stage))`.
`open_stage(stage) -> bool`: `studio.reopen(stage, stage_inputs(stage))`; when it says the checks must run, it runs them (`run_stage`) and returns True, else False.
`edit(path, value, now=None)` -> `studio.edit`, and for every stage marked stale records `pending[stage] = now` (`now` defaults to `time.monotonic()`); `due(now) -> list of stage ids` whose pending time is at least 0.3 s old; `run_due(now)` runs them with `run_stage`, clears them from `pending` and returns the ids; a second edit of the same stage inside 0.3 s moves its time (debounce).
`autosave() -> bool`: saves to `recipe_path` through `studio.save` only when `save_state == "unsaved"` and a recipe_path exists; returns whether it wrote. `undo()`/`redo()` -> the studio's marked stages (also put in `pending`). `change_category(c)`, `acknowledge(check_id, value)` delegate to the studio (acknowledge marks the recipe unsaved).
CLI `tools/hd-models/studio/run_audit.py GLB [RECIPE_JSON] [--stage S1]`: prints `json.dumps` of `audit.audit_all(...)` (or the one stage) to stdout, exit 0; exit 2 and a one-line message on stderr when the glb is missing. The Tk tab will run it as a subprocess (no threads in the editor). Test it with `subprocess.run([sys.executable, ...])`.

### Rules
- WRITE SMALL. Earlier runs read 150 KB, then died on provider read timeouts while generating one large file. Create a new file with at most 60 lines in one write, then grow it with further edits of at most 60 lines each. Do not re-read state.py, audit.py, test_studio_audit.py or recipe.py: the facts above are enough; open at most one function of them by grep when stuck.
- Do not change `state.py`, `audit.py`, `recipe.py`, `native_*.py` (verify.sh checks). If something there seems wrong, write BLOCKED with the reason.
- Every test must be able to fail: assert exact values (ids, states, glyphs, labels, orders), never "runs without error".
- Each test builds its own glb in a temp dir; no shared state between tests; tests pass headless in under 30 s in total.
- No new dependencies, no tkinter, no threads, no network. Code style: like `state.py` (a docstring at the top that says what the module is, small functions, no framework).

## You may change
`tools/hd-models/studio/{rail,knobs,checkrows,session,run_audit}.py` (create), `tools/hd-models/tests/test_studio_view.py` (create), `tools/hd-models/README.md` (one line naming the new modules, including the text `studio/session.py`).

## You must not touch
Everything else, including the structure of progress.md.

## Constraints
- One item per session: the loop re-runs each item's `check:` itself, ticks what passes and commits after every iteration.
- The test file grows by one class per item; keep classes independent.

## Acceptance
`bash verify.sh` exits 0.
