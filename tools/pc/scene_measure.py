#!/usr/bin/env python3
"""Reproduce the test scene and measure what a render setting changes in it.

The scene is the Test scenes mod's "field" (mods/test-scenes): L1 + Cross on
Option on the title menu opens a duel with Simon Muran on the standard field,
ten chosen monsters already on it. This script gets there by itself and
captures frames, windowed (OpenGL is on) with deterministic timing.

A replay from boot is not pixel-identical: two runs can drift one VBlank
apart during boot, and the field's shimmer and the monsters' animations run
on VBlanks. So the scene is reached once and saved as a state, and every
capture reloads that state: the same state and settings give the same frame.
A state only loads in the build that made it; `state` rebuilds it after a
rebuild of the game.

Every run gets a user folder of its own under the output directory (default
settings, no saves, no texture packs), and every setting that matters is
pinned on the command line, so a capture depends on nothing but the build,
the arguments and the machine.

    scene_measure.py state                    reach the scene, save the state
    scene_measure.py capture --pgxp 1 --scale 2 out.ppm
    scene_measure.py diff a.ppm b.ppm [--mask mask.png]
    scene_measure.py controls                 the determinism controls
    scene_measure.py compare                  Off vs Textures at each scale

`controls` must pass before any `compare` number means anything: the same
setting twice, and Off vs Textures at 1x (where Precise geometry is off),
must both change 0 pixels. Captures go to tmp/pc/measure by default, PNG
beside each PPM."""
import argparse, os, re, shutil, struct, subprocess, sys, zlib

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXE = "memories-pc.exe" if os.name == "nt" else "memories-pc"

# From cold boot to the scene, in the raw controller (SIO) layout, not
# input.h's: Start at the title, Down four times to Option, then Cross (4000)
# with L1 (0400) held.
SCENE_INPUT = ("910:0008,916:0000,1000:0040,1006:0000,1020:0040,1026:0000,"
               "1040:0040,1046:0000,1060:0040,1066:0000,1100:4400,1106:0000")
STATE_FRAME = 1700    # the field is filled at 1557; the camera has settled
CAPTURE_FRAME = 300   # frames into a run from the state (it resumes near 30)


def run_game(options, name, extra):
    """One windowed, deterministic run; returns its log's text."""
    out = os.path.abspath(options.out)
    os.makedirs(out, exist_ok=True)
    env = {key: value for key, value in os.environ.items() if not key.startswith("MEMORIES_")}
    env.update({
        "MEMORIES_USER_DIR": os.path.join(out, "user"),
        "MEMORIES_DETERMINISTIC": "1",
        "MEMORIES_MOD_TEST_SCENES": "1",
        "MEMORIES_MOD_3D_MONSTERS": "1",
        "MEMORIES_TRACE": "mods",
        "MEMORIES_CHECK_FOR_UPDATES": "0",
        "MEMORIES_SCALE": "2",  # the window; the picture is dumped at the internal scale
    })
    env.update(extra)
    log = os.path.join(out, name + ".log")
    with open(log, "w") as err, open(os.path.join(out, name + ".out"), "w") as std:
        code = subprocess.call([os.path.join(options.game, EXE)], env=env, stdout=std, stderr=err, cwd=ROOT)
    text = open(log, errors="replace").read()
    if code != 0:
        sys.exit(f"{name}: the game exited with {code}; see {log}")
    return text


def state_path(options):
    return os.path.join(os.path.abspath(options.out), "field.state")


def make_state(options):
    text = run_game(options, "state", {
        "MEMORIES_INPUT": SCENE_INPUT,
        "MEMORIES_PGXP": "0",
        "MEMORIES_INTERNAL_SCALE": "2",
        "MEMORIES_SAVE_STATE": f"{STATE_FRAME}:{state_path(options)}",
        "MEMORIES_DUMP_FRAME": str(STATE_FRAME + 5),
        "MEMORIES_DUMP_PICTURE": "1",
        "MEMORIES_DUMP_PATH": os.path.join(os.path.abspath(options.out), "state.ppm"),
    })
    frames = {what: int(frame) for frame, what in
              re.findall(r"frame (\d+) vb \d+ mods\] (?:test-scenes: )+(field scene armed|field filled)", text)}
    if "field filled" not in frames or not os.path.exists(state_path(options)):
        sys.exit("state: the scene was not reached; see state.log (is the Test scenes mod built?)")
    print(f"state: armed at frame {frames.get('field scene armed')}, filled at {frames['field filled']}, "
          f"saved at {STATE_FRAME}: {state_path(options)}")


def capture(options, path, pgxp, scale, frame=CAPTURE_FRAME):
    if not os.path.exists(state_path(options)):
        make_state(options)
    name = os.path.splitext(os.path.basename(path))[0]
    text = run_game(options, name, {
        "MEMORIES_LOAD_STATE": state_path(options),
        "MEMORIES_PGXP": str(pgxp),
        "MEMORIES_INTERNAL_SCALE": str(scale),
        "MEMORIES_DUMP_FRAME": str(frame),
        "MEMORIES_DUMP_PICTURE": "1",
        "MEMORIES_DUMP_PATH": os.path.abspath(path),
    })
    if "state load failed" in text or not os.path.exists(path):
        sys.exit(f"{name}: the state did not load (a different build made it?); run `state` again")
    width, height, _ = read_ppm(path)
    if (width, height) != (320 * scale, 240 * scale):
        sys.exit(f"{name}: {width}x{height} is not internal {scale}x; the setting did not take")
    write_png(path[:-4] + ".png", *read_ppm(path))
    return path


def read_ppm(path):
    data = open(path, "rb").read()
    fields, at = [], 0
    while len(fields) < 4:
        while data[at:at + 1].isspace():
            at += 1
        if data[at:at + 1] == b"#":
            at = data.index(b"\n", at)
            continue
        end = at
        while not data[end:end + 1].isspace():
            end += 1
        fields.append(data[at:end])
        at = end
    return int(fields[1]), int(fields[2]), data[at + 1:]


def write_png(path, width, height, rgb):
    rows = b"".join(b"\0" + rgb[y * width * 3:(y + 1) * width * 3] for y in range(height))
    chunk = lambda kind, body: struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))
    with open(path, "wb") as handle:
        handle.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)) +
                     chunk(b"IDAT", zlib.compress(rows, 6)) + chunk(b"IEND", b""))


def diff(a_path, b_path, mask=None):
    """(changed pixels, share of the frame, max channel delta); the mask shows
    changed pixels white over a darkened copy of the first picture."""
    wa, ha, a = read_ppm(a_path)
    wb, hb, b = read_ppm(b_path)
    if (wa, ha) != (wb, hb):
        sys.exit(f"diff: {wa}x{ha} against {wb}x{hb}")
    changed, worst = 0, 0
    out = bytearray(len(a)) if mask else None
    for at in range(0, len(a), 3):
        delta = max(abs(a[at] - b[at]), abs(a[at + 1] - b[at + 1]), abs(a[at + 2] - b[at + 2]))
        if delta:
            changed += 1
            worst = max(worst, delta)
        if out is not None:
            out[at:at + 3] = b"\xff\xff\xff" if delta else bytes((a[at] // 4, a[at + 1] // 4, a[at + 2] // 4))
    if out is not None:
        write_png(mask, wa, ha, bytes(out))
    return changed, changed / (wa * ha), worst


def describe(label, result):
    changed, share, worst = result
    print(f"{label}: {changed} changed pixels ({share * 100:.3f}%), max delta {worst}")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--game", default=os.path.join(ROOT, "tmp/pc/game32dbg"), help="the build to run")
    parser.add_argument("--out", default=os.path.join(ROOT, "tmp/pc/measure"), help="captures, logs, the state")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("state")
    one = sub.add_parser("capture")
    one.add_argument("path")
    one.add_argument("--pgxp", type=int, default=0)
    one.add_argument("--scale", type=int, default=2)
    one.add_argument("--frame", type=int, default=CAPTURE_FRAME)
    pair = sub.add_parser("diff")
    pair.add_argument("a")
    pair.add_argument("b")
    pair.add_argument("--mask")
    sub.add_parser("controls")
    compare = sub.add_parser("compare")
    compare.add_argument("--scales", default="2,4")
    options = parser.parse_args()
    here = lambda name: os.path.join(options.out, name)

    if options.command == "state":
        make_state(options)
    elif options.command == "capture":
        capture(options, options.path, options.pgxp, options.scale, options.frame)
    elif options.command == "diff":
        describe("diff", diff(options.a, options.b, options.mask))
    elif options.command == "controls":
        results = [
            ("same setting twice (2x, Off)",
             diff(capture(options, here("c_twice_a.ppm"), 0, 2), capture(options, here("c_twice_b.ppm"), 0, 2))),
            ("1x, Off vs Textures (Precise geometry is off below 2x)",
             diff(capture(options, here("c_1x_off.ppm"), 0, 1), capture(options, here("c_1x_tex.ppm"), 1, 1))),
        ]
        for label, result in results:
            describe(label, result)
        failed = [label for label, result in results if result[0]]
        print("controls: " + ("FAILED: " + "; ".join(failed) if failed else "pass"))
        sys.exit(1 if failed else 0)
    elif options.command == "compare":
        for scale in (int(s) for s in options.scales.split(",")):
            off = capture(options, here(f"off_{scale}x.ppm"), 0, scale)
            tex = capture(options, here(f"tex_{scale}x.ppm"), 1, scale)
            describe(f"{scale}x, Off vs Textures", diff(off, tex, here(f"mask_{scale}x.png")))


if __name__ == "__main__":
    main()
