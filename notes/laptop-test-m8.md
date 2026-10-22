# Laptop test: the mannequin, the dragon, the Library (M8)

Branch `feat/native-models-plug-and-play` (commit with this file or later). The build and `play-bls.ps1` setup are the ones of M5 (a checkout of
this branch built with `python tools/pc/build_game32.py`, with the Test scenes and 3D Monsters mods in its `tmp/pc/game32/mods`;
`-Repo` names that checkout). Needs `MEMORIES_DISC` (the disc .bin) and `pip install numpy pillow`.

## 1. The mannequin (CC0, in the repo: `examples/native-models/mannequin/`)

```powershell
cd <checkout>
.\tools\hd-models\play-bls.ps1 -Repo . -NativeModel .\examples\native-models\mannequin\model.json              # the field attack: the mannequin on BLS's card
.\tools\hd-models\play-bls.ps1 -Repo . -NativeModel .\examples\native-models\mannequin\model.json -Attack 0     # monsters just stand on the field (no attack); the arena attack is field_attack.py --arena (below)
.\tools\hd-models\play-bls.ps1 -Repo . -NativeModel .\examples\native-models\mannequin\model.json -NativeId -2  # every monster a mannequin
```

## 2. The dragon (CC0, built from your download: not committed, 20 MB)

Download "Black Dragon" (the Drive link you sent, `27-blender.rar`) and extract it into an empty folder (`tar -xf 27-blender.rar -C C:\dragon`).
Blender 4.5 must be installed (`--blender PATH` if it is not in `C:\Program Files\Blender Foundation\Blender 4.5`).

```powershell
python tools\hd-models\make_dragon.py C:\dragon $env:TEMP\dragon-pkg            # --height 450 by default (BLS is 373); try --height 300 or 600
.\tools\hd-models\play-bls.ps1 -Repo . -NativeModel $env:TEMP\dragon-pkg\model.json
.\tools\hd-models\play-bls.ps1 -Repo . -NativeModel $env:TEMP\dragon-pkg\model.json -Attack 0
```

Known: the asset has only idle, fly, run, walk (idle = Idel_New, enter/win = Fly_New, attack = Run_New, hit/guard/destroyed = idle), so the
attack is a run and nothing dies; the colour is grey (the atlas), not black. Size and these are `model.json` edits (`scale`, `clips`, `strike`)
that need no re-conversion.

## 3. The Library

Library (title menu), View > Library: show every card, Internal 2x. Open card 364 (Black Luster Soldier), press Triangle then Square for
the model view: it now shows the native model when a mod (or the test switch: `$env:MEMORIES_NATIVE_MODEL=...; $env:MEMORIES_NATIVE_MODEL_ID=363`)
gives the card one. Tell me whether the native model should show there by default.

## 4. As a mod (instead of the test switch)

```powershell
python tools\hd-models\new_native_mod.py .\examples\native-models\mannequin\... (a glb) --card 364 --out <game>\mods\my-model
```
then apply it in Mods, restart, Internal 2x or more. See `notes/adding-a-model.md`.

## Tested on the desktop (2026-10-22): the commands above ran; with `-Shot` they wrote a picture (mannequin and dragon on the field, both standing)

The arena attack (a real window, a sheet of frames): `$env:MEMORIES_DISC=...; python -I tools\hd-models\field_attack.py OUT --arena --setting mod.3d-monsters.attack=0 --env MEMORIES_NATIVE_MODEL=<model.json> --env MEMORIES_NATIVE_MODEL_ID=363`.
