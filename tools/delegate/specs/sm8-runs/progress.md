# Job sm8-runs: S8 run list, marks and checks (UI-free)

Read JOB.md first. One item per session; the check is the line under the item.

## Status
Not started.

## Items
- [ ] 1. `run_rows()` + class TestRows
  check: python3 tools/hd-models/tests/test_studio_runs.py -k TestRows
  symbols: tools/hd-models/studio/runs.py::run_rows
  min_tests: 1
- [ ] 2. `make_mark() + owning_stage()` + class TestMarks
  check: python3 tools/hd-models/tests/test_studio_runs.py -k TestMarks
  symbols: tools/hd-models/studio/runs.py::make_mark, owning_stage
  min_tests: 1
- [ ] 3. `row_status() + status_table()` + class TestStatus
  check: python3 tools/hd-models/tests/test_studio_runs.py -k TestStatus
  symbols: tools/hd-models/studio/runs.py::row_status, status_table
  min_tests: 1
- [ ] 4. `check_coverage()` + class TestCoverage
  check: python3 tools/hd-models/tests/test_studio_runs.py -k TestCoverage
  symbols: tools/hd-models/studio/runs.py::check_coverage
  min_tests: 1
- [ ] 5. `check_problem()` + class TestProblem
  check: python3 tools/hd-models/tests/test_studio_runs.py -k TestProblem
  symbols: tools/hd-models/studio/runs.py::check_problem
  min_tests: 1
- [ ] 6. `check_stale() + check_disc()` + class TestStaleDisc
  check: python3 tools/hd-models/tests/test_studio_runs.py -k TestStaleDisc
  symbols: tools/hd-models/studio/runs.py::check_stale, check_disc
  min_tests: 1
- [ ] 7. `run_s8()` + class TestRunS8
  check: bash verify.sh
  symbols: tools/hd-models/studio/runs.py::run_s8
  min_tests: 12
