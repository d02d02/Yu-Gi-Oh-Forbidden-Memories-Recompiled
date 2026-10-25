# -*- coding: utf-8 -*-
"""Resolution catalogue and helper functions.

Provides the pure‑Python implementation of the resolution API required by the job.
Only the `offered` function is needed for the first item; other functions are
stubbed for future items.
"""

# Catalogue mapping finding IDs to the ordered list of resolution kinds.
_CATALOGUE = {
    "S5.missing-act": [
        "provide.glb",
        "provide.library",
        "provide.file",
        "fallback",
        "accept",
    ],
    "S5.model": ["provide.glb", "provide.library", "provide.file", "fallback"],
    "S0.category": ["pick"],
    "S0.attribution": ["text"],
    "S9.provenance": ["text"],
    "S3.dropped": ["provide.file", "fallback", "accept"],
    "S3.atlas": ["provide.file", "fallback", "accept"],
    "S1.skin": ["provide.file"],
    "S2.map": ["provide.file"],
}


def _offered_raw(finding):
    """Return the raw catalogue list for *finding* (may be empty)."""
    fid = finding.get("id")
    return list(_CATALOGUE.get(fid, []))


def offered(finding):
    """Return the list of resolution kinds offered for *finding*.

    The rules are:
    * Use the catalogue defined above.
    * If the finding's ``level`` is ``"fail"`` the ``"accept"`` kind is removed
      (a fail never offers ``accept``).
    """
    kinds = _offered_raw(finding)
    if finding.get("level") == "fail":
        # Remove any accept entry – it may not be present.
        kinds = [k for k in kinds if k != "accept"]
    return kinds


def chosen(recipe, finding):
    """Return the chosen resolution for *finding*.

    Preference order:
    1. An explicit entry in ``recipe["resolutions"]`` matching the finding's ``id`` and ``value``.
    2. An ack entry in ``recipe["acks"]`` that matches – this yields an ``accept`` kind with empty data.
    Returns ``None`` if neither is present.
    """
    # Look for stored resolution
    check_id = finding.get("id")
    find_value = finding.get("value")
    for entry in recipe.get("resolutions", []):
        if entry.get("check") == check_id and entry.get("value") == find_value:
            return {"kind": entry.get("kind"), "data": entry.get("data", {})}
    # Ack fallback
    for ack in recipe.get("acks", []):
        if ack.get("check") == check_id and ack.get("value") == find_value:
            return {"kind": "accept", "data": {}}
    return None


def choose(recipe, finding, kind, **data):
    """Return a NEW recipe with the given choice stored.

    * Does not mutate the input ``recipe``.
    * ``kind`` must be one of ``offered(finding)``; otherwise ``ValueError``.
    * Stores a dict with keys ``check``, ``value``, ``kind`` and ``data`` in
      ``recipe["resolutions"]``. At most one entry per (check, value) exists –
      a new entry replaces any existing one.
    """
    # Validate kind
    if kind not in offered(finding):
        raise ValueError(f"kind {kind!r} not offered for finding {finding.get('id')}")
    # Prepare new recipe copy (shallow copy, but copy list of resolutions)
    new_recipe = dict(recipe)
    # Ensure we have a list to work with
    orig_res = recipe.get("resolutions", [])
    new_res = list(orig_res)
    # Build the entry
    entry = {
        "check": finding.get("id"),
        "value": finding.get("value"),
        "kind": kind,
        "data": data,
    }
    # Replace existing entry with same check and value
    for i, e in enumerate(new_res):
        if e.get("check") == entry["check"] and e.get("value") == entry["value"]:
            new_res[i] = entry
            break
    else:
        new_res.append(entry)
    new_recipe["resolutions"] = new_res
    return new_recipe


def is_resolved(recipe, finding):
    """Return ``True`` if *finding* has a chosen resolution (stored or ack), else ``False``.
    """
    return chosen(recipe, finding) is not None


def stand_ins(recipe):
    """Return a list of resolution entries whose ``kind`` is ``"fallback"`` or ``"accept"``.

    The entries are taken from ``recipe.get("resolutions", [])`` and returned in the
    stored order.
    """
    res = recipe.get("resolutions", [])
    return [e for e in res if e.get("kind") in ("fallback", "accept")]

