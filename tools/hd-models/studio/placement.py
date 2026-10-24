"""S4 (size and placement) maths for the Model Studio, UI-free.

Fits a model's rest-pose bounding box to game units using the recipe's size mode
(height / extent / percent), then exposes the footprint / ground / uniform-scale
checks used by the Model Studio audit. Depends only on numpy and studio.audit.
"""
import numpy as np

from studio import audit

# Footprint proxy of the standard monster disc (game units). The real footprint
# is not measured yet, so extents are compared against these box dimensions.
PROXY_FOOTPRINT_WIDTH_X = 191
PROXY_FOOTPRINT_DEPTH_Z = 236
DEFAULT_HEIGHT = 373
DEFAULT_EXTENT = PROXY_FOOTPRINT_WIDTH_X  # 191
DEFAULT_PERCENT = 100


def fit(lo, hi, mode="height", value=None):
    """Scale a rest-pose bbox (lo/hi, xyz) to game units.

    height:  scale so the height == value (default 373).
    extent:  scale so max(x extent, z extent) == value (default 191, proxy width_x).
    percent: scale = value / 100 (default 100).
    Returns {"scale", "height", "extent_x", "extent_z"} after applying the fit.
    """
    lo = np.asarray(lo, dtype=float)
    hi = np.asarray(hi, dtype=float)
    height = float(hi[1] - lo[1])
    extent_x = float(hi[0] - lo[0])
    extent_z = float(hi[2] - lo[2])
    if mode not in ("height", "extent", "percent"):
        raise ValueError(f"unknown fit mode: {mode!r}")
    if value is None:
        value = {"height": DEFAULT_HEIGHT, "extent": DEFAULT_EXTENT, "percent": DEFAULT_PERCENT}[mode]
    if mode == "height":
        scale = value / height
    elif mode == "extent":
        scale = value / max(extent_x, extent_z)
    elif mode == "percent":
        scale = value / 100.0
    return {
        "scale": float(scale),
        "height": height * scale,
        "extent_x": extent_x * scale,
        "extent_z": extent_z * scale,
    }


def body_extents(model, fitting):
    """x/z extents of the model's lower-half vertices, after the fit scale.

    Uses vertices with y <= lo_y + 0.5 * (hi_y - lo_y), so wings and other
    upper-body limbs do not inflate the footprint. Falls back to the full
    fitted extent when the lower half has no vertices.
    """
    lo_y = float(model.lo[1])
    hi_y = float(model.hi[1])
    cutoff = lo_y + 0.5 * (hi_y - lo_y)
    prims = getattr(model, "prims", [])
    lower = np.empty((0, 3))
    if prims:
        allpos = np.vstack([p["pos"] for p in prims])
        lower = allpos[allpos[:, 1] <= cutoff]
    if not len(lower):
        return {"extent_x": float(fitting["extent_x"]),
                "extent_z": float(fitting["extent_z"])}
    scale = float(fitting["scale"])
    return {
        "extent_x": float(lower[:, 0].max() - lower[:, 0].min()) * scale,
        "extent_z": float(lower[:, 2].max() - lower[:, 2].min()) * scale,
    }


def footprint_ratio(extent_x, extent_z):
    """Compare a model's footprint extents against the disc footprint proxy.

    Returns {"ratio": r, "proxy": True} where r = max(extent_x/191, extent_z/236):
    the fraction of the proxy card footprint the model occupies (1.0 = fills it).
    """
    ratio = max(float(extent_x) / PROXY_FOOTPRINT_WIDTH_X,
                float(extent_z) / PROXY_FOOTPRINT_DEPTH_Z)
    return {"ratio": ratio, "proxy": True}


def check_footprint(extent_x, extent_z):
    """Findings for a model's footprint vs the disc footprint proxy.

    None when r <= 1.10; warn above (never fail: the box is a proxy and wings exceed it).
    r = max(extent_x/191, extent_z/236). Percentages are rounded to whole
    numbers: N = how much wider than the card, M = scale to fit the card.
    """
    ratio = footprint_ratio(extent_x, extent_z)["ratio"]
    if ratio <= 1.10:
        return None
    level = "warn"
    wider_pct = round((ratio - 1) * 100)
    scale_pct = round(100 / ratio)
    message = f"Model is {wider_pct}% wider than the card footprint."
    fix = "Fit with a smaller pose, lower the scale to %d%%, or switch to Extent." % scale_pct
    return audit.finding("S4.footprint", level, message, fix=fix, value=wider_pct)


def check_ground(lowest_y, ground_offset=0, floating=False):
    """Finding S4.ground for a model's base relative to the ground.

    None when floating, or when abs(lowest_y - ground_offset) <= 8 game units
    (the model sits on / near the ground within tolerance). Warns otherwise,
    suggesting ground_offset be set to the base height or the model marked
    floating.
    """
    gap = abs(float(lowest_y) - float(ground_offset))
    if floating or gap <= 8:
        return None
    target = round(float(lowest_y))
    message = f"Model's lowest vertex is {round(gap)} units from ground_offset."
    fix = f"Set ground offset to {target} or mark the model as floating."
    return audit.finding("S4.ground", "warn", message, fix=fix, value=round(gap))


def check_uniform_scale(g):
    """Finding S4.uniform for non-uniform node scale on a glTF doc dict.

    A node's `scale` is [sx, sy, sz]; if any component differs from another by
    more than 1e-4 the node distorts the model in game. Fails, listing the
    offending nodes; the fix is to apply scale on export.
    """
    bad = []
    for i, n in enumerate(g.get("nodes", [])):
        s = n.get("scale")
        if s is None:
            continue
        s = np.asarray(s, dtype=float)
        if float(s.max() - s.min()) > 1e-4:
            bad.append(n.get("name", str(i)))
    if not bad:
        return None
    names = sorted(set(bad))[:4]
    message = "Non-uniform node scale on: " + ", ".join(names) + "."
    fix = "Re-export from Blender with applied scale."
    return audit.finding("S4.uniform", "fail", message, fix=fix, value=len(set(bad)))


def run_s4(glb_path, recipe=None):
    """Load a glb, apply the recipe's size fit, then run the S4 checks.

    recipe keys (all optional): size.mode (default "height"), size.value,
    size.ground_offset (default 0), size.floating (default False), and
    model.scale (integer percent, default 100, used as the percent-mode value
    when size.value is absent). Returns {"fit": <fit dict>, "findings": [...]}
    with the footprint, ground and uniform-scale findings collected in that order.

    The footprint check measures the body (lower-half) extents, stored in "fit"
    as body_extent_x/body_extent_z alongside the full extent_x/extent_z. When the
    full-extent ratio is more than 1.5x the body ratio, a note about excluded
    wings or limbs is appended to the footprint warning.
    """
    recipe = recipe or {}
    size = recipe.get("size", {}) or {}
    model_section = recipe.get("model", {}) or {}
    mode = size.get("mode", "height")
    value = size.get("value")
    if mode == "percent" and value is None:
        value = model_section.get("scale", 100)
    model = audit.Model(glb_path)
    fitting = fit(model.lo, model.hi, mode=mode, value=value)
    body = body_extents(model, fitting)
    fitting["body_extent_x"] = body["extent_x"]
    fitting["body_extent_z"] = body["extent_z"]
    footprint = check_footprint(body["extent_x"], body["extent_z"])
    if footprint:
        full_ratio = footprint_ratio(fitting["extent_x"], fitting["extent_z"])["ratio"]
        body_ratio = footprint_ratio(body["extent_x"], body["extent_z"])["ratio"]
        if full_ratio > 1.5 * body_ratio:
            n = round(full_ratio * 100)
            footprint["message"] += (" Wings or limbs excluded; full span is "
                                     "%d%% of the card footprint." % n)
    checks = (
        footprint,
        check_ground(model.lo[1], ground_offset=size.get("ground_offset", 0),
                     floating=bool(size.get("floating", False))),
        check_uniform_scale(model.doc),
    )
    findings = [f for f in checks if f]
    return {"fit": fitting, "findings": findings}
