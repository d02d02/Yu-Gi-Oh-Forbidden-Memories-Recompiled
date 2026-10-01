# A native 3D draw call, alongside the existing pipeline

Branch `feat/native-3d-draw-call`, off `origin/master` at `759465e`. Research
only, no code — per the standing process, this is the goal and the
constraints it runs into, researched against the current tree, before any
implementation branch.

## The goal, registered

From a model record to pixels, as the existing chain does it today:

1. **Load** — the record (model data, textures, palettes, animation, voices)
   is read into RAM through the game's 17-phase file-transfer sequence
   (`Model_LoadMonsterMerge`), real sector or modded virtual one alike.
2. **Parse** — `func_8004CB0C` builds the in-memory tree: rigid "parts"
   (`GsCOORDUNIT`, each with a local transform and a parent pointer), each
   owning a run of polygons, each carrying its own keyframe sequence
   (`GsSEQ`).
3. **Animate** (per frame) — each part's sequence steps one frame, updating
   its local rotation.
4. **Pose the hierarchy** (per frame) — walking root to leaf, each part's
   world transform is its local transform composed with its parent's.
5. **Transform through the GTE** — fixed-point vertex transform + lighting
   against that world transform and the camera, producing 2D screen
   coordinates and vertex colour. This is where the console's real limits
   live (fixed point, small vertex/texture-page budgets).
6. **Package and depth-sort** — screen-space primitives go into an ordering
   table by computed depth. No depth buffer anywhere in this chain:
   visibility is "draw the table back to front."
7. **Rasterize** — software GPU or `gl_picture.c`'s GL replay fills pixels,
   sampling an 8-bit indexed palette, Gouraud-shaded from step 5.
8. **Present.**

**Goal:** a separate draw call, its own camera, a real depth buffer —
inserted alongside this chain rather than replacing any of it, the way a
second renderer could in principle sit next to the first.

## What research against the current tree found

**Correction to the starting premise, worth stating plainly:** `gl_picture.c`
is not actually a precedent for "its own camera and a real depth buffer." It
has neither. Its own header comment is explicit: it replays the *same*
software-GPU primitive stream, decoding VRAM "exactly as the software GPU
samples it," with the software picture pass as its named oracle — no
dithering, no new blending modes, same no-depth-buffer ordering-table
semantics, because it must stay bit-identical to the software renderer at
1x (that identity is load-bearing for this project's matching/testing
culture, not incidental). `present_pass.c` is a further step past that: a
single full-screen quad blit with post-processing (sharp bilinear, xBR,
CRT), explicitly "the compatibility profile the presenter already draws
with (immediate mode, glOrtho)." **Both existing GL stages are
2D compositing over an already-finished flat picture. There is no 3D camera,
no perspective projection, and no depth buffer anywhere in the current GL
code.** A native 3D draw call would be the first of its kind here, not an
extension of something already proven at that job.

**What *is* reusable:** `gl_picture.c` already has the machinery a modern
pass needs — shader compile/link, VBOs, `VertexAttribPointer`, FBOs
(`GenFramebuffers`/`FramebufferTexture2D`). That's the right pattern to copy
for a new pass's own render target, not a reason to route through
`gl_picture.c` itself.

**The GL floor is already OpenGL 3.0, checked at runtime, not at context
creation.** `gl_picture.c` parses `glGetString(GL_VERSION)` after the
context exists and declines (falls back to the deterministic software
picture) below 3.0; nothing calls `SDL_GL_SetAttribute` for a version or
profile before context creation, so the context SDL grants is whatever the
driver's default compatibility context is. A native 3D pass can live on
this same accepted floor rather than demanding something new — but:

**No depth buffer is requested anywhere today.** Confirmed by its absence:
no `SDL_GL_SetAttribute(SDL_GL_DEPTH_SIZE, ...)` call in `sdl.c`. A real
depth-tested pass needs one explicitly — either on the window's default
framebuffer (affects the whole context) or, better and more self-contained,
its own FBO with a depth renderbuffer attached, using the FBO pattern
`gl_picture.c` already has.

**Mods have zero GL access today.** `src/pc/mods/modapi.h` exposes none of
this — no GL symbol, no rendering hook past what `GsSortPoly`-style packet
submission already allows. This cannot be built as a self-contained mod
against today's host API. It needs either new host functions added
specifically for a constrained 3D-draw capability (the same incremental
pattern that added `disc_read`/`disc_file_start`/`map_fixed` to the mod API
as mods needed them), or to live in `src/pc/render` as a core engine
feature configured the way settings/`mod.json` already are, not as mod C
code.

**Headless/CI testability has a precedent and a known workaround, not a
dead end.** `gl_context` is only created when a real `window` exists
(`sdl.c`), and `window` is `NULL` under `MEMORIES_HEADLESS=1` — so, exactly
like the existing GL-only precise-geometry (PGXP) feature, this would be
*invisible to `MEMORIES_HEADLESS` entirely*, including this project's own
smoke tests and CI. The project already solved this for PGXP, not by
giving up on testing it: `feat/test-scenes`' own notes record that dropping
`MEMORIES_HEADLESS` and adding `MEMORIES_DETERMINISTIC=1` gives "the same
fast frame-stepping as headless, but a real window/GL context still gets
created" — a real window, but still deterministic and scriptable. The same
path applies here.

**Cross-platform risk is low, because the GL context it would reuse is
already proven on both.** Windows (via llvm-mingw's cross-compile + Wine
for local testing) and Linux (native Mesa) both already run the existing GL
picture path; a new pass sharing that same context inherits that, rather
than opening new platform risk.

## The real open problem: compositing against no-depth-buffer content

This is the one the other findings point at, not a secondary detail. The
existing chain has *no per-pixel depth* for anything it draws — field tiles,
cards, hand, UI, all of it is ordering-table sequence, not a z-test. A
genuinely depth-buffered 3D pass has no principled way to interleave
per-pixel with content that was never given a depth to compare against:
there's nothing on the other side of that comparison.

**What this means in practice:** this has to be a composited *layer*, not a
pixel-level unification of two depth models. Concretely, the same shape the
3D Monsters mod and the 2D Monsters mod already use today — insert at one
chosen position in the existing coarse ordering-table depth sequence (e.g.
"after the field tiles, before the hand and interface," exactly how those
mods already place themselves in `D_800E9D90[...]`) — and let the *entire*
new 3D pass's output composite as one unit at that position, with real
depth-testing only *within* that pass's own content (so multiple native 3D
objects correctly occlude each other), not against the rest of the game.
That is a materially smaller, already-precedented problem: "pick the right
layer," which mods already do successfully, rather than "give the whole
engine a depth buffer," which would mean touching everything.

## Left to do

Nothing implemented. Open questions for whoever picks this up next:

1. Confirm the above compositing shape is acceptable (a layer, not
   per-pixel unification) before any code — it's the central design
   decision everything else follows from.
2. If so: scope the new host-facing surface (new mod API functions, or a
   core feature) — this determines whether a mod can ever drive it or
   whether it's engine-only.
3. Pick the FBO approach (dedicated render target + depth renderbuffer,
   composited in before `present_pass.c`'s final blit) and confirm where
   exactly in the frame sequence it inserts relative to `gl_picture.c`'s
   replay.
4. Validate headless testability early via the `MEMORIES_DETERMINISTIC`
   path PGXP already established, rather than discovering it late.
