# Job sm12-corpus: synthetic glb corpus C1-C8 with goldens

Read JOB.md first. One item per session; the check is the line under the item.

## Status
Not started.

## Items
- [ ] 1. `write_glb(path, bones, skinned=True, clips=True, meshes=1)` + class TestWriteGlb. `bones` is a list of `(name, parent_index_or_None, (x, y, z))`; writes a valid glb: one box mesh skinned to bone 0 when skinned, `meshes` unskinned box nodes when not, an `Idle` clip rotating the first bone when clips; test: the file opens with `audit.load_model`, joint count matches, an unskinned build has no joints
  check: python3 tools/hd-models/tests/test_studio_corpus.py -k TestWriteGlb
  symbols: tools/hd-models/studio/corpus.py::write_glb
  min_tests: 3
- [ ] 2. `humanoid_bones()` and `build(category, path)` for C1 and C2 + class TestHumanoids; test: `audit.detect_category` of the built file returns C1 resp. C2
  check: python3 tools/hd-models/tests/test_studio_corpus.py -k TestHumanoids
  symbols: tools/hd-models/studio/corpus.py::build
  min_tests: 2
- [ ] 3. `build` for C3 and C8 (unskinned tall box resp. wide box) + class TestStatic; test: detected C3 resp. C8
  check: python3 tools/hd-models/tests/test_studio_corpus.py -k TestStatic
  min_tests: 2
- [ ] 4. `build` for C4, C5, C6 + class TestCreatures; test: detected C4, C5, C6 (or the entry in `EXPECTED_DETECTED`)
  check: python3 tools/hd-models/tests/test_studio_corpus.py -k TestCreatures
  min_tests: 3
- [ ] 5. `build` for C7 (several unskinned nodes, not tall) + `EXPECTED_DETECTED` dict (category to what the audit really says) + class TestMulti; test: every one of C1-C8 builds and `detect_category` equals `EXPECTED_DETECTED[c]`
  check: python3 tools/hd-models/tests/test_studio_corpus.py -k TestMulti
  symbols: tools/hd-models/studio/corpus.py::EXPECTED_DETECTED
  min_tests: 2
- [ ] 6. `golden_of(path)` returns `{"category": str, "findings": {stage: sorted list of "id:level"}}` from `audit.audit_all`; `run_corpus(tmpdir, golden_path)` builds all eight, compares with the golden file and returns a list of difference strings (empty = equal); `python3 corpus.py --update` writes `reference/corpus_golden.json` (sorted keys, indent 1, trailing newline); class TestGolden: deterministic (build twice, same bytes), empty diff against the committed golden, `python3 corpus.py --check` prints the differences and exits 1 when any, else exits 0; and a changed golden gives a non-empty diff
  check: bash verify.sh
  symbols: tools/hd-models/studio/corpus.py::run_corpus
  min_tests: 3
