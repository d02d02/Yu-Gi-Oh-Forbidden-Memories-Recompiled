# Job sm2-audit

## Goal
`tools/hd-models/studio/audit.py` (the Model Studio's S0-S3 checks over a glTF, already written and running) gets a test
suite, `tools/hd-models/tests/test_studio_audit.py`, built from small synthetic glbs. Every check id below is exercised in
BOTH directions (the case that raises it, and the case that does not). Where a test exposes a real bug in `audit.py`, fix the
bug. Do not change any threshold or constant, and do not change a check's meaning (see "Rules").

## Facts and excerpts (pasted: do NOT re-read audit.py or synthetic_gltf.py in full; open them only to fix a bug)

### Running things
- From the repo root: `python3 tools/hd-models/tests/test_studio_audit.py -k TestS0` (unittest, `-k` filters by class name).
- Test file header to use (same as `test_studio_state.py`):
  ```python
  HERE = Path(__file__).resolve().parent
  sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
  from studio import audit, state
  import synthetic_gltf
  ```
- `synthetic_gltf.write(path)` writes a small rigged glb (a `.glb` at `path`). Its content:
  nodes: 0 Armature, 1 pelvis (y=1), 2 spine_01, 3 upperarm_r, 4 hand_r, 5 thigh_r, 6 foot_r, 7 Body (mesh 0, skin 0), 8 Sword (mesh 1, NOT skinned, child-less, translation -0.1,0,0).
  skin 0 joints = nodes [1,2,3,4,5,6] (bones in that order: pelvis, spine_01, upperarm_r, hand_r, thigh_r, foot_r), with inverse bind matrices that make rest pose == bind pose.
  mesh 0 has 2 primitives (box lower 0..1 m with material 0 "red" = textured 8x8 PNG, box upper 1..1.6 m with material 1 "blue" = colour only, UVs repeating twice), all JOINTS_0/WEIGHTS_0 `[j,0,0,0]` / `[1,0,0,0]`.
  animations: Idle, Sword_Attack, Death01, Victory, Walk. No `asset.extras`.
- To make a variant: read the glb, change the JSON chunk, write it back. Write this helper first (item 1):
  `variant(tmp_dir, mutate) -> Path`: calls `synthetic_gltf.write`, parses the glb (12-byte header, then chunks of `<I length><I type>`; JSON chunk type 0x4E4F534A, BIN chunk 0x004E4942), calls `mutate(doc)` on the JSON dict, re-packs with 4-byte padding (JSON padded with spaces, BIN with zeros) and a correct total length, returns the path.

### The audit API (audit.py)
- `audit.load_model(path) -> Model`; raises `audit.AuditError` for an unreadable file.
- `audit.audit_stage(stage, model, recipe=None, clips_from=None) -> {"findings": [...], "data": {...}}` for "S0".."S3".
- `audit.audit_all(path, recipe=None, clips_from=None) -> {"S0":..., "S1":..., "S2":..., "S3":...}`; a file that does not open gives only `S0.load` (fail).
- `audit.apply_to_studio(studio, results)` stores the results in a `state.Studio`.
- A finding: `{"id", "level": "info"|"warn"|"fail", "message", "fix", "value"?}`; `value` is the measured number an acknowledgement is stored with.
- `audit.detect_category(model) -> {"category", "confidence", "evidence"}`; `audit.classify_bone(name, x, cx) -> (region, slot)`.
- Constants (do not change): DRIFT_WARN 4.0, DRIFT_FAIL 12.0, WEIGHTS_FAIL_PCT 1.0, FLIPPED_WARN_PCT 1.0, ROOT_OFF_PCT 15.0, CONFIDENCE_WARN 60, UV_REPEATS 4, TRIANGLES_WARN 200000, TEXTURE_MB_WARN = spec.BUDGET_MB // 8. In tests, lower a threshold with `unittest.mock.patch.object(audit, "NAME", value)` instead of building huge models.

### The checks (id: level when raised; what raises it; the recipe keys it reads)
S0: `S0.licence` fail if `recipe["meta"]["license"]` empty/missing (the fix text mentions the file's own licence when `asset.extras.license` exists);
  `S0.attribution` warn if the licence text contains the word BY and `meta.author` is empty (value = the licence text);
  `S0.category` fail if `recipe["model"]["category"]` is missing; `S0.category-confidence` warn (value = confidence) if detection < 60 AND no category chosen;
  `S0.skins` warn (value = skin count) if more than one skin and `recipe["source"]["skin"]` missing; `S0.ok` info only when nothing else was raised.
S1: `S1.bones` fail if bones > spec.MAX_BONES (128) (patch `audit.spec.MAX_BONES` in a test); `S1.weights` warn if some vertices have weight sum < 0.01, fail if they are more than 1% (value = count);
  `S1.influences` info (value = vertices with more than 4 influences, needs a WEIGHTS_1 accessor); `S1.scale` warn when a mesh node or a joint's ancestor has scale 0.01, 100 or non-uniform;
  `S1.normals` warn when more than 1% of faces point against their vertex normals (value = percent); `S1.size` warn when triangles > TRIANGLES_WARN;
  `S1.bind-vs-rest` warn if the CLOSEST pose (rest pose, or frame 0 of any clip) still moves some region by more than 4% of the model height, fail above 12% (value = percent; the finding carries `region`); `S1.skin` fail when the file has no skin; `S1.merge` info always; `S1.ok` info when no warn/fail.
S2: `S2.chains` WARN (not fail: the game accepts several parentless bones) when bones are in a different tree from the root (value = count); `S2.map` fail for category C1-C3 when humanoid slots (hips spine head arm_l arm_r hand_l hand_r leg_l leg_r foot_l foot_r) are empty (value = number empty);
  `S2.root-side` warn when the root is more than 15% of the height away (horizontally) from the body centre (value = percent); `S2.reversed-scale` fail when a joint has negative scale (value = count);
  `S2.extras-weights` warn when a bone listed in `recipe["rig"]["extras"]` has no weights (value = bone name); `S2.skin` fail when no skeleton; `S2.ok` info.
S3: `S3.dropped` warn per material using an extension, a texCoord other than 0, or KHR_texture_transform (value = material name); `S3.vertex-colour` warn if a primitive has COLOR_0 (value = count);
  `S3.emissive` warn if a material has emissiveFactor != 0 or emissiveTexture (value = count); `S3.uv-repeat` warn if a primitive's UVs span more than 4 repeats (value = count);
  `S3.memory` warn if texture memory > TEXTURE_MB_WARN (value = MB); `S3.atlas` fail if `native_convert.build_textures` raises (patch `audit.nc.build_textures` in a test); `S3.ok` info.

### Rules
- Never change the constants, a check id, a level or a value's meaning. If a test seems to need it, write BLOCKED with the reason.
- A real bug (a crash, a wrong count) is fixed in `audit.py` with the smallest change; say so in the item's Result line.
- Every test must be able to fail: assert the specific check id AND its level (and the value where one is listed), and for the "does not raise" direction assert the id is absent. No test may be a bare "runs without error".
- Python 3.12, stdlib `unittest` only; numpy and Pillow exist. No new dependencies.

## Given (read-only for the agent)
None: the agent writes the tests. `tests/test_studio_state.py` and `studio/state.py` are not part of this job: do not touch them.

## Read first (only what is not pasted above)
- `tools/hd-models/tests/synthetic_gltf.py` lines 60-144: how the synthetic glb is built (only if a variant needs a detail not listed above).
- `tools/hd-models/studio/audit.py`: only the function of the check you are testing.

## You may change
`tools/hd-models/tests/test_studio_audit.py` (create), `tools/hd-models/studio/audit.py` (bug fixes only), `tools/hd-models/README.md` (one line).

## You must not touch
Everything else, including the structure of progress.md, `studio/state.py`, `tests/test_studio_state.py`.

## Constraints
- One item per session: the loop re-runs each item's `check:` itself, ticks what passes and commits after every iteration.
- The test file grows by one test class per item; keep each class independent (each builds its own variants in a temp dir).

## Acceptance
`bash verify.sh` exits 0.

## Hints for item 4 (TestS1BindVsRest), worked out for you: do not re-derive them
Read only `bind_vs_rest()` and the "bind vs rest" block of `s1()` in `studio/audit.py` (lines ~370-420), not the whole file.
- Synthetic skin joints (index: node): 0 pelvis(1), 1 spine_01(2), 2 upperarm_r(3), 3 hand_r(4), 4 thigh_r(5), 5 foot_r(6).
  Body vertices: y<0.5 weighted to joint 5 (foot_r), 0.5-1.0 to joint 0 (pelvis), above 1.0 to joint 1 (spine_01). Mesh spans y 0 to 1.6.
- Drift is how far the node rest pose moves a vertex away from the stored mesh, in percent of `model.height`. foot_r (node 6) has
  no children: setting its `translation` to `[0, -0.8 + d, 0]` moves only the foot vertices by d, so the worst region is the
  feet, drift = 100 * d / model.height. Read `model.height` from the loaded model and compute d from the percent you want
  (about 0 for no finding, 8% for warn, 20% for fail; assert the value within 0.2). Print the finding once to confirm its region name.
- The check uses the CLOSEST pose among the node rest pose and frame 0 of every clip. So for the warn and fail cases, empty the
  animations (`doc["animations"] = []`). For the last case keep them: a clip whose frame 0 puts foot_r back at the bind pose
  makes the file pass (add an animation with a translation channel on node 6 with times [0, 1] and values [[0,-0.8,0],[0,-0.8,0]]).
- Build each variant with the existing `variant(tmp_dir, mutate)` helper and audit it as the TestS1Mesh tests do.
