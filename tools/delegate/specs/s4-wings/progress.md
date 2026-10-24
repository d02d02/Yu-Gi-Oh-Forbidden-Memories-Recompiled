# Job s4-wings: S4 footprint measures the body, not the wings

Read JOB.md first. One item per session; the check is the line under the item.

## Status
Not started.

## Items
- [ ] 1. `body_extents(model, fit)` helper in placement.py (lower-half vertices, fallback full), with tests on a synthetic winged glb
  check: python tools/hd-models/tests/test_studio_placement.py
- [ ] 2. `run_s4` uses body extents for `check_footprint`, adds `body_extent_x/z` to "fit", appends the wings note when full ratio > 1.5x body ratio; tests for no-warn winged, warn too-wide body, note text
  check: python tools/hd-models/tests/test_studio_placement.py
- [ ] 3. One line in notes/studio/studio-view.md under S4 footprint saying the check measures the lower-half body
  check: grep -q "lower half" notes/studio/studio-view.md
