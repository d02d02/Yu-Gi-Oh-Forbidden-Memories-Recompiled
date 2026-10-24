# Job sm5-clips: S5 clip statistics and checks (UI-free)

Read JOB.md first. One item per session; the check is the line under the item.

## Status
Not started.

## Items
- [ ] 1. `loop_gap()` + class TestLoopGap
  check: python3 tools/hd-models/tests/test_studio_clips.py -k TestLoopGap
  symbols: tools/hd-models/studio/clips.py::loop_gap
  min_tests: 1
- [ ] 2. `root_drift()` + class TestRootDrift
  check: python3 tools/hd-models/tests/test_studio_clips.py -k TestRootDrift
  symbols: tools/hd-models/studio/clips.py::root_drift
  min_tests: 1
- [ ] 3. `speed_peak()` + class TestSpeedPeak
  check: python3 tools/hd-models/tests/test_studio_clips.py -k TestSpeedPeak
  symbols: tools/hd-models/studio/clips.py::speed_peak
  min_tests: 1
- [ ] 4. `bone_stretch()` + class TestBoneStretch
  check: python3 tools/hd-models/tests/test_studio_clips.py -k TestBoneStretch
  symbols: tools/hd-models/studio/clips.py::bone_stretch
  min_tests: 1
- [ ] 5. `clip_bbox()` + class TestBbox
  check: python3 tools/hd-models/tests/test_studio_clips.py -k TestBbox
  symbols: tools/hd-models/studio/clips.py::clip_bbox
  min_tests: 1
- [ ] 6. `check_loop/drift/speed/stretch` + class TestChecks
  check: python3 tools/hd-models/tests/test_studio_clips.py -k TestChecks
  symbols: tools/hd-models/studio/clips.py::check_loop, check_drift, check_speed, check_stretch
  min_tests: 4
- [ ] 7. `run_s5()` + class TestRunS5
  check: bash verify.sh
  symbols: tools/hd-models/studio/clips.py::run_s5
  min_tests: 10
