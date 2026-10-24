"""The Model Studio's look and camera-move rules (S7): headless checks over a recipe, no UI.

    look = default_look()                  # the eight look defaults
    look = normalize_look(recipe["look"])  # a full look dict, defaults filled in
    findings = check_move_count(shots)     # S7 checks over camera moves
"""

from studio import audit

LOOK_DEFAULTS = {
    "ambient": 20,
    "light_gain": 100,
    "normal_strength": 180,
    "highlight": 100,
    "flip_green": True,
    "camera_near": 1000,
    "camera_keep": 50,
    "camera_scale": 100,
}


def default_look():
    """The eight look defaults, a fresh dict each call."""
    return dict(LOOK_DEFAULTS)


def normalize_look(d):
    """A full look dict: missing keys from the defaults, unknown keys dropped, values coerced."""
    out = default_look()
    for key, val in (d or {}).items():
        if key not in out:
            continue
        if key == "flip_green":
            out[key] = bool(val)
        else:
            try:
                out[key] = int(val)
            except (TypeError, ValueError):
                raise ValueError(f"look value {key} is not a number: {val!r}") from None
    return out


MAX_SHOTS = 8

# Constants for move validation
YAW_EXTREME_THRESHOLD = 90
PITCH_EXTREME_THRESHOLD = 60
DISTANCE_EXTREME_THRESHOLD = 50


def check_move_count(shots):
    """A finding when there are more than 8 camera moves, else None."""
    n = len(shots or [])
    if n <= MAX_SHOTS:
        return None
    return audit.finding(
        "S7.move-count", "fail",
        f"Too many camera moves: {n} of 8.",
        fix="Delete or merge a move.",
    )


def check_move_range(shots, row_lengths):
    """A failing finding per camera move whose frame range is out of bounds, else None."""
    row_lengths = row_lengths or {}
    findings = []
    for i, shot in enumerate(shots or []):
        n = i + 1
        act = shot.get("act")
        frm = shot.get("from", 0)
        to = shot.get("to", 0)
        if act not in row_lengths:
            reason = f"act '{act}' is missing from row lengths"
        elif frm < 0:
            reason = f"negative from {frm}"
        elif frm >= to:
            reason = f"from {frm} is not below to {to}"
        elif to > row_lengths[act]:
            reason = f"to {to} is past the row length {row_lengths[act]}"
        else:
            continue
        findings.append(audit.finding(
            "S7.move-range", "fail",
            f"Move {n}: {reason}.",
            fix="Set from below to, inside the row.",
        ))
    if not findings:
        return None
    return findings


def check_move_extreme(shots):
    """A warning finding per move that ends far from the arena view, else None."""
    findings = []
    for i, shot in enumerate(shots or []):
        n = i + 1
        yaw = shot.get("yaw", 0)
        pitch = shot.get("pitch", 0)
        distance = shot.get("distance", 100)
        if abs(yaw) > YAW_EXTREME_THRESHOLD or abs(pitch) > PITCH_EXTREME_THRESHOLD \
                or distance < DISTANCE_EXTREME_THRESHOLD:
            findings.append(audit.finding(
                "S7.move-extreme", "warn",
                f"Move {n} ends far from the arena view.",
                fix="Lower yaw or raise distance.",
            ))
    if not findings:
        return None
    return findings


ALLOWED_EASES = {"linear", "in", "out", "inout"}
DIST_MIN, DIST_MAX = 20, 400
YAW_MIN, YAW_MAX = -180, 180
PITCH_MIN, PITCH_MAX = -89, 89


def check_move_values(shots):
    """Findings per camera move with invalid ease, distance, yaw or pitch, else None."""
    findings = []
    for i, shot in enumerate(shots or []):
        n = i + 1
        ease = shot.get("ease")
        if ease not in ALLOWED_EASES:
            findings.append(audit.finding(
                "S7.move-values", "fail",
                f"Move {n}: ease out of range.",
                fix="Use a value inside the allowed range.",
            ))
        dist = shot.get("distance")
        if not (isinstance(dist, int) and DIST_MIN <= dist <= DIST_MAX):
            findings.append(audit.finding(
                "S7.move-values", "fail",
                f"Move {n}: distance out of range.",
                fix="Use a value inside the allowed range.",
            ))
        yaw = shot.get("yaw")
        if not (isinstance(yaw, int) and YAW_MIN <= yaw <= YAW_MAX):
            findings.append(audit.finding(
                "S7.move-values", "fail",
                f"Move {n}: yaw out of range.",
                fix="Use a value inside the allowed range.",
            ))
        pitch = shot.get("pitch")
        if not (isinstance(pitch, int) and PITCH_MIN <= pitch <= PITCH_MAX):
            findings.append(audit.finding(
                "S7.move-values", "fail",
                f"Move {n}: pitch out of range.",
                fix="Use a value inside the allowed range.",
            ))
    if not findings:
        return None
    return findings


def check_brightness(model_lum, bls_lum):
    """Warn when model brightness differs from disc brightness by more than 15%.

    Returns a single finding dict or None.
    """
    if bls_lum is None or bls_lum <= 0:
        return None
    if model_lum is None:
        return None
    ratio = abs(model_lum - bls_lum) / bls_lum
    if ratio > 0.15:
        diff_percent = int(round(ratio * 100))
        return audit.finding(
            "S7.brightness",
            "warn",
            f"Model brightness differs from the disc by {diff_percent}%.",
            fix="Adjust light gain or ambient.",
            value=ratio,
        )
    return None


def run_s7(recipe, row_lengths, model_lum=None, bls_lum=None):
    """Run the S7 look and camera-move checks over a recipe."""
    recipe = recipe or {}
    shots = recipe.get("shots", [])
    findings = []

    count = check_move_count(shots)
    if count:
        findings.append(count)

    range_findings = check_move_range(shots, row_lengths)
    if range_findings:
        findings.extend(range_findings)

    value_findings = check_move_values(shots)
    if value_findings:
        findings.extend(value_findings)

    extreme_findings = check_move_extreme(shots)
    if extreme_findings:
        findings.extend(extreme_findings)

    if model_lum is not None and bls_lum is not None:
        brightness = check_brightness(model_lum, bls_lum)
        if brightness:
            findings.append(brightness)

    return {
        "look": normalize_look(recipe.get("look", {})),
        "shots": shots,
        "findings": findings,
    }