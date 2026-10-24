# Adding a new model (a dragon, a Dragon Ball character, anything)

Draft of the procedure (phase I of `progress.md`). It sits on top of the plug-and-play pipeline, which `notes/native-models.md`
explains (the package, the acts, the limits, troubleshooting). Steps marked **untested** have not been run on a real model of that
kind yet; the worked examples (a dragon, Goku) will replace them with tested commands and pictures.

Only models with a licence that allows this use are in scope (fan-made models shared under CC0 or CC-BY and the like). Put the
author and the licence in the package: `--author` and `--license` (they go into `model.json`; the game does not read them).

## 1. What do you have?

| You have | Go to |
|---|---|
| A **rigged** glb or glTF with animations (the clips are in the file) | 3, then 4 |
| A rigged humanoid with **no** animations | 2b (take clips from a library), then 4 |
| A **humanoid mesh with no rig** | 2a, then 4 |
| A rigged **non-humanoid** (dragon, beast, winged) with its own animations | 3 with `--rig generic`, then 4 |
| A non-humanoid mesh with no rig or no animations | 2c: this takes real animation work, plan for it |

Check the file first: `tools/hd-models/native_check.py MODEL.glb` is for packages; for a glb just open it in Blender (`blender -b FILE.glb --python-expr "import bpy; print(len(bpy.data.armatures), [a.name for a in bpy.data.actions])"`). Limits: 128 bones, 16 clips, 4 influences a vertex, one
texture set (several materials are packed into one), 512 MB of models in all.

## 2. Making it playable

**2a. A humanoid with no rig (untested beyond the angel).** Dress the CC0 Universal Animation Library's mannequin rig with the mesh
by weight transfer: the repo's `tools/hd-models/blender/angel_on_mannequin_weights.py` does it for the angel (its inputs: the mesh as an
object named `Angel`, the UAL as `UAL1_Standard.glb` with Unreal bone names). Expect to hand-fix capes, wings, swords and hair (the angel's
sword arm is still wrong). `export_rigged_glb.py` writes the skinned glb. Mixamo or Blender's Rigify are other ways to get a rig; the result
only has to be a glb with an armature (humanoid names: Mixamo's `mixamo` profile or Unreal's `ue`).

**2b. A rigged humanoid with no animations.** Borrow them: `--clips-from UAL1_Standard.glb --clips Sword_Attack,Sword_Idle,Hit_Chest,Death01,Idle_Loop`
works when the bone names match (`ue`, `mixamo` profiles). Choose an **upright** idle (`Idle_Loop`): a lunge such as `Sword_Idle` puts the feet
far from the hips and the monster looks off its card (seen on the mannequin; the origin was right).

**2c. A non-humanoid.** The clips must come with the model or be made in Blender (an action each for idle, attack, hit, death, and
optionally enter, win, guard). There is no retargeting from a humanoid set to a dragon. Name them so the converter finds the acts
(Idle, Attack, Hit, Death, Victory, Block, Intro) or map them by hand in `model.json` `clips`. **Untested.**

## 3. Convert it

```
python tools/hd-models/new_native_mod.py MODEL.glb --card 364 --out mods/my-model \
    --author "Name" --license "CC-BY 4.0" -- --rig generic --root <the hip or body bone> [--clips-from LIB.glb --clips A,B,C]
```

`--rig auto` finds Unreal and Mixamo names; `generic` needs `--root` (the bone the body hangs from: hips for a humanoid, the pelvis or
the base of the spine for a dragon). It writes `mods/my-model/` (the package, `mod.json`) and checks it as the game does.
`--card` is the card whose monster it replaces (more than one is allowed).

## 4. Look at it and tune it by data

Run the field attack and the arena attack and look (needs the disc: `MEMORIES_DISC=<the .bin>`):

```
python -I tools/hd-models/field_attack.py OUT --setting mod.my-model=1 --scale 2            # a sheet of the field attack
python -I tools/hd-models/field_attack.py OUT --setting mod.my-model=1 --clip --frames 235   # an mp4
python -I tools/hd-models/field_attack.py OUT --setting mod.my-model=1 --arena --setting mod.3d-monsters.attack=0 --start 1250 --every 40 --frames 1650
```

Then change `model.json` (no reconvert) in this order, and only as far as needed:

1. **Idle and act clips**: an upright idle; the right clip per act.
2. **`scale`** (percent, about the soles) when it is too big or small. A winged dragon is wider than the card: 60 to 70 is normal.
3. **`strike.attack`**: the frame of each blow, so the swing lands when the defender reacts (check with the effects off:
   `MEMORIES_MOD_3D_MONSTERS_EFFECTS=0`).
4. **Origin height** (reconvert with `--origin-height`; default 159, the game's monster class) when it floats or sinks, and `--height`
   (default 373) for a model that should be bigger or smaller than a standard monster: **say the size of a non-humanoid** (a dragon
   900, an imp 200); the default is only right for a humanoid of standard-monster size. The converter already makes the model stand on
   its card with its soles on the ground at the size of the game's own monsters, so this is for exceptions.
5. **`shots`** for camera moves, **`offset`** only as a last resort (it patches a model whose origin is wrong).

`MEMORIES_TRACE=model` gives the event log; `MEMORIES_NATIVE_SKIN_LOG=1` says where the model's axes point on screen.

## 4b. Live controls on a running preview (E3)

With the recompiled game (Route B) the preview can be driven while it runs, over the same control channel as
`shot`/`hash`. In Python (`tools/pc/yfm_control.py`, class `Game`):

```
game.anim_pause()                 # freeze the current frame
game.anim_phase(0.25)             # scrub: 0..1 of the act's row (same anim_frame path as play)
game.anim_frame(40)               # or an absolute clip frame; phase(..)/frame(-1) clears
game.anim_speed(0.5)              # free-running clips only (0.05..8)
game.anim_clip("Fly_New")         # force a clip by name; anim_clip(None) = auto
game.anim_resume()
game.anim_get()                   # {"clip": .., "paused": .., "phase": .., "frame": .., "speed": ..}
```

The raw commands are `anim clip NAME|auto`, `anim pause`, `anim resume`, `anim speed X`, `anim phase P`,
`anim frame N` and `anim get`; bad input answers `err ...`. With no client connected the game is untouched, and
until the first `anim` command the transport is inactive, so playback is exactly as before. For an attack, pause,
scrub to the phases you want and `shot()` each, then compare with a free run: `tools/hd-models/transport_demo.py`
does that for the dragon (`python -I tools/hd-models/transport_demo.py OUTDIR`; needs `MEMORIES_DISC` and the
installed `studio-preview` mod; `--selftest` needs neither).

## 5. Done when (the validation)

- `native_check.py mods/my-model` says 0 errors and 0 warnings.
- The field attack and the arena attack are captured: the model stands on its card, strikes on the defender's reaction, falls and goes,
  and nothing vanishes or flickers.
- No change to the engine was needed. If one was, that is a bug of the pipeline: fix it there, with a test, before the model is "done".

## Worked examples (to fill in, phase I5)

### A dragon (non-humanoid), first pass done

Source: a Blender file (`Dragon_Baked_Actions.blend`: one mesh of 19,895 vertices, a 136-bone armature, four actions: idle, fly,
run, walk; no attack, hit or death). Steps that worked, in order:

1. Get the file out of its archive into a folder of its own (a `.rar` extracts with Windows' `tar.exe`).
2. Blender 4.5 has no import of the old Blender-Internal materials: the file's textures are lost. Rebuild one material with the colour
   atlas on the UV layer that matches it (`UV_mirror` here), look at the atlas first.
3. The game takes at most 128 bones: keep the weighted ones and their parents, and merge the lightest leaf bones' weights into their
   parents until the count fits (136 -> 120).
4. Export a glb with the actions (deform bones only, sampled), then `new_native_mod.py MODEL.glb --card N --out mods/x -- --rig generic
   --root <hips bone> --clips all --height <units>`. A creature big by nature needs `--height`; check it in the Library's model view
   (open the card, Triangle then Square) before the field.
5. `model.json` `clips`: map the asset's own names (idle, enter, attack, hit, guard, destroyed, win); an act with no clip plays idle.
   Changing a clip means the strike frames must be inside it (the game notes it).

Facts (Black Dragon by 3DHaupt.com, modelled 2009-10): downloaded to `C:\Users\mda\games\dragon-dl` (a rar; the Drive download needs
`curl -C -` retries); glb in `tmp/agent/dragon/`; one material with `textures/Dragon_Bump_Col2.jpg` on `UV_mirror`; first-pass mod
`tmp/pc/game32/mods/dragon-test` (card 364), built with `--rig generic --root pelvic_2 --clips all --height 600`; `make_dragon.py`
now uses `--extent` (largest bounding side; a wingspan is about twice the height, so `--height 450` is about 2200 units wide) and
patches the `clips` map and `strike` afterwards. Licence: the same terms as the other models of this branch (third-party, fan-made,
properly licensed); the package `license` field says `unknown` until the user gives the text.
Status: plays in the Library; 600 is too big for the Library camera. Open: size, attack/hit/death clips (the asset has only
`Idel_New`, `Fly_New`, `Run_New`, `Walk_New`: idle/hit/guard/destroyed <- Idel_New, enter/win <- Fly_New, attack <- Run_New is a locomotion
cycle, see `native-models-fit-problem.md` sec. 4), strike frames, field and arena checks (`field_attack.py --native`). The fit problems
and the planned fixes are the studio's (`native-models-feasibility.md`); this example is written after them.

A dragon (non-humanoid) and Goku (humanoid with hair), each from the raw model to the captures above: the exact commands, the
problems met and their fixes, the pictures. They need the models themselves (a rigged glb each) from their authors.

#### The dragon through the Studio (2026-10-24, tested)
1. FM Editor, Studio tab, Open glb `tmp/agent/dragon/dragon.glb` (recipe saved beside it: `dragon.recipe.json`).
2. S0 Intake: Category C4 (detection said C2 at 40%; the humanoid slots check fails for C1-C3 on a creature). Set author, license, URL (S9 provenance check).
3. S4 Size: mode `extent`, value 600 (the footprint check only warns for wings). S5 Clips: `acts.attack.source = Fly_New` (the asset has no attack clip; the build maps every act to Fly_New). S6 then reads the real clip length (227 frames).
4. S9 Package: Build package (builds twice, ~1 min, must be byte-identical; sets `pkg.path`). Export report writes `report.md`.
5. S8 Validate: Run on Field attack / Arena attack (needs `MEMORIES_DISC`; route A launches the game headless, 17-55 s), then Looks right or Report a problem.
Result: the dragon flies and attacks in the field and the arena at about normal-monster size with its own texture; camera unchanged. Still open: S2 chains warning (68 bones in 4 trees, unjudged), 4 bone-stretch warnings in S5, no real attack/hit/death clips (the user supplies them or procedural acts), licence text.
