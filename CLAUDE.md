# Working in this repo

- **Branch/status tracking**: `progress.md` at the repo root — current work,
  what's done, what's next, live findings. Check it first; keep it updated.
- **Headless/scripted testing of the native PC port** (reaching a specific
  screen, forcing owned cards, scripting controller input, capturing a
  reproducible screenshot, testing a single C function standalone without a
  full game rebuild): `notes/pc-headless-testing.md`. Read it before
  reaching for a live/interactive session to verify a change — most of what
  you need is scriptable.
- Building: `tools/pc/build_game32.py` (what `play.bat`/`play.sh` call).
  First run fetches the toolchain into `tmp/pc/`; later runs are
  incremental. A fresh `git worktree` has none of that fetched yet — see
  "Reusing a worktree's fetched toolchain" in the testing notes before
  building there.
