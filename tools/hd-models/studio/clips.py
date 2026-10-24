"""S5 animation clip statistics and checks (headless, no numpy)."""
from studio import audit


def clip_bbox(P):
    """Axis-aligned bounding box over all frames and joints.

    Returns {"lo": (x, y, z), "hi": (x, y, z)}; zeros for an empty clip.
    """
    zero = {"lo": (0.0, 0.0, 0.0), "hi": (0.0, 0.0, 0.0)}
    if not P:
        return zero
    lo_x = lo_y = lo_z = None
    hi_x = hi_y = hi_z = None
    for frame in P:
        for pos in frame:
            x, y, z = pos
            if lo_x is None:
                lo_x = hi_x = x
                lo_y = hi_y = y
                lo_z = hi_z = z
            else:
                if x < lo_x:
                    lo_x = x
                if y < lo_y:
                    lo_y = y
                if z < lo_z:
                    lo_z = z
                if x > hi_x:
                    hi_x = x
                if y > hi_y:
                    hi_y = y
                if z > hi_z:
                    hi_z = z
    return {"lo": (lo_x, lo_y, lo_z), "hi": (hi_x, hi_y, hi_z)}


def loop_gap(P):
    """Largest distance any joint moves between first and last frame.

    P[f][j] is a position (x, y, z); returns 0.0 for fewer than 2 frames.
    """
    if len(P) < 2:
        return 0.0
    first = P[0]
    last = P[-1]
    best = 0.0
    for j in range(len(first)):
        fx, fy, fz = first[j]
        lx, ly, lz = last[j]
        d = ((lx - fx) ** 2 + (ly - fy) ** 2 + (lz - fz) ** 2) ** 0.5
        if d > best:
            best = d
    return best


def root_drift(P):
    """Root (joint 0) drift from the first to the last frame.

    Returns {"distance": float, "axis": (dx, dy, dz)}; zeros for fewer
    than 2 frames.
    """
    zero = {"distance": 0.0, "axis": (0.0, 0.0, 0.0)}
    if len(P) < 2:
        return zero
    fx, fy, fz = P[0][0]
    lx, ly, lz = P[-1][0]
    axis = (lx - fx, ly - fy, lz - fz)
    dist = (axis[0] ** 2 + axis[1] ** 2 + axis[2] ** 2) ** 0.5
    return {"distance": dist, "axis": axis}


def speed_peak(P, fps):
    """Fastest joint step between consecutive frames.

    Speed is the distance a joint moves between frame f-1 and f, times
    ``fps``. Returns {"speed": float, "joint": int, "frame": int} where
    frame is f (the later frame of the pair). For fewer than 2 frames or
    no motion, {"speed": 0.0, "joint": 0, "frame": 0}.
    """
    zero = {"speed": 0.0, "joint": 0, "frame": 0}
    if len(P) < 2:
        return zero
    best = zero["speed"]
    best_joint = 0
    best_frame = 0
    prev = P[0]
    for f in range(1, len(P)):
        cur = P[f]
        n = len(prev)
        if len(cur) > n:
            n = len(cur)
        for j in range(n):
            px, py, pz = prev[j]
            cx, cy, cz = cur[j]
            d = ((cx - px) ** 2 + (cy - py) ** 2 + (cz - pz) ** 2) ** 0.5
            speed = d * fps
            if speed > best:
                best = speed
                best_joint = j
                best_frame = f
        prev = cur
    return {"speed": best, "joint": best_joint, "frame": best_frame}


def bone_stretch(P, parents):
    """Bone length ratios relative to frame 0.

    For each non-root bone (parent != -1) of non-zero length in frame 0,
    compares its length in every frame to its frame 0 length. Returns
    {"ratio_min": float, "ratio_max": float, "joint": int} where ``joint``
    is the bone with the largest deviation from 1.0; bones of zero length in
    frame 0 are skipped; 1.0/1.0/0 when there are no eligible bones.
    """
    if not P:
        return {"ratio_min": 1.0, "ratio_max": 1.0, "joint": 0}
    frame0 = P[0]
    ratio_min = 1.0
    ratio_max = 1.0
    best_dev = -1.0
    best_joint = 0
    for j in range(1, len(frame0)):
        p = parents[j]
        if p < 0:
            continue
        f0x, f0y, f0z = frame0[j]
        px, py, pz = frame0[p]
        base = ((f0x - px) ** 2 + (f0y - py) ** 2 + (f0z - pz) ** 2) ** 0.5
        if base == 0.0:
            continue
        b_min = 1.0
        b_max = 1.0
        for f in range(len(P)):
            cur = P[f]
            if j >= len(cur) or p >= len(cur):
                continue
            cx, cy, cz = cur[j]
            qx, qy, qz = cur[p]
            length = ((cx - qx) ** 2 + (cy - qy) ** 2 + (cz - qz) ** 2) ** 0.5
            ratio = length / base
            if ratio < b_min:
                b_min = ratio
            if ratio > b_max:
                b_max = ratio
        if b_min < ratio_min:
            ratio_min = b_min
        if b_max > ratio_max:
            ratio_max = b_max
        dev = max(1.0 - b_min, b_max - 1.0)
        if dev > best_dev:
            best_dev = dev
            best_joint = j
    return {"ratio_min": ratio_min, "ratio_max": ratio_max, "joint": best_joint}


def check_loop(name, clip):
    """Warn if a looping clip has a gap between first and last frame > 20 units."""
    P = clip["positions"]
    if not clip.get("loop"):
        return []
    gap = loop_gap(P)
    if gap > 20:
        n = int(round(gap))
        return [audit.finding("S5.loop-gap", "warn",
                              f"Clip {name}: the last frame is {n} units from the first.",
                              fix="Close the loop or turn Loop off.",
                              value=gap)]
    return []


def check_drift(name, clip):
    """Warn if root (joint 0) drifts > 100 units from first to last frame."""
    P = clip["positions"]
    distance = root_drift(P)["distance"]
    if distance > 100:
        n = int(round(distance))
        return [audit.finding("S5.root-drift", "warn",
                              f"Clip {name}: the root drifts {n} units.",
                              fix="Remove the root motion or accept it.",
                              value=distance)]
    return []


def check_speed(name, clip):
    """Warn if any joint's speed > 4000 units per second."""
    P = clip["positions"]
    fps = clip["fps"]
    speed = speed_peak(P, fps)["speed"]
    if speed > 4000:
        n = int(round(speed))
        return [audit.finding("S5.speed", "warn",
                              f"Clip {name}: a joint moves {n} units per second.",
                              fix="Retime the clip or cut the pop.",
                              value=speed)]
    return []


def check_stretch(name, clip, parents):
    """Warn if any bone's length leaves 0.8..1.25 of its rest length."""
    P = clip["positions"]
    bs = bone_stretch(P, parents)
    rmin = bs["ratio_min"]
    rmax = bs["ratio_max"]
    joint = bs["joint"]
    violating = []
    if rmax > 1.25:
        violating.append(rmax)
    if rmin < 0.8:
        violating.append(rmin)
    if not violating:
        return []
    ratio = max(violating, key=lambda r: abs(r - 1.0))
    n = int(round(ratio))
    return [audit.finding("S5.bone-stretch", "warn",
                          f"Clip {name}: bone {joint} changes length to {n} times its rest length.",
                          fix="Check the retarget.",
                          value=ratio)]


def run_s5(clips, parents):
    """Run all S5 stats and checks for a set of clips.

    Args:
        clips: dict of name -> clip (with "positions", "fps", "loop")
        parents: list of parent indices for each joint

    Returns:
        {"stats": {name: {loop_gap, root_drift, speed_peak, bone_stretch, bbox}},
         "findings": [...]}
    """
    stats = {}
    findings = []
    for name in sorted(clips.keys()):
        clip = clips[name]
        P = clip["positions"]
        fps = clip["fps"]
        stats[name] = {
            "loop_gap": loop_gap(P),
            "root_drift": root_drift(P),
            "speed_peak": speed_peak(P, fps),
            "bone_stretch": bone_stretch(P, parents),
            "bbox": clip_bbox(P),
        }
        findings.extend(check_loop(name, clip))
        findings.extend(check_drift(name, clip))
        findings.extend(check_speed(name, clip))
        findings.extend(check_stretch(name, clip, parents))
    return {"stats": stats, "findings": findings}
