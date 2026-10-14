# tools/pc/rigs
LLMs/scripts: read `notes/dev-tools/AGENTS.md` first (one page: when to use, rules, command table).

`rigkit.py`: scripted situations on the control channel (`tools/pc/yfm_control.py`), made once at Internal 1x,
saved as a state named with the build id, then looked at at any scale (about 1 s even at 4x).
Subcommands: `hand`, `scene` (test-scenes mod), `duel` (controlled hand + plays), `sets` (contact sheet), `attack` (state before the battle, camera pinned via mods/camera-pin, shots at chosen battle sub-steps). Helpers: `battle_step`, `wait_battle_step`, `camera_read`, `camera_pin`.
Usage and caveats are in the module docstring; strategy docs live in `C:\Users\mdahh\.claude\shared\yfm-notes\dev-tools\`.

`pxkit.py`: exact pixel checks (`diff`, `count`, `golden`); runs are bit-identical so a count is a verdict.
`rigkit.py situation <spec.json> [--record|--check]`: a declarative situation (hand, plays into chosen columns,
attack, camera pin, shots at battle steps, pixel checks). `--record` stores goldens next to the spec (git-ignored),
`--check` exits 1 when a shot differs. Spec keys are in `run_situation`'s docstring; example `situations/odd-slot-attack.json`.

`rigkit.py ab <spec> --exe-a A --exe-b B [--settings-b k=v ...] [--max-pct N]`: the same situation on two builds (or one build with a
setting changed on side B), shots matched by battle step, per-shot pixel diff, wall time, `ab.json` + `ab-sheet.png`, exit 1 on a difference.

`rigkit.py matrix <matrix.json> --golden-dir G [--record|--check]`: mod QA matrix, one situation x combinations of mods/settings x scales
(per-combo `scales`, `boot_timeout`, `data_mods` linked by junction into the private exe copy). Example `situations/matrix-mods.json`.
A build with the Duel Links art data mod takes ~120 s to accept a client (600 PNGs at startup): give its combos `boot_timeout`.
