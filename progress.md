# Directions: picking up Unchiga's model-replace work

Branch `feat/model-replace-directions`, off `origin/master` at `759465e`.
Not an implementation branch yet — this is the options survey requested
before picking one, covering `Unchiga/Yu-Gi-Oh-Forbidden-Memories-
Recompiled#feat/model-replace` (analyzed read-only, cloned to
`/home/user/unchiga/yu-gi-oh-forbidden-memories-recompiled` in this
session; not part of this repo's history).

## What that branch built, in one paragraph

`mods/*/mod.json`'s new `"models"` list gives a card its own MODEL.MRG
record, served from virtual sectors past the disc so the game's real
17-phase loader loads it everywhere a model is used (the battle presentation,
the Library's model view, the 3D Monsters mod) with no parallel loading
path. `tools/pc/model_import.py` builds that record from any textured mesh:
decimates and welds it (Blender, `model_prepare.py`), transplants it onto a
disc monster's skeleton/animations/battle-moves/voices (its *template*),
binds vertices to bones by nearest-template-vertex-then-neighbor-vote, packs
textures into three 8-bit pages by surface area, and writes the template's
record back with only the geometry and textures replaced. Full reference:
`notes/model-replacement.md` and `notes/model-tutorial.md` on that branch.

Documented limits, several of which are the "directions" below: 1500
triangles (a real packet-buffer budget, not arbitrary — see below); three
8-bit texture pages only; 256 records max; `hd` (upscaled textures) reaches
the battle and Library but not the 3D Monsters mod's field-standing draws;
`scale` doesn't move the battle camera, so a large model can leave the
frame; no depth buffer, so close concave parts can still show a sliver
through each other, as on the console.

## Directions, roughly most- to least-recommended

### 1. HD textures for the 3D Monsters mod (recommended starting point)

**What:** close the one gap `model-replacement.md` names explicitly — a
custom model's `hd` upscaled textures show correctly in the battle and
Library, but the 3D Monsters mod's field-standing draw still shows the
base-resolution ones, because that mod samples its own private software-GPU
texture banks, which the texture pack's disc-offset tracking never sees.

**Mechanism (already validated elsewhere, not invented from scratch):** a
different Claude Code session already found and proved this pattern on the
simpler 2D Monsters card-art mod: on a cache miss, upload to real VRAM as
usual, but instead of restoring it immediately, hold it one extra frame
(the texture pack's `TexturePack_EntryFor` match only resolves on its next
per-frame service tick — confirmed live, it returns nothing the same frame
a texture lands, a real entry the frame after), call `TexturePack_EntryImage`
to pull the actual replacement, bake it into the mod's private bank at that
resolution, then restore the real VRAM. Exposure is ~1 frame, on a cache
miss only.

**Why this is the recommended target:** it's the specific loose end the
branch's own author flagged as out of scope for him, not a fresh invention;
the mechanism is understood and already proven on a simpler case; and it
directly extends work already reviewed in this session rather than starting
cold.

**The real risk, and how to sequence around it:** the *same* project
already had this exact class of assumption — "this VRAM is safe to hold a
bit longer" — break three unrelated live systems (opponent card art, a
fusion animation, the card-detail title) on that simpler mod, fully
reverted after. 3D Monsters' own transient VRAM borrow is more complex than
the card-art case: `load_monster()` today is one synchronous call with no
frame-spanning state, and the loader writes to that VRAM region across
several phases (texture blocks, palette, two stance strips), not one
`LoadImage`. **Do not start by editing `field_models.c` live.** Start by
building a baseline with the headless build-and-capture regression recipe
that earlier incident produced (documented in `feat/test-scenes`'s
`progress.md`, "How to test things" — `scene_measure.py`'s `capture()`,
reusable beyond the mod it was born from) *before* touching anything, so a
regression is a diffed frame, not a live surprise across three systems
again. Needs: turning the transient upload into a real two-phase state
machine (open on frame N, finish on N+1) per cached monster; deciding which
of the loader's several VRAM-writing phases the texture pack actually needs
to see.

**Effort/risk:** medium effort, real risk, but bounded and testable before
any live check, if sequenced as above.

### 2. Content: import more custom models with the existing pipeline

**What:** just use `tools/pc/model_import.py` as it stands to give more
cards upgraded models. No engine changes at all.

**Why:** zero systems risk — the pipeline is already built, tested, and
documented (tutorial included). Pure content work: picking source meshes,
picking good templates (a template near the new model's shape animates it
best), running the tool, checking the result.

**Effort/risk:** low risk, effort scales with how many cards you want done;
gated on finding good source meshes and matching templates, not on code.

### 3. Tooling polish: binding accuracy and texture detail

Two independent, smaller threads, either one a reasonable next PR on its
own:

- **Bone-binding accuracy.** The neighbor-vote smoothing already took wrong
  bindings from 10-19% to 5-8% (measured, round-tripping the disc's own
  models as a control). Further reduction would need a stronger heuristic
  than nearest-vertex-then-vote — e.g. weighting by geodesic distance along
  the mesh rather than straight-line, or a real bounded-optimization pass.
  Diminishing returns past a point; worth checking whether 5-8% is already
  imperceptible in practice before investing more here.
- **Texture detail at 1x.** "Small details are a few texels wide at 1x" is
  inherent to three 8-bit pages (128x256 texels each) — `hd` already covers
  this at Internal 2x and up in the battle/Library. Not much to do at 1x
  without more texture pages, which is direction 4 below, not a tooling fix.

**Effort/risk:** low-to-medium, self-contained, no shared-engine-state risk
like direction 1.

### 4. Relax limits carefully (triangle cap, texture pages, record count)

**What:** the creator said he'd "rather not be limited" by the ~1500-2000
triangle target. Each limit has a *specific* reason, not an arbitrary
round number, so relaxing any of them means re-deriving the new safe bound,
not just changing a constant:

- **1500 triangles:** tied to a real shared resource — 40 bytes/triangle
  GPU packet against a 140,000-byte buffer the arena, both duelists, and
  effects all share; the disc's own models reach 1764, median 828. Before
  raising this, stress-test the worst case (ten monsters + effects on
  screen at once via the 3D Monsters mod), not just the one model in
  isolation, the same class of check direction 1 needs.
- **Three texture pages:** a loader-format constraint (`MODEL_DATA_BYTES`,
  fixed sector counts) — more pages needs loader work first, which
  `notes/larger-disc-files-plan.md` (this repo) already scopes for other
  record types; worth reading before assuming it's a small change.
- **256 records / disc-end ceiling (LBA 449849):** same virtual-sector
  mechanism `more-cards` already extends; a higher ceiling is plausible but
  shares the same "how far can the virtual disc grow" question as that
  mechanism generally, not specific to models.

**Effort/risk:** medium-to-high depending on which limit; each needs its
own re-validation, don't treat them as a single "raise the numbers" task.

### 5. Fix `scale` leaving the battle frame

**What:** documented limitation — "`scale` does not move the camera: the
battle frames a model as big as the record's own, so a large scale can
leave the picture." A scoped, self-contained bug fix: either clamp `scale`
to what stays in frame, or adjust the battle camera's distance/FOV based on
the model's fitted size the way the 3D Monsters mod already does per-zone
fitting for the field.

**Effort/risk:** low-to-medium, self-contained, no shared-engine-state risk.

### 6. Full native model system rewrite (not recommended as a starting point)

The creator's own "in reality, it would be better to..." aside. Real in the
abstract — unbounded triangle counts, no palette limits, modern skinning —
but this is a rewrite of the packet format, the software rasterizer, and
palette-based texturing throughout the whole engine, not a polish pass, for
a project whose stated goal is faithful retail behavior. High effort, high
risk to everything else that depends on today's pipeline, and the creator
explicitly chose not to take this on yet. Not a good first move; if it ever
happens, it deserves its own deliberate scoping, not scope-creep from
picking up his branch.

## Are we on a safe branch right now?

Yes. `feat/field-card-stats` (this session's other open thread) was clean
and matched `origin` exactly before this branch was created — nothing was
at risk switching away from it. This branch, `feat/model-replace-directions`,
is fresh off `origin/master`'s current tip and carries only this file so
far.

## Left to do

Pick one direction above (or say if none of these are what you meant), and
only then does a real implementation branch get made for it, following the
same pattern as `feat/field-card-stats`: research, strategy in an `.md`
file, review, *then* code.
