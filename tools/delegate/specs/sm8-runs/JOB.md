# Job sm8-runs

## Goal
One UI-free module `tools/hd-models/studio/runs.py` and tests: the S8 (in-context validation) run list, marks and checks of the Model Studio, headless. Pure Python 3.12, stdlib `unittest`, no tkinter, no numpy. Tests: `tools/hd-models/tests/test_studio_runs.py`, one class per item.

## Facts (pasted: do NOT read other studio modules in full; `grep -n "def "` then read at most 30 lines)
- Run: `python3 tools/hd-models/tests/test_studio_runs.py -k TestRows` from the repo root. Test header: `HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))`, then `from studio import audit, runs`. The file MUST end with `if __name__ == "__main__":\n    unittest.main()`.
- Findings: `audit.finding(check, level, message, fix="", value=None)`; levels `"fail" "warn" "info"`.
- Scenes: `"library"` (no disc), `"field"` and `"arena"` (need the disc). Acts: `idle enter attack hit destroyed win guard`. Row ids: the three scene ids, then `"act:<name>"` for each act (10 rows). Acts run in the arena scene; act rows need the disc.
- Row statuses: `"not run"`, `"running"`, `"seen"`, `"problem"`. A mark is `{"row": str, "result": "seen"|"problem", "problem": str|None, "package_hash": str, "time": float}`; `problem` is one of `wrong size`, `wrong timing`, `clipping`, `pose pop`, `wrong look`. Problem to owning stage: wrong size S4, wrong timing S6, clipping S5, pose pop S5, wrong look S7.
- Recipe key `runs` is a list of marks (newest last; the latest mark per row counts). `stage_times` is a dict `{"S4": float, ...}` of last-change times per stage S0..S7.

## Items (see progress.md)
1. `run_rows(disc_available)` returns the 10 rows as dicts `{"id", "label", "needs_disc": bool}` in the order above; labels: "Library turntable", "Field attack", "Arena attack", "Act: idle" etc. `disc_available` does not change the list.
2. `make_mark(row, result, package_hash, time, problem=None)` returns a mark dict; raises `ValueError` on an unknown row, a result not seen/problem, a problem result without a valid problem choice, or a seen result with a problem. `owning_stage(problem)` returns the stage id string, `ValueError` on an unknown problem.
3. `row_status(marks, row_id, package_hash)` returns `"not run"` when no mark for the row, or the latest mark's package_hash differs from `package_hash`; else the latest mark's result. `status_table(marks, package_hash, disc_available)` returns `{row_id: status}` for all rows; rows needing the disc when it is absent are `"not run"`.
4. `check_coverage(table, disc_available)` finding `S8.coverage` fail listing rows still `"not run"` (message "Not run yet: a, b.", fix "Run the remaining rows."); rows needing the disc are skipped when it is absent; none when all covered.
5. `check_problem(marks, package_hash)` finding `S8.problem` fail per row whose current status is `"problem"` (message "<row>: <problem>.", fix "Open the stage named on the row.", value = owning stage id); none otherwise.
6. `check_stale(marks, stage_times)` finding `S8.stale-run` warn per row whose latest mark `time` is older than the newest value in `stage_times` (message "<row> ran before the latest change.", fix "Run it again."); none otherwise or when stage_times is empty. `check_disc(disc_available)` finding `S8.disc` info when False (message "Field and arena scenes need the disc.", fix "Library turntable only; set MEMORIES_DISC for field and arena."); none when True.
7. `run_s8(recipe, package_hash, disc_available, stage_times=None)` returns `{"rows": run_rows(...), "status": status_table(...), "findings": [...]}` running items 4-6 (marks = `recipe.get("runs", [])`). Tests: one clean recipe (all 10 rows seen, disc present) gives no findings; one bad recipe gives the expected ids. One README row for `studio/runs.py` is added by the supervisor: do NOT touch README.

## Constraints
One item per session; WRITE small: a new file at most 60 lines per write, grow it by edits of at most 60 lines. Do not edit anything except `studio/runs.py` and `tests/test_studio_runs.py`. Never change `audit.py`, `state.py`, `recipe.py`, `timemap.py`, `look.py`, README.

## Acceptance
`bash verify.sh` exits 0.
