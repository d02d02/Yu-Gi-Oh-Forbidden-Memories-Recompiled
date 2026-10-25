# Core design rule: every "missing" finding carries resolutions (decided 2026-10-25)

## Rule
When the glb lacks something the game needs, the audit raises a finding of kind `missing` that lists **resolutions**. Each resolution is a button in the check row; the choice is stored in the recipe and the stage re-runs. Nothing is supplied silently.

Resolution kinds (a finding offers the ones that apply):
| kind | meaning | recipe |
|---|---|---|
| `provide.glb` | use another clip/part from this glb | `acts.<act>.source = <name>` |
| `provide.library` | a library file (UAL, user's own) | `library.path`, `acts.<act>.source = lib:<clip>` (maps to `--clips-from`) |
| `provide.file` | a file the modder made in Blender; checked against the skeleton (bone names, rest pose) | `provide.<id> = {path, sha256}` |
| `fallback` | tool-made stand-in, labelled as such in S9 and the report | `acts.<act>.source = procedural:<kind>` |
| `accept` | go without (warn only, never for a fail) | `acks` (today's Accept) |

A `fail` must be resolved by `provide.*` or `fallback`; `accept` is not offered. The report (S9) lists every non-`provide` resolution as "stand-in" so a modder sees what is not authentic.

## Which findings are `missing` (of the 42 fail/warn ids today)
| id | missing | resolutions |
|---|---|---|
| S5.missing-act (idle fail, other acts warn) | a clip for an act | provide.glb, provide.library, provide.file, fallback (procedural idle: pose + bob/sway; acts: root moves), accept (non-idle) |
| S5.model | no animation data at all | same as idle |
| S0.category | a choice | pick (not a file) |
| S0.attribution, S9.provenance | author, licence, url | provide (text) |
| S3.dropped, S3.atlas | a texture usable by the engine | provide.file (baked texture), fallback (flat colour), accept |
| S1.skin, S2.map | a skeleton / bone mapping | provide.file (rigged glb), mapping table (S2 knob); rig is outside the Studio (Blender hand-off) |
| rest | quality findings (stretch, drift, size, budget...) | fix hint or accept, unchanged |

Not yet detected as missing (add): no mesh textures at all, no skin on a mesh that has a skeleton, no clip with the expected length for an act, no attack clip contact frame.

## Where we are (2026-10-25)
Done and landed: S0-S3 audit, S4 placement, S5 statistics/checks, S6 timemap, S7 look, S8 run list, S9 build/report, procedural root moves (sm11), Route A preview, E3 transport and E1 reload in the engine, Studio tab covering all stages through knobs. Corpus job `sm12-corpus` in progress.

Gaps against the rule:
1. `finding()` has `fix` text only: no `resolutions` list, no row buttons beyond Accept.
2. Library clips: recipe key is "new" in `recipe-schema.md`; no knob, no session support, S5 check ignores `--clips-from`.
3. Procedural idle fallback: not built (procedural.py covers root moves over an existing idle).
4. Quadruped path: nothing; UAL is humanoid. Needs a modder-supplied clip pack (`provide.file`) or the procedural fallback.
5. `provide.file` validation (bone names, rest pose vs skeleton): not built.
6. S9 "stand-in" listing: not built.

## Change to the procedure (build order)
| step | what | who |
|---|---|---|
| R1 | `audit.finding(..., resolutions=[...])` + a resolution catalogue per finding id; recipe `resolutions` generalises `acks` (migration: acks stay valid) | harness (spec), UI-free |
| R2 | Library clips: `library.path` knob, session samples library clips, S5 check and build pass `--clips-from`; test on UAL + angel | harness for session/build, me for converter check |
| R3 | Procedural idle fallback (`procedural.py`: idle from pose + bob/sway) and act mapping `procedural:<kind>` | harness |
| R4 | Check rows render resolution buttons; file picker for provide.*; re-run stage | me (Tk, SM3b) |
| R5 | `provide.file` validator (bone names / rest pose against the skeleton) | harness |
| R6 | S9 report lists stand-ins | harness |
| R7 | Corpus: add "missing" cases (no clips, no skeleton, no texture) with expected resolutions | harness (extends sm12) |

## Still to test from the previous design (not yet verified by a user)
* Studio tab walked end to end (user is doing it on the angel: S0-S4 checked, S5 reached; library gap found here).
* S2 chains warning on the dragon (68 bones in 4 trees) and 4 bone-stretch warnings: unjudged.
* Card footprint is a proxy (BLS bbox), not measured; S4 numbers depend on it.
* Winged footprint rule (body = lower half) judged on the dragon only.
* Route A speed and lack of scrub: user has not judged; gates E2/E4-E9.
* E1 hot reload does not load a new path; E7 real frame rate unmeasured; `control.c` is not compiled by the C tests (needs a full game build).
* Procedural root moves (sm11) not seen in the game.
* Determinism (byte-identical twice) shown on dragon only.
* S8 Run on the angel not yet done.
* Open design items: loop closing, root-motion removal as a converter edit, library retarget with rest-pose correction.

## Gate (2026-10-25)
Route B (studio linked to the running game) is tested before the previous plan is called stable; R1-R7 start after that.
