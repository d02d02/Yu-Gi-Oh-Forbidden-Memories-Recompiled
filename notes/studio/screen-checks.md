# Screen checks (one at a time; reply "checked" or what is wrong)

Expected results come from the code, not from having seen the screen. A mismatch is a finding.

| # | Open | Look at | Expected |
|---|---|---|---|
| 1 | FM Editor, Studio tab, dragon.glb | Left rail; right panel on S0 | Rail lists S0..S9 under Prepare / Fit / Judge / Ship. S0 heading "S0 <state>". Check rows with a coloured chip. Fields: Category (dropdown), Author, License, URL; grey "auto: ..." hints. Saved indicator reads Saved. |
| 2 | Same window | Click S4, S6, S7, S8, S9 | S4: 8 fields (size mode dropdown...). S6: 3 fields. S7: 9 fields (ambient...camera moves). S9: 2 fields. Each stage shows its own check rows; none crashes or leaves the old stage's fields. |
| 3 | Same window, S7 | Type 30 in "Ambient light", press Enter | Field keeps 30; a "Back to auto" button appears; Saved indicator flips to Saving... then Saved; Undo button enables, Undo restores the empty field. |
| 4 | Same window, S8 | The run list | 10 rows (Library turntable, Field attack, Arena attack, Act: idle ... Act: guard), status "not run", each with Run / Looks right / Report a problem. All Run buttons greyed. Note line "Build the package (S9) to enable Run." Click "Looks right" on one row: its status becomes "seen". |
| 5 | Game window, field attack, dragon package on card 364 | The attacker on the field | The dragon model (not the disc's monster) stands and attacks; it moves with the Fly animation; no black/missing textures; size roughly like a normal monster. |
| 6 | Game window, arena attack, same package | The arena fight | Dragon drawn in the arena at a sensible size, facing the opponent, animating; camera unchanged from vanilla. |

After 5 and 6 I record your result in the S8 marks.

| 8 | Studio tab, dragon, S9 | "Build package" and "Export report" buttons | Build runs ~1 min with the button greyed, then "Built: <path>" appears and S8 Run buttons enable. Export report writes `report.md` next to the glb (heading shows the path). |
| 9 | RDP: play the built dragon mod in the real game window (View > Internal 2x) | Field and arena attack | Same as rows 5-6, judged by the user's eyes: size, grey texture, wing clipping, facing. I only read capture frames; they looked right. |

New 2026-10-25 (one at a time, reply "checked" or what is wrong):

| # | Open | Look at | Expected |
|---|---|---|---|
| 10 | Studio, dragon or angel, S8, "Scrub the attack live..." (needs a card and the disc) | The game window and the "Live scrub" window | Package builds, game starts hidden, a Live scrub window opens; dragging the slider shows the phase and the engine phase beside it; Save a shot writes `runs/scrub/scrub/phase-N.png` |
| 11 | Same Live scrub window | Camera dropdown (front, side, top, three-quarter, close, game) | The camera changes in the game; "game" gives it back |
| 12 | Same window | bbox, grid, bones checkboxes (needs the GL window visible) | Yellow box, grey grid, green bone lines over the model; unchecking removes them |
| 13 | Same window | "show disc model" checkbox | The disc's own monster replaces the model in the same frame; unchecking brings the model back |
| 14 | S5 with a model that lacks an act | Make a clip / Use a clip / Library clip... buttons | Each fills the row; Undo reverts one step |
| 15 | S0 and S1/S2 | Choose card..., Open a rigged glb... (also on S2.map rows) | Card set in the recipe; glb opens and the checks re-run |
| 16 | Any stage after Open glb | Model preview at the top (Mesh, Bones, Box, Weights of, Front/Side/Back/Top, drag to orbit, wheel to zoom) | Angel shows its mesh and 69 bones; 36 red bones (no weight); picking a leg bone paints its weights blue to red |
