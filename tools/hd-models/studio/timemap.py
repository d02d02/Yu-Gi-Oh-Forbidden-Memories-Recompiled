#!/usr/bin/env python3
"""S6 timemap utilities.
Implements default_map, segments, and placeholder for future functions.
"""
from typing import List, Tuple, Dict

def default_map(clip_frames: int, row_length: int) -> List[List[int]]:
    """Return the default time‑map with two points.
    Args:
        clip_frames: total number of clip frames (M).
        row_length: total number of disc row frames (N).
    Returns:
        [[0, 0], [clip_frames, row_length]]
    """
    return [[0, 0], [clip_frames, row_length]]

def segments(points: List[List[int]]) -> List[Dict[str, object]]:
    """Convert a list of map points to segment descriptors.
    Each segment is a dict with keys:
        "clip": (c0, c1)
        "row": (r0, r1)
        "stretch": float = (r1 - r0) / (c1 - c0)
    Raises:
        ValueError if fewer than 2 points are supplied.
    """

    if len(points) < 2:
        raise ValueError("At least two points are required to compute segments")
    segs: List[Dict[str, object]] = []
    for i in range(len(points) - 1):
        c0, r0 = points[i]
        c1, r1 = points[i + 1]
        if c1 == c0:
            raise ValueError("Segment with zero clip delta")
        stretch = (r1 - r0) / (c1 - c0)
        segs.append({
            "clip": (c0, c1),
            "row": (r0, r1),
            "stretch": stretch,
        })
    return segs


def check_monotonic(points: List[List[int]]) -> List[Dict[str, object]]:
    """Check that both clip and row columns are strictly increasing.

    Returns a list containing a single finding if the points are not monotonic,
    otherwise an empty list.
    """
    from . import audit
    for i in range(len(points) - 1):
        c0, r0 = points[i]
        c1, r1 = points[i + 1]
        if c1 <= c0 or r1 <= r0:
            return [audit.finding(
                "S6.monotonic",
                "fail",
                "Time-map points are not in order.",
                "Move a point.",
            )]
    return []


# check_stretch implementation moved below
def row_to_clip(points: List[List[int]], row_phase: float) -> float:
    """Map a disc row_phase to a clip frame using piecewise‑linear interpolation.

    The map is clamped to the first and last points.
    """
    # Clamp to range
    if row_phase <= points[0][1]:
        return float(points[0][0])
    if row_phase >= points[-1][1]:
        return float(points[-1][0])
    # Find segment
    for i in range(len(points) - 1):
        c0, r0 = points[i]
        c1, r1 = points[i + 1]
        if r0 <= row_phase <= r1:
            # Linear interpolation
            return c0 + (row_phase - r0) * (c1 - c0) / (r1 - r0)
    # Should not reach here
    return float(points[-1][0])


def clip_to_row(points: List[List[int]], clip_frame: float) -> float:
    """Map a clip frame to disc row_phase using piecewise‑linear interpolation.

    The map is clamped to the first and last points.
    """
    if clip_frame <= points[0][0]:
        return float(points[0][1])
    if clip_frame >= points[-1][0]:
        return float(points[-1][1])
    for i in range(len(points) - 1):
        c0, r0 = points[i]
        c1, r1 = points[i + 1]
        if c0 <= clip_frame <= c1:
            return r0 + (clip_frame - c0) * (r1 - r0) / (c1 - c0)
    return float(points[-1][1])


def contact_for(arena_rows: Dict, card_id: str, act: str = "attack") -> Dict[str, int] | None:
    """Return contact info for a card.

    arena_rows: data structure as in reference JSON.
    Returns dict with keys "contact_frame" and "row_length" or None.
    Conditions for None: card missing, act not "attack", contact missing/null, suspect true.
    """
    # Only attack act is supported
    if act != "attack":
        return None
    cards = arena_rows.get("cards", {})
    card = cards.get(str(card_id))
    if not card:
        return None
    contact = card.get("contact")
    if not contact:
        return None
    # suspect flag may be missing; treat missing as False
    if contact.get("suspect"):
        return None
    # Required fields
    cf = contact.get("contact_frame")
    rl = contact.get("row_length")
    if cf is None or rl is None:
        return None
    return {"contact_frame": cf, "row_length": rl}


def check_stretch(points: List[List[int]], rng: tuple = (0.6, 1.8)) -> List[Dict[str, object]]:
    """Check segment stretch factors.

    * Warn if any segment stretch is outside the given `rng` (default 0.6‑1.8).
    * Fail if any stretch is outside hard limits 0.3‑3.0.
    * The finding's `value` is the worst stretch factor (one decimal).
    * Message mentions the worst segment index (1‑based) and its factor.
    """
    from . import audit
    # Compute segment stretches
    segs = segments(points)
    # Determine worst stretch (farther from 1) for reporting
    worst_seg_idx = -1
    worst_factor = 1.0
    worst_distance = 0.0
    for idx, seg in enumerate(segs):
        f = seg["stretch"]
        dist = abs(f - 1.0)
        if dist > worst_distance:
            worst_distance = dist
            worst_factor = f
            worst_seg_idx = idx
    # Check limits
    low_hard, high_hard = 0.3, 3.0
    low_warn, high_warn = rng
    level = None
    if worst_factor < low_hard or worst_factor > high_hard:
        level = "fail"
    elif worst_factor < low_warn or worst_factor > high_warn:
        level = "warn"
    if level:
        msg = f"Segment {worst_seg_idx + 1} stretch {worst_factor:.1f} out of range."
        return [audit.finding(
            "S6.stretch",
            level,
            msg,
            "Trim the clip or add a time-map point.",
             round(worst_factor, 1),
         )]
    return []


def check_strike(points, strike_frame, contact):
    """Check strike timing against the disc contact reference.

    Args:
        points: time-map points.
        strike_frame: clip frame of the strike.
        contact: dict from contact_for, or None when no reference exists.

    Returns:
        A list with a single finding, or an empty list when the strike is
        close enough to the disc contact.
    """
    from . import audit
    if contact is None:
        return [audit.finding(
            "S6.no-reference",
            "info",
            "No disc reference for this act.",
            "Strike timing is unchecked here; measure this act on the disc to enable the check.",
        )]
    strike_row = clip_to_row(points, strike_frame)
    gap = abs(strike_row - contact["contact_frame"])
    n = round(gap)
    if gap > 10:
        return [audit.finding(
            "S6.strike-vs-contact",
            "fail",
            f"Strike lands {n} frames from the disc contact.",
            "Drag the red marker onto the green line, or add a time-map point.",
            n,
        )]
    if gap > 3:
        return [audit.finding(
            "S6.strike-vs-contact",
            "warn",
            f"Strike lands {n} frames from the disc contact.",
            "Drag the red marker onto the green line, or add a time-map point.",
            n,
        )]
    return []


def suggest_point(points, strike_frame, contact):
    """Return a new points list with one point inserted or moved so that
    clip ``strike_frame`` maps to ``contact_frame``.

    If ``contact`` is None or the result would break monotonic order,
    the input is returned unchanged.
    """
    if contact is None:
        return [list(p) for p in points]

    target_row = contact["contact_frame"]
    new_points = []
    moved = False
    for p in points:
        if p[0] == strike_frame:
            new_points.append([p[0], target_row])
            moved = True
        else:
            new_points.append([p[0], p[1]])

    if not moved:
        idx = 0
        for i, p in enumerate(new_points):
            if p[0] > strike_frame:
                idx = i
                break
            idx = i + 1
        new_points.insert(idx, [strike_frame, target_row])

    if not check_monotonic(new_points):
        return new_points
    return [list(p) for p in points]


def run_s6(recipe, act, clip_frames, card_id, arena_rows):
    """Run S6 checks and return adjusted points and findings.

    Args:
        recipe: dict with optional ``acts.<act>.timemap``, ``acts.<act>.strike``,
                ``timing.stretch_range``.
        act: act name (e.g. "attack").
        clip_frames: total clip frames (M).
        card_id: card identifier for disc reference.
        arena_rows: arena rows data structure.

    Returns:
        {"points": [...], "findings": [...]}
    """
    recipe = recipe or {}
    acts = recipe.get("acts", {}) if isinstance(recipe, dict) else {}
    act_data = acts.get(act, {}) if isinstance(acts, dict) else {}
    points = act_data.get("timemap")
    timing = recipe.get("timing", {}) if isinstance(recipe, dict) else {}
    rng = timing.get("stretch_range", (0.6, 1.8)) if isinstance(timing, dict) else (0.6, 1.8)

    contact = contact_for(arena_rows, card_id, act)

    if points is None:
        row_length = contact["row_length"] if contact else 0
        points = default_map(clip_frames, row_length)

    strike_frames = act_data.get("strike") or []
    strike_frame = strike_frames[0] if strike_frames else None

    if strike_frame is not None and contact is not None:
        points = suggest_point(points, strike_frame, contact)

    findings = []
    findings.extend(check_monotonic(points))
    findings.extend(check_stretch(points, rng))
    if strike_frame is not None:
        findings.extend(check_strike(points, strike_frame, contact))

    return {"points": points, "findings": findings}


