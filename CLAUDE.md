# Working in this repo

- **Branch/status tracking**: `progress.md` at the repo root — current work,
  what's done, what's next, live findings. Check it first; keep it updated.
- **Headless/scripted testing of the native PC port** (reaching a specific
  screen, forcing owned cards, scripting controller input, capturing a
  reproducible screenshot, testing a single C function standalone without a
  full game rebuild): `C:\Users\mdahh\.claude\shared\yfm-notes\pc-headless-testing.md`
  (shared copy; `notes/pc-headless-testing.md` is only a pointer). Read it before
  reaching for a live/interactive session to verify a change — most of what
  you need is scriptable.
- Building: `tools/pc/build_game32.py` (what `play.bat`/`play.sh` call).
  First run fetches the toolchain into `tmp/pc/`; later runs are
  incremental. A fresh `git worktree` has none of that fetched yet — see
  "Reusing a worktree's fetched toolchain" in the testing notes before
  building there.
- **Shared notes across all branches/worktrees**: `C:\Users\mdahh\.claude\shared\yfm-notes\`
  (outside the repo; start at `INDEX.md`). Read it at the start of work in any
  new branch or worktree — it holds the test/screenshot procedure and
  cross-branch findings. Write there (not only in a worktree's own notes) when
  the user asks for notes other branches should see, or when you learn
  something that would save the next session time; update the existing file,
  keep it short, drop resolved items, and register a new worktree in
  `INDEX.md`. Per-branch status stays in `progress.md` / `WIP_NOTES.md`.
