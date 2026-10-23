# Recipe schema (draft v0)

Derived from the knob tables in `studio-view.md`, checked against the converter's arguments (`tools/hd-models/native_convert.py`, read) and the package format (`notes/native-models.md`, read). Draft: names can still change while the screens change; nothing is implemented.

`recipe.json` is the only input besides the source glb. `convert(recipe) -> package` is deterministic (SD2). Mapping column: **flag** = existing `native_convert.py` option; **model.json** = existing package member; **mod.json** = existing mod entry; **new** = no home today (needs converter or engine work, listed in `engine-needs.md`).

## Top level
| Key | Type | Maps to |
|---|---|---|
| `schema` | int, 1 | new |
| `studio` | string, version of the studio that last wrote it | new (informational) |
| `source` | object (below) | glb path, hash |
| `model` | object | category, name, cards, per-card overrides |
| `meta` | object | `author`, `license`, `source` of model.json |
| `audit`, `rig`, `mat`, `size`, `acts`, `look`, `shots`, `pkg` | objects (below) | |
| `acks` | list of `{check, value}` | new (warn acknowledgements, SD rule 1) |
| `runs` | list of `{scene, result, package_hash}` | new (S8 marks) |

## Keys by section
| Key | Stage | Maps to | Notes |
|---|---|---|---|
| `source.path` | S0 | converter `gltf` argument | stored relative to the recipe |
| `source.sha256` | S0 | new | determinism, stale-source detection |
| `source.skin` | S0 | new | converter picks the skin itself today |
| `source.meshes` | S0 | new | include/exclude list |
| `model.category` | S0 | new | C1-C8; drives presets only |
| `model.name` | S0/S9 | flag `--name` | |
| `model.cards` | S0/S9 | mod.json `cards` | at most 64 per entry |
| `model.card_overrides` | S9 | mod.json `native_models` entry `scale` / `offset` | **new** optional members (Q11); several entries may share one package |
| `meta.author`, `meta.license` | S0 | flags `--author`, `--license` | |
| `meta.url`, `meta.attribution` | S0 | model.json `source` for the URL; attribution **new** | |
| `audit.fix_axes`, `audit.smooth_passes`, `audit.normalise`, `audit.mirror`, `audit.drop_parts` | S1 | new | today Blender-side |
| `audit.bone_limit`, `audit.merge` | S1 | new | the 128-bone merge is done in Blender (`export_dragon_blend.py`) |
| `rig.profile` | S2 | flag `--rig` (auto, ue, mixamo, generic) | |
| `rig.root` | S2 | flag `--root` | |
| `rig.humanoid` | S2 | new | bone-slot map; profiles are built in today |
| `rig.feet` | S2 | new | feet detection is internal to `convert` |
| `rig.strike` | S2 | new | default strike bone |
| `rig.extras`, `rig.follow` | S2 | flag `--follow BONE=SOURCE[@FRACTION]` | `follow` exists; rigid/cut roles **new** |
| `mat.atlas` | S3 | flag `--texture-max` | |
| `mat.no_pbr` | S3 | flag `--no-pbr` | |
| `mat.items`, `mat.alpha_cutoff` | S3 | new | per-material overrides; alpha cut at half is fixed in the engine |
| `mat.normal_strength`, `mat.flip_green` | S3/S7 | model.json `look.normal_strength`, `look.flip_green` | these are look values, same keys |
| `size.mode` | S4 | which of `--scale`, `--extent`, `--root-height`, `--height` is set | precedence: scale > extent > root-height > height |
| `size.value` | S4 | the value of that flag | |
| `size.origin_height` | S4 | flag `--origin-height` | default 159 |
| `size.center` | S4 | flag `--no-center` (inverted) | |
| `size.fit_pose` | S4 | new | fit on a chosen pose |
| `size.offset` | S4 | model.json `offset` `[x, y, z]` whole numbers (the model's own axes: x right, y down, z forward) | the studio's origin drag and ground offset are UI conveniences that compute this triple |
| `size.scale_pct` | S4 | model.json `scale` | integer percent about the soles |
| `acts.<act>.source` | S5 | `--clips`, `--clips-from`; model.json `clips` | asset clip name; library and procedural are **new** |
| `acts.<act>.trim`, `.speed`, `.mirror`, `.crossfade` | S5 | new | engine crossfade is 6 frames, fixed today |
| `acts.<act>.loop`, `.close_loop` | S5 | new | |
| `acts.<act>.root_motion` | S5 | flag `--keep-root-motion` (global today) | per-act is **new** |
| `acts.<act>.strike` | S6 | model.json `strike` | at most 4 frames, attack only |
| `acts.<act>.strike_joints` | S6 | new | today the converter picks the fastest joint |
| `acts.<act>.timemap`, `.hold` | S6 | new | needs the sampler to read it |
| `timing.stretch_range` | S6 | new (studio checks only) | |
| `look.ambient`, `.light_gain`, `.highlight`, `.normal_strength`, `.flip_green`, `.camera_near`, `.camera_keep`, `.camera_scale` | S7 | model.json `look` | existing, percent unless noted |
| `look.tint` | S7 | new | not in the engine |
| `shots[]` | S7 | model.json `shots` | existing, see the correction below |
| `pkg.name` | S9 | folder and `model.json` `name` | |
| `pkg.write_mod` | S9 | `new_native_mod.py` behaviour | |

Acts are `idle, enter, attack, hit, destroyed, win, guard` (attack2 dropped, Q12). `model.json` has no `attack2` clip today: row 4 plays `attack`. **attack2 is new in the recipe, with no package home**, so either drop it from S5 or add it to the package (engine change). Recommendation: drop it from the studio until the engine has it, and show row 4 as "plays Attack".

## Corrections the schema forces on the UX docs
1. **S7 `shots`**: in the package, a shot is an arena camera move over a frame range of one act (`act, from, to, yaw, pitch, distance %, height, ease, other`), at most 8, not a static "field shot / arena shot" framing. The S7 knob table in `studio-view.md` must become a shot list editor (add, edit, scrub-to-preview). Camera presets for the viewport (S4) are a separate studio feature, not saved in the package.
2. **S7 look**: real keys are the eight in `native-models.md` (Look). `tint` and a free "arena camera distance/height" do not exist; remove or mark *(new)*.
3. **Per-card scale/offset** (multi-card): see `model.card_overrides` above. Decided (Q11).
4. **Alpha cutoff** in S3 is fixed at half in the engine; make it a read-only fact, not a knob, unless the converter bakes alpha.
5. **Attack 2**: see above.
6. **Crossfade**: fixed at 6 frames; remove as a knob or mark *(new)*.

## Determinism rules (recipe -> bytes)
Sorted keys and one JSON formatter; integers where the game's JSON reader needs them (`scale`, `offset`, `shots`, `strike`); no timestamps or paths in the output; `converter` field = studio version plus source hash only; pinned numpy and Pillow versions recorded in the recipe's `studio` string; the glb hash must match `source.sha256` or the build refuses.

## Versioning
`schema` is an integer. A new studio opens older schemas through migration functions and shows what changed. An older studio refuses a newer schema naming the version needed. The package `format` (1) is independent.

## Example (dragon, abridged)
```json
{
  "schema": 1,
  "source": {"path": "dragon.glb", "sha256": "…", "skin": "Armature"},
  "model": {"category": "C5", "name": "Dragon", "cards": []},
  "meta": {"author": "…", "license": "CC-BY-4.0"},
  "rig": {"root": "Body_Center", "feet": [], "strike": "Jaw"},
  "size": {"mode": "extent", "value": 600, "origin_height": 159, "scale_pct": 85, "offset": [0, 0, 0]},
  "acts": {
    "idle": {"source": "Flying_Idle", "loop": true},
    "attack": {"source": "Bite_01", "strike": [11]},
    "hit": {"source": {"procedural": "recoil", "distance": 30, "frames": 10}}
  },
  "look": {"ambient": 20, "light_gain": 100},
  "acks": [{"check": "S4.footprint", "value": 1.9}]
}
```

## New questions
Q11 and Q12 are decided (see `open-questions.md`): per-card overrides as optional `scale`/`offset` on a mod.json entry; attack2 dropped.
