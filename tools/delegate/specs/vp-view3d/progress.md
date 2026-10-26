# Job vp-view3d: Studio preview math (headless)

Read JOB.md first. One item per session; the check is the line under the item.

## Status
Not started.

## Items
- [ ] 1. `orbit_view()` + class TestOrbit
  check: python3 tools/hd-models/tests/test_studio_view3d.py -k TestOrbit
  symbols: tools/hd-models/studio/view3d.py::orbit_view
  min_tests: 1
- [ ] 2. `project()` + class TestProject
  check: python3 tools/hd-models/tests/test_studio_view3d.py -k TestProject
  symbols: tools/hd-models/studio/view3d.py::project
  min_tests: 1
- [ ] 3. `fit_camera()` + class TestFit
  check: python3 tools/hd-models/tests/test_studio_view3d.py -k TestFit
  symbols: tools/hd-models/studio/view3d.py::fit_camera
  min_tests: 1
- [ ] 4. `wire_edges()` + class TestWire
  check: python3 tools/hd-models/tests/test_studio_view3d.py -k TestWire
  symbols: tools/hd-models/studio/view3d.py::wire_edges
  min_tests: 1
- [ ] 5. `bone_segments()` + class TestBones
  check: python3 tools/hd-models/tests/test_studio_view3d.py -k TestBones
  symbols: tools/hd-models/studio/view3d.py::bone_segments
  min_tests: 1
- [ ] 6. `vertex_weight()` + class TestWeights
  check: python3 tools/hd-models/tests/test_studio_view3d.py -k TestWeights
  symbols: tools/hd-models/studio/view3d.py::vertex_weight
  min_tests: 1
- [ ] 7. `depth_order()` + class TestDepth
  check: python3 tools/hd-models/tests/test_studio_view3d.py -k TestDepth
  symbols: tools/hd-models/studio/view3d.py::depth_order
  min_tests: 1
