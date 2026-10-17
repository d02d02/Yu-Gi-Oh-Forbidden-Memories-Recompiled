# Native models: a monster drawn from a modern model file

How it works inside, how the models are made and tested, the traps and what is open: [native-models-dev.md](native-models-dev.md); tools: [`tools/hd-models/`](../tools/hd-models/README.md).

A data mod can replace a monster's battle model with a modern one: a skinned, textured mesh with its own skeleton and animation clips,
drawn by the OpenGL picture (Internal 2x or more) instead of the console's packets. The game's logic, sound, effects and save states are
untouched: the original model keeps running out of sight, and the new one follows its position, its animation row and its timing.

```json
{
    "id": "angel-bls",
    "name": "Fallen angel for Black Luster Soldier",
    "min_api": 17,
    "enabled": true,
    "native_models": [
        { "model": 363, "file": "angel.hdm" }
    ],
    "settings": [
        { "key": "camera_keep", "label": "Camera: how much of a close shot stays", "type": "int", "default": 50, "min": 20, "max": 100, "step": 5 }
    ]
}
```

| Key | Meaning |
|---|---|
| `model` | the disc's model id: the monster card's id minus one (Black Luster Soldier is card 364, model 363) |
| `file` | an HDM4 file inside the mod (`tools/hd-models/rigged_to_hdm4.py` writes one from a rigged glTF) |

At most 8 models in all. A file that is missing or malformed is a note beside the mod in the Mods window, and the monster keeps its disc model.

## Settings (all optional; the first mod that has native models supplies them)

Declared like any mod setting (`settings`); a value in the environment wins for one run.

| Setting (environment) | Default | Meaning |
|---|---|---|
| `camera_near` (`MEMORIES_ARENA_CAMERA_NEAR`) | 1000 | the arena camera's shots closer than this to their look-at point are pushed out |
| `camera_keep` (`MEMORIES_ARENA_CAMERA_KEEP`, 0.2..1) | 50 (%) | how much of the way in stays: 100 = the game's camera |
| `camera_scale` (`MEMORIES_ARENA_CAMERA_SCALE`) | 100 (%) | the whole arena camera, farther or nearer |
| `ambient` (`MEMORIES_NATIVE_AMBIENT`) | 20 (%) | added to the game's ambient light |
| `light_gain` (`MEMORIES_NATIVE_LIGHT_GAIN`) | 100 (%) | the game's lights, multiplied |
| `normal_strength` (`MEMORIES_NATIVE_NORMAL_STRENGTH`) | 180 (%) | how strongly the model's normal map shows |
| `highlight` (`MEMORIES_NATIVE_SPEC`) | 100 (%) | the strength of the metal/gloss highlight |

The camera is only changed in a battle one of whose two monsters is drawn natively; every other battle, the credits and a
picture below Internal 2x keep exactly the console's camera. Below 2x (or when the OpenGL picture cannot draw the model) the
monster is the disc's own model, as without the mod.

## How the model is chosen and played

* The disc animation row picks the clip (idle, enter, attack, hit, destroyed, win) and the clock inside the row picks the frame; the attack row is
  time-warped so the clip's strike lands on the game's contact frames (`NativeAnim_Choose` in `native_anim.c`). A change of row cross-fades over 6 frames.
* The model stands at the body root's position and facing; the clip is in place (its root motion is stripped when the file is made).
* Lighting is the game's own three lights; with a normal map and a metal/roughness map in the file the surface is lit per pixel.

## Code mods that draw monsters (3D Monsters)

A code mod that draws a slot itself (`func_800540B4`) says what the draw is just before, with
`NativeModel_SetInstance` (`src/pc/render/native_model.h`; bind it with `host->symbol` so the mod still loads on a game
without it): the context (field, big card, or measuring), its own key for the monster, the card, a fade and the disc frame
its blow lands at. A native model then keeps its own animation per monster, fades with it, and sorts at its depth.

## Testing

`MEMORIES_NATIVE_MODEL=<file.hdm>` with `MEMORIES_NATIVE_MODEL_ID=<model>` (default 363, Black Luster Soldier) loads one model
without a mod (a test switch). A file the game refuses says why on the console and, for a mod, beside the mod in the Mods window. `MEMORIES_NATIVE_TIME=1`
logs the GPU time of the model's draw. Saved states are tied to the exact build: after a rebuild make a new one.
