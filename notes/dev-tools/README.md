# Dev tools: strategy docs (snapshot)

Versioned snapshot, taken 2026-10-13, of the working copy kept outside git at
`hacking\shared\yfm-notes\dev-tools\` (OneDrive; `C:\Users\mdahh\.claude\shared\yfm-notes` is a junction to it).
**The shared folder is the working copy**: it also holds the evidence (screenshots of the disc, logs) and the recipe
copies, which are not committed. Refresh this snapshot with a copy of `0*.md` when the shared ones change materially.

| File | Answers |
|---|---|
| `01-state-of-the-art.md` | What exists, where, measured speeds |
| `02-gaps-and-roadmap.md` | Limitations, ranked improvements, the `situation()` design and what was built |
| `03-playbook.md` | Per use case: which tool, exact recipe, traps |
| `04-testing-strategy.md` | Test levels, determinism, pre-flight checklist, test data |
| `05-release-strategy.md` | Gates and checklists per release type |
| `06-run-report-2026-10-13.md` | What was run, results |

The tools themselves are in `tools/pc/rigs/` (`rigkit.py`, `pxkit.py`, `situations/`) and `mods/camera-pin/`.
