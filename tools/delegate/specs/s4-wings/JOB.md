# Job s4-wings

## Goal
S4 footprint check (`tools/hd-models/studio/placement.py`, `check_footprint`, `run_s4`) compares the FULL model extents with the card footprint proxy (191 x 236). A winged dragon at extent 600 always warns because of the wingspan. Decision (supervisor): measure the BODY footprint, keep the full extent as extra info.

## Rule
- Body footprint = x/z extents of the model's vertices whose y is <= lo_y + 0.5*(hi_y - lo_y) (lower half of the height), after the same fit scale `fit()` applies. If the lower half has no vertices, fall back to the full extent.
- `check_footprint` keeps its signature and thresholds (None when r <= 1.10, else a "warn", never "fail"), but `run_s4` passes it the BODY extents. When the full-extent ratio is more than 1.5x the body ratio, append to the message: " Wings or limbs excluded; full span is N% of the card footprint." (N = round(full ratio*100)).
- `run_s4` result "fit" gains keys `body_extent_x`, `body_extent_z` (same units as `extent_x`/`extent_z`). Existing keys unchanged.

## Facts
- Python is `python`. LF endings. Do not push. Stdlib unittest; tests run as `python tools/hd-models/tests/test_studio_placement.py`.
- Vertex access: read `class Model` in `tools/hd-models/studio/audit.py` with `grep -n "self\." ` (at most 40 lines) to find how positions are exposed; do NOT edit audit.py (protected). If positions are not exposed, compute them in placement.py from the Model's glTF accessors using helpers already in audit.py; if impossible, write BLOCKED with the reason.
- Tests build a tiny synthetic glb in the existing test file's style (read the top 40 lines of tests/test_studio_placement.py first): a body box plus a wide thin "wing" slab in the upper half must give no footprint warning when the body fits, and a warning when the body is too wide.

## Hard rules
- Write files with LF endings only (no CRLF conversion of any file; never run a bulk reformat or `git add -A` of untouched files). Touch only the files in Limits.
- The code change is the point: an item is not done until the function exists and the new tests exercise it.

## Limits
Edit only: `tools/hd-models/studio/placement.py`, `tools/hd-models/tests/test_studio_placement.py`, `notes/studio/studio-view.md` (one line in the S4 footprint description). Anything else: write BLOCKED.

## Acceptance
`bash verify.sh` passes. Final message: files changed, functions touched, open problems.
