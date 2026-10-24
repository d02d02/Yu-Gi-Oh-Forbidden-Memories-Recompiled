# Job sm6-timemap: S6 time-map maths and checks (UI-free)

Read JOB.md first. One item per session; the check is the line under the item.

## Status
Not started.

## Items
- [ ] 1. `default_map()` + `segments()` + class TestSegments
  check: python3 tools/hd-models/tests/test_studio_timemap.py -k TestSegments
- [ ] 2. `check_monotonic()` + class TestMonotonic
  check: python3 tools/hd-models/tests/test_studio_timemap.py -k TestMonotonic
- [ ] 3. `check_stretch()` + class TestStretch
  check: python3 tools/hd-models/tests/test_studio_timemap.py -k TestStretch
- [ ] 4. `row_to_clip()` / `clip_to_row()` + class TestMapping
  check: python3 tools/hd-models/tests/test_studio_timemap.py -k TestMapping
- [ ] 5. `contact_for()` + class TestContactFor
  check: python3 tools/hd-models/tests/test_studio_timemap.py -k TestContactFor
- [ ] 6. `check_strike()` + class TestCheckStrike
  check: python3 tools/hd-models/tests/test_studio_timemap.py -k TestCheckStrike
- [ ] 7. `suggest_point()` + `run_s6()` + TestRunS6, README row
  check: bash verify.sh
