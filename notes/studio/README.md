# Model Studio: design docs

The studio is the FM Editor add-on that turns a rigged `.glb` into a native-model package through ten stages (S0-S9), a recipe file and the real game engine as the viewport. Direction and reasons: `../native-models-feasibility.md` (verdict, stages, categories, engine gaps). These docs hold the **UX and GUI design**, which comes before any code (decision J).

Status 2026-10-23: structure drafted, **nothing built**. The three-view structure is unproven until each view is detailed; `studio-view.md` is being detailed first.

## Map
| File | Holds | State |
|---|---|---|
| `decisions.md` | decisions taken, UX rules adopted, what is out of scope | v1 |
| `studio-view.md` | the Studio screen: anatomy, state model, interaction rules, per-stage detail | S0-S9 and cross-stage behaviour detailed (first full pass) |
| `models-view.md` | the Models list (entry point, first run, multi-card, provenance) | outline + questions |
| `flow-presets.md` | per-category flow and presets (C1-C8 x S0-S9) | matrix + questions |
| `tk-mapping.md` | how the web wireframes translate to Tk widgets and the editor's limits | v1 |
| `engine-needs.md` | everything the screens ask of the engine and converter, deduplicated | grows with studio-view |
| `open-questions.md` | undecided points, who decides, what blocks | live |
| `wireframes-v1.html` | the clickable mock (open in a browser); also published as an artifact | v1, not yet updated for the detail docs |

## Conventions
* *(new)* = does not exist in the engine or converter today. Every *(new)* in a screen must appear in `engine-needs.md`.
* Check ids look like `S4.footprint`; knob ids like `size.fit_mode` and map one-to-one to `recipe.json` keys (schema is derived later, from these names).
* Game units: the standard monster is 373 tall, root 159 above the soles. Frames are game frames (30 per second) unless a doc says clip frames.
* States: `todo`, `pass`, `warn`, `fail`, `stale` (see `studio-view.md`).

## UX method
The VectorLab skills (`vectorlab-ux-skills:*`) guide the web wireframes: name the page pattern first (Models = List, Studio = Split Pane), surface rules (inline for one field, slide-over for short tasks, a page for long ones, named destructive confirmation), verb-first buttons, errors that offer recovery, empty states inside the frame, full keyboard access. The editor is Tk, so those rules are kept and the visuals are translated (`tk-mapping.md`).
