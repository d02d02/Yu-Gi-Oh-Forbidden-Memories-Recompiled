# Open questions

Owner: U = user decides, C = Claude can resolve by reading code or measuring, U+C = both.

| # | Question | Owner | Blocks |
|---|---|---|---|
| Q1 | Is the 3-view structure right? Resolve by detailing each view (studio first, then models, then flow). | U+C | everything |
| Q2 | **Decided 2026-10-23 (delegated to Claude):** rail keeps ten stages and ten gates, shown under four group headings: Prepare (S0-S3), Fit (S4-S6), Judge (S7-S8), Ship (S9). Revisit after S0-S3 are detailed. | done | |
| Q2b | **Decided 2026-10-23 (user: yes):** S1 and S2 share one rail entry "Skeleton (S1–S2)" with two sections and two gates. Ids S1 and S2 stay as they are so check ids and recipe keys do not change. The rail has nine entries; docs still say S0–S9. | done | |
| Q3 | **Decided 2026-10-23 (user: yes to recommendation):** keep the Models view, small; see `models-view.md`. | done | |
| Q4 | Where do the card footprint dimensions and the BLS outline come from (disc data, stored outline, measured)? | C | S4 ghost and grid |
| Q5 | **Decided 2026-10-23 (user):** with no disc ground truth the reference is shown empty ("No disc reference for this act"), no guessed contact frame is drawn, and the contact check is not run. | done | |
| Q6 | **Decided 2026-10-23 (user: "ok", read as confirming the recommendation; Q5 was already decided):** stream low-res frames into the Tk viewport (works on every OS), plus a "Pop out game window" button for full-speed live play. Docking the game window is not portable (see `tk-mapping.md`). | done | |
| Q7 | Does the studio need the disc? (S0-S3 do not; S4+ need the BLS reference.) Can a stored reference cut that? | U | CI, first run |
| Q8 | Undo/redo scope: per knob, per stage, or recipe snapshots only? | U | studio-view |
| Q9 | Is "Reset to auto" per stage enough, or also per knob (the dot icon in the mock)? | U | studio-view |
| Q10 | **Decided 2026-10-23 (user: yes to recommendation):** the category matrix is data plus a popover, not a screen; see `flow-presets.md`. | done | |
| Q11 | Per-card scale/offset for one model on several cards: one package per card, or a package-level override table (needs a mod loader change)? See `recipe-schema.md`. | U+C | multi-card |
| Q12 | `attack2` (disc row 4) has no clip in the package; drop it from S5 until the engine has it (recommended), or add it to the package? | U | S5 |
| Q13 | Studio views that the schema corrected: S7 shots become a shot-list editor and the look keys are the real eight; update `studio-view.md` S7 and the mock. | C | S7 |
