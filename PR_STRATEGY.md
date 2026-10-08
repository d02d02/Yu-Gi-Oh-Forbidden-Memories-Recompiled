# Pushing to the PR: strategy

Branch `ccr-4419a39d-cr1tf0` is a working branch. It sits on top of the head of
PR #302 (`fix/assets-hd-anime-frame`, upstream `Unchiga/Yu-Gi-Oh-Forbidden-Memories-Recompiled`).
The PR itself is never pushed to from here: its commits are cherry-picked onto it.

## Rules

- Work and commit on this branch only. One commit per reviewable change, with a message that says what and why.
- Keep each commit applicable on its own on top of the PR head, in order. Say in the message when one needs an earlier one.
- To submit, cherry-pick the commits onto the PR branch, oldest first, then push:

      git fetch origin ccr-4419a39d-cr1tf0
      git checkout fix/assets-hd-anime-frame
      git cherry-pick <oldest> ... <newest>
      git push

- To squash into one commit, cherry-pick with `--no-commit` and commit once.
- This file is working-branch only. Leave it out of the cherry-pick.
- If the PR head moves (a review fix, a merge), rebase this branch onto it before picking.

## Submitted or ready to pick (on top of 4d4dddc)

| Commit | What |
|---|---|
| `63665d0` | A ritual spell wears magic's frame colour only when the layout has no ritual frame of its own (`CardLayout_RitualWearsMagic`), with a test and test stubs. Answers the review on #302. |
| `99656ce` | HD pack: no `ritual` frame without a ritual PNG, so the hand's small frame and the card view's big one agree. Needs `63665d0`. |

## Frame rule these commits follow

`Cards_FrameColor` is the single decision for both sizes (card view's big frame, hand's small frame).
A ritual frame is designated when the layout names a ritual image that is a different file from magic's.
Designated: both sizes use the ritual frame. Not designated: both use magic's. Anime frame off: retail.

## Next milestone: ATK/DEF digit size

Goal: the digits fill the stat box better, and use the original font.
- Stat box inner area is about 51x17 units; the digits are 6x13 each, about 24x13 for four.
- They are drawn in `src/game/func_80028B08.c` at native size. A larger size needs a quad of its own, like `CardLayout_DrawArt`.
- The HD digit sheet is built from `stats.png` in `tools/pc/hd_assets_pack.py`.
- Needed from the owner: the font file (not committed; the pack reads it from the assets folder) and a screenshot of the current digits.
- Not checkable here (no disc data): test in game at Internal 4x.
