#!/usr/bin/env python3
"""E3 transport demo: pause a native dragon attack, scrub its phases and compare with free play.

    python -I transport_demo.py OUTDIR [--phases 0,.25,.5,.75,1] [--card 364]
    python -I transport_demo.py --selftest        # no disc, no game

The live run sets up one duel (the card attacks once), saves the state at the attack commit, then in a second game pauses
the transport, scrubs each phase and takes a shot.  It reloads the same state for a free-playing pass, steps until the
game's own phase reaches each scrub phase (anim get reports it), pauses and shoots.  Both hashes are printed per phase.
Needs MEMORIES_DISC and the installed `studio-preview` mod.  --selftest only checks argument handling and hash comparison
on synthetic data.
"""
import argparse
import io
import os
import sys
from contextlib import redirect_stderr
from pathlib import Path

PHASES = (0.0, 0.25, 0.5, 0.75, 1.0)
REPO = Path(__file__).resolve().parents[2]
GAME_ENV = {"MEMORIES_FPS": "-1", "MEMORIES_WINDOW_HIDDEN": "1", "MEMORIES_NO_AUDIO": "1"}   # no window, no sound


def phase_grid(text):
    """Argument type: comma-separated phases, each 0..1."""
    try:
        phases = tuple(float(part) for part in text.split(",") if part.strip())
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"not a phase list: {text!r}") from exc
    if not phases:
        raise argparse.ArgumentTypeError("phase list is empty")
    for phase in phases:
        if not 0.0 <= phase <= 1.0:
            raise argparse.ArgumentTypeError(f"phase out of range 0..1: {phase}")
    return phases


def build_parser():
    parser = argparse.ArgumentParser(description="Pause/scrub a native dragon attack and print scrub/free-run hashes.")
    parser.add_argument("out", nargs="?", type=Path, help="output folder (shots, state, game logs)")
    parser.add_argument("--selftest", action="store_true", help="argument/hash checks only; no disc or game")
    parser.add_argument("--phases", type=phase_grid, default=PHASES, help="phases to scrub (default 0,.25,.5,.75,1)")
    parser.add_argument("--card", type=int, default=364, help="dragon card id (default 364)")
    parser.add_argument("--exe", default=None, help="game executable (default YGO_EXE, then tmp/pc/e3-build)")
    parser.add_argument("--scale", type=int, default=2, help="internal render scale (default 2)")
    parser.add_argument("--max-steps", type=int, default=600, help="free-run vblank limit per phase (default 600)")
    return parser


def parse_args(argv):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.selftest and args.out is None:
        parser.error("OUTDIR is needed unless --selftest is given")
    if args.max_steps < 1:
        parser.error("--max-steps must be at least 1")
    if args.card < 1:
        parser.error("--card must be positive")
    return args


def compare_hashes(scrubbed, free_run):
    """Rows (phase, scrub hash, free hash, same?) for two {phase: hash} maps."""
    rows = []
    for phase in sorted(set(scrubbed) | set(free_run)):
        left, right = scrubbed.get(phase), free_run.get(phase)
        rows.append((phase, left, right, left is not None and right is not None and left == right))
    return rows


def default_exe():
    for name in ("YGO_EXE", "YFM_EXECUTABLE"):
        if os.environ.get(name):
            return Path(os.environ[name])
    for candidate in (REPO / "tmp/pc/e3-build/memories-pc.exe", REPO / "tmp/pc/game32/memories-pc.exe"):
        if candidate.is_file():
            return candidate
    return REPO / "tmp/pc/e3-build/memories-pc.exe"


def selftest():
    """Checks the pure parts; raises AssertionError on a regression."""
    assert parse_args(["--selftest"]).phases == PHASES
    assert parse_args(["out", "--phases", "0,0.5,1"]).phases == (0.0, 0.5, 1.0)
    for bad in ([], ["out", "--phases", "1.5"], ["out", "--phases", ""], ["out", "--max-steps", "0"]):
        with redirect_stderr(io.StringIO()):
            try:
                parse_args(bad)
            except SystemExit as exc:
                assert exc.code != 0, bad
            else:
                raise AssertionError(f"accepted bad arguments: {bad}")
    same = compare_hashes({0.0: 0x11, 0.5: 0x22}, {0.0: 0x11, 0.5: 0x22})
    assert all(row[3] for row in same) and len(same) == 2, same
    mixed = compare_hashes({0.0: 0x11, 0.5: 0x22}, {0.0: 0x11, 0.5: 0x33, 1.0: 0x44})
    assert [row[3] for row in mixed] == [True, False, False], mixed
    assert mixed[1][1] == 0x22 and mixed[2][2] == 0x44, mixed
    print("transport_demo selftest: ok (arguments, phase grid, hash compare)")
    return 0


def load_client():
    sys.path.insert(0, str(REPO / "tools/pc"))
    import yfm_control  # noqa: E402
    sys.path.insert(0, str(REPO / "tools/hd-models"))
    global rigkit
    import rigkit  # noqa: E402
    return yfm_control


def game_settings(args):
    return {"mod.3d-monsters": 1, "mod.3d-monsters.attack": 2, "mod.studio-preview": 1, "mod.dragon-test": 0, "mod.native-test": 0, "mod.angel-test": 0,
            "mod.camera-pin": 1, "internal_scale": args.scale}


def make_attack_state(yc, args, state):
    """One duel up to the attack commit, saved in `state` (as field_attack.py does)."""
    hand = [58, args.card, args.card, 332, 683]
    with yc.Game(executable=args.exe, out=args.out / "make", settings=game_settings(args),
                 env=GAME_ENV, headless=False) as game:
        game.goto("duel", opponent=1, deck=",".join(str(card) for card in hand))
        game.duel_ready(before_deal=lambda g: g.arrange_deck(0, hand))
        rigkit.play_at(game, 0, 4, face_up=True)  # the filler the game asks for every turn
        game.end_turn()
        game.wait_turn(("hand",))
        rigkit.play_at(game, 0, 1, face_up=True)  # the dragon
        field = game.field()
        columns = [column for column, card in enumerate(field[2]) if card]
        if not columns:
            raise RuntimeError("the dragon was not placed on the field")
        targets = [column for column, card in enumerate(field[1]) if card]
        game._settle = lambda *a, **k: game.save(state)   # save at the attack commit
        game.attack(columns[0], targets[0] if targets else None)
    return state


def open_state(yc, args):
    return yc.Game(executable=args.exe, out=args.out / "run", settings=game_settings(args),
                   env=GAME_ENV, headless=False)


def phase_of(game):
    """The phase the engine last used, from `anim get` (`at`); None when absent."""
    try:
        return float(game.anim_get().get("at", 0.0))
    except (TypeError, ValueError):
        return None


def scrub_pass(yc, args, state, phases):
    """Pause, scrub each phase, shoot it; returns {phase: (hash, actual phase)}."""
    shots, result = {}, {}
    with open_state(yc, args) as game:
        game.load(state)
        game.anim_pause()
        game.step(1)
        for phase in phases:
            game.anim_phase(phase)
            game.step(1)
            path = args.out / "scrub" / f"phase-{phase:.2f}.png"
            game.shot(path)
            result[phase] = (game.hash(), phase_of(game))
            shots[phase] = path
    return result, shots


def free_run_pass(yc, args, state, phases):
    """Free play from the same state; pause near each phase; returns {phase: (hash, actual phase)}."""
    shots, result = {}, {}
    with open_state(yc, args) as game:
        game.load(state)
        game.anim_frame(-1)
        game.anim_phase(-1.0)
        game.anim_speed(1.0)
        game.anim_resume()
        for phase in phases:
            steps, actual = 0, phase_of(game)
            while (actual is None or actual < phase - 1e-4) and steps < args.max_steps:
                game.step(1)
                steps += 1
                actual = phase_of(game)
            if actual is None:
                raise RuntimeError("anim get does not report the current phase (at=)")
            game.anim_pause()
            path = args.out / "free" / f"phase-{phase:.2f}.png"
            game.shot(path)
            result[phase] = (game.hash(), actual)
            shots[phase] = path
            game.anim_resume()
    return result, shots


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.selftest:
        return selftest()
    if not os.environ.get("MEMORIES_DISC"):
        sys.exit("transport_demo: no disc: set MEMORIES_DISC (--selftest runs without one)")
    args.exe = Path(args.exe) if args.exe else default_exe()
    if not Path(args.exe).is_file():
        sys.exit(f"transport_demo: no game at {args.exe}")
    if not (Path(args.exe).parent / "mods" / "studio-preview").is_dir():
        print(f"transport_demo: warning: studio-preview is not installed beside {args.exe}", flush=True)
    args.out = args.out.resolve()
    args.out.mkdir(parents=True, exist_ok=True)
    yc = load_client()

    state = args.out / "attack.state"
    if not state.exists():
        print("setting up the attack...", flush=True)
        make_attack_state(yc, args, state)
    print("pausing and scrubbing...", flush=True)
    scrubbed, scrub_shots = scrub_pass(yc, args, state, args.phases)
    print("free run...", flush=True)
    free, free_shots = free_run_pass(yc, args, state, args.phases)
    print("phase  scrub-hash  scrub-at  free-hash  free-at  same", flush=True)
    for phase, left, right, same in compare_hashes({p: v[0] for p, v in scrubbed.items()},
                                                   {p: v[0] for p, v in free.items()}):
        left_at, right_at = scrubbed[phase][1], free[phase][1]
        print(f"{phase:5.2f}  {left:08x}  {left_at:8.4f}  {right:08x}  {right_at:7.4f}  {'yes' if same else 'no'}",
              flush=True)
        print(f"       scrub {scrub_shots[phase]}", flush=True)
        print(f"       free  {free_shots[phase]}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
