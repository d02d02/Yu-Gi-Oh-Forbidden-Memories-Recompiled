# Open questions

Owner: U = user decides, C = Claude can resolve by reading code or measuring, U+C = both.

| # | Question | Owner | Blocks |
|---|---|---|---|
| Q1 | All three views are now detailed (Studio S0-S9, Models small, flow as data). The structure holds so far; the user confirms by reviewing the mock and `studio-view.md`. | U | everything |
| Q2 | **Decided 2026-10-23 (delegated to Claude):** rail keeps ten stages and ten gates, shown under four group headings: Prepare (S0-S3), Fit (S4-S6), Judge (S7-S8), Ship (S9). Revisit after S0-S3 are detailed. | done | |
| Q2b | **Decided 2026-10-23 (user: yes):** S1 and S2 share one rail entry "Skeleton (S1–S2)" with two sections and two gates. Ids S1 and S2 stay as they are so check ids and recipe keys do not change. The rail has nine entries; docs still say S0–S9. | done | |
| Q3 | **Decided 2026-10-23 (user: yes to recommendation):** keep the Models view, small; see `models-view.md`. | done | |
| Q4 | **Decided 2026-10-23 (delegated to Claude):** measured from the disc once (build step SM0) and stored as a reference pack; see `build-plan.md`. | done | |
| Q5 | **Decided 2026-10-23 (user):** with no disc ground truth the reference is shown empty ("No disc reference for this act"), no guessed contact frame is drawn, and the contact check is not run. | done | |
| Q6 | **Decided 2026-10-23 (user: "ok", read as confirming the recommendation; Q5 was already decided):** stream low-res frames into the Tk viewport (works on every OS), plus a "Pop out game window" button for full-speed live play. Docking the game window is not portable (see `tk-mapping.md`). | done | |
| Q7 | **Decided 2026-10-23 (delegated to Claude):** S0-S3 never need the disc; S4-S7 use the reference pack; S8 field and arena need the disc. | done | |
| Q8 | **Decided 2026-10-23 (delegated to Claude):** one linear undo history per recipe, one entry per knob change or finished viewport gesture. | done | |
| Q9 | **Decided 2026-10-23 (delegated to Claude):** both per-stage reset and a per-knob back-to-auto control. | done | |
| Q10 | **Decided 2026-10-23 (user: yes to recommendation):** the category matrix is data plus a popover, not a screen; see `flow-presets.md`. | done | |
| Q11 | **Decided 2026-10-23 (delegated to Claude):** per-card scale/offset become optional `scale`/`offset` members on a `native_models` entry in `mod.json` (one entry per card group, several entries may point to the same package). Additive mod API change; model.json stays as is. Checked in `src/pc/render/native_registry.c`: each entry loads its own package (own bytes and decoded maps), so two entries on one package cost two copies of the memory. The loader would need to share one load between entries with the same path; until then, multi-card use of one model should list all its cards in ONE entry (same scale for all) and per-card overrides cost a second copy. | done | multi-card |
| Q12 | **Decided 2026-10-23 (delegated to Claude):** drop `attack2` from the studio until the package has the clip; row 4 shows "plays Attack". | done | |
| Q13 | **Done 2026-10-23:** S7 rewritten to the real look keys and a camera-move list; S3 alpha and S5 crossfade made read-only facts. Mock still shows the old S7 UI. | done | |
