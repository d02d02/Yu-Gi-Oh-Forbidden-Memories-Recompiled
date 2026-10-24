# Job <id>

## Goal
<what exists when this is done, in two or three sentences>

## Facts and excerpts (pasted by the supervisor: do NOT re-read the sources they come from)
<the constants, signatures, rules and short code excerpts the items need, copied in. Every file the agent would otherwise
open to find a fact belongs here as the fact itself. In recipe-v1 the agent read the same four sources 3 to 5 times
across sessions because only pointers were given.>

## Given (read-only for the agent)
<test files or fixtures the supervisor wrote; the agent writes code to make them pass and may not edit them. If the job has
none, say "none: the agent writes its own tests per item".>

## Read first (only what is not pasted above; paths with the lines that matter)
- <path:lines> <why>

## You may change
<exact paths or globs>

## You must not touch
Everything else, including progress.md structure (only tick items and add Result/Failed lines) and the "Given" files.

## Constraints
- Test file: never edit or move its tail (`if __name__ == "__main__":` + `unittest.main()`), never delete or overwrite an existing test class; add new classes above the tail with edits that only add lines. (after-iter.py restores dropped classes, but do not rely on it.)
- Python 3.12 in this Linux shell; numpy and Pillow are installed. No GPU, no game window, no disc image.
- Match the surrounding code's style; no new dependencies.
- One item per session: the loop re-runs each item's `check:` itself, ticks what passes and commits after every iteration.

## Acceptance
`bash verify.sh` exits 0.
