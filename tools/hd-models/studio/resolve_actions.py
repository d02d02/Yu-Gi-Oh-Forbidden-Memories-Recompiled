#!/usr/bin/env python3
"""Resolution actions for missing acts.

Provides helper functions used by the UI‑free module to resolve missing act findings.
"""

from pathlib import Path

import native_convert
from . import resolutions


def missing_act_finding(act):
    """Return the finding dict for a missing act.

    The finding has the fixed id ``"S5.missing-act"``.
    * If *act* is ``"idle"`` the level is ``"fail"`` and ``value`` is ``None``.
    * Otherwise the level is ``"warn"`` and ``value`` is the act name.
    Raises ``ValueError`` if *act* is not a known act (see ``native_convert.spec.ACTS``).
    """
    if act not in native_convert.spec.ACTS:
        raise ValueError(f"act {act!r} not valid")
    level = "fail" if act == "idle" else "warn"
    value = None if act == "idle" else act
    return {"id": "S5.missing-act", "level": level, "value": value}


def use_clip(studio, act, clip_name):
    """Resolve a missing act by assigning a GLB clip.

    * ``act`` must be a valid act name (validated against ``native_convert.spec.ACTS``).
    * ``clip_name`` must be a non‑empty string.
    * Edits the recipe:
        - sets ``acts.<act>.source`` to ``clip_name``
        - records a resolution entry of kind ``provide.glb`` with data ``{"act": act, "clip": clip_name}``
    * Returns the number of edits performed (2).
    """
    # Validate inputs before any edit
    if act not in native_convert.spec.ACTS:
        raise ValueError(f"act {act!r} not valid")
    if not clip_name:
        raise ValueError("clip_name must be non‑empty")
    finding = missing_act_finding(act)
    updated = resolutions.choose(studio.recipe, finding, "provide.glb", act=act, clip=clip_name)
    studio.edit_many([(f"acts.{act}.source", clip_name), ("resolutions", updated["resolutions"])])
    return 2


def use_library(studio, library_path, act, clip_name):
    """Resolve a missing act by assigning a library glb.

    * ``act`` must be a valid act name (validated against ``native_convert.spec.ACTS``).
    * ``library_path`` must be a non‑empty string or path; it is stored as a string.
    * ``clip_name`` must be a non‑empty string.
    * Edits the recipe:
        - sets ``library.path`` to ``str(library_path)``.
        - sets ``acts.<act>.source`` to ``clip_name``.
        - records a resolution entry of kind ``provide.library`` with data ``{"act": act, "clip": clip_name, "path": str(library_path)}``.
    * Returns the number of edits performed (3).
    """
    # Validate inputs before any edit
    if act not in native_convert.spec.ACTS:
        raise ValueError(f"act {act!r} not valid")
    if not library_path:
        raise ValueError("library_path must be non‑empty")
    if not Path(library_path).is_file():
        raise ValueError(f"library file not found: {library_path}")
    if not clip_name:
        raise ValueError("clip_name must be non‑empty")
    finding = missing_act_finding(act)
    updated = resolutions.choose(studio.recipe, finding, "provide.library", act=act, clip=clip_name, path=str(library_path))
    studio.edit_many([("library.path", str(library_path)), (f"acts.{act}.source", clip_name),
                      ("resolutions", updated["resolutions"])])
    return 3
