# Job sm3-model: the Studio's UI-free view layer for S0-S3 (rail, knobs, check rows, session)

Read JOB.md first (goal, pasted facts, rules, acceptance). One item per session; the check is the line under the item.

## Status
Not started.

## Items
- [ ] 0. Create `tools/hd-models/tests/test_studio_view.py` with ONE small class TestRail holding ONE test (`rail(studio)` returns 4 group headings and 9 entries) using the synthetic glb helper, under 60 lines; `studio/rail.py` may already exist from an earlier session, reuse it
  check: python3 tools/hd-models/tests/test_studio_view.py -k TestRail
- [ ] 1. `studio/rail.py` and tests/test_studio_view.py class TestRail: `rail(studio)` rows (4 group headings, 9 entries, S1+S2 merged into "Skeleton" with the worse state), `next_stage`, `footer` (previous, verb-first next label, enabled and reason; last stage reads "Build package")
  check: python3 tools/hd-models/tests/test_studio_view.py -k TestRail
- [ ] 2. `studio/knobs.py` and class TestKnobs: the knob tables of S0-S3 as data, `knobs(stage)`, `value`, `is_changed`, `back_to_auto`; every knob path belongs to its stage per `state.stage_of_path`, and a sample value for every knob passes `recipe.validate` without an error finding
  check: python3 tools/hd-models/tests/test_studio_view.py -k TestKnobs
- [ ] 3. `studio/checkrows.py` and class TestCheckRows: `check_rows(studio, stage)` sorted fail, warn, acknowledged warn, info; info rows collapse to one summary row beyond four; each row carries its `fix_target` knob path from the table in JOB.md
  check: python3 tools/hd-models/tests/test_studio_view.py -k TestCheckRows
- [ ] 4. `studio/session.py` part 1 and class TestSessionOpen: `Session.open` (glb, new or existing recipe, source.sha256), `stage_inputs`, `run_stage` on a cached model, `open_stage` (silent return of a stale stage whose inputs are unchanged, re-run when they changed)
  check: python3 tools/hd-models/tests/test_studio_view.py -k TestSessionOpen
- [ ] 5. `studio/session.py` part 2 and `studio/run_audit.py`, class TestSessionEdit: `edit` with the 300 ms debounce (`due(now)`), `autosave`, `undo`/`redo`, `change_category`, `acknowledge`; the CLI `run_audit.py GLB [RECIPE] [--stage S1]` prints the audit JSON and is tested through a subprocess
  check: python3 tools/hd-models/tests/test_studio_view.py -k TestSessionEdit
- [ ] 6. Class TestWalk: one end-to-end walk on the synthetic glb (open, S0 fails on licence, set licence and category through the session, S0 passes, open S1, acknowledge its warnings, `footer` allows Next, undo brings the fail back), and one line about the new modules in `tools/hd-models/README.md`
  check: bash verify.sh
