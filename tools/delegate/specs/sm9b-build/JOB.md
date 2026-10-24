# Job sm9b-build

## Goal
One module `tools/hd-models/studio/build.py` and tests: the S9 build step of the Model Studio, headless. It turns a recipe into the `new_native_mod.py` command, runs it twice through an injectable runner, hashes the outputs and feeds `package.run_s9`. Pure Python 3.12, stdlib `unittest`, no tkinter. Tests use a FAKE runner (no numpy, no real conversion): `tools/hd-models/tests/test_studio_build.py`, one class per item.

## Facts (pasted: do NOT read other studio modules in full; `grep -n "def "` then read at most 30 lines)
- Run: `python3 tools/hd-models/tests/test_studio_build.py -k TestFlags` from the repo root. Test header: `HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))`, then `import recipe` and `from studio import build, package`. The file MUST end with `if __name__ == "__main__":\n    unittest.main()`.
- `recipe.convert_args(recipe)` returns a dict of native_convert option dests (only keys the recipe sets). Known dests and their flags: `clips` `--clips` (str), `clips_from` `--clips-from` (path), `rig` `--rig` (str), `root` `--root` (str), `root_height` `--root-height` (number), `origin_height` `--origin-height`, `height` `--height`, `extent` `--extent`, `scale` `--scale` (numbers), `texture_max` `--texture-max` (int), `follow` `--follow` (a LIST: repeat the flag per item), `no_center` `--no-center`, `keep_root_motion` `--keep-root-motion`, `no_pbr` `--no-pbr` (booleans: the bare flag when True, nothing when False), `name` `--name`, `author` `--author`, `license` `--license` (str).
- `new_native_mod.py MODEL.glb --card N [--card M ...] --out DIR [--id ID] [--name NAME] [--author A] [--license L] [-- <native_convert options>]`. It runs with `sys.executable`, script path `tools/hd-models/new_native_mod.py` (use `Path(__file__).resolve().parent.parent / "new_native_mod.py"` in build.py).
- A build is a list of `(relative_path, sha256_hex)` pairs, sorted by path. `package.run_s9(meta, native_text, build_a=None, build_b=None)` returns `{"parsed": ..., "findings": [...]}`; `package.valid_package_name(name)` returns bool.
- A runner is `runner(argv) -> (returncode: int, text: str)`; the real one is `subprocess.run` with stdout and stderr merged, UTF-8, text mode.

## Items (see progress.md)
1. `flags(args)` turns a dict of dests (above) into a list of command tokens in sorted dest order; raises `ValueError` on an unknown dest. Booleans: bare flag when True, nothing when False; lists repeat the flag; other values `[flag, str(value)]`.
2. `command(recipe, glb, out_dir, cards)` returns the full argv: `[sys.executable, "-I", <new_native_mod.py>, str(glb), "--card", N ... , "--out", str(out_dir), "--id", <pkg.name>, "--", *flags(recipe.convert_args(recipe))]`. `pkg.name` comes from `recipe["pkg"]["name"]`, default the glb's stem; raises `ValueError` when the name fails `package.valid_package_name` or `cards` is empty. (Name the parameter `rec` to avoid shadowing the `recipe` module.) Omit the `--` when there are no flags.
3. `hash_tree(folder)` returns the sorted build list for every file under the folder (relative POSIX paths, sha256 hex); `[]` when the folder is missing.
4. `real_runner(argv)` runs the command with `subprocess.run` (capture, merge stderr into stdout, `encoding="utf-8"`, `errors="replace"`) and returns `(returncode, text)`. Test only that it returns `(0, "x")` for `[sys.executable, "-c", "print('x')"]` after `.strip()` of the text.
5. `build_twice(rec, glb, out_dir, cards, runner=real_runner)` builds into `out_dir/"a"` then `out_dir/"b"` (create `out_dir`; the runner creates the rest), stops after the first nonzero return code, and returns `{"ok": bool, "text": <text of build a>, "build_a": [...], "build_b": [...], "returncode": int}` (build_b is `[]` when it did not run).
6. `run_build_s9(rec, glb, out_dir, cards, runner=real_runner)` runs `build_twice`; when not ok returns `{"build": that, "findings": [audit-style fail finding id "S9.build" message "The build failed (code N).", fix "Open the stage named in the log."]}`; when ok returns `{"build": that, "findings": package.run_s9(rec.get("meta", {}), text, build_a, build_b)["findings"]}`. Import the finding helper as `from studio import audit` and use `audit.finding`. Tests: fake runner that writes the same file twice (no identity finding), one that writes different bytes the second time (S9.identical fail), one that returns 1 (S9.build). One README row for `studio/build.py` is added by the supervisor: do NOT touch README.

## Constraints
One item per session; WRITE small: a new file at most 60 lines per write, grow it by edits of at most 60 lines. Do not edit anything except `studio/build.py` and `tests/test_studio_build.py`. Never edit any other file, in particular not `tests/test_studio_audit.py`, `package.py`, `recipe.py`, README.

## Acceptance
`bash verify.sh` exits 0.
