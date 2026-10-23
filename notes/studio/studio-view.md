# Studio view

Page pattern: **Split Pane**. Left = stage list (S0-S9), right = the open stage. One model open at a time. Inputs: feasibility note sec. 2-3. Detail below is complete for S4, S5, S6; the other stages are outlined at the end and are next.

## 1. Anatomy (same for every stage)

```
[Models]  Dragon  C5 winged creature  recipe saved        [Export report] [Open in Blender] [Remove model]
+--------+----------------------------------------------------------------+
| S0 ok  | Stage title                          gate line          [state]  |
| S1 !   | +------------------------------------------------------------+ |
| S2 ok  | |  ENGINE VIEWPORT (game window frames)                      | |
| S3 ok  | |                                                            | |
| S4 !   | +-- transport: play/pause, act, speed, scrub  | overlays ----+ |
| S5 x   | [stage-specific strip: act table / time map / ruler]           |
| S6 .   | +-- Checks --------------------+ +-- Knobs ------------------+  |
| ...    | | state, text, fix link        | | labelled controls        |  |
|        | +------------------------------+ +---------------------------+ |
|        | [Previous] [Reset to auto]            [ack warnings] [Next]    |
+--------+----------------------------------------------------------------+
```

* **Rail**: four group headings (Prepare S0-S3, Fit S4-S6, Judge S7-S8, Ship S9; headings are labels, not gates), then id, name, one-word subtitle, state dot per stage. Arrow keys move, Enter moves focus to the first knob. Clicking a later stage than the first non-pass stage is allowed (looking is free); Next is what is gated.
* **Header**: model name (inline rename, Enter saves), category chip (opens the category picker, which re-applies presets only to stages still at auto), recipe state (`saved`, `unsaved changes`, `building`).
* **Viewport**: always the engine. Transport (play/pause, act, speed 0.25x-2x, scrub by clip frame *(new)*) plus overlay toggles. Overlays offered per stage, not all everywhere.
* **Checks**: one row per check: state chip, plain sentence with the measured number, and a fix line that names a knob (click focuses it) or a hand-off. Rows sorted fail, warn, pass. Pass rows collapse to one line when there are more than four.
* **Knobs**: grouped, labelled (visible label on every control), with units and the auto value shown as a hint. A knob changed from auto shows a dot and a "back to auto" icon.
* **Footer**: Previous, Reset to auto (this stage only, says what changed, one undo), Next. Next label is verb-first; the last stage reads "Build package".

## 2. State model

Per stage: `todo` (never run) | `pass` | `warn` | `fail` | `stale`.

* A stage's checks run when it is opened and after every knob change, debounced 300 ms, as a subprocess polled from Tk (no threads in the editor).
* **Dependencies** (an edit in the left stage marks the right ones `stale`, keeping their knob values):
  `S1 -> S2 -> S4, S5`; `S5 -> S6`; `S4, S5, S6, S3 -> S7 -> S8 -> S9`. S3 is independent of S2. Category change marks everything except S0 stale.
* `stale` is shown as a hollow dot. Opening a stale stage re-runs its checks; if none of its inputs actually changed in value, it returns to its old state silently.
* **Acknowledgement** of a warn is stored as `(check id, measured value)`; if the value changes, the ack is dropped and the stage returns to "needs acknowledgement".
* Build needs S1-S8 `pass` or acknowledged `warn`; S9 itself only adds the packaging checks.
* Going back: free. Nothing is lost; later stages go `stale`, not `todo`.

## 3. Interaction rules for the viewport

* The viewport is read-and-point: the person points (drag a marker, click a bone, scrub) and numbers update in the knobs; typing a number moves the marker. Every viewport gesture has a keyboard equivalent through its knob.
* Gestures that edit: drag the **origin marker** on the ground plane (S4), drag **time-map points** on the ruler (S6), click a **bone** to pick it for a field that asks for a bone (S2, S6 strike joint). Nothing is edited by dragging the mesh itself.
* Camera: presets (field, arena, side, top, free orbit *(new)*). The preset used by a stage's checks is shown in the viewport tag so a number never refers to an unseen view.
* The viewport tag always says: model, act, clip frame, camera preset, and "paused" or the speed.

## 4. Stage detail

### S4 Size and placement

**Job**: make the model the right size and put its origin where the game expects, for this class.
**Viewport**: camera `side` by default (switch to `field` / `arena` / `top`). Overlays: BLS ghost (373 tall, root 159), card footprint grid, neighbour monster at its field offset, ground line, origin and root markers, bounding box. The fit pose is selectable: `idle`, `as exported`, `widest pose of the attack` (reveals the worst case).

**Knobs** (recipe keys in brackets)
| Knob | Control | Auto | Notes |
|---|---|---|---|
| Fit by `[size.mode]` | segmented: Height / Extent / Percent | by category: C1-C3, C7 Height; C4-C6, C8 Extent | precedence in the converter stays percent > extent > root-height > height |
| Target `[size.value]` | number (game units, or %) | 373 / footprint width | label changes with the mode |
| Fit pose `[size.fit_pose]` | select | idle | C5 offers `wings folded` when a clip pose is tagged so |
| Root height `[size.root_height]` | number | 159 for humanoids; body centre for others | marker follows |
| Origin height `[size.origin_height]` | number | 159 / support-area centre | |
| Origin offset x,z `[size.origin_offset]` | two numbers + drag handle | centred on the feet or support area | |
| Ground offset `[size.ground_offset]` | number | 0; 40 for floaters (C5 flying, C6) | shown as a gap under the model |
| Scale % `[model.scale]`, Offset `[model.offset]` | integer, 3 numbers | 100, 0 | the two `model.json` fields; integers only (the game's JSON reader) |

**Checks**
| id | Fails/warns when | Fix line |
|---|---|---|
| `S4.footprint` | warn if the chosen fit pose exceeds the footprint by >10%; fail by >60% | "Fit with a smaller pose, lower the scale to N%, or switch to Extent." |
| `S4.footprint-attack` | warn if the widest attack pose exceeds 1.5x the footprint | "Lower scale or accept clipping into the neighbour." |
| `S4.head-clearance` | fail if the head is cut by the near plane in the arena preset | "Lower the height or raise camera distance in S7." |
| `S4.ground` | warn if the lowest idle point is more than 8 units off the ground (no floater flag) | "Set ground offset to N or mark the model as floating." |
| `S4.neighbour` | warn if the model overlaps the neighbour's footprint at its field offset | "Lower scale or change the offset." |
| `S4.uniform` | fail if the node tree carries non-uniform scale after the audit | "Re-export from Blender with applied scale." |

**Gate**: no fail; every warn acknowledged. **Reset to auto** restores category defaults and drops the ack.
**Needs** *(new)*: engine commands to load a package/recipe, set pose, camera preset, overlays (ghost, grid, markers, bbox), read back bounding boxes (see `engine-needs.md`). The BLS silhouette for the ghost comes from the disc and so needs the disc (or a stored outline).
**Open**: where the card footprint's real dimensions come from (Q4 in `open-questions.md`).

### S5 Clips

**Job**: say which clip plays each act, fix loops, and fill gaps.
**Layout**: the **act table** replaces the strip: nine rows, one per disc row, then a detail pane for the selected act under the viewport.

| Act (disc rows) | Source | Clip | Length | Flags |
|---|---|---|---|---|
| Idle (0, 1) | asset / library / procedural / Blender import | name | frames | loop gap %, drift, speed peak |
| Enter (2) | | | | |
| Attack (3) | | | | |
| Attack 2 (4, second guardian star) | | | | |
| Hit (5) | | | | |
| Destroyed (6) | | | | |
| Win (7) | | | | |
| Guard (8) | | | | |

Rows with no source show today's fallback in grey ("plays Hit", "plays Idle") so a gap is visible rather than silent. Clip count limit shown as `n of 16` over the table.

**Source chooser** (slide-over, 2-4 fields, under ten seconds): tabs *Asset clips* (list with length, drift, loop gap, a one-line preview), *Library* *(new)* (retargeted humanoid clips; only offered when the model is C1-C3), *Procedural* *(new)* (a type per act with its parameters), *Blender import* (file picker, adds a clip). Confirm button reads "Use this clip".

**Detail pane knobs for the selected act**
| Knob | Control | Auto |
|---|---|---|
| Source clip `[acts.<act>.source]` | read-only name + "Change source" | by name, then by motion match |
| Trim in/out `[acts.<act>.trim]` | two numbers + range handles on the mini ruler | whole clip |
| Speed `[acts.<act>.speed]` | number | 1.0 (S6 owns stretch; this is pre-stretch) |
| Loop `[acts.<act>.loop]` | toggle | on for idle/guard, off otherwise |
| Close loop `[acts.<act>.close_loop]` | toggle + frames | on when gap > threshold |
| Remove root travel `[acts.<act>.root_motion]` | select: remove x/z (keep y) / keep all | remove x/z |
| Mirror `[acts.<act>.mirror]` | toggle | off |
| Crossfade frames `[acts.<act>.crossfade]` | number | 6 |
| Procedural params | per type (see below) | by type |

**Procedural types**: hit = recoil distance + time along facing; destroyed = collapse style (fall, sink, tip) + scale-fade; guard = brace (crouch %, flare %); win = bob height or raise; attack = anticipation, lunge distance, recovery; enter = rise or slide from a side. Each has 2-4 numbers and a live preview.

**Mini graphs for the selected clip**: root drift (x/z over time), joint speed peak, loop gap per bone region. Each is a sparkline with the threshold drawn.

**Checks**
| id | Fails/warns when | Fix line |
|---|---|---|
| `S5.missing-act` | fail for idle; warn for others (a fallback plays) | "Choose a clip, a library clip, or a procedural act." |
| `S5.travel-clip` | fail when an attack clip's root drift exceeds 25% of the model height | "This clip travels (a run). Pick another or use a procedural lunge." |
| `S5.loop` | warn when a looped clip's first/last pose gap > 3% of height, fail > 10% | "Turn on close loop (N frames)." |
| `S5.root-drift` | warn when a loop drifts more than 5% | "Remove root travel." |
| `S5.stretch-bone` | warn when a bone's length changes > 8% in the clip | "Clip does not suit this rig; try a retarget or another clip." |
| `S5.count` | fail beyond 16 clips | "Drop unused clips." |
| `S5.extras` | warn for extra bones (C2) that no clip moves | "Choose rigid, follow a bone, or bake in Blender." |

**Gate**: every act has a source (fallbacks allowed with a warn), loops close.
**Needs** *(new)*: play any clip by name at any phase, pause and scrub (today `MEMORIES_NATIVE_CLIP` is read once); clip statistics returned as data (today printed); retarget engine and procedural clips on the converter side.
**Hand-offs**: "Author a clip in Blender" opens Blender with the current file and waits, like the header button.

### S6 Timing against the disc

**Job**: make anticipation, strike and recovery land where the disc's effect, hit and damage happen.
**Background**: the native clip is stretched once over the disc row; today only the strike warp breaks that. The studio adds a time map per act *(new)*.
**Layout**: the **time-map editor** under the viewport: two stacked tracks for the selected act.

```
disc row     |0 ---------------------------------------- N frames|
                 ^ disc contact frame (from ground truth)
clip         |0 ------ anticipation -- STRIKE -- recovery --- M |
points         o--------o--------------o----------------------o     (draggable)
stretch      0.9x       1.6x           0.7x
```

* Points pair a clip frame with a position on the disc row. Default: first and last point only (uniform stretch). Add a point by double-click or `+`; delete with Delete; move with arrows (1 frame; Shift = 5). Dragging a point left or right never reorders points (clamped between neighbours).
* **Strike marker(s)** (up to 4, as the game allows): auto-placed from the fastest tracked joint. The joint is picked in the viewport (click a bone) or the select. The marker is a red line on the clip track; the disc's contact frame is a green line on the disc track. The gap between them is printed in game frames.
* Stretch factor per segment shown under the track, coloured against the allowed range (default 0.6x-1.8x).
* The viewport plays the act on the **disc clock**: scrub the disc row and the model shows the stretched pose; with a "BLS compare" overlay *(new)* the disc's own model plays the same act beside it.

**Knobs**
| Knob | Control | Auto |
|---|---|---|
| Time map points `[acts.<act>.timemap]` | the editor + a table of (clip frame, row phase) | two points |
| Strike joints `[acts.<act>.strike_joints]` | click bone / select, up to 4 | fastest hand/weapon joint; none for non-attacks |
| Strike frames `[acts.<act>.strike]` | numbers; "snap to joint peak" button | from the joint |
| Hold last frame `[acts.<act>.hold]` | number | 0 |
| Speed range `[timing.stretch_range]` | two numbers | 0.6, 1.8 |

**Checks**
| id | Fails/warns when | Fix line |
|---|---|---|
| `S6.stretch` | warn outside the range, fail beyond 0.3x-3x | "Trim the clip or add a time-map point." |
| `S6.strike-vs-contact` | warn when the strike is more than 3 frames from the disc's contact frame, fail beyond 10 | "Drag the red marker onto the green line, or add a time-map point." |
| `S6.no-reference` | info (not a warn) when the disc has no measured contact frame for this act/class; the disc track shows "No disc reference", no green line is drawn, and `S6.strike-vs-contact` is not run | "Strike timing is unchecked here; measure this act on the disc to enable the check (see engine-needs D1)." |
| `S6.pop` | warn when the idle restart has a visible pose jump | "Close the loop in S5." |
| `S6.monotonic` | fail when time-map points are not strictly increasing | "Move a point." |

**Gate**: every attack has a strike frame; stretch in range or acknowledged.
**Needs** *(new)*: disc ground truth per act and class (row lengths, contact frames); a scrub-by-row-phase engine command; the time-map applied in the render-side sampler (D2: pure C, captured inputs only, so a map is data the sampler reads); BLS compare overlay.
**No ground truth**: decided (Q5): show empty, never guess.

## 5. Outlined stages (to detail next)

| Stage | Detail still needed |
|---|---|
| S0 Intake | first-run layout, class detection explanation ("why C5"), multi-skin, mesh include/drop UI, Blender conversion path, licence capture rules |
| S1 Audit | bind-vs-rest overlay and heat-map spec, per-region report, bone merge preview, what "re-pose" in Blender returns |
| S2 Rig | bone tree widget, humanoid map editor, extras rules, picking bones in the viewport |
| S3 Materials | atlas preview, per-material override flow, what the engine draws (emissive, vertex colour) to confirm |
| S7 Look | lighting compare against BLS, camera shot editor (field/arena shots) |
| S8 Validate | scripted run list, contact sheet/video outputs, pass criteria |
| S9 Package | build progress, native_check output, byte-identity check, where the package lands |
| Cross-stage | recipe versioning, undo/redo scope, multi-card use, Blender round trip, error screens (crash of the engine process, missing disc) |
