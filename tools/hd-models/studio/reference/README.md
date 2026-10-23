# Studio reference pack (SM0)

`arena_rows.json`: disc ground truth per attacker card, measured from real arena attacks (not guessed).

| Field | Meaning |
|---|---|
| `model` | disc model id of the attacker (card - 1) |
| `rows` | `{animation row: length in disc frames}` seen on the attacker (1 idle, 2 walk/ready, 3 attack, ...) |
| `contact.attack_row`, `row_length` | the attack row played and its length |
| `contact.contact_frame` | attacker's clock / 16 (the clock advances 16 per game frame) when the defender is first told a reaction row (5, 6, 8) = where the blow lands |
| `contact.suspect` | contact within 2 frames of the row end, or the attacker had left its attack row: do not trust |

Cards with no 3D model on the disc are absent. Cards without `contact` never reached a reaction in the run.

## How it was measured
`measure_reference.py` runs `attack_window_evlog.py` per card (hand `374,<card>,100,332,683`: the card attacks defender 332 in the arena, `MEMORIES_TRACE=model`), then reads the `evt draw` lines (`slot`, `row`, `frame`, `len`). Needs the disc (`MEMORIES_DISC`, absolute path), the game build and the capture harness. `build_reference.py WORK_DIR` turns the logs into this file; output is sorted, two builds are byte-identical.

`bls_outline.json`: Black Luster Soldier (card 364) from the disc record via `hmd_export.py` + `measure_outline.py`: bbox, height 373, front (x,y) and side (z,y) convex hulls, game units, feet at 0. The model sits off the origin in z (-699..-463): centre it before drawing the ghost.

Not measured yet: card footprint and arena camera shots. Both need engine work (no constant for the footprint was found; the camera needs the temporary per-frame `cam` log line described in `camera_distance_from_log.py`, a C change and a rebuild).

## Arena camera (`arena_camera.json`)
`build_camera.py` reads the `cam f= phase= eye= ref=` lines that `Model_UpdateScene` now logs (`MEMORIES_TRACE=model`, `src/game/model_scene_states.c`, MEMORIES_PC only) for cards 364, 1, 12, 250, 600. Per phase: frames, eye-to-look-at distance min/max, eye/ref first and last.
Finding: the phase script is the same for every attacker (same phases, same frame counts, opening orbit 1799, wide shot 1199), but the close-shot distance depends on the monster: phase 5/6 = 462 (card 364), 959 (card 1), 708 (card 12), 507 (card 250), 651 (card 600). So the camera reference is per monster class, not global. Rebuild with `measure_reference.py` + `build_camera.py`.

Card footprint: no footprint exists in the arena camera or draw logs; the field slot geometry is a separate (field-view) measurement, still open.

## Per-card camera and classes (`arena_camera_all.json`, `classes.json`)
`arena_camera_all.json`: distance range per camera phase for 620 cards. The close-shot distance (phase 5) takes 129 distinct values from 462 to 967: it is a **per-monster** value, not a class value. Height does not predict it (correlation 0.13), so `classes.json` (height buckets of 50, one representative each, median attack-row length and contact frame) is a convenience grouping only; use the per-card data for anything exact. What drives the camera distance is not yet identified (not the model height).
