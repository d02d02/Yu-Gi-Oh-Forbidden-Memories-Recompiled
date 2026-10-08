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
| `bf50ab9`, `c096cc7`, `9caae8a` | ATK/DFD digits from a font (strip of 40x48 texel cells, engine draw, centred on the measured stat boxes; stars fix). In this order, after the two above. |

## Frame rule these commits follow

`Cards_FrameColor` is the single decision for both sizes (card view's big frame, hand's small frame).
A ritual frame is designated when the layout names a ritual image that is a different file from magic's.
Designated: both sizes use the ritual frame. Not designated: both use magic's. Anime frame off: retail.

## Milestone: ATK/DEF digits (done, untested in game)

Font chosen by the owner: Yu-Gi-Oh! Matrix Regular Small Caps (file "2"), stretch 1.25. Build with `--digit-font <that .ttf>`.


Goal: the digits fill the stat box and use the card game's font (a thin,
wide Matrix Regular Small Caps look).
- `tools/pc/card_digits.py` draws a 200x88 strip (5x2 cells of 40x44) from a .ttf; `hd_assets_pack.py --digit-font <ttf>` adds it as `card_layout.digits`. The font is read, never committed.
- `CardLayout_Digits` (card_layout.c) reads the key; `CardLayoutArt_DigitCell` (card_layout_art.c) puts the strip in the frame's bank (page slot 9); `CardLayout_DrawDigits` (func_80028B08.c) draws each stat's digits at the key's size, centred on the box.
- Only with the anime frame on; retail and a layout without `digits` are unchanged. A raised/lowered stat keeps retail's tinted digits.
- Known: five digits (stat above 9999) are 50 units wide in a 51-unit box. Not run in the game (no disc data here): check at Internal 4x.
