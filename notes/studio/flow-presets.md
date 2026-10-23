# Flow and presets by category

Source: `../native-models-feasibility.md` sec. 2-3. Draft. Open question: is this a screen at all, or only the data behind the presets and the category chip?

## Effort matrix (what the person does)
auto = accept the default; guided = look and adjust; manual = work outside the studio; n/a = skipped.

| | S0 | S1 | S2 | S3 | S4 | S5 | S6 | S7 | S8 | S9 |
|---|---|---|---|---|---|---|---|---|---|---|
| C1 humanoid, standard | auto | auto | auto | auto | auto | auto | auto | auto | auto | auto |
| C2 humanoid, custom/extras | auto | auto | manual | auto | auto | guided | auto | guided | auto | auto |
| C3 humanoid, no rig | auto | manual | manual | auto | auto | guided | guided | guided | auto | auto |
| C4 quadruped/beast | auto | auto | guided | auto | guided | guided | guided | guided | auto | auto |
| C5 winged creature | auto | guided | guided | auto | guided | guided | guided | guided | auto | auto |
| C6 legless/floating | auto | auto | guided | auto | guided | guided | guided | guided | auto | auto |
| C7 rigid multi-part | auto | guided | auto | auto | auto | guided | guided | guided | auto | auto |
| C8 static mesh | auto | n/a | n/a | auto | guided | guided | guided | guided | auto | auto |

## What a category preset sets
Per category, the preset fills: S2 root and foot joints; S4 fit mode, fit pose, root/origin heights, ground offset; S5 act sources and procedural types for missing acts; S6 strike joint guess; S7 starting light. The table of preset values per category is **not written yet**; it is derived while detailing each stage in `studio-view.md` (one column per category in each knob table).

## Honest-expectation text
Each category shows, on S0, a short expectation line (feasibility sec. 1: good / decent / looks like a moving statue) and the human-effort estimate once measured on the corpus (no number is promised before then).

## Questions
1. Is the matrix a screen, or does it become the category picker's tooltip plus the preset data?
2. Should the rail dim stages marked n/a for the category, and hide them?
3. Does a person ever change category mid-run? (The studio-view state model makes everything stale; is that acceptable?)

## Recommendation after detailing the Studio (2026-10-23, awaiting the user)
The matrix is **data and a tooltip, not a screen**: it lives as the preset table the category select applies (one column per category beside each knob table in `studio-view.md`) and as a small "What to expect" popover on the category chip in S0 and in the header, showing effort per stage for that category. Stages marked n/a for the category stay in the rail, dimmed, and open to a one-line "Skipped for this category" panel (they can still be opened). Changing category mid-run is allowed; everything but S0 goes stale and the person is told so in a confirm dialog naming the model.
