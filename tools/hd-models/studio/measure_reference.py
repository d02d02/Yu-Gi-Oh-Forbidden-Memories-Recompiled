#!/usr/bin/env python3
"""SM0: measure the disc's animation rows per attacker, from real arena attacks (needs the disc and the game build).

    python -I studio/measure_reference.py OUT.json [--cards 364,1,...] [--defender 332] [--exe EXE] [--work DIR]

Per card it runs attack_window_evlog.py (MEMORIES_TRACE=model), reads the `evt draw` lines of the measuring run and records, for the
attacker's slot: every row seen with its length (`len=`), and the attacker's clock (`frame=`) in its attack row (3 or 4) when the
defender's row first becomes a reaction row (5, 6, 8) = the contact frame. MEMORIES_DISC must be an absolute path.
"""
import argparse, json, re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DRAW = re.compile(r"evt draw f=(\d+) slot=(\d+) model=(-?\d+) row=(-?\d+) prev=(-?\d+) state=(-?\d+) frame=(-?\d+) len=(-?\d+)")
REACTION = (5, 6, 8)
ATTACK = (3, 4)


def parse(log: str) -> dict:
    """{'models': {slot: model}, 'rows': {slot: {row: [lengths]}}, 'contact': [...]} from the text of a game.log."""
    rows, models, by_frame, contact = {}, {}, {}, []
    for m in DRAW.finditer(log):
        f, slot, model, row, _, _, clock, length = map(int, m.groups())
        if slot > 1:
            continue
        models[slot] = model
        rows.setdefault(slot, {}).setdefault(row, set()).add(length)
        by_frame.setdefault(f, {})[slot] = (row, clock, length)
    last_attack = {}
    seen = set()
    for f in sorted(by_frame):
        pair = by_frame[f]
        for slot, other in ((0, 1), (1, 0)):
            if slot not in pair or other not in pair:
                continue
            if pair[slot][0] in ATTACK:
                last_attack[slot] = pair[slot]
            if pair[other][0] in REACTION and slot in last_attack and slot not in seen:
                # the attacker's clock in its attack row at the first reaction frame (its last draw in that row when it has already left it)
                seen.add(slot)
                row, clock, length = last_attack[slot]
                contact.append({"attacker_slot": slot, "attacker_model": models[slot], "attack_row": row,
                                "row_length": length, "contact_clock": clock, "contact_frame": clock // 16, "suspect": clock // 16 >= length - 2 or pair[slot][0] not in ATTACK,
                                "defender_row": pair[other][0], "presented_frame": f})
    return {"models": models, "rows": {s: {r: sorted(v) for r, v in d.items()} for s, d in rows.items()}, "contact": contact}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out", type=Path)
    ap.add_argument("--cards", default="364")
    ap.add_argument("--defender", default="332")
    ap.add_argument("--exe", default="")
    ap.add_argument("--work", type=Path, default=Path("tmp/agent/sm0"))
    ap.add_argument("--frames", type=int, default=1500)
    ap.add_argument("--every", type=int, default=1)
    a = ap.parse_args()
    result = json.loads(a.out.read_text()) if a.out.exists() else {}
    for card in [int(c) for c in a.cards.split(",")]:
        work = a.work / f"card{card}"
        command = [sys.executable, "-I", str(HERE.parent / "attack_window_evlog.py"), str(work), "--hand", f"374,{card},100,{a.defender},683",
                   "--frames", str(a.frames), "--every", str(a.every), "--start", "999999", "--scale", "1"]
        if a.exe:
            command += ["--exe", a.exe]
        done = subprocess.run(command, capture_output=True, text=True)
        log = work / "look-measure" / "game.log"
        if done.returncode or not log.exists():
            result[str(card)] = {"error": (done.stderr or done.stdout)[-300:]}
        else:
            result[str(card)] = parse(log.read_text(errors="replace"))
        print(card, json.dumps(result[str(card)].get("contact") or result[str(card)].get("error")), flush=True)
        a.out.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
