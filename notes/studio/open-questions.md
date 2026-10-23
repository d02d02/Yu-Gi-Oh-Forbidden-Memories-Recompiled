# Open questions

Owner: U = user decides, C = Claude can resolve by reading code or measuring, U+C = both.

| # | Question | Owner | Blocks |
|---|---|---|---|
| Q1 | Is the 3-view structure right? Resolve by detailing each view (studio first, then models, then flow). | U+C | everything |
| Q2 | **Decided 2026-10-23 (delegated to Claude):** rail keeps ten stages and ten gates, shown under four group headings: Prepare (S0-S3), Fit (S4-S6), Judge (S7-S8), Ship (S9). Revisit after S0-S3 are detailed. | done | |
| Q2b | Observation after detailing S0-S3: S0-S2 and S3 need no engine and could run before the disc is touched, S2 largely continues S1 (same bone overlay, same Blender hand-off). Candidate: merge S1+S2 into one "Skeleton" stage with two sections. S7-S9 are now detailed and do not change this. Recommendation: merge S1+S2 into "Skeleton" (nine stages, gates stay: audit gate and rig gate inside one stage); keep the rest. Awaiting the user. | U | rail |
| Q3 | Is the list view needed for a handful of models, or is a picker in the Studio header enough? | U | models-view |
| Q4 | Where do the card footprint dimensions and the BLS outline come from (disc data, stored outline, measured)? | C | S4 ghost and grid |
| Q5 | **Decided 2026-10-23 (user):** with no disc ground truth the reference is shown empty ("No disc reference for this act"), no guessed contact frame is drawn, and the contact check is not run. | done | |
| Q6 | **Decided 2026-10-23 (user: "ok", read as confirming the recommendation; Q5 was already decided):** stream low-res frames into the Tk viewport (works on every OS), plus a "Pop out game window" button for full-speed live play. Docking the game window is not portable (see `tk-mapping.md`). | U | all engine stages |
| Q7 | Does the studio need the disc? (S0-S3 do not; S4+ need the BLS reference.) Can a stored reference cut that? | U | CI, first run |
| Q8 | Undo/redo scope: per knob, per stage, or recipe snapshots only? | U | studio-view |
| Q9 | Is "Reset to auto" per stage enough, or also per knob (the dot icon in the mock)? | U | studio-view |
| Q10 | The category matrix: screen or data? | U | flow-presets |
