# Angel through the Studio: warnings and user feedback (2026-10-25)

Model: `tmp/agent/angel/work/angel_rigged.glb` (no clips; mesh and skeleton from a generator, material `tripo_mat_*`). Recipe beside it. Library: UAL (`tmp/agent/angel/incoming/ual/Universal Animation Library[Standard]/Unreal-Godot/UAL1_Standard.glb`, 45 clips, CC0).

## Warnings seen, per stage
| stage | result | action taken |
|---|---|---|
| S0 | fail `S0.category` (none chosen; detection suggests C2); info licence empty | set category C2, author/licence/url filled |
| S1 | pass (`S1.ok`; bone merge not measured, info only) | none. The old note that the angel fails bind-vs-rest does NOT hold for `angel_rigged.glb` |
| S2 | no warning | none |
| S3 | warn `S3.dropped`: material `tripo_mat_e5b85d13` uses UV set other than 0, not applied | Accepted; judge texture in S8; fix = bake in Blender |
| S4 | warn `S4.footprint`: 31% wider than the card footprint at extent 250 (height 320: 52%; extent 600: 214%) | extent 250, Accepted |
| S5 (before library) | fail `S5.missing-act` idle; warn enter, attack, hit, destroyed, win, guard: no clips in the glb | blocked until library clips existed |
| S5 (with library) | warn win, guard: no clip; warn `S5.bone-stretch` on bone 1 in 10 library clips (Death01, Fixing_Kneeling, Jump_Land, Jump_Start, Roll, Roll_RM, Sitting_Enter, Sitting_Exit, Sword_Attack, Sword_Attack_RM) | Accept win/guard and stretch; judge the attack in S8 |

## Problems found while walking
1. No way to give a model library clips (gap): built `library.path` (commit `01e2002bb`).
2. The user mistyped the library path (missing space in `Animation Library`); the Studio showed an error but there is no editor log, errors go to the terminal. Needs: a file picker (Browse) for path fields, and the error text visible in the check row.
3. The first S4 advice contradicted itself (height vs extent); extent 250 was the smallest warning.
4. The S5 "bone 1" message gives no bone name (hard to judge); show the bone name.

## User feedback and decisions (verbatim intent)
* Wants the angel glb imported and applied to the game; wants short step-by-step instructions, minimal words, no assumed knowledge.
* Asked where the dragon's animations came from (answer: its own glb; sm11 added procedural root moves on top).
* Idea: extract the disc's animations for all monsters (harness), sort by category, offer them as an importable library. Not decided; disc data cannot be redistributed, must run per user on their own disc; skeletons differ per monster. Later addition behind the same library field.
* Question: a free-licence Mario-like glb with no clips, a pony glb with no animation: what do users do? Answer: humanoid with a standard rig uses UAL; no rig needs rigging first; pony has no fitting library.
* Decision: add a procedural idle fallback (not built).
* Decision: core design rule = every missing finding offers resolutions (provide / library / Blender file / labelled fallback / accept); written in `resolutions.md`. Wants a solid, stable way for a modder to add clips, flagged each time something is missing.
* Decision: keep the previous plan first; test Route B (studio linked to the running game) before calling it stable; the resolutions work (R1-R7) starts after that.
* Process: keep the harness fed with previous-plan work, do everything that does not need the user, discuss design atomically (one question at a time).
* Visual checks done earlier: confirmed, nothing to report.
* Reply style: military, minimal.
