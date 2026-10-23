"""Check rows for the Model Studio: transform findings into display rows.
Pure data in, plain data out; no UI, no tkinter."""
from studio.state import STAGES


FIX_TARGET = {
    "S0.licence": "meta.license",
    "S0.attribution": "meta.author",
    "S0.category": "model.category",
    "S0.category-confidence": "model.category",
    "S0.skins": "source.skin",
    "S1.bones": "audit.bone_limit",
    "S1.weights": "audit.smooth_passes",
    "S1.merge": "audit.merge",
    "S1.scale": "audit.fix_axes",
    "S1.normals": "audit.fix_axes",
    "S2.map": "rig.humanoid",
    "S2.root-side": "rig.root",
    "S2.extras-weights": "rig.extras",
    "S3.atlas": "mat.atlas",
    "S3.memory": "mat.atlas",
}


def _is_acked(studio, finding):
    """True when a warn finding has a matching acknowledgement in the recipe."""
    if finding["level"] != "warn":
        return False
    acks = studio.recipe.get("acks", [])
    return any(a.get("check") == finding["id"] and a.get("value") == finding.get("value") for a in acks)


def _chip(finding, acknowledged):
    """Return the chip label for a finding."""
    if finding["level"] == "fail":
        return "fail"
    if finding["level"] == "warn":
        return "acked" if acknowledged else "warn"
    return "info"


def check_rows(studio, stage):
    """Return rows and summary for a stage's findings.
    Returns: {"rows": [...], "summary": {"fail": n, "warn": n, "acked": n, "info": n}}
    Row: {"id", "level", "chip", "message", "fix", "value", "acknowledged": bool, "fix_target": path|None}
    Order: fail, warn, acked, info; ties keep finding order. Info > 4 collapses to one summary row."""
    findings = studio.findings.get(stage, [])
    rows = []
    summary = {"fail": 0, "warn": 0, "acked": 0, "info": 0}

    for f in findings:
        acked = _is_acked(studio, f)
        chip = _chip(f, acked)
        row = {
            "id": f["id"],
            "level": f["level"],
            "chip": chip,
            "message": f["message"],
            "fix": f.get("fix", ""),
            "value": f.get("value"),
            "acknowledged": acked,
            "fix_target": FIX_TARGET.get(f["id"]),
        }
        rows.append(row)
        summary[f["level"]] += 1
        if f["level"] == "warn" and acked:
            summary["warn"] -= 1
            summary["acked"] += 1

    # Sort: fail, warn, acked, info; stable for ties
    order = {"fail": 0, "warn": 1, "acked": 2, "info": 3}
    rows.sort(key=lambda r: order[r["chip"]])

    # Collapse info rows beyond 4
    info_rows = [r for r in rows if r["chip"] == "info"]
    if len(info_rows) > 4:
        non_info = [r for r in rows if r["chip"] != "info"]
        collapsed_ids = [r["id"] for r in info_rows]
        collapsed = {
            "id": "info*",
            "level": "info",
            "chip": "info",
            "message": f"{len(info_rows)} checks passed",
            "fix": "",
            "value": None,
            "acknowledged": False,
            "fix_target": None,
            "collapsed": collapsed_ids,
        }
        rows = non_info + [collapsed]

    return {"rows": rows, "summary": summary}