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
    scene_measure.py trace                    M1, M2, M4 per triangle and vertex

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

# Camera moves from the state, with the Hand camera mod (mods/hand-camera):
# held L1 (0400) turns left, 20 units a frame of a 4096 turn; held L3 (0002)
# brings the camera closer, R3 (0004) takes it away, 6 a frame from 600
# (200 to 1400). Away is not useful here: past ~900 the duel's fog (black far
# colour) swallows the field. Frames are this run's; the camera stays where
# it is left, and the capture is at CAPTURE_FRAME.
CAMERAS = {
    "near": "60:0002,110:0000",                   # closer: 600 to 300
    "near-half": "60:0002,85:0000",               # closer, 600 to 450
}
TURN_STEP, TURN = 20, 4096


def camera_input(camera):
    """A CAMERAS name; turn:<degrees> at the duel's own distance (negative
    left with L1, positive right with R1), which keeps the field's edges in
    the picture as in play; or MEMORIES_INPUT itself."""
    if camera.startswith("turn:"):
        degrees = float(camera[5:])
        frames = max(1, round(abs(degrees) / 360 * TURN / TURN_STEP))
        return f"60:{'0400' if degrees < 0 else '0800'},{60 + frames}:0000"
    return CAMERAS.get(camera, camera)


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


def capture(options, path, pgxp, scale, frame=CAPTURE_FRAME, trace=None, input=""):
    if not os.path.exists(state_path(options)):
        make_state(options)
    name = os.path.splitext(os.path.basename(path))[0]
    extra = {
        "MEMORIES_LOAD_STATE": state_path(options),
        "MEMORIES_PGXP": str(pgxp),
        "MEMORIES_INTERNAL_SCALE": str(scale),
        "MEMORIES_DUMP_FRAME": str(frame),
        "MEMORIES_DUMP_PICTURE": "1",
        "MEMORIES_DUMP_PATH": os.path.abspath(path),
    }
    if trace:
        extra["MEMORIES_PGXP_MEASURE"] = os.path.abspath(trace)
    if input:
        extra["MEMORIES_INPUT"] = input
    text = run_game(options, name, extra)
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


def read_csv(path):
    with open(path) as handle:
        names = handle.readline().strip().split(",")
        return [dict(zip(names, line.strip().split(","))) for line in handle if line.strip()]


def percentile(values, share):
    return values[min(len(values) - 1, int(share * len(values)))] if values else 0.0


def summarize_trace(prefix, width, height):
    """M1, M2 and M4 of one traced frame, against the thresholds fixed in
    progress.md before measuring: a texel shift of 1 picture pixel is
    visibly changed, 2 clearly; a vertex rounding of 1 pixel is noticeable in
    motion. Areas are summed over triangles, which overlap, so a share of the
    frame is an upper bound."""
    frame = width * height
    triangles = read_csv(prefix + ".triangles.csv")
    # Positions are in VRAM's picture units: the game draws into two buffers
    # side by side, so a frame can sit a whole picture width to the right.
    for t in triangles:
        t["x"], t["y"] = str(float(t["x"]) % width), str(float(t["y"]) % height)
    kinds = {kind: [t for t in triangles if t["kind"] == kind] for kind in "pma"}
    perspective = kinds["p"]
    shifts = sorted(float(t["shift"]) for t in perspective if float(t["shift"]) >= 0)
    area = lambda rows: sum(float(t["area"]) for t in rows)
    print(f"  textured triangles: {len(triangles)}: {len(perspective)} perspective, "
          f"{len(kinds['m'])} mixed, {len(kinds['a'])} affine")
    print(f"  M1 texel shift (perspective): max {shifts[-1] if shifts else 0:.2f} px, "
          f"median {percentile(shifts, 0.5):.2f}, 95th {percentile(shifts, 0.95):.2f}")
    for limit, word in ((0.5, "under 0.5 px (invisible)"), (1, "0.5 to 1 px"), (2, "1 to 2 px (visibly changed)"),
                        (float("inf"), "2 px or more (clearly visible)")):
        low = {0.5: 0, 1: 0.5, 2: 1, float("inf"): 2}[limit]
        rows = [t for t in perspective if low <= float(t["shift"]) < limit]
        print(f"    {word}: {len(rows)} triangles, {area(rows) / frame * 100:.2f}% of the frame")
    mixed = kinds["m"]
    edge = [t for t in mixed if min(float(t["x"]), width - float(t["x"]), float(t["y"]), height - float(t["y"]))
            < 0.05 * min(width, height)]
    print(f"  M2 mixed triangles: {len(mixed)}, {area(mixed) / frame * 100:.2f}% of the frame; "
          f"{len(edge)} with their centre near the picture's edge")
    if os.path.exists(prefix + ".rejects.csv"):
        r = read_csv(prefix + ".rejects.csv")[0]
        total = sum(int(r[k]) for k in ("kept", "saturated", "behind", "window"))
        print(f"  projections: {total}; kept precise {r['kept']}, rejected: division saturated {r['saturated']}, "
              f"not in front {r['behind']}, outside the window {r['window']} (farthest miss {r['farthest_miss']} "
              f"console px)")
    # A vertex's true position minus the console pixel it was put on. That
    # pixel is floored (and the GTE's division is approximate), so the
    # offsets share a bias, about +0.77 console pixels on each axis: level 2
    # moves the models by it as a whole. What wobbles in motion is the
    # spread around it, reported apart.
    vertices = read_csv(prefix + ".vertices.csv")
    if not vertices:
        print("  M4: no precise vertices")
        return
    dx = [float(v["dx"]) for v in vertices]
    dy = [float(v["dy"]) for v in vertices]
    bias_x, bias_y = sum(dx) / len(dx), sum(dy) / len(dy)
    spread = sorted(((x - bias_x) ** 2 + (y - bias_y) ** 2) ** 0.5 for x, y in zip(dx, dy))
    width_x = percentile(sorted(dx), 0.95) - percentile(sorted(dx), 0.05)
    width_y = percentile(sorted(dy), 0.95) - percentile(sorted(dy), 0.05)
    noticeable = sum(1 for r in spread if r >= 1)
    print(f"  M4 vertex offset from its console pixel: {len(vertices)} vertices; bias {bias_x:+.2f}, {bias_y:+.2f} px; "
          f"5th-95th width {width_x:.2f} x {width_y:.2f} px")
    print(f"    around the bias: median {percentile(spread, 0.5):.2f} px, 95th {percentile(spread, 0.95):.2f}, "
          f"max {spread[-1]:.2f}; {noticeable} ({noticeable / len(spread) * 100:.1f}%) at 1 px or more")


def overlay(prefix, width, height):
    """<prefix>.overlay.png: the capture darkened, with the triangles that
    matter painted over it: red a texel shift of 2 px or more, yellow 1 to 2,
    blue mixed (drawn affine beside perspective neighbours)."""
    w, h, rgb = read_ppm(prefix + ".ppm")
    out = bytearray(value // 3 for value in rgb)
    with open(prefix + ".triangles.csv") as handle:
        rows = list(csv_rows(handle))
    for t in rows:
        shift = float(t["shift"])
        colour = (b"\x40\x80\xff" if t["kind"] == "m" else b"\xff\x30\x30" if shift >= 2
                  else b"\xff\xe0\x30" if shift >= 1 else None)
        if colour is None:
            continue
        # Back from the second draw buffer, by the offset of the centre.
        ox, oy = float(t["x"]) - float(t["x"]) % width, float(t["y"]) - float(t["y"]) % height
        xs = [float(t[f"x{i}"]) - ox for i in range(3)]
        ys = [float(t[f"y{i}"]) - oy for i in range(3)]
        area = (xs[1] - xs[0]) * (ys[2] - ys[0]) - (xs[2] - xs[0]) * (ys[1] - ys[0])
        if not area:
            continue
        for y in range(max(0, int(min(ys))), min(h, int(max(ys)) + 1)):
            for x in range(max(0, int(min(xs))), min(w, int(max(xs)) + 1)):
                px, py = x + 0.5, y + 0.5
                b1 = ((px - xs[0]) * (ys[2] - ys[0]) - (xs[2] - xs[0]) * (py - ys[0])) / area
                b2 = ((xs[1] - xs[0]) * (py - ys[0]) - (px - xs[0]) * (ys[1] - ys[0])) / area
                if b1 >= 0 and b2 >= 0 and b1 + b2 <= 1:
                    at = (y * w + x) * 3
                    out[at:at + 3] = bytes((rgb[at + c] + colour[c]) // 2 for c in range(3))
    write_png(prefix + ".overlay.png", w, h, bytes(out))


def csv_rows(handle):
    names = handle.readline().strip().split(",")
    for line in handle:
        if line.strip():
            yield dict(zip(names, line.strip().split(",")))


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
    one.add_argument("--camera", default="", help="a name from CAMERAS, or MEMORIES_INPUT from the state")
    pair = sub.add_parser("diff")
    pair.add_argument("a")
    pair.add_argument("b")
    pair.add_argument("--mask")
    sub.add_parser("controls")
    compare = sub.add_parser("compare")
    compare.add_argument("--scales", default="2,4")
    traced = sub.add_parser("trace")
    traced.add_argument("--scales", default="2,4")
    traced.add_argument("--camera", default="", help="a name from CAMERAS, or MEMORIES_INPUT from the state")
    traced.add_argument("--name", default="", help="names the files: trace_<name>_<scale>x")
    options = parser.parse_args()
    here = lambda name: os.path.join(options.out, name)

    if options.command == "state":
        make_state(options)
    elif options.command == "capture":
        capture(options, options.path, options.pgxp, options.scale, options.frame,
                input=camera_input(options.camera))
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
    elif options.command == "trace":
        view = camera_input(options.camera)
        for scale in (int(s) for s in options.scales.split(",")):
            prefix = here(f"trace_{options.name}_{scale}x" if options.name else f"trace_{scale}x")
            capture(options, prefix + ".ppm", 1, scale, trace=prefix, input=view)
            print(f"{scale}x, Textures ({320 * scale}x{240 * scale}):")
            summarize_trace(prefix, 320 * scale, 240 * scale)
            overlay(prefix, 320 * scale, 240 * scale)
            print(f"  overlay: {prefix}.overlay.png (red: shift >= 2 px, yellow: 1-2 px, blue: mixed)")


if __name__ == "__main__":
    main()
