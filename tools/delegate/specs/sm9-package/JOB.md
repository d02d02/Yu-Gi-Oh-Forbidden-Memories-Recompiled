# Job sm9-package

## Goal
One UI-free module `tools/hd-models/studio/package.py` and tests: the S9 (package) checks of the Model Studio, headless. Pure Python 3.12, stdlib `unittest`, no tkinter, no numpy. It never runs a build or `native_check`; it only judges their outputs. Tests: `tools/hd-models/tests/test_studio_package.py`, one class per item.

## Facts (pasted: do NOT read other studio modules in full; `grep -n "def "` then read at most 30 lines)
- Run: `python3 tools/hd-models/tests/test_studio_package.py -k TestNativeCheck` from the repo root. Test header: `HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))`, then `from studio import audit, package`. The file MUST end with `if __name__ == "__main__":\n    unittest.main()`.
- Findings: `audit.finding(check, level, message, fix="", value=None)`; levels `"fail" "warn" "info"`.
- `native_check.py` prints lines `error: <where>: <text>` and `warning: <where>: <text>`, ends with `<N> errors, <M> warnings`, and prints `<mod>: <X.Y> MB for all its models, if they all show (the game's budget: <B> MB)`. Other lines (indented, or `<where>: N vertices ...`) are descriptive and ignored.
- Budget: 512 MB default. Warn at 80% or more of the budget, fail over it.
- Provenance: `meta` dict with keys `author`, `license`, `url`; S9 requires all three non-empty strings (after strip).
- Identity: two builds are lists of `(relative_path, sha256_hex)` pairs, compared as sets.
- Package name: see item 5.

## Items (see progress.md)
1. `parse_native_check(text)` returns `{"errors": [(where, text)], "warnings": [(where, text)], "total_mb": float|None, "budget_mb": int|None}` from the printed text; ignores other lines; tolerant of blank text.
2. `check_native(parsed)` finding `S9.native_check` fail per error (message "<where>: <text>", fix "Open the stage named in the message."), value = where; none when no errors. (Warnings give `warn` findings with the same id.)
3. `check_budget(parsed)` finding `S9.budget`: fail when `total_mb > budget_mb`, warn when `>= 0.8 * budget_mb` (message "Native models use N MB of B MB.", N one decimal, fix "Lower the atlas or triangle count."), none below or when either value is None.
4. `check_identical(build_a, build_b)` finding `S9.identical` fail when the sets differ (message "N file(s) differ between two builds.", N = size of the symmetric difference by path, fix "Report this: the recipe is not deterministic."), value = sorted list of differing paths; none when equal.
5. `check_provenance(meta)` finding `S9.provenance` fail per missing/empty key of author, license, url (message "Missing <key>.", fix "Fill S0."); none when all present. `valid_package_name(name)` returns bool per the fact above (1..64 chars `[A-Za-z0-9_-]`, first char not `-`).
6. `run_s9(meta, native_text, build_a=None, build_b=None)` returns `{"parsed": ..., "findings": [...]}` running items 2-5 (identity only when both builds are given). Tests: one clean input gives no findings; one bad input gives the expected ids. One README row for `studio/package.py` is added by the supervisor: do NOT touch README.

## Constraints
One item per session; WRITE small: a new file at most 60 lines per write, grow it by edits of at most 60 lines. Do not edit anything except `studio/package.py` and `tests/test_studio_package.py`. Never change `audit.py`, `state.py`, `recipe.py`, `timemap.py`, `look.py`, `runs.py`, README.

## Acceptance
`bash verify.sh` exits 0.
