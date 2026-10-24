"""Knob tables for S0-S3: data-driven UI controls. Pure data in, plain data out."""
from studio.state import stage_of_path


S0_KNOBS = [
    {"path": "model.category", "stage": "S0", "label": "Category", "control": "select",
     "choices": ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"],
     "unit": None, "auto": "detected", "help": "Model category (C1-C8)"},
    {"path": "source.path", "stage": "S0", "label": "Source path", "control": "readonly",
     "choices": None, "unit": None, "auto": "", "help": "Path to the GLB file"},
    {"path": "meta.author", "stage": "S0", "label": "Author", "control": "text",
     "choices": None, "unit": None, "auto": "", "help": "Author name"},
    {"path": "meta.license", "stage": "S0", "label": "License", "control": "text",
     "choices": None, "unit": None, "auto": "", "help": "License text (empty warns)"},
    {"path": "meta.url", "stage": "S0", "label": "URL", "control": "text",
     "choices": None, "unit": None, "auto": "", "help": "Source URL"},
    {"path": "meta.attribution", "stage": "S0", "label": "Attribution required", "control": "toggle",
     "choices": None, "unit": None, "auto": "on when license contains BY", "help": "Whether attribution is required"},
    {"path": "source.skin", "stage": "S0", "label": "Skin", "control": "select",
     "choices": None, "unit": None, "auto": "skin with most bound vertices", "help": "Skin to use (if multiple)"},
    {"path": "source.meshes", "stage": "S0", "label": "Meshes", "control": "list",
     "choices": None, "unit": None, "auto": "", "help": "Mesh names to include"},
    {"path": "model.cards", "stage": "S0", "label": "Registry cards", "control": "chips",
     "choices": None, "unit": None, "auto": "empty", "help": "Registry card IDs"},
]

S1_KNOBS = [
    {"path": "audit.fix_axes", "stage": "S1", "label": "Fix axes", "control": "toggle",
     "choices": None, "unit": None, "auto": "on", "help": "Auto-fix coordinate axes"},
    {"path": "audit.bone_limit", "stage": "S1", "label": "Bone limit", "control": "select",
     "choices": ["merge", "drop", "fail"], "unit": None, "auto": "merge", "help": "Action when bone count exceeds limit"},
    {"path": "audit.merge", "stage": "S1", "label": "Merge bones", "control": "list",
     "choices": None, "unit": None, "auto": "", "help": "Bone names to merge"},
    {"path": "audit.smooth_passes", "stage": "S1", "label": "Weight smoothing (passes)", "control": "number",
     "choices": None, "unit": "passes", "auto": "0", "help": "Number of weight smoothing passes"},
    {"path": "audit.normalise", "stage": "S1", "label": "Normalise weights", "control": "toggle",
     "choices": None, "unit": None, "auto": "on", "help": "Normalise vertex weights to sum to 1"},
    {"path": "audit.drop_parts", "stage": "S1", "label": "Drop parts", "control": "list",
     "choices": None, "unit": None, "auto": "", "help": "Mesh part names to drop"},
    {"path": "audit.mirror", "stage": "S1", "label": "Mirror", "control": "select",
     "choices": ["none", "x"], "unit": None, "auto": "none", "help": "Mirror axis"},
]

S2_KNOBS = [
    {"path": "rig.profile", "stage": "S2", "label": "Rig profile", "control": "select",
     "choices": ["auto", "ue", "mixamo", "generic"], "unit": None, "auto": "auto", "help": "Target rig profile"},
    {"path": "rig.root", "stage": "S2", "label": "Root bone", "control": "text",
     "choices": None, "unit": None, "auto": "pelvis for biped", "help": "Root bone name"},
    {"path": "rig.humanoid", "stage": "S2", "label": "Humanoid map", "control": "map",
     "choices": None, "unit": None, "auto": "", "help": "Humanoid bone mapping"},
    {"path": "rig.feet", "stage": "S2", "label": "Feet bones", "control": "list",
     "choices": None, "unit": None, "auto": "", "help": "Foot bone names"},
    {"path": "rig.strike", "stage": "S2", "label": "Strike bone", "control": "text",
     "choices": None, "unit": None, "auto": "", "help": "Strike bone name"},
    {"path": "rig.extras", "stage": "S2", "label": "Extra bones", "control": "list",
     "choices": None, "unit": None, "auto": "", "help": "Additional bones to include"},
    {"path": "rig.follow", "stage": "S2", "label": "Follow bones", "control": "list",
     "choices": None, "unit": None, "auto": "", "help": "Follow bone constraints (BONE=SOURCE[@FRACTION])"},
]

S3_KNOBS = [
    {"path": "mat.atlas", "stage": "S3", "label": "Atlas size (px)", "control": "select",
     "choices": [512, 1024, 2048], "unit": "px", "auto": "smallest that keeps texel density", "help": "Texture atlas size"},
    {"path": "mat.items", "stage": "S3", "label": "Material items", "control": "list",
     "choices": None, "unit": None, "auto": "", "help": "Material item definitions"},
    {"path": "mat.normal_strength", "stage": "S3", "label": "Normal strength", "control": "number",
     "choices": None, "unit": None, "auto": "1.0", "help": "Normal map strength multiplier"},
    {"path": "mat.no_pbr", "stage": "S3", "label": "No PBR", "control": "toggle",
     "choices": None, "unit": None, "auto": "off", "help": "Disable PBR materials"},
]

S6_KNOBS = [
    {"path": "acts.attack.strike", "stage": "S6", "label": "Strike frame (clip)", "control": "ints",
     "choices": None, "unit": "frames", "auto": "", "help": "Clip frame of the blow; the disc contact frame maps to it"},
    {"path": "acts.attack.timemap", "stage": "S6", "label": "Time map points", "control": "pairs",
     "choices": None, "unit": None, "auto": "straight line", "help": "clip:row pairs, e.g. 0:0, 30:60"},
    {"path": "timing.stretch_range", "stage": "S6", "label": "Allowed stretch (min, max)", "control": "floats",
     "choices": None, "unit": None, "auto": "0.6, 1.8", "help": "Speed range the time map may use"},
]

S7_KNOBS = [
    {"path": "look.ambient", "stage": "S7", "label": "Ambient light", "control": "number",
     "choices": None, "unit": "%", "auto": "20", "help": "Ambient light share"},
    {"path": "look.light_gain", "stage": "S7", "label": "Light gain", "control": "number",
     "choices": None, "unit": "%", "auto": "100", "help": "Scene light multiplier"},
    {"path": "look.normal_strength", "stage": "S7", "label": "Normal strength", "control": "number",
     "choices": None, "unit": "%", "auto": "180", "help": "Normal map strength in the scene"},
    {"path": "look.highlight", "stage": "S7", "label": "Highlight", "control": "number",
     "choices": None, "unit": "%", "auto": "100", "help": "Specular highlight strength"},
    {"path": "look.flip_green", "stage": "S7", "label": "Flip green (normals)", "control": "toggle",
     "choices": None, "unit": None, "auto": "on", "help": "Flip the green channel of normal maps"},
    {"path": "look.camera_near", "stage": "S7", "label": "Camera near", "control": "number",
     "choices": None, "unit": "units", "auto": "1000", "help": "Near plane distance"},
    {"path": "look.camera_keep", "stage": "S7", "label": "Camera keep", "control": "number",
     "choices": None, "unit": "%", "auto": "50", "help": "Share of the arena camera kept"},
    {"path": "look.camera_scale", "stage": "S7", "label": "Camera scale", "control": "number",
     "choices": None, "unit": "%", "auto": "100", "help": "Camera distance scale"},
    {"path": "shots", "stage": "S7", "label": "Camera moves", "control": "json",
     "choices": None, "unit": None, "auto": "", "help": "Up to 8 moves: act, from, to, yaw, pitch, distance, height, ease, other"},
]

ALL_KNOBS = S0_KNOBS + S1_KNOBS + S2_KNOBS + S3_KNOBS + S6_KNOBS + S7_KNOBS
KNOB_BY_PATH = {k["path"]: k for k in ALL_KNOBS}


def knobs(stage):
    """Return the knob table for a stage as a list of dicts in display order."""
    if stage == "S0":
        return S0_KNOBS
    if stage == "S1":
        return S1_KNOBS
    if stage == "S2":
        return S2_KNOBS
    if stage == "S3":
        return S3_KNOBS
    if stage == "S6":
        return S6_KNOBS
    if stage == "S7":
        return S7_KNOBS
    return []


def parse_text(control, text):
    """Typed value for a text-entry control, or raise ValueError. Shown form is `show_text`."""
    text = text.strip()
    parts = [p.strip() for p in text.split(",") if p.strip()]
    if control == "ints":
        return [int(p) for p in parts]
    if control == "floats":
        return [float(p) for p in parts]
    if control == "pairs":
        out = []
        for p in parts:
            a, b = p.split(":")
            out.append([int(a), int(b)])
        return out
    if control == "json":
        import json
        value = json.loads(text)
        if not isinstance(value, list):
            raise ValueError("a list is expected")
        return value
    raise ValueError(control)


def show_text(control, value):
    """Text for a typed value: the inverse of parse_text."""
    if value is None:
        return ""
    if control == "pairs":
        return ", ".join(f"{a}:{b}" for a, b in value)
    if control == "json":
        import json
        return json.dumps(value)
    if isinstance(value, list):
        return ", ".join(map(str, value))
    return str(value)


def parse_text(control, text):
    """Typed value for a text-entry control, or raise ValueError. Shown form is `show_text`."""
    text = text.strip()
    parts = [p.strip() for p in text.split(",") if p.strip()]
    if control == "ints":
        return [int(p) for p in parts]
    if control == "floats":
        return [float(p) for p in parts]
    if control == "pairs":
        out = []
        for p in parts:
            a, b = p.split(":")
            out.append([int(a), int(b)])
        return out
    if control == "json":
        import json
        value = json.loads(text)
        if not isinstance(value, list):
            raise ValueError("a list is expected")
        return value
    raise ValueError(control)


def show_text(control, value):
    """Text for a typed value: the inverse of parse_text."""
    if value is None:
        return ""
    if control == "pairs":
        return ", ".join(f"{a}:{b}" for a, b in value)
    if control == "json":
        import json
        return json.dumps(value)
    if isinstance(value, list):
        return ", ".join(map(str, value))
    return str(value)


def knob(path):
    """Return the knob dict for a path, or None if not a known knob."""
    return KNOB_BY_PATH.get(path)


def value(recipe, path):
    """Return the recipe value at path, or None if absent."""
    from studio.state import get_path
    return get_path(recipe, path)


def is_changed(recipe, path):
    """True when the key is present in the recipe (shows the dot and 'back to auto')."""
    from studio.state import get_path
    return get_path(recipe, path) is not None


def back_to_auto(studio, path):
    """Reset a knob to its auto value by removing it from the recipe."""
    return studio.edit(path, None)