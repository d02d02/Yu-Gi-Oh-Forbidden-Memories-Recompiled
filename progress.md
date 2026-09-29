# Progress

What is current: decisions, state, what's left. Finished and superseded work, with
the full write-up, is in **`history.md`**; this file keeps a short summary of each
with a pointer there. Update in place as work continues instead of re-deriving it
next session.

## 2D Monsters mod

**Done** (full write-up: `history.md`): `mods/2d-monsters/` built — a flat,
camera-facing card-art cutout in place of the 3D Monsters mod's loaded model.
Disabled by default, conflicts with `3d-monsters`. Compiles cleanly through
`build_mod.py` and the full `build_game32.py`; both the mod object and the 32-bit
`memories-pc` it builds against link correctly. Pushed to
`claude/2d-art-replace-3d-models-bbpme7`.

**Left to do: record the smoke-test baseline.** `tests/pc/smoke/duel-2d-monsters.json`
is committed with no `sha256` yet (reuses `duel-3d-monsters.json`'s recorded duel
input, ten monsters face up, five a side, `mod.3d-monsters` off / `mod.2d-monsters`
on), so it currently fails if run — no session so far has had the private retail
disc image this class of test needs (`notes/continuous-integration.md`). On a
machine with the disc set up (`MEMORIES_DISC` pointed at it):

```sh
python3 tools/pc/build_game32.py
python3 tools/pc/smoke.py --record
```

Then **look at the dumped frame** at `tmp/pc/smoke/duel-2d-monsters.ppm` before
committing the recorded hash — `--record` only accepts whatever the current build
renders; it does not itself confirm the cutouts look right. Check in particular:
card art appears above each face-up field monster (not a 3D model, not the tiny
default field-card sprite alone), sized and positioned plausibly relative to its
card, and correctly depth-sorted against nearer/farther field cards. If the size
needs tuning, the mod's `pixels`/`lift`/`depth` settings (`mod.json`) are read
live, no rebuild needed, so adjust and re-dump rather than editing the code.

Once the baseline looks right and is committed, this item is done and its
write-up moves to `history.md`.
