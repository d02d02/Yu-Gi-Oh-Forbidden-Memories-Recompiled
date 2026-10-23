# Job sm5-placement: S4 size and placement maths (UI-free)

Read JOB.md first. One item per session; the check is the line under the item.

## Status
Not started.

## Items
- [ ] 1. `fit()` in studio/placement.py + class TestFit
  check: python3 tools/hd-models/tests/test_studio_placement.py -k TestFit
- [ ] 2. `footprint_ratio()` + class TestFootprintRatio
  check: python3 tools/hd-models/tests/test_studio_placement.py -k TestFootprintRatio
- [ ] 3. `check_footprint()` + class TestCheckFootprint
  check: python3 tools/hd-models/tests/test_studio_placement.py -k TestCheckFootprint
- [ ] 4. `check_ground()` + class TestCheckGround
  check: python3 tools/hd-models/tests/test_studio_placement.py -k TestCheckGround
- [ ] 5. `check_uniform_scale()` + class TestUniform
  check: python3 tools/hd-models/tests/test_studio_placement.py -k TestUniform
- [ ] 6. `run_s4()` + class TestRunS4 and one README row mentioning `studio/placement.py`
  check: bash verify.sh
