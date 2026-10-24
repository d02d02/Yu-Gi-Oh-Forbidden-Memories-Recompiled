# Job <id>: <one-line goal>

Read JOB.md first (goal, pasted facts, limits, acceptance). One item per session; the check is the line under the item.
Size an item so one session finishes it in about 10 minutes: one function or one test class, not a module.

## Status
Not started.

## Items
- [ ] 1. <small unit: one function or one test class>
  check: <command that exits 0 only when the unit is really done>
  symbols: <path::name, name, ...>   (optional; each needs a def/class of that name in that file; checked by the loop)
  min_tests: <N>                     (optional; the check must report at least N tests run)
- [ ] 2. <next unit>
  check: <command>
