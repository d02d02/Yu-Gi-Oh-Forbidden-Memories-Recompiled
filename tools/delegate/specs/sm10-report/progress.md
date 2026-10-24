# Job sm10-report: S9 Export report (headless)

Read JOB.md first. One item per session; the check is the line under the item.

## Status
Not started.

## Items
- [ ] 1. `stage_status()` + class TestStageStatus
  check: python3 tools/hd-models/tests/test_studio_report.py -k TestStageStatus
  symbols: tools/hd-models/studio/report.py::stage_status
  min_tests: 1
- [ ] 2. `stage_lines()` + class TestStageLines
  check: python3 tools/hd-models/tests/test_studio_report.py -k TestStageLines
  symbols: tools/hd-models/studio/report.py::stage_lines
  min_tests: 1
- [ ] 3. `summary_table()` + class TestSummaryTable
  check: python3 tools/hd-models/tests/test_studio_report.py -k TestSummaryTable
  symbols: tools/hd-models/studio/report.py::summary_table
  min_tests: 1
- [ ] 4. `build_lines()` + class TestBuildLines
  check: python3 tools/hd-models/tests/test_studio_report.py -k TestBuildLines
  symbols: tools/hd-models/studio/report.py::build_lines
  min_tests: 1
- [ ] 5. `runs_lines()` + class TestRunsLines
  check: python3 tools/hd-models/tests/test_studio_report.py -k TestRunsLines
  symbols: tools/hd-models/studio/report.py::runs_lines
  min_tests: 1
- [ ] 6. `render()` + class TestRender
  check: bash verify.sh
  symbols: tools/hd-models/studio/report.py::render
  min_tests: 3
