# Headless/scripted testing recipes (native PC port)

Reusable techniques for driving `tmp/pc/game32/memories-pc.exe` (or any
build under `tmp/pc/<build>/`) without a human at the controls: reaching a
specific screen, forcing game state, and capturing a reproducible
screenshot to inspect. Everything here is an environment variable the exe
reads at startup; combine as needed. See also `progress.md`'s own "How to
test things" section, which this complements.

## Core recipe

```powershell
$env:MEMORIES_HEADLESS = "1"          # no visible window, fast frame-stepping
$env:MEMORIES_NO_UPDATE_CHECK = "1"
$env:MEMORIES_NO_AUDIO = "1"
$env:MEMORIES_NO_GAMEPAD = "1"
$env:MEMORIES_SPEED = "-1"            # run as fast as possible, not real-time
$env:MEMORIES_SHOW_HUD = "0"
$env:MEMORIES_USER_DIR = (Resolve-Path ".\tmp\pc\some-test-profile").Path
$env:MEMORIES_WATCHDOG = "0"          # don't auto-kill a run that's still figuring out input
& ".\tmp\pc\game32\memories-pc.exe"
```

Always point `MEMORIES_USER_DIR` at a throwaway folder (create it under
`tmp\pc\`, it's gitignored) — never the player's real profile
(`Documents\My Games\YFM Re-Decomp`).

## Reaching a specific screen without real navigation

`MEMORIES_MODE_AT=<frame>:<mode>` force-jumps the active main-mode byte
directly at the given frame, skipping real menu navigation entirely. Modes
are the `MAIN_MODE_*` enum in `src/game/main_modes.h` (3 Duel, 4 Library, 7
Build Deck, 9 Name Entry, 10 Password, 14 Trade, ...). Needs a short
bootstrap input first to get past the title screen:

```
MEMORIES_INPUT="910:0008,916:0000,1000:0040,1006:0000,1020:0040,1026:0000,1040:0040,1046:0000,1060:0040,1066:0000,1100:4000,1106:0000"
MEMORIES_MODE_AT="1000:<mode>"
```

**Caveat, confirmed the hard way twice this session:** this is a blunt
instrument. It skips whatever real setup normally populates a screen's own
state (a Trade session's two inventories, a campaign duel's own deck/chest
workspace) — expect blank/empty lists unless the screen's data is trivially
derived. It's fine for reaching rendering code cheaply, not a substitute for
a real playthrough when a screen's own data matters.

## Owning cards without a real save

`MEMORIES_DEBUG_CHEST=<n>` (every card, n copies) and
`MEMORIES_DEBUG_DECK="<ids/ranges>"` (e.g. `"1-40"` or `"5"` for all of one
card) — debug cheats in `src/pc/debug/cheats.c`. **Both require a save
already "loaded"** (`Cheats_SaveLoaded()`: `player_deck[0] != 0`), which a
raw `MEMORIES_MODE_AT` jump does NOT set up by itself. In practice: jumping
straight to `MAIN_MODE_DUEL` (3) works, because `D_8009B26E` defaults to 0
(the pre-duel chest step), which itself sets up a usable, ownable deck
workspace. Jumping to `MAIN_MODE_TRADE` (14) does NOT — Trade's own
inventories need a real trade session to populate, so expect empty lists
there regardless of these two variables.

## Scripting controller input

`MEMORIES_INPUT="<frame>:<hexbits>,<frame>:<hexbits>,..."` (port 0/pad 1).
`MEMORIES_INPUT2` is the same for pad 2. Each press needs a release a few
frames later. The hex bits are the **raw PSX controller (SIO) layout**, NOT
`src/game/input.h`'s `PAD_BUTTON_*` enum — different encoding, easy to
confuse:

| bits | button | bits | button |
|---|---|---|---|
| `0001` | Select | `0100` | L2 |
| `0002` | L3 | `0200` | R2 |
| `0004` | R3 | `0400` | L1 |
| `0008` | **Start** | `0800` | R1 |
| `0010` | Up | `1000` | Triangle |
| `0020` | Right | `2000` | Circle |
| `0040` | Down | `4000` | **Cross** |
| `0080` | Left | `8000` | Square |

A known-good path from cold boot into a real campaign duel with a monster
placed face-up on the field: replay `tests/pc/smoke/duel-3d-monsters.json`'s
own `input` field verbatim (reaches frame 6760). Combine with
`MEMORIES_DEBUG_DECK` to control which card ends up on the field.

## Capturing a screenshot

```
MEMORIES_DUMP_FRAME=<n>
MEMORIES_DUMP_PATH=<path.ppm>
```

Dumps a raw PPM at exact frame `<n>`. Same inputs always produce the same
frame — fully reproducible. Convert to PNG for viewing:

```python
from PIL import Image
Image.open("out.ppm").save("out.png")
```

**GL-only effects (PGXP, HD text, the HD texture-pack path at internal
resolution above 1x) need a real GL context.** Plain `MEMORIES_HEADLESS=1`
never creates one (`Platform_Open` skips it), so the dump is the software
GPU's picture only, byte-identical regardless of any GL-only setting. Add
`MEMORIES_DETERMINISTIC=1` alongside `MEMORIES_HEADLESS=1` to get a real
(offscreen) GL context while keeping fast deterministic frame-stepping, or
drop `MEMORIES_HEADLESS` entirely for a real visible window.

## Internal resolution / HD rendering

`MEMORIES_INTERNAL_SCALE=<1-8>` (also `MEMORIES_SCALE_AT=<frame>:<scale>` to
script a change mid-run, matching the View menu). Needs
`MEMORIES_DETERMINISTIC=1` (see above) to actually show up in a headless
dump.

## Toggling settings/mods for a run

Any setting: `MEMORIES_<KEY>=<value>` (see `src/pc/platform/settings.c` for
the exact key per setting, e.g. `MEMORIES_CARD_BROWSE=1`,
`MEMORIES_INTERNAL_SCALE=4`). Any mod's own setting:
`MEMORIES_MOD_<ID>_<KEY>=<value>`, id uppercased, non-alnum to `_` (e.g.
`MEMORIES_MOD_3D_MONSTERS_GLOW=0`, `MEMORIES_MOD_3D_MONSTERS_STYLE=1` for
Card art style). Or write a settings file (`mod.<id>=1` /
`mod.<id>.<key>=value` per line) and point `MEMORIES_SETTINGS` at it.

## Testing a pure C function in isolation, without the whole game

For a self-contained function (no live guest-memory state, e.g. `art.c`'s
`CardArt_FieldArtFromImage`), skip the whole engine and compile a tiny
standalone probe directly against the real source file — far faster than a
full game rebuild per iteration, and tests the actual compiled code, not a
reimplementation of it in another language:

```bash
CC="tmp/pc/tools/llvm-mingw/llvm-mingw-20260922-ucrt-x86_64/bin/i686-w64-mingw32-clang.exe"
WIN32_DEPS="tmp/pc/win32-deps"
"$CC" -std=c11 -Isrc -Isrc/pc/cards -I"$WIN32_DEPS/include" -I"$WIN32_DEPS/include/freetype2" \
  my_probe.c src/pc/cards/art.c src/pc/compat/fs.c \
  "$WIN32_DEPS/lib/libfreetype.a" "$WIN32_DEPS/lib/libpng16.a" "$WIN32_DEPS/lib/libzs.a" -lshell32 \
  -o tmp/pc/my_probe.exe
```

Stub any of the file's own external calls the probe never exercises (check
with the linker's undefined-symbol errors) rather than linking in more of
the engine than needed. The toolchain/libs under `tmp/pc/tools` and
`tmp/pc/win32-deps` are already fetched once by the normal
`python tools/pc/build_game32.py` build — reuse them, never refetch.

## Reusing a worktree's fetched toolchain in a new worktree

A fresh `git worktree add` has no `tmp/` at all — the first build would
otherwise refetch the whole toolchain (Python, llvm-mingw, cmake, ninja; a
few hundred MB). Share it instead:

```powershell
New-Item -ItemType Directory -Force -Path ".\tmp\pc"
New-Item -ItemType Junction -Path ".\tmp\pc\tools" -Target "<other-worktree>\tmp\pc\tools"
New-Item -ItemType Junction -Path ".\tmp\pc\win32-deps" -Target "<other-worktree>\tmp\pc\win32-deps"
```

Only junction `tools` and `win32-deps` (pure host toolchain/compiled
libraries, not tied to any branch's source) — never `game32`/`mod-build`
(build output, must stay per-worktree since it's compiled from that
worktree's own source).
