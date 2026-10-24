# Job sm7-look: S7 look and camera-move rules and checks (UI-free)

Read JOB.md first. One item per session; the check is the line under the item.

## Status
Not started.

## Items
- [ ] 1. `default_look() + normalize_look()` + class TestDefaults
  check: python3 tools/hd-models/tests/test_studio_look.py -k TestDefaults
  symbols: tools/hd-models/studio/look.py::default_look, normalize_look
  min_tests: 1
- [ ] 2. `check_move_count()` + class TestMoveCount
  check: python3 tools/hd-models/tests/test_studio_look.py -k TestMoveCount
  symbols: tools/hd-models/studio/look.py::check_move_count
  min_tests: 1
- [ ] 3. `check_move_range()` + class TestMoveRange
  check: python3 tools/hd-models/tests/test_studio_look.py -k TestMoveRange
  symbols: tools/hd-models/studio/look.py::check_move_range
  min_tests: 1
- [ ] 4. `check_move_values()` + class TestMoveValues
  check: python3 tools/hd-models/tests/test_studio_look.py -k TestMoveValues
  symbols: tools/hd-models/studio/look.py::check_move_values
  min_tests: 1
- [ ] 5. `check_move_extreme()` + class TestMoveExtreme
  check: python3 tools/hd-models/tests/test_studio_look.py -k TestMoveExtreme
  symbols: tools/hd-models/studio/look.py::check_move_extreme
  min_tests: 1
- [ ] 6. `check_brightness()` + class TestBrightness
  check: python3 tools/hd-models/tests/test_studio_look.py -k TestBrightness
  symbols: tools/hd-models/studio/look.py::check_brightness
  min_tests: 1
- [ ] 7. `run_s7()` + TestRunS7
  check: bash verify.sh
  symbols: tools/hd-models/studio/look.py::run_s7
  min_tests: 14
