"""The Model Studio's rail (left sidebar): groups, stages, next/previous, footer.
Pure data in, plain data out; no UI, no tkinter."""
from studio.state import STAGES, GROUPS


STAGE_NAMES = {
    "S0": "Intake",
    "S1": "Skeleton",
    "S2": "Skeleton",  # S1 and S2 are merged into one entry "Skeleton"
    "S3": "Materials",
    "S4": "Size",
    "S5": "Clips",
    "S6": "Timing",
    "S7": "Look",
    "S8": "Validate",
    "S9": "Package",
}

STAGE_SUBTITLES = {
    "S0": "triage",
    "S1": "audit and rig",
    "S2": "audit and rig",
    "S3": "textures",
    "S4": "placement",
    "S5": "acts",
    "S6": "strikes",
    "S7": "light",
    "S8": "in game",
    "S9": "build",
}

GLYPHS = {"pass": "ok", "warn": "!", "fail": "x", "stale": "o", "todo": "."}


def _worse_state(s1, s2):
    order = {"fail": 0, "warn": 1, "stale": 2, "todo": 3, "pass": 4}
    return s1 if order.get(s1, 5) <= order.get(s2, 5) else s2


def rail(studio):
    """Return list of dicts for the rail: group headers and stage entries.
    Groups: Prepare S0-S3, Fit S4-S6, Judge S7-S8, Ship S9.
    Nine stage entries: S1+S2 merged into "Skeleton" with the worse state.
    Each entry: {"kind": "group", "label"} or {"kind": "stage", "ids", "name", "subtitle", "state", "glyph"}."""
    items = []
    for group_label, stage_ids in GROUPS:
        items.append({"kind": "group", "label": group_label})
        # S1 and S2 are merged in the Prepare group
        if "S1" in stage_ids and "S2" in stage_ids:
            s1_state = studio.state("S1")
            s2_state = studio.state("S2")
            merged_state = _worse_state(s1_state, s2_state)
            items.append({
                "kind": "stage",
                "ids": ("S1", "S2"),
                "name": "Skeleton",
                "subtitle": "audit and rig",
                "state": merged_state,
                "glyph": GLYPHS[merged_state],
            })
            # Add all other stages in this group except S1 and S2
            for sid in stage_ids:
                if sid not in ("S1", "S2"):
                    st = studio.state(sid)
                    items.append({
                        "kind": "stage",
                        "ids": (sid,),
                        "name": STAGE_NAMES[sid],
                        "subtitle": STAGE_SUBTITLES[sid],
                        "state": st,
                        "glyph": GLYPHS[st],
                    })
        else:
            for sid in stage_ids:
                st = studio.state(sid)
                items.append({
                    "kind": "stage",
                    "ids": (sid,),
                    "name": STAGE_NAMES[sid],
                    "subtitle": STAGE_SUBTITLES[sid],
                    "state": st,
                    "glyph": GLYPHS[st],
                })
    return items


def next_stage(stage):
    """Return the next stage id in STAGES, or None if at the end."""
    try:
        idx = STAGES.index(stage)
        return STAGES[idx + 1] if idx + 1 < len(STAGES) else None
    except ValueError:
        return None


def footer(studio, stage):
    """Return footer data for a stage: previous, next, next_label, next_enabled, next_reason."""
    prev = STAGES[STAGES.index(stage) - 1] if stage != STAGES[0] else None
    nxt = next_stage(stage)

    cur_state = studio.state(stage)
    if nxt is None:
        # Last stage S9
        return {
            "previous": prev,
            "next": None,
            "next_label": "Build package",
            "next_enabled": False,
            "next_reason": "",
        }

    # Next is enabled only when CURRENT stage is "pass"
    next_enabled = cur_state == "pass"

    # Build reason if not enabled
    if not next_enabled:
        if cur_state == "fail":
            reason = f"{stage} is fail"
        elif cur_state == "warn":
            # Count unacknowledged warnings
            warns = studio.unacknowledged(stage)
            reason = f"{stage} has {len(warns)} warning{'s' if len(warns) != 1 else ''} to acknowledge"
        elif cur_state == "stale":
            reason = f"{stage} is stale"
        else:  # todo
            reason = f"{stage} was never run"
    else:
        reason = ""

    # Verb-first label naming the target
    nxt_name = STAGE_NAMES[nxt]
    if nxt == "S9":
        next_label = "Build package"
    else:
        next_label = f"Continue to {nxt} {nxt_name}"

    return {
        "previous": prev,
        "next": nxt,
        "next_label": next_label,
        "next_enabled": next_enabled,
        "next_reason": reason,
    }