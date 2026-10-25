'''Module providing utilities to extract skeleton information from a GLB file and validate provided models.

Functions:
- skeleton_of(path): returns (names, pose) where names is a list of bone names and pose is a dict mapping each name to {'pos': (x, y, z), 'rot': (qx, qy, qz, qw), 'scale': s}.
- check_provided(model_path, provided_path): runs validation between a model and a provided GLB, returning findings.
- record(recipe, finding, provided_path, findings): on success stores file info in a recipe.
'''

from pathlib import Path

from . import audit
from . import provided as provided_mod
from . import resolutions
import hashlib


def _unreadable_finding(path_str, exc):
    return {
        "id": "provide.unreadable",
        "level": "fail",
        "message": f"{path_str} cannot be read: {exc}",
        "fix": "export the file again as glb",
    }


def skeleton_of(path):
    """Extract bone names and rest‑pose information from a GLB file.

    Returns a tuple ``(names, pose)`` where ``names`` is ``model.names`` (list of bone names)
    and ``pose`` maps each bone name to a dict with keys ``pos``, ``rot`` and ``scale``.
    ``pos`` is a 3‑tuple of floats, ``rot`` a 4‑tuple quaternion, and ``scale`` the mean of the
    three scale components (as a float).
    Raises ``audit.AuditError`` if the file cannot be loaded.
    """
    try:
        model = audit.load_model(str(path))
    except audit.AuditError as e:
        # Propagate the same exception type for callers that expect it.
        raise
    # model.names already ordered to match model.joints
    names = list(model.names)
    pose = {}
    for name, joint_idx in zip(names, model.joints):
        rest = model.scene.rest.get(joint_idx)
        if rest is None:
            # Should not happen for properly built models, but skip gracefully.
            continue
        trans, quat, scale_seq = rest
        # Ensure plain Python floats/tuples
        pos = tuple(float(v) for v in trans)
        rot = tuple(float(v) for v in quat)
        # Scale may be a sequence of three numbers; compute mean.
        if hasattr(scale_seq, "__len__"):
            scale = float(sum(scale_seq) / len(scale_seq))
        else:
            scale = float(scale_seq)
        pose[name] = {"pos": pos, "rot": rot, "scale": scale}
    return names, pose


def check_provided(model_path, provided_path):
    """Validate a provided GLB against a model GLB.

    Returns a list of findings. If the provided file cannot be read, returns a single
    ``provide.unreadable`` finding.
    """
    try:
        prov_names, prov_pose = skeleton_of(provided_path)
    except audit.AuditError as exc:
        return [_unreadable_finding(str(provided_path), exc)]
    # model skeleton – let any load errors propagate (they indicate a bad model).
    model_names, model_pose = skeleton_of(model_path)
    return provided_mod.validate(prov_names, prov_pose, model_names, model_pose)


def record(recipe, finding, provided_path, findings):
    """Store a successful provision of a file in the recipe.

    * Raises ``ValueError`` if any fail‑level findings are present.
    * On success returns a new recipe with the resolution added.
    """
    if provided_mod.fail_count(findings) > 0:
        raise ValueError("fail findings present, cannot record")
    sha = hashlib.sha256(Path(provided_path).read_bytes()).hexdigest()
    return resolutions.choose(recipe, finding, "provide.file", path=str(provided_path), sha256=sha)
