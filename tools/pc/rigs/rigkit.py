#!/usr/bin/env python3
"""rigkit: the two verified ways to get the game into a known situation and screenshot it.
(Verified 2026-10-13 on the dev worktree's tmp/pc/game32 build; see ../03-playbook.md.)

  python -I rigkit.py hand  --deck 374,380,332,683,364,670 --scale 4 --out DIR
  python -I rigkit.py scene --set trap --scale 4 --out DIR [--settings k=v ...] [--env K=V ...]
  python -I rigkit.py duel  --hand 100,332,683,301,364 --plays 0:up,0:down --scale 2 --out DIR
  python -I rigkit.py sets  --scale 2 --out DIR          (every scene set -> sheet.png)
  python -I rigkit.py situation situations/odd-slot-attack.json [--record | --check] --out DIR
      a declarative situation (hand, plays with COLUMNS, attack, camera, shots, pixel checks), see situations/*.json
  python -I rigkit.py ab spec.json --exe-a A/memories-pc.exe --exe-b B/memories-pc.exe --out DIR [--max-pct 0]
      the same situation on two builds (each in its own private copy), shots matched by battle step, per-shot pixel
      diff + wall time, ab.json and ab-sheet.png, exit 1 when any shot differs by more than --max-pct. Both builds must
      have the mods the spec turns on (camera-pin only when the spec pins a camera).
  python -I rigkit.py attack --deck 374 --camera 2048,400 --at 2,4,7,10 --scale 2 --out DIR
      attack = monster attacks monster; the state is saved just before the battle (made at 1x), then loaded at
      --scale, the camera pinned (--camera angle[,distance]; needs the camera-pin mod, built in) and a shot taken
      the first vblank each battle sub-step in --at is reached (names: attack-s<step>-vb<n>.png).

duel = a free duel with a CONTROLLED HAND (arrange_deck) and one play per own turn ("slot:up|down";
slot is the hand slot at that moment): the way to get traps, spells, equips, rituals on the field
(the test-scenes mod only places monsters and its set "hand" keys are ignored by v1.1).

Both make the situation ONCE at Internal 1x (about 3 s hand, 9 s scene), save a state named with the
build id, then load that state in a game running at --scale and shoot (about 1 s even at 4x; building
the same situation at 4x takes 100 s). States are tied to the exact exe: the build id is in the name.
No paths are hardcoded: --repo / $YFM_REPO is the checkout whose tools/pc/yfm_control.py and exe are used
(default: the dev worktree), --exe / $YFM_EXECUTABLE picks another exe (a release install, a PR build).
Run with python -I from a folder of its own. The game runs from a PRIVATE COPY of the build folder (OUT/_exe), so a
rig never locks the real build (a running exe makes the user's link fail "Permission denied"); --in-place disables it.
Never kill games by image name (taskkill /IM memories-pc.exe also kills the user's own game): Game ends its own process.
"""
import argparse, json, os, sys, time
from pathlib import Path

DEFAULT_REPO = r"C:\Users\mdahh\OneDrive\Desktop\Perso\hacking\Yu-Gi-Oh-Forbidden-Memories-Recompiled-dev"


def kv(items):
    return dict(i.split("=", 1) for i in (items or []))


def load_client(repo):
    sys.path.insert(0, str(Path(repo) / "tools" / "pc"))
    import yfm_control
    return yfm_control


# The battle phase (scene phase 9) runs a sub-step machine in the low nibble of D_8009B174. Observed 2026-10-13,
# monster attacks monster, ~225 vblanks, deterministic: (vblank from the start of the battle phase, sub-step)
#   0:1 camera tween 334->600 (12) | 12:2 | 13-30:3 | 54:4 | 103:7 | 148:10 | 206:6 | 208:11 | 225: back to field (phase 5)
# (the high bits of the byte, 0x80/0x40, are wait flags: always mask with 0xF).
BATTLE = 9
BATTLE_STEPS = (1, 2, 3, 4, 7, 8, 10, 6, 11)


def battle_step(g):
    """The battle sub-step (low nibble of D_8009B174), or None outside the battle phase."""
    return g.u8("D_8009B174") & 0xF if g.phase() == BATTLE else None


def wait_battle_step(g, step, timeout=900):
    """Step one vblank at a time until the battle is in `step`; returns the vblanks it took."""
    return g.wait_until(lambda g: battle_step(g) == step, timeout, what=f"battle step {step}")


def camera_read(g):
    """(angle, distance) of the duel camera (D_800F2848: s16 distance at +0, s16 angle at +2)."""
    import struct
    distance, angle = struct.unpack("<hh", g.peek("D_800F2848", 4))
    return angle, distance


def camera_pin(g, angle=None, distance=None):
    """Hold the duel camera at angle (0..4095, 1024 = the usual view) and/or distance (200..1400) in every scene
    phase, through the camera-pin mod's pad-2 mailbox (mod must be enabled in the run AND in the run that saved a
    state: a state loads only with the same mods and mod settings). camera_pin(g) clears the pin."""
    if angle is None and distance is None:
        g.pad(0x2000, 2); g.step(1)
    if angle is not None:
        g.pad(0x4000 | (angle & 0xFFF), 2); g.step(1)
    if distance is not None:
        g.pad(0x8000 | (distance & 0x7FF), 2); g.step(1)
    g.pad(0, 2)


def run_ab(a):
    """Run the situation spec on build A and build B (two child processes, each with a private copy of its build),
    match the shots by their battle step (s<step>-vb<n> or the single 'situation.png'), diff them, time them."""
    import subprocess, time
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import pxkit
    from PIL import Image, ImageDraw
    out = Path(a.out).resolve(); out.mkdir(parents=True, exist_ok=True)
    results = {}
    for side, exe in (("a", a.exe_a), ("b", a.exe_b)):
        spec_path = a.spec
        if side == "b" and a.settings_b:
            sp = json.loads(Path(a.spec).read_text(encoding="utf-8"))
            sp.setdefault("settings", {}).update(dict(i.split("=", 1) for i in a.settings_b))
            (out / "b").mkdir(exist_ok=True); spec_path = str(out / "b" / "spec-b.json")
            Path(spec_path).write_text(json.dumps(sp), encoding="utf-8")
        cmd = [sys.executable, "-I", str(Path(__file__).resolve()), "situation", spec_path, "--repo", a.repo, "--exe", exe,
               "--out", str(out / side)]
        t = time.time()
        r = subprocess.run(cmd, capture_output=True, text=True)
        results[side] = {"exit": r.returncode, "wall_s": round(time.time() - t, 1), "tail": (r.stdout + r.stderr)[-400:]}
        res_file = out / side / "result.json"
        if not res_file.is_file():
            print(f"build {side.upper()} produced no result:\n{results[side]['tail']}")
            return 2
        results[side]["shots"] = {e["shot"].split("-vb")[0].replace(".png", ""): e["shot"] for e in json.loads(res_file.read_text())["shots"]}
    rows, ok = [], True
    for key in sorted(set(results["a"]["shots"]) | set(results["b"]["shots"])):
        fa, fb = results["a"]["shots"].get(key), results["b"]["shots"].get(key)
        if not fa or not fb:
            rows.append({"shot": key, "ok": False, "detail": "missing in " + ("A" if not fa else "B")}); ok = False; continue
        d = pxkit.diff(out / "a" / fa, out / "b" / fb)
        good = d["pct"] <= a.max_pct
        ok &= good
        rows.append({"shot": key, "a": fa, "b": fb, "ok": good, **d})
    report = {"spec": a.spec, "exe_a": a.exe_a, "exe_b": a.exe_b, "max_pct": a.max_pct, "ok": ok, "rows": rows,
              "wall_s": {"a": results["a"]["wall_s"], "b": results["b"]["wall_s"]}}
    (out / "ab.json").write_text(json.dumps(report, indent=1))
    # side-by-side sheet: A | B per shot
    tiles = []
    for r in rows:
        if "a" in r:
            ia, ib = Image.open(out / "a" / r["a"]).convert("RGB"), Image.open(out / "b" / r["b"]).convert("RGB")
            w, h = ia.size; sc = 480 / w
            ia, ib = ia.resize((480, int(h * sc))), ib.resize((480, int(h * sc)))
            tile = Image.new("RGB", (960, ia.size[1] + 14)); tile.paste(ia, (0, 14)); tile.paste(ib, (480, 14))
            ImageDraw.Draw(tile).text((4, 1), f"{r['shot']}  A | B  differ {r['pct']}%", fill="white"); tiles.append(tile)
    if tiles:
        sheet = Image.new("RGB", (960, sum(t.size[1] for t in tiles))); y = 0
        for t in tiles:
            sheet.paste(t, (0, y)); y += t.size[1]
        sheet.save(out / "ab-sheet.png")
    for r in rows:
        print(f"{'PASS' if r['ok'] else 'FAIL'} {r['shot']:8s} differ {r.get('pct', '-')}% bbox {r.get('bbox')}")
    print(f"wall A {report['wall_s']['a']} s, B {report['wall_s']['b']} s; verdict {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def play_at(g, slot, column=None, face_up=True, star=0):
    """play_card, but into zone `column` (0-4, left to right) instead of the first free one. Sequence found by
    tracing (2026-10-13): Cross selects the card, Right = face up, a second Cross opens the ZONE CHOICE (phase is still
    'hand'; the field cursor FIELD_CURSOR col/row bytes now move with Left/Right; the game picks the row: monsters
    2, spells/traps 3), a third Cross confirms (placement phase). Verified from field() afterwards."""
    import yfm_control as yc
    D = yc.DUEL_PHASES
    if column is None:
        return g.play_card(slot, face_up=face_up, star=star)
    g.wait_turn(("hand",))
    g._hand_to(slot)
    card = g.duel()[0]["hand"][slot]["id"]
    g.press("cross", hold=4, after=30)
    if face_up:
        g.press("right", hold=4, after=12)
    g.press("cross", hold=4, after=30)            # the zone choice
    g._cursor_to(yc.FIELD_CURSOR, column, "zone")
    g.press("cross", hold=4, after=30)            # confirm the zone
    g.press_until(lambda g: g.phase() != D["placement"] or g.duel_over(), "cross", every=40, timeout=1200, what="the placement")
    if g.phase() == D["position"] and star:
        for _ in range(star):
            g.press("down", hold=4, after=12)
    if g.phase() == D["position"]:
        g.press_until(lambda g: g.phase() != D["position"] or g.duel_over(), "cross", every=40, timeout=1200, what="the guardian star")
    g._settle()
    if not any(g.field()[r][column] == card for r in (2, 3)):
        raise RuntimeError(f"play_at: card {card} is not in column {column}: {g.field()}")


def run_situation(a, yc, out, base):
    """Spec keys: opponent, hand [5 ids], opp_hand [5 ids, optional], turns [{"play": [[slot,"up|down",column?,star?]...],
    "attack": [column, target|null]}], camera [angle, distance?], at [battle steps], delay N (vblanks after reaching a step before its shot, default 3), every N, tail N, steps N (shot after
    the last turn when there is no attack), scale, settings {k: v}, env {K: V}, checks {"max_pct": f, "region": [x,y,w,h]}."""
    import hashlib, time
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import pxkit
    spec = json.loads(Path(a.spec).read_text(encoding="utf-8"))
    settings = {"mod.3d-monsters": 0, "mod.camera-pin": 1, **spec.get("settings", {})}
    env = dict(spec.get("env", {}))
    scale = int(spec.get("scale", a.scale))
    key = hashlib.sha1(json.dumps({k: spec.get(k) for k in ("opponent", "hand", "opp_hand", "turns", "settings", "env")}, sort_keys=True).encode()).hexdigest()[:10]
    t0 = time.time()
    with yc.Game(out=out / "make", settings={**settings, "internal_scale": 1}, env=env, **base) as g0:
        build = f"{g0.info()['build']:08x}"
        state = out / "states" / f"{key}-{build}.state"
        if not state.exists():
            state.parent.mkdir(exist_ok=True)
            hand = spec.get("hand", [100, 100, 100, 100, 100])
            g0.goto("duel", opponent=spec.get("opponent", 1), deck=",".join(map(str, hand)))

            def arrange(g):
                g.arrange_deck(0, hand)
                if spec.get("opp_hand"):
                    g.arrange_deck(1, spec["opp_hand"])
            g0.duel_ready(before_deal=arrange)
            for n, turn in enumerate(spec.get("turns", [])):
                if n:
                    g0.end_turn(); g0.wait_turn(("hand",))
                for pl in turn.get("play", []):
                    play_at(g0, pl[0], pl[2] if len(pl) > 2 else None, face_up=(pl[1] == "up"), star=pl[3] if len(pl) > 3 else 0)
                if turn.get("attack"):
                    col, tgt = turn["attack"]
                    g0._settle = lambda *x, **k: g0.save(state)
                    g0.attack(col, tgt)
            if not state.exists():
                g0.save(state)
    res = {"spec": str(a.spec), "state": state.name, "scale": scale, "shots": [], "ok": True}
    gold = Path(a.spec).resolve().parent / "golden" / f"{Path(a.spec).stem}-{scale}x"
    chk = spec.get("checks", {})
    shots = []
    with yc.Game(out=out / "look", settings={**settings, "internal_scale": scale}, env=dict(env, MEMORIES_DUMP_PICTURE="1"), **base) as g:
        g.load(state)
        cam = spec.get("camera")
        if cam:
            camera_pin(g, int(cam[0]), int(cam[1]) if len(cam) > 1 else None)
        if any(t.get("attack") for t in spec.get("turns", [])):
            want, every, start, seen, ended, in_battle = set(spec.get("at", [])), spec.get("every", 0), g.vblank, set(), None, False
            while g.vblank - start < 1200:
                step, vb = battle_step(g), g.vblank - start
                name = None
                if step in want and step not in seen:
                    seen.add(step)
                    g.step(spec.get("delay", 3))          # the picture shows a change a frame or two after it is made
                    vb = g.vblank - start; name = f"s{step}-vb{vb}"
                elif every and vb % every == 0:
                    name = f"f{vb:04d}-s{step}"
                if name:
                    shots.append(g.shot(out / f"{name}.png"))
                if step is not None:
                    in_battle = True
                if step is None and in_battle and ended is None:
                    ended = vb
                if ended is not None and vb - ended >= spec.get("tail", 0):
                    break
                g.step(1)
        else:
            g.step(spec.get("steps", 30)); shots.append(g.shot(out / "situation.png"))
    for p in shots:
        entry = {"shot": Path(p).name}
        if a.record:
            pxkit.golden(p, gold, "record"); entry["ok"] = True
        elif a.check:
            g_img = gold / Path(p).name
            d = pxkit.diff(p, g_img, tuple(chk["region"]) if chk.get("region") else None) if g_img.is_file() else {"pct": 100.0, "count": None}
            entry.update(ok=d["pct"] <= chk.get("max_pct", 0.0), detail=d); res["ok"] &= entry["ok"]
        res["shots"].append(entry)
    res["wall_s"] = round(time.time() - t0, 1)
    (out / "result.json").write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps(res, default=str)[:700])
    return 0 if res["ok"] else 1


def find_set(repo, name):
    """sets/<name>.json from the repo's test-scenes, else the dev worktree's (only dev tracks the sets)."""
    for root in (Path(repo), Path(DEFAULT_REPO)):
        f = root / "mods/test-scenes/sets" / f"{name}.json"
        if f.is_file():
            return f
    raise FileNotFoundError(f"no scene set {name}")


def title_to_option_scene(g):
    """Cold boot -> title menu -> hold L1 + confirm OPTION = the test-scenes duel (mod.test-scenes=1)."""
    g.goto("title")
    g.step(1800)                     # goto('title') returns during the Konami logo; the menu needs ~1800 vblanks
    g.press("start", hold=6, after=60)
    for _ in range(4):               # NEW GAME, LOAD, 2P DUEL, TRADE, OPTION
        g.press("down", hold=6, after=20)
    g.press(["l1", "cross"], hold=8, after=10)
    g.pad(0)
    g.step(500)
    assert g.mode() == 3, f"scene did not open (mode {g.mode()}): mod.test-scenes=1 set? every zone card a monster?"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("kind", choices=["hand", "scene", "duel", "sets", "attack", "situation", "ab"])
    ap.add_argument("--repo", default=os.environ.get("YFM_REPO", DEFAULT_REPO))
    ap.add_argument("--exe", default=os.environ.get("YFM_EXECUTABLE"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--scale", type=int, default=1)
    ap.add_argument("--deck", default="374,380,332,683,364,670")
    ap.add_argument("--opponent", type=int, default=3)
    ap.add_argument("--hand", default="100,332,683,301,364", help="duel: the opening hand, 5 card ids")
    ap.add_argument("--plays", default="0:up", help="duel: one 'slot:up|down' per own turn")
    ap.add_argument("--camera", default="", help="attack: angle[,distance] pinned (4096-unit turn, 1024 usual; 200..1400, 600 usual)")
    ap.add_argument("--every", type=int, default=0, help="attack: also a shot every N vblanks from the battle start to --tail after it")
    ap.add_argument("--tail", type=int, default=60, help="attack: vblanks to keep filming after the battle phase ends")
    ap.add_argument("--at", default="1,2,3,4,7,8,10,6,11", help="attack: battle sub-steps to shoot (see BATTLE_STEPS)")
    ap.add_argument("spec", nargs="?", help="situation: path of the JSON spec")
    ap.add_argument("--record", action="store_true", help="situation: store the shots as goldens next to the spec")
    ap.add_argument("--check", action="store_true", help="situation: compare the shots with the goldens (exit 1 on a difference)")
    ap.add_argument("--exe-a", help="ab: build A (the reference)")
    ap.add_argument("--exe-b", help="ab: build B (the change)")
    ap.add_argument("--settings-b", nargs="*", help="ab: key=value settings applied to side B only (compare a setting, or a build with a setting changed)")
    ap.add_argument("--max-pct", type=float, default=0.0, help="ab: allowed differing pixels, percent of the picture")
    ap.add_argument("--in-place", action="store_true", help="run the exe where it is (locks it while running)")
    ap.add_argument("--set", default="plain", help="scene: a name in <repo>/mods/test-scenes/sets/")
    ap.add_argument("--settings", nargs="*", help="key=value player settings, e.g. mod.anime-art=1")
    ap.add_argument("--env", nargs="*", help="KEY=VALUE extra MEMORIES_* variables")
    ap.add_argument("--steps", type=int, default=30, help="vblanks to run after loading, before the shot")
    ap.add_argument("--press", default="", help="comma list of keys pressed (e.g. triangle) after loading")
    a = ap.parse_args()
    if a.kind == "ab":
        return run_ab(a)
    if a.kind == "sets":
        return run_sets(a)
    yc = load_client(a.repo)
    out = Path(a.out).resolve(); out.mkdir(parents=True, exist_ok=True)
    settings, env = kv(a.settings), kv(a.env)
    t0 = time.time()
    lap = lambda m: print(f"{time.time() - t0:6.1f}s {m}", flush=True)
    if a.kind == "scene":
        sc = json.loads(find_set(a.repo, a.set).read_text())
        for i in range(5):
            env[f"MEMORIES_MOD_TEST_SCENES_P{i+1}"] = str(sc["player"][i])
            env[f"MEMORIES_MOD_TEST_SCENES_O{i+1}"] = str(sc["opponent"][i])
        settings.setdefault("mod.test-scenes", "1")
    exe = Path(a.exe or Path(a.repo) / "tmp/pc/game32/memories-pc.exe")
    if not a.in_place and exe.is_file():
        import shutil
        private = out / "_exe"
        if not private.exists():
            shutil.copytree(exe.parent, private, ignore=shutil.ignore_patterns("*.pdb", "*.c", "*.s", "obj"))
        exe = private / exe.name
    base = dict(executable=str(exe))
    if a.kind == "situation":
        return run_situation(a, yc, out, base)
    if a.kind == "attack":
        return run_attack(a, yc, out, settings, env, base)
    # 1) the situation, once, at 1x
    with yc.Game(out=out / "make", settings={**settings, "internal_scale": 1}, env=env, **base) as g:
        build = f"{g.info()['build']:08x}"
        tag = {"scene": a.set, "duel": "p" + a.plays.replace(":", "").replace(",", "_") + "-h" + a.hand.replace(",", "_")}.get(a.kind, "deck")
        state = out / f"{a.kind}-{tag}-{build}.state"
        if not state.exists():
            if a.kind == "hand":
                g.goto("duel", opponent=a.opponent, deck=a.deck); g.duel_ready()
            elif a.kind == "duel":
                hand = [int(x) for x in a.hand.split(",")]
                g.goto("duel", opponent=a.opponent, deck=",".join(map(str, hand)))
                g.duel_ready(before_deal=lambda g: g.arrange_deck(0, hand))
                plays = [p.split(":") for p in a.plays.split(",") if p]
                for n, (slot, how) in enumerate(plays):
                    if n:
                        g.end_turn(); g.wait_turn(("hand",))
                    g.play_card(int(slot), face_up=(how == "up"))
                print("field", g.field(), flush=True)
            else:
                title_to_option_scene(g)
            g.save(state)
        lap(f"state {state.name}")
    # 2) look at it at the wanted scale
    env2 = dict(env, MEMORIES_DUMP_PICTURE="1")      # without it shot() is the 320x240 VRAM, not the scaled picture
    with yc.Game(out=out / "look", settings={**settings, "internal_scale": a.scale}, env=env2, **base) as g:
        g.load(state)                                 # through the channel: MEMORIES_LOAD_STATE at startup gave a black frame
        if a.press:
            g.press(a.press.split(","))
        g.step(a.steps)
        png = g.shot(out / f"{a.kind}-x{a.scale}.png")
        lap(f"shot {png}")


def run_attack(a, yc, out, settings, env, base):
    settings = {"mod.3d-monsters": 0, "mod.camera-pin": 1, **settings}
    state = out / "attack-before-battle.state"
    with yc.Game(out=out / "make", settings={**settings, "internal_scale": 1}, env=env, **base) as g:
        g.goto("duel", opponent=a.opponent, deck=a.deck); g.duel_ready()
        g.play_card(0, face_up=True); g.end_turn(); g.play_card(0, face_up=True)
        col = next(i for i, c in enumerate(g.field()[2]) if c)
        tgt = next((i for i, c in enumerate(g.field()[1]) if c), None)
        g._settle = lambda *x, **k: g.save(state)       # the attack is committed; keep the moment before the battle
        g.attack(col, tgt)
    want = [int(x) for x in a.at.split(",") if x]
    with yc.Game(out=out / "look", settings={**settings, "internal_scale": a.scale}, env=dict(env, MEMORIES_DUMP_PICTURE="1"), **base) as g:
        g.load(state)
        if a.camera:
            ang, _, dist = a.camera.partition(",")
            camera_pin(g, int(ang), int(dist) if dist else None)
        start, seen, log, ended = g.vblank, set(), [], None
        while g.vblank - start < 1200:
            step, vb = battle_step(g), g.vblank - start
            if step in want and step not in seen:
                seen.add(step)
                g.shot(out / f"attack-s{step}-vb{vb}.png"); log.append((vb, step, camera_read(g)))
            elif a.every and vb % a.every == 0:
                g.shot(out / f"attack-f{vb:04d}-s{step}.png")
            if step is None and seen and ended is None:
                ended = vb
            if ended is not None and vb - ended >= (a.tail if a.every else 0):
                break
            g.step(1)
        print("battle log (vblank, step, (angle, distance)):", log)


def run_sets(a):
    """Every scene set at --scale -> OUT/sheet.png (name under each tile). Each set costs ~9 s."""
    from PIL import Image, ImageDraw
    names = sorted(p.stem for p in (Path(DEFAULT_REPO) / "mods/test-scenes/sets").glob("*.json"))
    out = Path(a.out).resolve()
    shots = []
    for n in names:
        sys.argv = [sys.argv[0], "scene", "--repo", a.repo, "--set", n, "--scale", str(a.scale), "--out", str(out / n),
                    "--steps", str(a.steps)] + (["--exe", a.exe] if a.exe else [])
        main()
        shots.append(Image.open(out / n / f"scene-x{a.scale}.png").convert("RGB").resize((320, 240)))
    sheet = Image.new("RGB", (320 * 4, 250 * ((len(shots) + 3) // 4)))
    d = ImageDraw.Draw(sheet)
    for i, (im, n) in enumerate(zip(shots, names)):
        sheet.paste(im, ((i % 4) * 320, (i // 4) * 250)); d.text(((i % 4) * 320 + 4, (i // 4) * 250 + 238), n, fill="white")
    sheet.save(out / "sheet.png"); print("sheet", out / "sheet.png")


if __name__ == "__main__":
    sys.exit(main() or 0)
