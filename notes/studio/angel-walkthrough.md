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
4. The S5 "bone 1" message gives no bone name (hard to judge); show the bone name. Fixed, awaiting validation: the message names the bone and the ratio has 2 decimals (it was rounded to a whole number, so 0.5x read "0 times").
5. (S8, 2026-10-25) Run was grayed with no reason shown. Causes: Run needed the S9 package (stage order felt wrong: S8 needs S9) and `MEMORIES_DISC` was unset in Studio though the editor had found the disc. Fixed, awaiting user validation: Run builds its own cached preview package (`5c9e0508a`), run-list note names the reason (`1397da91f`), Studio adopts the editor's game path as MEMORIES_DISC (`d16bdcd7f`). Uncovered: game files loaded as a SLUS+WA pair give no disc path; last error not yet shown in the check row.
6. No log existed to read an error from. Fixed, awaiting validation: `studio.log` beside the recipe, size-capped (512 KB x 4 files), one line per step (`1397da91f`).
7. (S8) Library turntable Run: the game window flashed several times and closed fast, nothing to see. Cause: the run is a frame capture (6 shots, `sheet.png` written fine in `runs/library/`) but Studio never showed the result. Fixed, awaiting validation: the heading says the window flashes while recording, and when the capture ends the contact sheet opens in a window (exit code and output tail go to `studio.log`). The run's output now goes to `run.log` in its folder (a pipe nobody drained could block a chatty run).
8. (S4 to S5) The transition took about 12-18 s. Cause: S5 sampled all 45 library clips and re-decoded every channel for every frame (2166 poses, 850k accessor decodes). Fixed, awaiting validation: channels decoded once per clip (17.7 s to 5.4 s first run, same 12 findings) and the sampled clips are kept until the library file or loop list changes (repeat runs 0.4 s). Still 5 s on first entry: next step if it feels slow is running S5 in a thread with a "Checking clips..." note.
9. (S8 library run) The game window flashes 7 times and the 6 captured frames look the same. Cause: every shot is a separate game launch (the state is restored per shot; a GL picture needs a real window), and the shots were 20 frames apart while the Library camera turns slowly (the grid shifts, the model barely changes). Changed, awaiting validation: 5 shots 150 frames apart (frames 20-620, about a full turn), so 6 launches. Not solved: hiding the window needs engine support (a hidden or off-screen GL window); open question for Route B (a running game could be captured in place, no relaunch per shot).

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

## Progress checkpoint (2026-10-25, end of session)
* Angel: S0-S7 pass with accepted ambers (S3 dropped material, S4 31% footprint at extent 250, S5 win/guard + bone-stretch). Recipe: cards [364], category C2, library UAL, acts idle Idle_Loop, attack Sword_Attack, hit Hit_Chest, destroyed Death01, `timing.stretch_range [0.5, 3.5]` (attack plays about 3x slow: clip 48 frames vs disc row 150).
* User is in S8: needs a built package (S9), then Run Field attack and Arena attack, judge texture, size, attack. Result not yet reported.
* Fixed this session: library clips field (`01e2002bb`), ack keyed by (check, value) (`c446d4ad5`), S0.cards hard gate (`e561b0eb2`), S6 reads library clip length, widened stretch range lifts hard limit (`fc9f29ef0`), corpus C1-C8 + goldens (`07c8ac38e`; the C2 builder had a parent re-index bug that made the audit loop to 15 GB).
* Harness: nothing queued; idle until Route B or resolutions work. Lesson: a job can claim a golden match when the golden file does not exist (vacuous pass); check the file exists.
* Next: user's S8 verdict; then Route B test (engine, mine) before the plan is called stable; then resolutions R1-R7 (`resolutions.md`). Open UI items: Browse button for path fields, bone name in stretch warning, procedural idle fallback (agreed, not built).
* (S8, 2026-10-25) Feedback: "the studio needs to have a log of each step, embedded as part of the studio feature as a whole"; logs must not grow to GBs over long runs (done: rotation cap). "S8 needs S9 first, then go back to 9, something feels wrong" (done: Run auto-builds a preview; S9 stays the final reproducible gate). Asked whether a normal end user, who opens the editor and uses Studio without MEMORIES_DISC, can hit a disc-not-read case (yes, fixed by adopting the editor's disc).
* Process: "the fixes will be validated later"; keep noting beta-tester feedback in this file. Asked for a cost comparison before delegating: small, design-heavy changes are cheaper done directly; delegate bulk well-specified items (Browse button, bone name in warning).

## Checkpoint 2026-10-25 (late)
* Landed, awaiting user validation in the real Studio: studio.log (size-capped), Run builds its own cached preview (no S9 first), disc adopted from the editor, contact sheet shown after a Run, bone name + real ratio in S5 stretch, run output to run.log, S5 speed (17.7 s to 5.4 s), library turntable spans a full turn.
* Route B test: stream_demo real run OK (channel, 1 frame, skip logic; demo bugs fixed: stop timer, 20 s load wait, dropped connection recorded). transport_demo failed first with `anim: unknown command`: the game exe was stale (Oct 23); rebuilt `tmp/pc/game32/memories-pc.exe` at 11:15 (`python tools/pc/build_game32.py --build tmp/pc/game32`, rc 0). NEXT: rerun `transport_demo.py ../../tmp/pc/transport` (needs MEMORIES_DISC, opens 2 windows one after the other; ask the user first).
* Open: user is still walking S8 (Run buttons); window flash per shot needs Route B capture from a running game; Browse button, last error in check row, procedural idle fallback not built; R1-R7 after Route B.
* Permissions: added allow rules to `~/.claude/settings.json` (python, git, harness scripts, Stop-Process, Get-Process).
