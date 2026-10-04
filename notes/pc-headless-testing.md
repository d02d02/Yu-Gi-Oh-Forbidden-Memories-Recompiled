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
own `input` field verbatim. Dumping frame 6760 of that replay consistently
shows a monster already placed and face-up (glow effect active, if the 3D
Monsters mod's Card art style is on) — confirmed repeatedly this session,
though whether 6760 lands exactly at a final "placed" state or a
still-interactive "reticle/preview" state that already renders the model
(`progress.md` calls it "a card-placement reticle screen") was not
rigorously pinned down; treat it as "a monster is visibly on the field and
face-up here", not as a precise phase boundary.

**This is one fixed recorded trace, not a general "get into any duel"
tool.** It's someone's real play session, captured as raw button presses;
reusing it verbatim reliably reaches the same screens in the same order
every time (that's the whole point — determinism), but it does not let you
choose a different path through the menus, a different opponent, or a
different moment to act at. See "Reaching other points in a duel" and
"Choosing a specific card" below for what varying it safely does and
doesn't give you.

## Choosing a specific card

`MEMORIES_DEBUG_DECK` (see above) takes the exact same syntax `set_deck()`
in `src/pc/debug/cheats.c` parses: comma-separated ids and/or `first-last`
ranges, repeated to fill the 40-card deck if shorter than that.

```
MEMORIES_DEBUG_DECK="5"          # all 40 slots: card 5 (Ryukishin)
MEMORIES_DEBUG_DECK="1-40"       # one copy each of cards 1 through 40
MEMORIES_DEBUG_DECK="5,22,82"    # cycles 5, 22, 82, 5, 22, 82, ... to fill 40
```

This controls which card(s) are *available to place* (the whole deck is
one card, so a scripted "place whatever's highlighted" input reliably picks
that card) — it does not by itself choose which hand slot gets selected if
the deck has more than one distinct card; see below for that.

## Reaching other points in a duel

Two tools, two very different reliability levels:

- **`MEMORIES_MODE_AT=<frame>:3`** (jump straight to `MAIN_MODE_DUEL`) only
  reaches `Main_RunDuel`'s own step 0, the pre-duel chest screen (see
  `card_browse.c`'s own doc comment on `move_duel_chest_cursor`) — **not** a
  live duel with a real hand, field, or opponent. Scene setup
  (`Duel_InitScene`, the opponent's AI data, the hand) never runs; there is
  nothing to place. Confirmed this session: this path is only good for the
  chest/deck-prep screen, not the duel itself.
- **A real recorded replay** (like `duel-3d-monsters.json`) is therefore
  the only reliable way to reach a live duel headlessly right now. To see
  an *earlier* point in the same duel than its own target frame, just dump
  an earlier frame of the same replay — the whole prefix of button presses
  up to that point still ran, so the state at frame 6200 (say) is whatever
  that recorded session was actually doing at frame 6200. This was not
  exhaustively mapped out this session: the input's own shape (a long run
  of repeated Cross presses from ~1800 to ~5780, then a short, more varied
  burst from 6000-6700) suggests the long stretch is mashing through
  campaign intro dialogue and the short burst at the end is the actual
  duel-engagement/placement input, but dump a handful of frames in that
  range yourself to confirm before relying on a specific one.

## Choosing which hand card to place, and placing traps/rituals face-down

**Not verified this session — here's where to start, not a working
recipe.** The duel's hand-navigation/card-play phase is scene-state 4,
`DuelScene_UpdateHandActions` in `src/game/duel_scene_hand_actions.c` (see
that file's own header comment for the state's layout). A recorded
replay's own button presses during that phase are specific to whatever hand
the original session had — they do not generalize to "press X to pick the
3rd card" for an arbitrary hand, since which physical button press lands on
which card depends on cursor position, which depends on hand order, which
depends on what's in the deck.

The practical way to get a specific, repeatable "my hand, I choose this
card, placed this way (attack/defense/face-down)" scenario is almost
certainly: pair `MEMORIES_DEBUG_DECK` (so the hand's contents are known and
controlled) with **building your own save state once, live**, then
replaying cheaply from it — this is the project's own established pattern
for exactly this kind of iteration (see `progress.md`'s PGXP section, "A
save state made by..."):

```powershell
# Once, interactively (drop MEMORIES_HEADLESS so you have a real window,
# no MEMORIES_DUMP_FRAME): play by hand up to the exact moment you want
# (hand visible, your chosen card highlighted, trap/ritual menu open,
# whatever), then press F5. Or script it once with MEMORIES_SAVE_STATE
# ="<frame>:<path>" if you already know the frame.

# From then on, reload that exact moment in ~60 frames instead of
# replaying thousands of scripted button presses:
$env:MEMORIES_LOAD_STATE = "<path or slot>"
```

A state only loads in the exact build it was saved from (compiled
checksums differ build to build, and definitely release vs. debug) — save
a fresh one per build you're iterating on, not once and reused forever.

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

## Known pitfalls (things that went wrong this session, and why)

**`MEMORIES_HEADLESS=1` + `MEMORIES_DETERMINISTIC=1` + `MEMORIES_INTERNAL_SCALE=4`
can hang indefinitely.** Tried combining all three (to capture the HD
texture-pack path headlessly) twice; both times the process never produced
its dump and had to be killed after several minutes, versus the same test
at `MEMORIES_INTERNAL_SCALE=1` (or without `MEMORIES_DETERMINISTIC`)
reliably finishing in seconds. Not root-caused this session. Dropping
`MEMORIES_HEADLESS` for a real window at scale 4 *did* run to completion,
but:

**A real (non-headless) window can dump an all-black frame.** Same
scripted run, same frame number, `MEMORIES_HEADLESS` dropped and
`MEMORIES_INTERNAL_SCALE=4` kept — completed without hanging, but
`MEMORIES_DUMP_PATH` came out solid black. Not root-caused either; maybe
the window needing focus, maybe a timing difference versus the
`MEMORIES_DETERMINISTIC` path. **Net effect: this session found no reliable
scripted way to capture the HD/internal-scale-above-1x rendering path.** If
you need to confirm something only visible there, check it in a real
interactive session (no `MEMORIES_HEADLESS`, no dump variables, just play)
rather than trust a headless/scripted capture of it.

**A stale `memories-pc.exe` process blocks the next build.** Rebuilding
while any previous run (especially a backgrounded one you forgot about) is
still holding the exe open fails the link step with a plain
`Permission denied` — easy to misread as a real compile error. Always
`Get-Process -Name memories-pc | Stop-Process -Force` before rebuilding if
you've launched anything since the last build.

**PowerShell can flag a successful run as an error.** The game prints some
startup lines to stderr even on a totally normal run (e.g. its own RAM-
mirror notice). PowerShell's native-command handling surfaces that as a
`NativeCommandError`/non-zero-looking exit even though the process is fine
and still produces its dump — check whether the expected output file
actually exists before concluding a run failed.

**A worktree can be checked out on the wrong branch, and everything still
"works" except the one thing you're testing.** Spent real time debugging a
feature as "not working" live before realizing the worktree being tested
in was still on an older branch that never had the fix — the build
succeeded, the game ran fine, nothing errored, it just silently wasn't
running the code being changed. Before trusting a "still broken" report
from live testing, confirm `git log --oneline -1` in the exact worktree
being launched from matches the commit you think you just built.

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
