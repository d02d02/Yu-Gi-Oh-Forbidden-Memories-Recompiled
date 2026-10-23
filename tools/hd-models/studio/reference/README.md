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

Not measured yet: BLS outline, card footprint, camera shots.
