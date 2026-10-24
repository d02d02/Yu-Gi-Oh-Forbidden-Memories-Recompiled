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
