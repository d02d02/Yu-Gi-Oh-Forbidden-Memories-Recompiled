# tools/pc/rigs

`rigkit.py`: scripted situations on the control channel (`tools/pc/yfm_control.py`), made once at Internal 1x,
saved as a state named with the build id, then looked at at any scale (about 1 s even at 4x).
Subcommands: `hand`, `scene` (test-scenes mod), `duel` (controlled hand + plays), `sets` (contact sheet), `attack` (state before the battle, camera pinned via mods/camera-pin, shots at chosen battle sub-steps). Helpers: `battle_step`, `wait_battle_step`, `camera_read`, `camera_pin`.
Usage and caveats are in the module docstring; strategy docs live in `C:\Users\mdahh\.claude\shared\yfm-notes\dev-tools\`.
