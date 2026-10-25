"""Procedural root-motion tracks for poses a clip does not cover.

Pure Python 3.12, stdlib only. A track is a list with one entry per frame:
{"pos": (x, y, z), "rot": (qx, qy, qz, qw), "scale": s}, an offset applied on
top of the model's rest/idle pose at its root. y is up. forward=(fx, fz) is a
horizontal unit vector; the model faces +z by default, i.e. forward=(0.0, 1.0).
"""

import math

IDENTITY = (0.0, 0.0, 0.0, 1.0)

KINDS = ("recoil", "collapse", "brace", "lunge", "rise", "idle")


def ease(t, kind):
    """Easing factor in 0..1. t is clamped to [0, 1]; kind in
    linear/in/out/inout. 0 -> 0 and 1 -> 1 for every kind."""
    t = max(0.0, min(1.0, t))
    if kind == "linear":
        return t
    if kind == "in":
        return t * t
    if kind == "out":
        return 1.0 - (1.0 - t) ** 2
    if kind == "inout":
        return 3.0 * t * t - 2.0 * t ** 3
    raise ValueError("unknown ease kind: %r" % (kind,))


def quat_axis_angle(axis, angle):
    """Unit quaternion (x, y, z, w) for rotate about unit axis by angle rad.
    The axis is normalised inside. A zero axis raises ValueError."""
    ax, ay, az = float(axis[0]), float(axis[1]), float(axis[2])
    length = math.sqrt(ax * ax + ay * ay + az * az)
    if length <= 0.0:
        raise ValueError("zero rotation axis")
    ax /= length
    ay /= length
    az /= length
    s = math.sin(angle / 2.0)
    return (ax * s, ay * s, az * s, math.cos(angle / 2.0))


def quat_mul(a, b):
    """Hamilton product of two quaternions, (x, y, z, w) order."""
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
        aw * bw - ax * bx - ay * by - az * bz,
    )


def quat_conjugate(q):
    x, y, z, w = q
    return (-x, -y, -z, w)


def quat_rotate(q, v):
    """Rotate vector v=(x,y,z) by unit quaternion q. Returns (x, y, z)."""
    x, y, z = v
    qc = quat_mul(q, (x, y, z, 0.0))
    r = quat_mul(qc, quat_conjugate(q))
    return (r[0], r[1], r[2])


def axis_back(forward):
    """Horizontal axis perpendicular to forward that tips the model's top back.
    For forward=(fx, fz) (model faces +z by default) this is (-fz, 0, fx)."""
    fx, fz = forward
    return (-fz, 0.0, fx)


def tip(forward, angle):
    """Quaternion tipping the model backwards by `angle` radians about the
    horizontal axis perpendicular to forward. A positive angle moves the top
    (0,1,0) away from forward (opposite to its horizontal direction)."""
    return quat_axis_angle(axis_back(forward), angle)


def _frame(pos, rot, scale):
    return {"pos": pos, "rot": rot, "scale": scale}


def recoil(frames, height, forward=(0.0, 1.0), strength=0.08):
    """Pushed back along -forward by `strength * height` and tipped back
    0.12 rad at 30% of the track (ease out), then eased back to identity at
    the last frame (ease inout). Frame 0 and the last frame are identity."""
    if frames < 2:
        raise ValueError("frames must be >= 2")
    fx, fz = forward
    peak = 0.3
    peak_pos = (-fx * strength * height, 0.0, -fz * strength * height)
    track = []
    for i in range(frames):
        if i == 0 or i == frames - 1:
            track.append(_frame((0.0, 0.0, 0.0), IDENTITY, 1.0))
            continue
        t = i / (frames - 1)
        if t <= peak:
            f = ease(t / peak, "out")
        else:
            f = 1.0 - ease((t - peak) / (1.0 - peak), "inout")
        pos = (peak_pos[0] * f, peak_pos[1] * f, peak_pos[2] * f)
        rot = quat_axis_angle(axis_back(forward), 0.12 * f)
        track.append(_frame(pos, rot, 1.0))
    return track


def collapse(frames, height, forward=(0.0, 1.0), sink=0.35):
    """Tip the model back up to 1.4 rad over the first 60% (ease in) while it
    sinks down by `sink * height` and shifts back along -forward by 0.25 *
    height; then holds that final pose to the end. Frame 0 is identity."""
    if frames < 2:
        raise ValueError("frames must be >= 2")
    fx, fz = forward
    peak_t = 0.6
    sink_pos = (-fx * 0.25 * height, -sink * height, -fz * 0.25 * height)
    track = []
    for i in range(frames):
        if i == 0:
            track.append(_frame((0.0, 0.0, 0.0), IDENTITY, 1.0))
            continue
        t = i / (frames - 1)
        if t <= peak_t:
            f = ease(t / peak_t, "in")
        else:
            f = 1.0
        pos = (sink_pos[0] * f, sink_pos[1] * f, sink_pos[2] * f)
        rot = quat_axis_angle(axis_back(forward), 1.4 * f)
        track.append(_frame(pos, rot, 1.0))
    return track


def brace(frames, height, forward=(0.0, 1.0), crouch=0.12):
    """Crouch down by `crouch * height` and lean forward 0.15 rad (a negative
    tip), both reached by 40% of the track easing out; hold the pose until
    80%; then ease back to identity at the last frame. First and last frame are
    identity."""
    if frames < 2:
        raise ValueError("frames must be >= 2")
    t_in, t_hold, t_out = 0.4, 0.8, 1.0
    peak_pos = (0.0, -crouch * height, 0.0)
    track = []
    for i in range(frames):
        t = i / (frames - 1)
        if i == 0 or i == frames - 1:
            track.append(_frame((0.0, 0.0, 0.0), IDENTITY, 1.0))
            continue
        if t <= t_in:
            f = ease(t / t_in, "out")
        elif t <= t_hold:
            f = 1.0
        else:
            f = 1.0 - ease((t - t_hold) / (t_out - t_hold), "in")
        pos = (peak_pos[0] * f, peak_pos[1] * f, peak_pos[2] * f)
        rot = quat_axis_angle(axis_back(forward), -0.15 * f)
        track.append(_frame(pos, rot, 1.0))
    return track


def lunge(frames, height, strike_frame, forward=(0.0, 1.0), reach=0.3):
    """Anticipate back (pos -forward * 0.1*height, tip back 0.1 rad) easing in
    over the first half up to the strike, then lunge forward (pos +forward *
    reach*height, tip forward 0.2 rad) easing out to strike_frame, then ease
    back to identity at the last frame. `strike_frame` must satisfy
    0 < strike_frame < frames - 1, else ValueError. At strike_frame the
    position projected along forward equals `reach * height`."""
    if frames < 2:
        raise ValueError("frames must be >= 2")
    if not (0 < strike_frame < frames - 1):
        raise ValueError("strike_frame must be 0 < strike_frame < frames - 1")
    fx, fz = forward
    a = strike_frame * 0.5  # frame index of the anticipation midpoint
    track = []
    for i in range(frames):
        if i == 0 or i == frames - 1:
            track.append(_frame((0.0, 0.0, 0.0), IDENTITY, 1.0))
            continue
        if i < a:
            f = ease(i / a, "in")
            pos_fwd = -0.1 * height * f
            angle = 0.1 * f
        elif i <= strike_frame:
            f = ease((i - a) / (strike_frame - a), "out")
            pos_fwd = height * (-0.1 + (reach + 0.1) * f)
            angle = 0.1 - 0.3 * f
        else:
            f = ease((i - strike_frame) / (frames - 1 - strike_frame), "inout")
            pos_fwd = reach * height * (1.0 - f)
            angle = -0.2 * (1.0 - f)
        pos = (fx * pos_fwd, 0.0, fz * pos_fwd)
        rot = quat_axis_angle(axis_back(forward), angle)
        track.append(_frame(pos, rot, 1.0))
    return track


def rise(frames, height, bob=0.05):
    """Win pose: the model lifts up by `bob * height` and back down over the
    track, one sine hump (`bob * height * sin(pi * t)`) so the endpoints are
    at rest. Scale peaks at 1.02 at the hump. Both ends are identity."""
    if frames < 2:
        raise ValueError("frames must be >= 2")
    track = []
    for i in range(frames):
        if i == 0 or i == frames - 1:
            track.append(_frame((0.0, 0.0, 0.0), IDENTITY, 1.0))
            continue
        t = i / (frames - 1)
        s = math.sin(math.pi * t)
        pos = (0.0, bob * height * s, 0.0)
        rot = IDENTITY
        scale = 1.0 + 0.02 * s
        track.append(_frame(pos, rot, scale))
    return track


def idle(frames, height, forward=(0.0, 1.0), bob=0.01, sway=0.02, cycles=1):
    """Idle bob and sway loop.
    Raises ValueError when frames < 2 or cycles < 1.
    """
    if frames < 2:
        raise ValueError("frames must be >= 2")
    if cycles < 1:
        raise ValueError("cycles must be >= 1")
    fx, fz = forward
    track = []
    for i in range(frames - 1):
        t = i / (frames - 1)
        y = bob * height * math.sin(2 * math.pi * cycles * t)
        angle = sway * math.sin(2 * math.pi * cycles * t + math.pi / 2)
        rot = quat_axis_angle((0.0, 1.0, 0.0), angle)
        track.append(_frame((0.0, y, 0.0), rot, 1.0))
    track.append(dict(track[0]))   # the last frame is the first: a seamless loop
    return track

def sample(kind, frames, height, **kw):
    """Dispatch to one of the track generators named in KINDS."""
    if kind not in KINDS:
        raise ValueError(f"unknown kind: {kind!r}")
    fn = globals()[kind]
    return fn(frames, height, **kw)


def check_track(track, frames):
    """Return a list of problem strings; empty means the track satisfies the
    invariants (correct length, finite numbers, unit rotation, scale > 0)."""
    problems = []
    if len(track) != frames:
        problems.append(f"length {len(track)} != frames {frames}")
    for i, f in enumerate(track):
        pos = f["pos"]
        rot = f["rot"]
        scale = f["scale"]
        for j, v in enumerate((*pos, *rot, scale)):
            if not math.isfinite(v):
                problems.append(f"frame {i} value {j} is not finite")
        if abs(sum(c * c for c in rot) - 1.0) > 1e-6:
            problems.append(f"frame {i} rot is not unit")
        if not (scale > 0.0):
            problems.append(f"frame {i} scale {scale} <= 0")
    return problems


if __name__ == "__main__":
    pass
