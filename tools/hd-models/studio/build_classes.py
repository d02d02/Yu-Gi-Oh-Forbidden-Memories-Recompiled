#!/usr/bin/env python3
"""SM0: group the monsters into classes and write studio/reference/classes.json.

    python -I studio/build_classes.py CAM_ALL.json OUTLINES_DIR [OUT.json]

Inputs: measure_reference.py --clean output (rows, contact, camera per card) and measure_outline.py files (OUTLINES_DIR/<card>.json).
Class key = model height bucket of 50 game units. Per class: cards, height and close-shot distance ranges, median attack-row length and
contact frame (suspect contacts left out), and the representative (the card whose height is closest to the class median)."""
import json, statistics as st, sys
from pathlib import Path

BUCKET = 50


def main(cam: Path, outlines: Path, out: Path):
    cams = json.loads(cam.read_text())
    classes = {}
    for card, v in sorted(cams.items(), key=lambda kv: int(kv[0])):
        f = outlines / f"{card}.json"
        if not f.exists() or "camera" not in v:
            continue
        o = json.loads(f.read_text())
        h = o["height"]
        entry = classes.setdefault(str(h // BUCKET * BUCKET), {"cards": [], "heights": [], "close": [], "row_length": [], "contact": []})
        entry["cards"].append(int(card))
        entry["heights"].append(h)
        p5 = v["camera"].get("5")
        if p5:
            entry["close"].append(p5["dist_min"])
        c = [c for c in v.get("contact", []) if c["attacker_slot"] == 0 and not c.get("suspect")]
        if c:
            entry["row_length"].append(c[0]["row_length"])
            entry["contact"].append(c[0]["contact_frame"])
    result = {}
    for key, e in sorted(classes.items(), key=lambda kv: int(kv[0])):
        med = st.median(e["heights"])
        rep = min(e["cards"], key=lambda c: abs(e["heights"][e["cards"].index(c)] - med))
        rng = lambda xs: [min(xs), max(xs)] if xs else None
        result[key] = {"height_bucket": [int(key), int(key) + BUCKET], "count": len(e["cards"]), "representative": rep,
                       "height_range": rng(e["heights"]), "close_shot_range": rng(e["close"]),
                       "attack_row_length_median": st.median(e["row_length"]) if e["row_length"] else None,
                       "contact_frame_median": st.median(e["contact"]) if e["contact"] else None, "cards": e["cards"]}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    for k, c in result.items():
        print(k, c["count"], "rep", c["representative"], "close", c["close_shot_range"], "row", c["attack_row_length_median"], "contact", c["contact_frame_median"])


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3] if len(sys.argv) > 3 else Path(__file__).resolve().parent / "reference" / "classes.json"))
