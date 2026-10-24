# Job sm11-procedural: procedural root-motion tracks (headless, pure Python)

Read JOB.md first. One item per session; the check is the line under the item.

## Status
Not started.

## Items
- [ ] 1. `ease/quat helpers` + class TestEase
  check: python3 tools/hd-models/tests/test_studio_procedural.py -k TestEase
  symbols: tools/hd-models/studio/procedural.py::ease
  min_tests: 1
- [ ] 2. `recoil` + class TestRecoil
  check: python3 tools/hd-models/tests/test_studio_procedural.py -k TestRecoil
  symbols: tools/hd-models/studio/procedural.py::recoil
  min_tests: 1
- [ ] 3. `collapse` + class TestCollapse
  check: python3 tools/hd-models/tests/test_studio_procedural.py -k TestCollapse
  symbols: tools/hd-models/studio/procedural.py::collapse
  min_tests: 1
- [ ] 4. `brace` + class TestBrace
  check: python3 tools/hd-models/tests/test_studio_procedural.py -k TestBrace
  symbols: tools/hd-models/studio/procedural.py::brace
  min_tests: 1
- [ ] 5. `lunge` + class TestLunge
  check: python3 tools/hd-models/tests/test_studio_procedural.py -k TestLunge
  symbols: tools/hd-models/studio/procedural.py::lunge
  min_tests: 1
- [ ] 6. `rise()`, `sample()`, `check_track()` + class TestSampleAndCheck
  check: bash verify.sh
  symbols: tools/hd-models/studio/procedural.py::check_track
  min_tests: 1
