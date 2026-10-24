# Job sm9b-build: S9 build step (headless, injectable runner)

Read JOB.md first. One item per session; the check is the line under the item.

## Status
Not started.

## Items
- [ ] 1. `flags()` + class TestFlags
  check: python3 tools/hd-models/tests/test_studio_build.py -k TestFlags
  symbols: tools/hd-models/studio/build.py::flags
  min_tests: 1
- [ ] 2. `command()` + class TestCommand
  check: python3 tools/hd-models/tests/test_studio_build.py -k TestCommand
  symbols: tools/hd-models/studio/build.py::command
  min_tests: 1
- [ ] 3. `hash_tree()` + class TestHashTree
  check: python3 tools/hd-models/tests/test_studio_build.py -k TestHashTree
  symbols: tools/hd-models/studio/build.py::hash_tree
  min_tests: 1
- [ ] 4. `real_runner()` + class TestRunner
  check: python3 tools/hd-models/tests/test_studio_build.py -k TestRunner
  symbols: tools/hd-models/studio/build.py::real_runner
  min_tests: 1
- [ ] 5. `build_twice()` + class TestBuildTwice
  check: python3 tools/hd-models/tests/test_studio_build.py -k TestBuildTwice
  symbols: tools/hd-models/studio/build.py::build_twice
  min_tests: 1
- [ ] 6. `run_build_s9()` + class TestRunBuildS9
  check: bash verify.sh
  symbols: tools/hd-models/studio/build.py::run_build_s9
  min_tests: 4
