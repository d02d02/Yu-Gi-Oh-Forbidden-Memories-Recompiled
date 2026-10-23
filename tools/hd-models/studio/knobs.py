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

ALL_KNOBS = S0_KNOBS + S1_KNOBS + S2_KNOBS + S3_KNOBS
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
    return []


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