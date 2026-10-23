#!/usr/bin/env python3
"""SM0: build studio/reference/arena_rows.json from the measuring runs' game.log files (see measure_reference.py).

    python -I studio/build_reference.py WORK_DIR [OUT.json]       WORK_DIR holds card<N>/look-measure/game.log

Per card: model id, {row: length} of the attacker, and the contact (attack row, row length, contact frame = attacker clock / 16 at the
defender's first reaction row; `suspect` = within 2 frames of the row end, do not trust). Sorted keys, so two builds are identical."""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from measure_reference import parse  # noqa: E402


def build(work: Path) -> dict:
    cards = {}
    for log in sorted(work.glob("card*/look-measure/game.log"), key=lambda p: int(p.parts[-3][4:])):
        card = log.parts[-3][4:]
        got = parse(log.read_text(errors="replace"))
        rows = got["rows"].get(0, {})
        entry = {"model": got["models"].get(0), "rows": {str(r): v[0] if len(v) == 1 else v for r, v in sorted(rows.items())}}
        hit = [c for c in got["contact"] if c["attacker_slot"] == 0]
        if hit:
            c = hit[0]
            entry["contact"] = {k: c[k] for k in ("attack_row", "row_length", "contact_frame", "suspect", "defender_row")}
        cards[card] = entry
    return {"source": "arena attacks, defender card 332, attacker in slot 0", "cards": cards}


if __name__ == "__main__":
    out = Path(sys.argv[2] if len(sys.argv) > 2 else Path(__file__).resolve().parent / "reference" / "arena_rows.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    data = build(Path(sys.argv[1]))
    out.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n")
    cards = data["cards"].values()
    print(len(data["cards"]), "cards;", sum("contact" in c for c in cards), "with contact;", sum(c.get("contact", {}).get("suspect", False) for c in cards), "suspect")
