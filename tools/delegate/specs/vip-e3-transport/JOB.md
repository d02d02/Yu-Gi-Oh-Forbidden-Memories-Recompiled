# VIP job e3-transport (phase 1: MAKE IT WORK, no hardening yet)

Goal: Route B of the Studio engine needs live control of the native model preview. Add to the recompiled game a transport the studio can drive over the EXISTING control channel (`src/pc/debug/control.c`, client `tools/pc/yfm_control.py`): set act or clip by name, pause/resume, speed, scrub to a phase (0..1 of the act row) or to a clip frame, and report the current act/clip/phase. Read `notes/studio/engine-needs.md` (E1, E3, E7 and the Route B lines) first.

Read: `src/pc/render/native_anim.c` (the director, `strike_warp`, phase from `anim_frame`; MEMORIES_NATIVE_CLIP free clock), `src/pc/render/gl_picture.c` around 1895-1910, `src/pc/debug/control.c`, `tools/pc/yfm_control.py`, `tools/hd-models/field_attack.py`, `tools/hd-models/library_shot.py`, `notes/adding-a-model.md`, `notes/build.md`.

Constraints (phase 1):
* Everything gated: with the control channel off or no transport command sent, behaviour and frame output are unchanged. Keep edits to existing functions minimal and list each one in your report.
* Scrubbing must feed the same `phase`/`anim_frame` inputs the game uses, so a scrubbed frame equals the same frame in real play (the game squeezes the whole attack clip over the attack row; do not bypass that).
* Add the matching methods to `tools/pc/yfm_control.py` and a small script that demonstrates: pause the dragon attack in the library or field scene, scrub to 5 phases, `shot` each, show frames differ and match a free-run capture at the same phase.
* No hardening, fuzzing or sanitizer work yet; no E7 streaming, E4, E5, E6, E8 in this job.
* Work in your own git worktree on branch `feat/e3-transport`; never push; commit in small steps.
* Build and run on Windows: see `notes/build.md`; set `MEMORIES_DISC=C:\Users\mda\games\iso\ygofm-us.bin` per command. Dragon mod already installed as `tmp/pc/game32/mods/studio-preview` (card 364).

Acceptance: the demo script runs from a clean build, prints the five phases with distinct frame hashes, and a free-run capture at the same phase gives the same hash (or you explain and measure the difference). Report: files changed, existing functions touched, how to run the demo, open problems.

You own every action from here to the report: reading, design within this brief, code, tests, Windows build, running the game and demo with the disc, judging your own captured frames, debugging to green, small commits, updating the notes you affect (`notes/studio/engine-needs.md`, `notes/adding-a-model.md` if relevant), appending a dated entry to `progress.md`, and the final report. Prepare the user's eye check (launcher command, what to look at) but do not ask for it until the demo passes on your side. Do not push.
