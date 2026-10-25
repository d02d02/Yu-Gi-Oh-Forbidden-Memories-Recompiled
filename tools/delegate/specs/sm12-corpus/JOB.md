# Job sm12-corpus

## Goal
Test corpus for the Model Studio audit (SM8): one small synthetic glb per category C1-C8 generated from code, golden audit results, and a regression runner. One module `tools/hd-models/studio/corpus.py`, tests `tools/hd-models/tests/test_studio_corpus.py` (one class per item), golden file `tools/hd-models/studio/reference/corpus_golden.json`. Pure Python 3.12, stdlib `unittest`, PIL ok, no tkinter.

## Facts (do NOT read other modules in full; `grep -n "def "` then read at most 30 lines)
- Test header: `HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))`, then `from studio import corpus, audit`. File MUST end with `if __name__ == "__main__":\n    unittest.main()`. Run from repo root: `python3 tools/hd-models/tests/test_studio_corpus.py -k TestX`.
- `tools/hd-models/tests/synthetic_gltf.py` has `Builder` (buf, views, accessors; `.accessor(values, kind, component=5126)` returns an accessor index), `box(x0,x1,y0,y1,z0,z1)` returns (positions, normals, uvs, indices), `quat(axis, degrees)`, `png_bytes(size, colour)`. Read its `write(path)` function (line 70 to the end) once as the template for assembling a glb (nodes, skin, mesh, animation, glb container).
- `audit.load_model(path)` opens a glb; `audit.detect_category(model)` returns `{"category", "confidence", "evidence"}`; `audit.audit_all(path)` returns `{"S0": {"findings": [...], "data": {}}, ... "S3": ...}`; a finding is a dict with `id`, `level`, `message`. Detection looks at bone NAMES (Unreal style: pelvis, spine_01, spine_02, neck_01, head, clavicle_l/r, upperarm_l/r, lowerarm_l/r, hand_l/r, thigh_l/r, calf_l/r, foot_l/r; wings: bones containing "wing"; tail: "tail"), at leg/wing/tail counts, and for unskinned files at the bounding box. Read `detect_category` (audit.py, search `def detect_category`, 40 lines) once.
- `audit.load_model(path)` returns a Model: `model.joints` is the list of joint node indices (empty when unskinned), `model.names` their names, `model.skins` is an int COUNT (not a list), `model.doc` the glTF dict (`model.doc["skins"][0]["joints"]`, `model.doc.get("animations", [])`). Test joint counts with `len(model.joints)`.
- Intended categories: C1 humanoid standard Unreal names; C2 humanoid with extras (same plus a cape or extra bones, still >= 80% slots); C3 humanoid statue, no rig (unskinned, tall box); C4 quadruped (4 leg chains, spine, head, tail, no humanoid names); C5 winged creature (wing bones >= 2, not humanoid); C6 legless (spine chain, no legs); C7 rigid multi-part (several unskinned mesh nodes, not tall); C8 static mesh (one unskinned wide box).
- Detection is a heuristic: if a category cannot be produced, record in `EXPECTED_DETECTED` what it really detects (for example C7 detects as C8) with a comment; never change audit.py.

## Constraints
One item per session; WRITE small: a new file at most 60 lines per write, grow it by edits of at most 60 lines. Only edit `studio/corpus.py`, `tests/test_studio_corpus.py` and create `studio/reference/corpus_golden.json`. Never edit any other file; README is the supervisor's.

## Acceptance
`bash verify.sh` exits 0.
