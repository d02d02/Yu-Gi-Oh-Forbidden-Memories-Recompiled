# Prompt for an LLM: design the "anything in, game-ready model out" system

Give everything below the line to an LLM (with web search and code tools if it has them). It is written so the answer is a buildable
system, not an essay.

---

## ROLE

You are a senior technical artist and pipeline engineer (3D generation, rigging, animation retargeting, glTF, Blender scripting, Python
tooling). Design, then specify to the level of runnable scripts, a system that turns a simple input from me into a complete, validated
model package for a game mod, so that I only have to drop the output folder into my mod editor.

## THE GAME SIDE (fixed, do not redesign it)

The target is the PC port of Yu-Gi-Oh! Forbidden Memories. A mod can replace a monster's 3D battle model with a modern skinned
model. The game side is done and tested; your system must produce exactly what it reads.

**Output = a mod folder:**
```
mods/<id>/
  mod.json                      {"id","name","version","author","description","native_models":[{"cards":[<card ids>],"package":"models/<name>/model.json"}]}
  models/<name>/
    model.hdm                   the mesh, skeleton and animation clips in the game's binary format "HDM4" (made by our converter, see below)
    base.png                    base colour (opaque where the model is solid; alpha below half is cut)
    normal.png                  optional, glTF convention (green up)
    metal_roughness.png         optional, glTF convention (roughness in green, metal in blue)
    model.json                  metadata, hand-editable (acts -> clips, strike frames, scale, offset, camera shots, look, author, licence, source)
```
**You do not write HDM4 yourself.** Our converter does it from a rigged glTF/glb:
```
python tools/hd-models/new_native_mod.py MODEL.glb --card <id> --out mods/<id> --author "<A>" --license "<L>" \
    -- [--rig auto|ue|mixamo|generic] [--root <hip bone>] [--clips-from LIBRARY.glb --clips A,B,C] [--height 373] [--origin-height 159] [--no-center]
python tools/hd-models/native_check.py mods/<id>      # the same checks the game makes; must say 0 errors, 0 warnings
```
So **your system's job is to produce a rigged, animated glb that satisfies the converter**, plus the choices that go in `model.json`.

**Hard limits of the format:** at most 128 bones; at most 16 animation clips; at most 4 bone influences per vertex; textures: one
set per model (several materials are packed into one atlas by the converter, at most 2048 px a side); the whole game is a 32-bit
program with a 512 MB budget for all native models (keep a model under about 50 MB in memory; a few tens of thousands of triangles
is plenty, 100k is the practical ceiling). Clips are baked at 30 fps, in place (the game moves the monster, so no root motion).

**The game's model standard (the converter applies it; your model only has to be right in proportion):** a standard monster is 373
game units tall, soles on the ground, origin 159 units above the soles, facing -Z in glTF after export (the converter handles the axis
change). A creature that is big or small by nature (a dragon, an imp) must declare its size (`--height`, e.g. 900 and 200).

**The acts the game plays** (each maps to one clip; an act with no clip plays the idle; clip names are matched by words, or mapped
by hand in `model.json` `clips`): `idle` (an UPRIGHT standing loop, never a lunge: the model stands on its card with it),
`enter` (summon), `attack` (the swing or strike; the converter guesses the blow frames from the fastest hand/weapon speed, check
them), `hit` (the reaction when struck), `destroyed` (death), `win`, `guard`. Minimum useful set: idle, attack, hit, destroyed.

**Rig profiles the converter understands:** `ue` (Unreal/Quaternius humanoid bone names: pelvis, hand_r...), `mixamo` (Hips, RightHand...),
`generic` (any rig, you name the root bone; for a non-humanoid give the body's central bone). Extra bones (wings, tails, capes) are
fine and may be driven by `--follow BONE=SOURCE`.

**How the result is judged** (our tools, already built; your system should call them as its last stage):
```
python -I tools/hd-models/field_attack.py OUT --setting mod.<id>=1 --clip --frames 235      # an mp4 of the monster attacking on the field
python -I tools/hd-models/field_attack.py OUT --setting mod.<id>=1 --arena ...              # the same in the 3D arena
```
Pass means: it stands on its card at the standard size, the attack lands when the defender reacts, nothing flickers or floats,
the textures and lighting look right.

## WHAT I WANT YOU TO DESIGN

**Input, in any of these shapes (the system picks the path):**
1. a text description ("a winged dragon, black scales, red eyes"),
2. one or several pictures (concept art, a character sheet, a screenshot),
3. a short video or turnaround,
4. an existing 3D file (a static mesh, or an already rigged model) in glb, fbx, obj, vrm, or a Mixamo/Sketchfab download,
5. a name of a known character (the user supplies a legally usable source; the system does not fetch or pirate assets).

**Output:** the mod folder above, validated, plus a short report (what was generated, what was guessed, what to check by eye).

**Stages to cover (propose the best current tool for each, free/open-source and locally runnable on Windows 10 with an NVIDIA GPU
first, hosted services as an option, and say which you chose and why):**
- Text/image/video -> textured 3D mesh (single-image and multi-view generators; mesh clean-up: decimation to the triangle budget,
  watertight/manifold fixes, texture baking into one atlas, PBR maps).
- Mesh -> rig: a decision tree. Humanoid (auto-rig and skinning-weight quality checks; or weight transfer onto a CC0 reference
  rig such as the Universal Animation Library mannequin, which our repo already has scripts for), quadruped, winged/serpentine/
  other (what to do when no auto-rigger fits; a generic skeleton template and automatic weights, with the failure cases listed).
- Rig -> the animation clips: humanoid retargeting from a CC0 library (names and quality), and for non-humanoids how to get
  idle/attack/hit/death (procedural clips from a template, motion generation models, or hand keys), with the quality bar for each.
- The glb "export contract": bone names, one skin, bind pose, no scaling on bones, transforms applied, textures embedded, animation
  tracks sampled; a Blender script that enforces it and fails loudly.
- Packaging and validation: the converter and checker commands above; automatic sizing (proportions -> `--height`), the choice of idle clip,
  the blow frames, a screenshot/video of the result.
- Licences: record author and licence in the package; refuse or flag sources whose licence forbids this use.

**Be concrete.** For each stage give: the tool and version, the exact install and run commands, the input and output files, the
failure modes you expect with their detection and the fix, the time and VRAM it needs, and a quality rating. Prefer a few robust
steps over many fragile ones.

## DELIVERABLES (in this order)

1. **Architecture**: a one-page diagram (text) of the stages, the decision points and the files passed between them.
2. **Tool choices** table (stage, tool, why, licence, runs locally Y/N, known limits), with 1-2 fallbacks per stage.
3. **A runnable repo layout and the scripts**: a single entry command (`make_model.py INPUT --card <id> --size <height|auto> --out mods/<id>`),
   one script per stage, Blender scripts included, a config file, and a README. Write the real code, not pseudocode.
4. **Three worked examples** end to end with the exact commands and what you expect to see: (a) one image of a standing humanoid
   character, (b) a text prompt for a winged dragon, (c) an existing static glb mesh of a monster.
5. **Test plan**: how each stage and the whole are tested automatically (golden inputs, checks on the glb contract, the converter
   and `native_check.py` as the gate, a rendered contact sheet), and how a human reviews the final video in two minutes.
6. **Risk list**: what will not work well (hands, wings, multi-limbed creatures, thin parts, hair, transparent materials), what to
   do about each, and where a human must step in.
7. **Roadmap**: the smallest version that works in a day (humanoid from an existing mesh), then the next steps.

## RULES FOR YOUR ANSWER

- Use real, current tools and say when you are unsure a tool exists or what its licence is; do not invent project names, flags
  or APIs. If you must assume, label it ASSUMPTION and say how to verify it.
- Output formats must match this spec exactly; if something here is ambiguous, list your question once at the top and proceed with the
  safest assumption.
- Keep it plain and technical. No marketing, no filler.
