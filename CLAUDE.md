# Working in this repo

Durable conventions for this repo. Branch-specific status/progress goes in
`WIP_NOTES.md` instead (see there, on whatever branch is checked out) — this
file is for things that stay true across branches and sessions.

Like `WIP_NOTES.md`, this file is tracked and pushed on the user's own fork
but is not meant to reach upstream — exclude it (and `WIP_NOTES.md`) when
cherry-picking commits onto a clean PR branch.

## Git workflow

- Remotes: `origin` is the user's own fork, `upstream` is the original repo.
  Sync direction is upstream → master → origin.
- Real work happens on `dev` (or a `feat/*` branch); merge `master` into it
  regularly. **Never rebase `dev`** or any shared work branch.
- First thing each session: fetch `origin` and `upstream`, report any drift
  found, and **ask before pulling, resetting, or rebasing** — don't do it
  unprompted.
- Never PR a branch with personal/WIP commits mixed in (this file,
  `WIP_NOTES.md`, scratch experiments). Cherry-pick the real code commits
  onto a clean PR branch first.
- Do not add a `Claude-Session` trailer line to commits or PRs in this repo.

## Build / test

- Build: `python tools/pc/build_game32.py --build tmp/pc/game32dbg` (or
  `game32` for the user's own copy) from the repo root.
- Two separate binaries by convention: `game32` is the user's own, played
  normally; `game32dbg` is Claude's own build/test copy, with its own user
  data dir (e.g. `MEMORIES_USER_DIR=../game32dbg-user`). Ask the user to
  close `game32dbg` if the exe is locked before rebuilding, and don't trust
  a build without rebuilding it first. Never cross-load the user's own save
  states into the debug copy.
- Fresh-install / shipped-defaults testing: never use the real
  `Documents/My Games` profile for this, even with the environment
  cleared — always point `MEMORIES_USER_DIR` at a dedicated, never-reused
  empty directory.
- For UI/rendering features, "looks right live" is the actual spec. Ask the
  user to drive live-game verification or tell you what to press — don't
  blind-guess controls or replay long boot sequences repeatedly to get to a
  test screen.

## Editing files on Windows

PowerShell's `Get-Content`/`Set-Content` mangle UTF-8 (BOM/encoding issues)
when rewriting repo files. Never use them to rewrite a tracked file — use
the Edit tool, or if a shell must do it, write via .NET with no BOM.

## Branch status

See `WIP_NOTES.md` at the repo root on the active branch for current
progress, open issues, and next steps — not this file, and not Claude's own
memory.
