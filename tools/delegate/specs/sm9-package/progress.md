# Job sm9-package: S9 package checks (UI-free)

Read JOB.md first. One item per session; the check is the line under the item.

## Status
Not started.

## Items
- [ ] 1. `parse_native_check()` + class TestParse
  check: python3 tools/hd-models/tests/test_studio_package.py -k TestParse
  symbols: tools/hd-models/studio/package.py::parse_native_check
  min_tests: 1
- [ ] 2. `check_native()` + class TestNativeCheck
  check: python3 tools/hd-models/tests/test_studio_package.py -k TestNativeCheck
  symbols: tools/hd-models/studio/package.py::check_native
  min_tests: 1
- [ ] 3. `check_budget()` + class TestBudget
  check: python3 tools/hd-models/tests/test_studio_package.py -k TestBudget
  symbols: tools/hd-models/studio/package.py::check_budget
  min_tests: 1
- [ ] 4. `check_identical()` + class TestIdentical
  check: python3 tools/hd-models/tests/test_studio_package.py -k TestIdentical
  symbols: tools/hd-models/studio/package.py::check_identical
  min_tests: 1
- [ ] 5. `check_provenance() + valid_package_name()` + class TestProvenance
  check: python3 tools/hd-models/tests/test_studio_package.py -k TestProvenance
  symbols: tools/hd-models/studio/package.py::check_provenance, valid_package_name
  min_tests: 1
- [ ] 6. `run_s9()` + class TestRunS9
  check: bash verify.sh
  symbols: tools/hd-models/studio/package.py::run_s9
  min_tests: 10
