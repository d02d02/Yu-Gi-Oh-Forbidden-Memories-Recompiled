# Native models: a monster drawn from a modern model file

How it works inside, the traps and what is open: [native-models-dev.md](native-models-dev.md); the tools: [`tools/hd-models/`](../tools/hd-models/README.md).

A data mod can replace a monster's battle model with a modern one: a skinned, textured mesh with its own skeleton and animation clips,
drawn by the OpenGL picture (View > Internal 2x or more) instead of the console's packets. The game's logic, sound, effects and save
states are untouched: the original model keeps running out of sight, and the new one follows its position, its animation row and its
timing. No C, no disc and no Blender script is needed: a rigged glTF goes in, a mod folder comes out.

## From a model to the game, in five steps

1. **A rigged model**: a `.glb` or `.gltf` with an armature, the mesh skinned to it and its animation clips (Mixamo, Quaternius / Unreal
   rigs, or anything Blender exports as glTF). Check its licence lets you share it.
2. **The tools need numpy and Pillow**, once: `pip install numpy pillow`.
3. **Make the mod**:
   `python tools/hd-models/new_native_mod.py angel.glb --card 364 --out my-angel --license CC-BY-4.0`
   (`--card` again for more cards; converter options after `--`, for example `-- --clips-from UAL1_Standard.glb --root-height 320`).
   Run it again with another model and the same `--out` to put several models in one mod.
4. **Read the report**: the size, the clip each act plays, the attack's blow frames, the textures. Change what is wrong in
   `my-angel/models/angel/model.json` (below) and check again with `python tools/hd-models/native_check.py my-angel`.
5. **Play**: copy `my-angel` into the game's `mods` folder (or the `mods` folder of your user directory), apply it in Mods, restart the
   game, set View > Internal 2x or more. Below 2x the monster is the disc's own model, as without the mod.

## The mod

```json
{
    "id": "my-angel",
    "name": "Fallen angel for Black Luster Soldier",
    "enabled": true,
    "native_models": [
        { "cards": [364], "package": "models/angel/model.json" },
        { "card": 1, "file": "dragon.hdm", "setting": "dragon" },
        { "model": 363, "file": "angel.hdm" }
    ]
}
```

| Key of an entry | Meaning |
|---|---|
| `cards` / `card` | the cards it is drawn for (card ids; at most 64 per entry) |
| `model` | instead of cards: the disc model id, the card id minus one (Black Luster Soldier is card 364, model 363) |
| `package` | a `model.json` inside the mod (below), or |
| `file` | a bare HDM4 file (its own texture, the default clip names) |
| `setting` | (optional) the entry is used only while this setting of the mod is on, as other rule lists do ([modding.md](modding.md)) |

At most 64 entries in all the mods. A model is read when a slot first needs it, not at start. When two mods have a model for the same card the
later mod's is drawn; a model that cannot be used is a note beside its mod in the Mods window, and the earlier mod's model (else the disc model)
is drawn. With the card unknown (the Library's model view) an entry for a card stands for that card's disc model. A mod with native models
needs a restart to change.

## The package: `model.json`

What `native_convert.py` writes, every member but `model` optional; files are named from the package's folder and stay inside the mod:

```json
{
    "format": 1,
    "name": "Fallen angel",
    "model": "model.hdm",
    "textures": { "base": "base.png", "normal": "normal.png", "metal_roughness": "metal_roughness.png" },
    "clips": { "idle": "Sword_Idle", "enter": "Idle_Loop", "attack": "Sword_Attack", "hit": "Hit_Chest",
               "destroyed": "Death01", "win": "Sword_Idle", "guard": "Sword_Idle" },
    "strike": { "attack": [11, 30] },
    "scale": 100,
    "look": { "ambient": 20, "light_gain": 100 },
    "author": "...", "license": "CC-BY-4.0", "source": "angel.glb"
}
```

| Member | Meaning |
|---|---|
| `model` | the HDM4 file: mesh, skeleton, clips |
| `textures` | PNG files drawn over the file's own: `base` (colour, alpha below half is cut), `normal` (normal map, green up as glTF), `metal_roughness` (glTF's: roughness in green, metal in blue). Swap a PNG and restart: no conversion. Above 2048 a side (`MEMORIES_NATIVE_TEXTURE_MAX`) a texture is halved until it fits |
| `clips` | the clip each act plays (acts below); an act left out plays the default name, else the first clip |
| `strike` | the attack clip's frames where its blows land (at most 4): where the game knows when the blow lands (3D Monsters on the field), the attack clip is time-warped so the first one lands then |
| `scale` | percent, about the soles (110 = a tenth taller, feet where they were) |
| `offset` | `[x, y, z]`, whole numbers in game units: moves the model along its own axes (x right, y down, z forward), the same at any `scale`. To nudge where it stands on its card. The axes are the model's own, so they turn with it: for the attacker on the field's camera, -x is toward the viewer and +z to the left (`[-60, 0, 40]` moves it about a card's width fraction forward and left); check with `MEMORIES_NATIVE_SKIN_LOG=1` (the `rv axes` line says where each model axis points on screen) |
| `shots` | camera shots in the arena (at most 8): `[{"act": "attack", "from": 0, "to": 60, "yaw": 40, "pitch": 10, "distance": 80, "height": 0, "ease": 8, "other": false}]`. While the monster (or, with `"other": true`, the other monster of the battle) plays that act, within those frames of its row, the camera turns `yaw` degrees about its look-at point (positive = clockwise seen from above), rises `pitch` degrees and `height` units, and its distance becomes `distance` percent, easing in and out over `ease` frames. In the arena, and in the 3D Monsters field fight (there the same move is made on the fight's own camera orbit: yaw and pitch as turns of it, distance as a factor, the height on the eye). Only in a battle this model is drawn in; the game's own camera and the length of the battle are not changed. Whole numbers |
| `look` | the model's light and camera (below), in percent (`camera_near` in game units, `flip_green` 0 or 1) |
| `name`, `author`, `license`, `source`, `converter` | for people; the game does not read them |

An unknown member, act, clip name or a bad value is a note beside the mod; the rest of the package is used.

### Acts

The game's animation row decides the act, the row's clock the frame inside the clip (the clip is stretched over the row; the game's timing,
sounds and effects never change):

| Act | When |
|---|---|
| `idle` | standing (rows 0 and 1, and the other guardian star's attack row) |
| `enter` | entering the battle (row 2) |
| `attack` | the attack (row 3, or row 4 when the card fights with its second guardian star) |
| `hit` | hit and still standing (row 5) |
| `destroyed` | destroyed (row 6) |
| `win` | the winner's pose (row 7) |
| `guard` | guarding (row 8) |

A change of act cross-fades over 6 frames. An act with no clip (in `clips`, nor of the default name) plays another's: guard and destroyed the
hit's, the others the idle's. The converter guesses the clips by name and puts the idle where it finds nothing: check them.

### Look

Each value: the environment (one run) over the mod's setting of the same name (declare it in `settings` to let players tune it) over the
package's `look` over the default.

| Name (environment) | Default | Meaning |
|---|---|---|
| `camera_near` (`MEMORIES_ARENA_CAMERA_NEAR`) | 1000 | the arena camera's shots closer than this to their look-at point are pushed out |
| `camera_keep` (`MEMORIES_ARENA_CAMERA_KEEP`, 0.2..1) | 50 (%) | how much of the way in stays: 100 = the game's camera |
| `camera_scale` (`MEMORIES_ARENA_CAMERA_SCALE`) | 100 (%) | the whole arena camera, farther or nearer |
| `ambient` (`MEMORIES_NATIVE_AMBIENT`) | 20 (%) | added to the game's ambient light |
| `light_gain` (`MEMORIES_NATIVE_LIGHT_GAIN`) | 100 (%) | the game's lights, multiplied |
| `normal_strength` (`MEMORIES_NATIVE_NORMAL_STRENGTH`) | 180 (%) | how strongly the normal map shows |
| `highlight` (`MEMORIES_NATIVE_SPEC`) | 100 (%) | the strength of the metal/gloss highlight |
| `flip_green` (`MEMORIES_NATIVE_NORMAL_FLIPY`) | 1 | the normal map's green: 1 = glTF's (up), 0 = DirectX's (down) |

The camera only changes in a battle one of whose two monsters is drawn natively (the attacker's look first); every other battle, the
credits and a picture below Internal 2x keep exactly the console's camera.

## What a model can be

| | Limit |
|---|---|
| bones | 128 (remove twist and helper bones) |
| clips | 16 (`--clips` picks them; the acts' clips are kept first) |
| influences | 4 bones per vertex (the strongest; the converter says how much weight it dropped) |
| triangles | no limit of the game's (279,000 drew in 2-4 ms on a laptop GPU) |
| textures | one set per model: several materials are packed into one texture by the converter |
| memory | 512 MB for all the native models read (`MEMORIES_NATIVE_BUDGET_MB`): the game is a 32-bit program. A model past it is not read |

Size and placement: the game places a monster by its body root and sizes it as the disc's Black Luster Soldier (BLS) is sized: 373 game
units from the soles to the top, with the placed point 159 above the soles. The converter makes every model to that standard, whatever its
rig or proportions: the model is scaled to 373 tall (`--height`), and its origin, the point the game puts on the card, is on its vertical
axis 159 above its soles (`--origin-height`) and, horizontally, at the middle of its feet in the idle pose (`--no-center` keeps the hips).
So a model stands on its card with its soles on the ground at the size of the game's own monsters, with nothing to tune. The clips are made
in place (the game moves the monster). `--scale` (game units per glTF unit) and `--root-height` (the older way: the root bone is the origin,
that high above the soles) are there for the cases the standard does not fit; `scale` in `model.json` makes it bigger or smaller afterwards
(a dragon that should tower over the others: 150).

## Troubleshooting

| What you see | Why, and what to do |
|---|---|
| the disc model, not yours | Internal 1x (the native pass needs 2x or more); the mod not applied or not restarted; a note beside the mod in the Mods window says what was refused. `native_check.py` gives the same reasons offline |
| floating or sunk | the origin height: convert again with `--origin-height` (the soles' distance below the origin, 159 by default): a larger one lowers the soles (it floats less), a smaller one raises them |
| too big or too small | `scale` in `model.json` (percent, about the soles) |
| the wrong animation in a moment of the battle | that act's clip in `clips` |
| the blow lands early or late | `strike.attack` (the attack clip's frame of each blow) |
| black or flat | no base texture (the report says so), or the look: `ambient`, `light_gain` |
| bumps look inverted | `flip_green` 0 |
| holes in the surface | the base texture's alpha below half is cut: make it opaque |

## Code mods that draw monsters (3D Monsters)

A code mod that draws a slot itself (`func_800540B4`) says what the draw is just before, with `NativeModel_SetInstance`
(`src/pc/render/native_model.h`; bind it with `host->symbol` so the mod still loads on a game without it): the context (field, big card,
or measuring), its own key for the monster, the card, a fade and the disc frame its blow lands at. A native model then keeps its own
animation per monster, fades with it, and sorts at its depth. The card it names picks the model, as the battle's cards do in the arena.

3D Monsters does this: each monster it draws on the field or on the attack cards keeps its own pose (two native monsters never mix),
fades with the summon and the destruction, and in its attack the clip's first strike frame lands half way through the attack row,
where the mod has the defender react. With the attacker's effects on (`effects`) the effects decide when the blow lands, which is not
known ahead, so the attack clip then runs evenly over the row. A card a card mod added shows the native model of the card whose disc
model it borrows.

## Testing

`MEMORIES_NATIVE_MODEL=<file.hdm or model.json>` with `MEMORIES_NATIVE_MODEL_ID=<model>` (default 363, Black Luster Soldier; -2 every duel
slot) loads one model without a mod, over every mod's (a test switch). A model the game refuses says why on the console and, for a mod, beside
the mod in the Mods window. `MEMORIES_NATIVE_TIME=1` logs the GPU time of the model's draw, `MEMORIES_TRACE=model` one line per native draw
(`evt native ... mesh=<entry> card=<card>`). Saved states are tied to the exact build: after a rebuild make a new one.
