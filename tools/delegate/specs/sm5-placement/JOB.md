# Job sm5-placement

## Goal
One UI-free module `tools/hd-models/studio/placement.py` and tests: the S4 (size and placement) maths and checks of the Model Studio, on a glb, headless. Pure Python 3.12, numpy, stdlib `unittest`, no tkinter. Tests: `tools/hd-models/tests/test_studio_placement.py`, one class per item.

## Facts (pasted: do NOT read audit.py, state.py or recipe.py in full; `grep -n "def "` then read at most 30 lines)
- Run: `python3 tools/hd-models/tests/test_studio_placement.py -k TestFit` from the repo root. Test header: `HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))`, then `from studio import audit, placement` and `import synthetic_gltf`. `synthetic_gltf.write(path)` writes a small rigged glb.
- `audit.Model(path)` (class at audit.py:52) loads a glb; after init it has `model.lo`, `model.hi` (numpy xyz min and max of the rest-pose mesh, glTF units, y up) and `model.height = hi[1]-lo[1]`. Use only these.
- Reference: `tools/hd-models/studio/reference/bls_outline.json` keys `bbox_min` `[-108,0,-699]`, `bbox_max` `[83,373,-463]`, `height` 373 (game units; the disc's standard monster). Footprint PROXY (the real footprint is not measured yet): width_x = 191, depth_z = 236 (bbox extents), label it `"proxy": true` in results.
- Game units: the converter scales the model to a target height (default 373) so units are game units after fit. Fit modes (recipe `size.mode`): `height` (scale so height = value, default 373), `extent` (scale so max(x extent, z extent) = value, default = footprint width_x), `percent` (scale = value %). Recipe keys: `size.mode`, `size.value`, `size.ground_offset` (default 0), `model.scale` (integer percent, default 100).
- Findings are made with `audit.finding(check, level, message, fix="", value=None)`; levels `"fail" "warn" "info"`.

## Items (see progress.md)
1. `fit(lo, hi, mode="height", value=None)` returns `{"scale": float, "height": h, "extent_x": x, "extent_z": z}` after applying the fit; value defaults per mode (373 / 191 / 100).
2. `footprint_ratio(extent_x, extent_z)` against the proxy footprint: returns `{"ratio": r, "proxy": True}` with r = max(extent_x/191, extent_z/236).
3. `check_footprint(extent_x, extent_z)` returns a finding: id `S4.footprint`; none when r <= 1.10; `warn` when 1.10 < r <= 1.60 (message "Model is N% wider than the card footprint.", fix "Fit with a smaller pose, lower the scale to M%, or switch to Extent."), `fail` above 1.60; values rounded to whole numbers.
4. `check_ground(lowest_y, ground_offset=0, floating=False)` finding `S4.ground`: warn when not floating and abs(lowest_y - ground_offset) > 8 units (fix "Set ground offset to N or mark the model as floating."), else none.
5. `check_uniform_scale(g)` on the glTF dict: finding `S4.uniform` fail when any node's `scale` has unequal components (tolerance 1e-4); fix "Re-export from Blender with applied scale."
6. `run_s4(glb_path, recipe)` ties them together: loads `audit.Model`, applies the recipe fit, returns `{"fit": ..., "findings": [...]}`; test on the synthetic glb with each fit mode.

## Constraints
One item per session; WRITE small: a new file at most 60 lines per write, grow it by edits of at most 60 lines. Do not edit anything except `studio/placement.py`, `tests/test_studio_placement.py`, and one row in `tools/hd-models/README.md`. Never change `audit.py`, `state.py`, `recipe.py`.

## Acceptance
`bash verify.sh` exits 0.
