"""Sample a glb's clips into the plain data clips.py judges: P[frame][joint] = (x, y, z) in the model's units."""
import numpy as np

from studio import audit

DEFAULT_FPS = 30.0
MAX_FRAMES = 600     # a clip longer than this is sampled at a coarser step, not cut


def clip_length(model, clip_name):
    """Seconds: the largest keyframe time of the clip's samplers."""
    for i, an in enumerate(model.doc.get("animations", [])):
        if an.get("name", f"clip{i}") == clip_name:
            ends = [float(audit.nc.accessor(model.g, s["input"]).max()) for s in an["samplers"]]
            return max(ends) if ends else 0.0
    raise KeyError(clip_name)


def sample_clip(model, clip_name, fps=DEFAULT_FPS, loop=False):
    """{"positions", "fps", "loop"} for one clip; joint positions come from the posed world matrices."""
    length = clip_length(model, clip_name)
    frames = max(1, int(round(length * fps)) + 1)
    step = max(1, -(-frames // MAX_FRAMES))
    pose_of = lambda t: audit.pose_function(model, (model.g, model.scene), clip_name, t)
    positions = []
    for f in range(0, frames, step):
        world = pose_of(min(f / fps, length))
        positions.append([tuple(float(v) for v in np.asarray(world(k))[:3, 3]) for k in range(len(model.joints))])
    return {"positions": positions, "fps": fps / step, "loop": bool(loop)}


def sample_all(model, fps=DEFAULT_FPS, loops=()):
    """Every clip of the model by name; `loops` names the clips that must close."""
    names = [an.get("name", f"clip{i}") for i, an in enumerate(model.doc.get("animations", []))]
    return {n: sample_clip(model, n, fps, n in loops) for n in names}
