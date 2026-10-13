#!/usr/bin/env python3
"""rigkit: the two verified ways to get the game into a known situation and screenshot it.
(Verified 2026-10-13 on the dev worktree's tmp/pc/game32 build; see ../03-playbook.md.)

  python -I rigkit.py hand  --deck 374,380,332,683,364,670 --scale 4 --out DIR
  python -I rigkit.py scene --set trap --scale 4 --out DIR [--settings k=v ...] [--env K=V ...]
  python -I rigkit.py duel  --hand 100,332,683,301,364 --plays 0:up,0:down --scale 2 --out DIR
  python -I rigkit.py sets  --scale 2 --out DIR          (every scene set -> sheet.png)
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
Run with python -I from a folder of its own; never leave a game running (kill memories-pc.exe).
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
    ap.add_argument("kind", choices=["hand", "scene", "duel", "sets", "attack"])
    ap.add_argument("--repo", default=os.environ.get("YFM_REPO", DEFAULT_REPO))
    ap.add_argument("--exe", default=os.environ.get("YFM_EXECUTABLE"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--scale", type=int, default=1)
    ap.add_argument("--deck", default="374,380,332,683,364,670")
    ap.add_argument("--opponent", type=int, default=3)
    ap.add_argument("--hand", default="100,332,683,301,364", help="duel: the opening hand, 5 card ids")
    ap.add_argument("--plays", default="0:up", help="duel: one 'slot:up|down' per own turn")
    ap.add_argument("--camera", default="", help="attack: angle[,distance] pinned (4096-unit turn, 1024 usual; 200..1400, 600 usual)")
    ap.add_argument("--at", default="1,2,3,4,7,8,10,6,11", help="attack: battle sub-steps to shoot (see BATTLE_STEPS)")
    ap.add_argument("--set", default="plain", help="scene: a name in <repo>/mods/test-scenes/sets/")
    ap.add_argument("--settings", nargs="*", help="key=value player settings, e.g. mod.anime-art=1")
    ap.add_argument("--env", nargs="*", help="KEY=VALUE extra MEMORIES_* variables")
    ap.add_argument("--steps", type=int, default=30, help="vblanks to run after loading, before the shot")
    ap.add_argument("--press", default="", help="comma list of keys pressed (e.g. triangle) after loading")
    a = ap.parse_args()
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
    base = dict(executable=a.exe)
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
        start, seen, log = g.vblank, set(), []
        while g.vblank - start < 900:
            step = battle_step(g)
            if step in want and step not in seen:
                seen.add(step)
                g.shot(out / f"attack-s{step}-vb{g.vblank - start}.png"); log.append((g.vblank - start, step, camera_read(g)))
            if log and step is None and g.phase() != BATTLE and seen:
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
    main()
