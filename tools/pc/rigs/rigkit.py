#!/usr/bin/env python3
"""rigkit: the two verified ways to get the game into a known situation and screenshot it.
(Verified 2026-10-13 on the dev worktree's tmp/pc/game32 build; see ../03-playbook.md.)

  python -I rigkit.py hand  --deck 374,380,332,683,364,670 --scale 4 --out DIR
  python -I rigkit.py scene --set trap --scale 4 --out DIR [--settings k=v ...] [--env K=V ...]
  python -I rigkit.py duel  --hand 100,332,683,301,364 --plays 0:up,0:down --scale 2 --out DIR
  python -I rigkit.py sets  --scale 2 --out DIR          (every scene set -> sheet.png)

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
    ap.add_argument("kind", choices=["hand", "scene", "duel", "sets"])
    ap.add_argument("--repo", default=os.environ.get("YFM_REPO", DEFAULT_REPO))
    ap.add_argument("--exe", default=os.environ.get("YFM_EXECUTABLE"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--scale", type=int, default=1)
    ap.add_argument("--deck", default="374,380,332,683,364,670")
    ap.add_argument("--opponent", type=int, default=3)
    ap.add_argument("--hand", default="100,332,683,301,364", help="duel: the opening hand, 5 card ids")
    ap.add_argument("--plays", default="0:up", help="duel: one 'slot:up|down' per own turn")
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
