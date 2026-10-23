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

### S0 Intake and triage

**Job**: load the file, learn what it is, record who made it, choose the category. Needs no engine (viewport shows a static preview of the file, E7 not required).
**Entry**: "Start from .glb" opens S0 with the file already read; the Studio never shows an empty S0 except after "Replace source".
**Layout**: the viewport shows the model in its exported pose with the bounding box; beside it a **contents table** (meshes, skins, clips, materials, each with counts and an include checkbox).

**Knobs**
| Knob | Control | Auto |
|---|---|---|
| Category `[model.category]` | select C1-C8 with a one-line expectation under it ("good", "decent", "moving statue") | detected |
| Source file `[source.path]` | read-only + "Replace source" (keeps the recipe; all later stages go stale) | the picked file |
| Author, Licence, Source URL `[meta.author/licence/url]` | three text fields, visible labels | read from glb `asset` extras when present, else empty |
| Attribution required `[meta.attribution]` | toggle + text | on when the licence text contains BY |
| Skin `[source.skin]` | select (only if several) | the skin with most bound vertices |
| Included meshes `[source.meshes]` | checkbox per mesh | all except names matching LOD, proxy, collision, helper |
| Card id(s) `[model.cards]` | chips, can stay empty until S9 | empty |

**"Why this category" panel** (collapsed by default, one click): lists the evidence used: skeleton shape, humanoid profile match %, limb count, wing-like chains, skinned or not, clip count. A confidence figure. Changing the category re-applies presets to stages still at auto and marks the rest stale.

**Checks**
| id | Fails/warns when | Fix line |
|---|---|---|
| `S0.load` | fail if the file does not parse or has no mesh | "This file did not open: <reason>. Re-export as glb 2.0, or convert .blend/.fbx through Blender." |
| `S0.format` | info for `.blend` / `.fbx`: Blender conversion runs first | "Converting through Blender (button: Convert)." |
| `S0.licence` | fail if licence is empty | "Add the licence so it is stored in the package and shown in the Library." |
| `S0.attribution` | warn if attribution is required but the author is empty | "Add the author name." |
| `S0.category-confidence` | warn if confidence < 60% | "Check the evidence panel and choose the category." |
| `S0.skins` | warn if several skins and none chosen | "Choose the skin to use." |

**Gate**: category chosen, licence present.
**Needs**: C1 (findings as data), detection heuristics in the converter *(new, extracted from `convert`)*; Blender conversion button *(new)*.
**Sample for users**: the mannequin is the built-in sample ("Open sample") so a first run can see a finished model.

### S1 Mesh and skin audit

**Job**: tell the person, before anything else, whether the asset is sound enough, and where it is not.
**Viewport**: engine not required for the first measures; the bind-vs-rest overlay *(new)* needs the converter's skinning in Python (no engine), so S1 can run without the disc. Camera `front`; overlays: bones, weight heat map for the picked bone, bind-vs-rest distance heat map.

**Layout**: under the viewport a **report table** by region (head, torso, left arm, right arm, hands, legs, feet, wings, tail, other), columns: vertices, worst drift %, weight issues, verdict dot. Clicking a row frames that region and selects its worst vertices' bone in the weight heat map.

**Knobs**
| Knob | Control | Auto |
|---|---|---|
| Fix axes and units `[audit.fix_axes]` | toggle | on (y up, metres) |
| Bone limit action `[audit.bone_limit]` | select: merge lightest / drop listed / fail | merge lightest, with a preview list of what merges |
| Merged bones list `[audit.merge]` | list with checkboxes; unchecking keeps a bone and forces another to merge | computed |
| Weight smoothing `[audit.smooth_passes]` | number | 0 (1 when issues found) |
| Normalise / limit to 4 `[audit.normalise]` | toggle | on |
| Drop stray parts `[audit.drop_parts]` | list of detached islands with checkboxes | none |
| Mirror `[audit.mirror]` | select none / x | none |

**Checks**
| id | Fails/warns when | Fix line |
|---|---|---|
| `S1.bind-vs-rest` | warn if frame 0 of any clip moves a region > 4% of height from the bind mesh; fail > 12% | "The mesh and rig rest in different poses (region). Re-pose in Blender, or choose another rig." |
| `S1.bones` | fail > 128 after merge | "Too many bones. Allow more merging, or drop the tail/hair chain." |
| `S1.merge` | warn when bones were merged and weight moved > 5% on one region (wings) | "Review the merged list; keep the wing bones and merge elsewhere." |
| `S1.weights` | warn: unweighted vertices > 0; fail > 1% | "Fix weights in Blender (button), or let auto-smooth fill them." |
| `S1.influences` | info: vertices cut from 5+ to 4 influences, count | "" |
| `S1.scale` | warn: node scale 0.01 or 100 or non-uniform | "Apply scale on export, or accept the auto fix." |
| `S1.normals` | warn: flipped normals > 1% | "Fix in Blender or turn on auto-flip." |
| `S1.size` | warn: triangle count or texture memory beyond the budget | "Reduce in Blender (decimate)." |

**Gate**: no fail; warns acknowledged.
**Hand-off**: "Open in Blender" passes the current file; on return the studio re-reads, re-runs S1 and S2 only, and marks the later stages stale. A banner states "Blender returned a new file" with a diff of counts.
**Needs**: C8 bind-vs-rest report, C1; the audit measurements as data. No engine needed.

### S2 Rig

**Job**: tell the game which bone is the body root, which bones are which limbs (humanoids), which bones ride others, and which bone strikes.
**Viewport**: engine or Python preview; the bone overlay with colours by role. **Bone tree** at the side (replaces the checks column on narrow windows): expand/collapse, search, role badge per bone.

**Interactions**: click a bone in the viewport or the tree to select it; the knob panel shows its role, parent, weight count and "used by" (root, foot, strike, follow). Assigning a role to the selected bone: a select (`Root`, `Left foot`, `Strike`, `Extra: rigid`, `Extra: follow …`, `Cut`). Humanoid map editor (C1-C3): a stick-figure grid of the required slots (hips, spine, head, arms, hands, legs, feet); each slot shows the mapped bone and turns green when filled; "Auto map" fills by name then by position.

**Knobs**
| Knob | Control | Auto |
|---|---|---|
| Root bone `[rig.root]` | pick in viewport or select | pelvis (biped), body centre otherwise |
| Humanoid map `[rig.humanoid]` | slot grid | auto map; "non-humanoid" toggle for C4-C8 |
| Foot joints `[rig.feet]` | multi-pick or None | detected for biped/quadruped; None for floaters |
| Strike bone default `[rig.strike]` | pick | head/hand by category |
| Extras `[rig.extras]` | list: bone -> rigid / follow BONE at % / cut | rigid |
| Follow rules `[rig.follow]` | "A copies B at 60%" rows | none |

**Checks**
| id | Fails/warns when | Fix line |
|---|---|---|
| `S2.chains` | fail if a bone has no path to the root | "Reconnect in Blender, or cut the bone." |
| `S2.map` | fail for C1-C3 if a required slot is empty | "Pick a bone for <slot>, or switch to non-humanoid." |
| `S2.root-side` | warn if the root is not near the body centre (> 15% off) | "Choose a bone closer to the pelvis." |
| `S2.reversed-scale` | fail if a bone has negative scale | "Fix in Blender (apply scale)." |
| `S2.extras-weights` | warn if an extra bone carries no weights | "Nothing will move; cut it or paint weights." |

**Gate**: root chosen; map complete or non-humanoid confirmed.
**Needs**: bone/root/feet detection extracted from `convert` as data (C1); picking bones in the engine viewport needs E6 (joint positions); with Python preview it needs none.

### S3 Materials and textures

**Job**: make sure the model looks textured as it will in the game and nothing is silently dropped.
**Viewport**: engine (the only way to see what the game draws). Overlays: UV density, atlas view (a second view showing the packed atlas with material outlines).

**Knobs**
| Knob | Control | Auto |
|---|---|---|
| Atlas size `[mat.atlas]` | select 512/1024/2048 | smallest that keeps texel density |
| Per-material table `[mat.items]` | rows: name, thumbnail, alpha mode, two-sided, tint, override file | from glb |
| Alpha cutoff `[mat.alpha_cutoff]` | number | 0.5 |
| Normal strength `[mat.normal_strength]` | number | 1.0 |
| Roughness/metal override `[mat.pbr]` | numbers, "no PBR" toggle | from glb |

**Checks**
| id | Fails/warns when | Fix line |
|---|---|---|
| `S3.atlas` | fail if the atlas cannot be built at the chosen size | "Raise the atlas size or lower texture sizes." |
| `S3.uv-repeat` | warn when UVs exceed four repeats (engine clamps) | "Bake the tiling into the texture." |
| `S3.dropped` | warn per material that would be lost (e.g. Blender-Internal) | "Bake to a texture in Blender, or give it a replacement file." |
| `S3.vertex-colour` | warn: vertex colours are not drawn | "Bake them into the texture." |
| `S3.emissive` | warn: emissive may not be drawn (confirm against the engine) | "Bake glow into the base colour." |
| `S3.memory` | warn: texture memory beyond the per-model budget | "Lower the atlas size." |

**Gate**: atlas builds and previews textured.
**Needs**: E1 (load and replace), E3/E7 for the preview, atlas builder returns data (C1). To confirm: what the engine draws for emissive and vertex colour (read `gl_picture.c`, not read yet).

## 5. Outlined stages (to detail next)

| Stage | Detail still needed |
|---|---|
| S7 Look | lighting compare against BLS, camera shot editor (field/arena shots) |
| S8 Validate | scripted run list, contact sheet/video outputs, pass criteria |
| S9 Package | build progress, native_check output, byte-identity check, where the package lands |
| Cross-stage | recipe versioning, undo/redo scope, multi-card use, Blender round trip, error screens (crash of the engine process, missing disc) |
