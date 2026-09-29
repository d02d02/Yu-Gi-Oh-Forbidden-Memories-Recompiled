# History

Finished and superseded work, moved out of `progress.md` as it stood. Each section
is kept word for word as it was written; `progress.md` keeps a short summary of each
with a pointer here.

## 2D Monsters mod

### Built and verified compiling (2026-09-29)

**Goal.** An alternative to the 3D Monsters mod (`mods/3d-monsters/field_models.c`):
instead of a loaded battle model standing on a face-up field card, show an enlarged,
camera-facing cutout of the card's own art. `mods/2d-monsters/` (`mod.json`,
`field_art.c`), disabled by default, `"conflicts": ["3d-monsters"]` (both would
otherwise fight over the same software-GPU texture-bank range,
`src/pc/render/soft_gpu.h`'s `SOFT_GPU_BANKS`).

**Approach, reusing 3D Monsters' patterns where the mechanism is the same:** the
host-API helpers (`say()`/`tunable()`), the LRU texture-bank cache (12 entries,
least-recently-drawn replaced first), `duel_field_up()`'s gating (only draws with
the field seen from above), and reusing the ordering table
`D_800E9D90[0]` (the one the battle presentation's model draw normally uses, unused
while the field is up — 3D Monsters' own reasoning for borrowing it).

What had to differ, since there is no model to load or animate: the card's own
102x96 art record is read straight from `WA_MRG.MRG` (the same disc data the
card-detail panel uses, `func_80029164`'s sector arithmetic: `(Cards_BaseId(card) -
1) * 7 + CARD_COUNT`), patched through `Cards_PatchArtRecord` so a card mod's own
artwork still applies, then copied directly into a private bank (no VRAM
round-trip needed, since nothing else ever reads it). Every card's cutout is the
same record shape, so one world-space height serves all of them (`fit_height`,
found once a frame by projecting two points, not by measuring drawn packets the
way 3D Monsters' `fit()` does for a model of unknown size) and perspective alone
scales it by distance. Screen placement and its ordering-table depth both come
from a single `RotTransPers` call per corner-pair, under the frame's own
world-screen matrix (`D_800FE148`) — the same projection `func_80015EF4` uses for
a field card's own ground sprite. `RotTransPers`'s returned depth (`SZ >> 2`,
confirmed in `src/pc/sdk/libgte.c`) is already scaled the way that table's other
content is (a model's "quarter of its distance", per `field_models.c`'s own
comment), so no extra fudge factor was needed.

**Verified:** `python3 tools/pc/build_mod.py mods/2d-monsters` and the full
`python3 tools/pc/build_game32.py` both succeed; `2d-monsters` links as a valid
32-bit ELF relocatable object and is listed among the built mods. No warnings
specific to `field_art.c` under `-Wall` (checked directly with `gcc -m32
-fsyntax-only`, isolating pre-existing header warnings elsewhere in the tree from
anything in this file). **Not verified: how it actually looks.** No PS1 disc image
was available in the session's container, so the game could not be launched, and
no visual/behavioral check was possible — see `progress.md` for what recording a
smoke-test baseline still needs.

### This session's container was missing 32-bit build/runtime libs entirely (2026-09-29)

Not a repo issue — worth a note for whoever hits it in a fresh container. `gcc -m32`
and `clang --target=i386-pc-linux-gnu` could not even link a hello-world: no
`crt1.o`/`crti.o`, no 32-bit `libc`/`libgcc`, and critically no 32-bit dynamic
linker (`/lib/ld-linux.so.2` did not exist) — so `build_game32.py` could produce a
real i386 ELF (mod objects don't need libc, since they're built `-ffreestanding
-nostdinc -r`), but the *game* executable it linked could never actually run,
`ldd` calling it "not a dynamic executable". Fixed for that session with:

```sh
dpkg --add-architecture i386
apt-get update
apt-get install -y gcc-multilib g++-multilib libc6-dev-i386
apt-get install -y libgl1:i386   # pulled in the rest of the 32-bit Mesa/GLX/X11 stack
```

After that, a clean rebuild's `memories-pc` ran up to "Could not open ROM setup:
No available video device" (the container has no display server — expected,
unrelated to the libs) with zero missing shared libraries. This is local container
setup, not tracked by the repository, and won't persist to a new session/container.

### Pushing to GitHub needed the App's write access enabled (2026-09-29)

`git push` and the GitHub MCP server's write calls (e.g. `create_branch`) both
failed with `403 Resource not accessible by integration`, while read calls (`get_me`,
`list_branches`) worked fine — a real permissions gap, not a network flake; retrying
the identical push did not help. Fixed by the user reconnecting GitHub with a
fresh authorization (https://claude.ai/connect-github, forcing re-auth) — after
that, `git push -u origin claude/2d-art-replace-3d-models-bbpme7` succeeded and
created the remote branch. (The other route, when reconnecting alone isn't enough:
an org owner adds/confirms the repo under the Claude GitHub App's installation at
https://github.com/apps/claude/installations/select_target.)
