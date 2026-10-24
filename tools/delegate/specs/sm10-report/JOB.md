# Job sm10-report

## Goal
One UI-free module `tools/hd-models/studio/report.py` and tests: the S9 "Export report" of the Model Studio (a human-readable summary of a model's stages), headless. Pure Python 3.12, stdlib `unittest`, no tkinter. Tests: `tools/hd-models/tests/test_studio_report.py`, one class per item.

## Facts (pasted: do NOT read other studio modules in full; `grep -n "def "` then read at most 30 lines)
- Run: `python3 tools/hd-models/tests/test_studio_report.py -k TestStageLines` from the repo root. Test header: `HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))`, then `from studio import report`. The file MUST end with `if __name__ == "__main__":\n    unittest.main()`.
- A finding is a dict `{"id": "S4.footprint", "level": "fail"|"warn"|"info", "message": str, "fix": str, optionally "value"}`. The stage of a finding is the part of its id before the first dot ("S4").
- Stages in order: `S0 S1 S2 S3 S4 S5 S6 S7 S8 S9`. Stage names: S0 Intake, S1 Skeleton, S2 Skeleton, S3 Materials, S4 Size, S5 Clips, S6 Timing, S7 Look, S8 Validate, S9 Package. Groups: Prepare (S0-S3), Fit (S4-S6), Judge (S7-S8), Ship (S9).
- Input: `findings` is a dict `{stage: [finding, ...]}` (a stage missing from it was never run); `acks` is a list of acknowledged finding ids; `meta` is a dict with optional `author`, `license`, `url`, `name`; `build` is None or `{"ok": bool, "files": [(path, sha256)], "text": str}`; `runs` is a list of marks `{"row": str, "result": "seen"|"problem", "problem": str|None, "time": float}`.
- A stage status is: `"not run"` when absent from `findings`; `"fail"` when any finding has level fail that is not acknowledged; `"warn"` when any warn (acknowledged or not) and no unacknowledged fail; else `"pass"`. Acknowledgement only counts for warn findings (a fail is never hidden).

## Items (see progress.md)
1. `stage_status(findings_for_stage, acks)` returns the status string above for one stage's list (`None` input means `"not run"`).
2. `stage_lines(stage, findings_for_stage, acks)` returns a list of Markdown lines for one stage: a heading line `### S4 Size - fail`, then one bullet per finding `- **fail** S4.footprint: <message> (<fix>)` (the fix part omitted when empty, `[acknowledged]` appended for an acknowledged warn), or the single line `Not run.` for a stage that never ran, or `No findings.` for a run with an empty list.
3. `summary_table(findings, acks)` returns Markdown lines of a table with columns `Group | Stage | Name | Status` for all 10 stages in order (header, separator, 10 rows).
4. `build_lines(build)` returns Markdown lines for the build: `Not built.` for None; else `Build: ok|failed`, the file count, and one bullet per file `- path sha256[:12]`; at most the first 20 files then `- ... N more`.
5. `runs_lines(runs)` returns Markdown lines: `No scene runs recorded.` for none, else one bullet per mark `- row: seen` or `- row: problem (<problem>)`, the latest mark per row only, in first-seen row order.
6. `render(findings, acks, meta, build, runs)` returns the whole report as one string: `# Model report: <name or "unnamed">`, a line with author/licence/url (each shown only when set; `Provenance missing.` when none is set), `## Summary` + table, `## Stages` + all stage lines separated by blank lines, `## Build` + build lines, `## Scene runs` + runs lines; ends with a newline. Tests: one full report for a clean model, one for a model with a fail, an acknowledged warn, a failed build and a problem mark. One README row for `studio/report.py` is added by the supervisor: do NOT touch README.

## Constraints
One item per session; WRITE small: a new file at most 60 lines per write, grow it by edits of at most 60 lines. Do not edit anything except `studio/report.py` and `tests/test_studio_report.py`. Never edit any other file, in particular not `tests/test_studio_audit.py`, README or any other `studio/*.py`.

## Acceptance
`bash verify.sh` exits 0.
