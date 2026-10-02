# WIP notes: feat/custom-card-art

Scratch status file for the current feature branch. Tracked and pushed so
work can resume in a fresh session, but **not meant to reach upstream** --
cherry-pick real code commits onto a clean PR branch and leave the
commit(s) touching this file behind.

Kept short on purpose: resolved items get rolled out of here once they're
committed (git log + the commit message + code comments are the history;
this file is only what's still in flight). Replace wholesale when a new
feature branch starts.

## Goal

Duel-Links-style full-bleed card presentation (hide frame/title/
description, enlarge art, reposition stats) behind `SET_CARD_LAYOUT`
(off by default), additive via `#ifdef MEMORIES_PC` -- retail's
byte-matched path untouched. Tip as of 2026-10-02: `44e4d0145` (origin).

Architecture, resolved findings, and the mechanism used throughout
(`DisplayObject_SubmitPacket`'s case-4/5 dispatch for projected quads) are
documented in `src/pc/cards/card_layout.c`/`.h` and `src/game/
func_80028B08.c`'s own comments, and in the commit messages for `93f5032dc`
/ `f781688e0` -- read those rather than expecting a duplicate here.

## Open issue (deferred on purpose -- user's call, 2026-10-02)

The art (`CARD_LAYOUT_ART`, `card_layout.c`) falls short of the
card-viewer's wider backdrop -- the one that also covers where
description text normally sits, further right -- by ~15-20px, exposing
background through the gap (confirmed by pixel-measuring a live
screenshot). Not a left/right translation bug. **Leave it** until the
rect is rethought as ratios that include that wider right-hand area --
don't patch with an isolated nudge.

## Next steps

1. Rethink the art/stat-row rect as ratios including the right-hand text
   area (the open issue above), once everything else is confirmed working.
2. Build a gold/olive backdrop bar for the icon/ATK-DEF row (Duel Links
   reference) -- stars/attribute/ATK/DEF still float with no backdrop.

## Workflow notes

- Build: `python tools/pc/build_game32.py --build tmp/pc/game32dbg`. Exe
  locks if still running -- ask the user to close it first.
- Test: `MEMORIES_USER_DIR=../game32dbg-user`, `MEMORIES_CARD_LAYOUT=1`,
  `MEMORIES_TRACE=card_layout MEMORIES_LOG=card_layout.log`.
- Reference images used so far: `maxresdefault.png` (repo root, untracked)
  and `game/pixels.png` (untracked/ignored) -- both local-only, not in git.
