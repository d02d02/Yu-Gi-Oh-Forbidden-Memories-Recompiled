#!/usr/bin/env python3
"""Read and validate a studio recipe.json (pure Python, stdlib only).

This module provides:
- load(): read a recipe from a dict or a JSON file, return a deep copy.
- validate(): check the recipe against the schema, return findings (errors/warnings).
- canonical_json(): deterministic JSON output with sorted keys and whole numbers.
- convert_args(): map recipe keys to native_convert.py's argparse dest names.
- model_json_members(): map recipe keys to model.json members.

Schema: notes/studio/recipe-schema.md (the table "Keys by section" is the contract).
Limits from native_spec.py (imported as spec): ACTS, MAX_SHOTS, SHOT_RANGES, MAX_STRIKES,
REGISTRY_CARDS, LOOK_KEYS, TEXTURE_MAX, MAX_SIDE.
"""
import copy
import json
import re
from pathlib import Path

import native_spec as spec  # noqa: E402
from studio import timemap  # noqa: E402


SCHEMA = 1


class RecipeError(ValueError):
    """Raised when a recipe is not loadable (schema violation, bad JSON, etc.)."""
    pass


# Known top-level keys (from schema + JOB.md)
KNOWN_TOP_KEYS = {
    "schema", "studio", "source", "model", "meta", "audit", "rig", "mat",
    "size", "acts", "look", "shots", "pkg", "acks", "runs", "timing", "library"
}

# Acts (from spec.ACTS)
VALID_ACTS = set(spec.ACTS)

# Rig profiles
VALID_RIG_PROFILES = {"auto", "ue", "mixamo", "generic"}

# Root motion modes
VALID_ROOT_MOTION = {"remove", "keep"}

# Size modes
VALID_SIZE_MODES = {"scale", "extent", "root_height", "height"}

# Follow pattern: BONE=SOURCE[@FRACTION]
FOLLOW_PATTERN = re.compile(r"^[^=@\s]+=[^=@\s]+(@[0-9.]+)?$")

# SHA256 pattern (64 hex chars)
SHA256_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")


def load(source) -> dict:
    """Load a recipe from a dict or a JSON file path.

    Args:
        source: A dict, or a str/Path to a JSON file.

    Returns:
        A deep copy of the parsed recipe dict.

    Raises:
        RecipeError: If not a JSON object; "schema" missing or not an int;
            schema < 1; schema > SCHEMA (message contains "newer studio");
            the file is not valid JSON.
    """
    if isinstance(source, (str, Path)):
        path = Path(source)
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as e:
            raise RecipeError(f"cannot read {path}: {e}") from e
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise RecipeError(f"invalid JSON in {path}: {e}") from e
    elif isinstance(source, dict):
        data = source
    else:
        raise RecipeError("source must be a dict or a file path")

    if not isinstance(data, dict):
        raise RecipeError("recipe must be a JSON object")

    schema = data.get("schema")
    if not isinstance(schema, int):
        raise RecipeError("recipe \"schema\" must be an integer")
    if schema < 1:
        raise RecipeError("recipe \"schema\" must be >= 1")
    if schema > SCHEMA:
        raise RecipeError(f"recipe schema {schema} is newer than this studio (max {SCHEMA})")

    return copy.deepcopy(data)


def _convert_whole_floats(obj):
    """Recursively convert whole floats to ints (so JSON writes 3 not 3.0)."""
    if isinstance(obj, float) and obj.is_integer():
        return int(obj)
    if isinstance(obj, dict):
        return {k: _convert_whole_floats(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_convert_whole_floats(item) for item in obj]
    return obj


def canonical_json(recipe) -> str:
    """Return a deterministic JSON string of the recipe.

    Uses sorted keys, indent=2, ensure_ascii=False, and writes whole floats as ints.
    """
    normalized = _convert_whole_floats(recipe)
    return json.dumps(normalized, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def _is_int(value):
    """True for a real int (bool excluded)."""
    return isinstance(value, int) and not isinstance(value, bool)


def validate(recipe) -> list[dict]:
    """Validate the recipe. Returns list of findings: {"path", "level", "message"}."""
    findings = []
    if not isinstance(recipe, dict):
        findings.append({"path": "", "level": "error", "message": "recipe must be a JSON object"})
        return findings

    findings += _validate_top_level(recipe)
    findings += _validate_source(recipe.get("source"))
    findings += _validate_model(recipe.get("model"))
    findings += _validate_meta(recipe.get("meta"))
    findings += _validate_size(recipe.get("size"))
    findings += _validate_rig(recipe.get("rig"))
    findings += _validate_mat(recipe.get("mat"))
    findings += _validate_acts(recipe.get("acts"))
    findings += _validate_look(recipe.get("look"))
    findings += _validate_shots(recipe.get("shots"))
    findings += _validate_acks(recipe.get("acks"))
    return findings


def _validate_top_level(recipe):
    """Top level: source and model are required; unknown keys warn."""
    findings = []
    # source and model are required
    if "source" not in recipe:
        findings.append({"path": "source", "level": "error", "message": "missing 'source' section"})
    if "model" not in recipe:
        findings.append({"path": "model", "level": "error", "message": "missing 'model' section"})
    # unknown top-level keys
    for key in recipe:
        if key not in KNOWN_TOP_KEYS:
            findings.append({"path": key, "level": "warn", "message": f"unknown top-level key '{key}'"})
    return findings


def _validate_source(source):
    """source: path non-empty str; sha256 optional 64 hex; skin optional str; meshes list of str."""
    findings = []
    if not isinstance(source, dict):
        return findings  # top-level already flags missing; nothing more to check
    path = source.get("path")
    if path is None:
        findings.append({"path": "source.path", "level": "error", "message": "source.path is required"})
    elif not isinstance(path, str) or not path:
        findings.append({"path": "source.path", "level": "error", "message": "source.path must be a non-empty string"})
    sha = source.get("sha256")
    if sha is not None and not (isinstance(sha, str) and SHA256_PATTERN.match(sha)):
        findings.append({"path": "source.sha256", "level": "error", "message": "source.sha256 must be 64 hex characters"})
    skin = source.get("skin")
    if skin is not None and not isinstance(skin, str):
        findings.append({"path": "source.skin", "level": "error", "message": "source.skin must be a string"})
    meshes = source.get("meshes")
    if meshes is not None:
        if not isinstance(meshes, list) or not all(isinstance(m, str) for m in meshes):
            findings.append({"path": "source.meshes", "level": "error", "message": "source.meshes must be a list of strings"})
    return findings


def _validate_model(model):
    """model: category in C1..C8; name optional non-empty str; cards list of ints >=1, <=REGISTRY_CARDS, no dupes."""
    findings = []
    if not isinstance(model, dict):
        return findings
    valid_categories = {"C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"}
    category = model.get("category")
    if category is None:
        findings.append({"path": "model.category", "level": "error", "message": "model.category is required"})
    elif category not in valid_categories:
        findings.append({"path": "model.category", "level": "error", "message": f"model.category must be one of {sorted(valid_categories)}"})
    name = model.get("name")
    if name is not None and not (isinstance(name, str) and name):
        findings.append({"path": "model.name", "level": "error", "message": "model.name must be a non-empty string"})
    cards = model.get("cards")
    if cards is not None:
        if not isinstance(cards, list) or not all(_is_int(c) and c >= 1 for c in cards):
            findings.append({"path": "model.cards", "level": "error", "message": "model.cards must be a list of ints >= 1"})
        elif len(cards) > spec.REGISTRY_CARDS:
            findings.append({"path": "model.cards", "level": "error", "message": f"model.cards has at most {spec.REGISTRY_CARDS} entries"})
        elif len(set(cards)) != len(cards):
            findings.append({"path": "model.cards", "level": "error", "message": "model.cards has duplicate entries"})
    return findings


def _validate_meta(meta):
    """meta: author, license, url optional str; license missing/empty warns 'licence is empty'."""
    findings = []
    if not isinstance(meta, dict):
        return findings
    for key in ("author", "license", "url"):
        val = meta.get(key)
        if val is not None and not isinstance(val, str):
            findings.append({"path": f"meta.{key}", "level": "error", "message": f"meta.{key} must be a string"})
    license_val = meta.get("license")
    if not license_val:
        findings.append({"path": "meta.license", "level": "warn", "message": "licence is empty"})
    return findings


def _validate_size(size):
    """size: mode in scale,extent,root_height,height; value>0 with mode; origin_height>=0;
    scale_pct int 10..500; offset list of 3 ints; center bool."""
    findings = []
    if not isinstance(size, dict):
        return findings
    mode = size.get("mode")
    value = size.get("value")
    if mode is not None and mode not in VALID_SIZE_MODES:
        findings.append({"path": "size.mode", "level": "error", "message": f"size.mode must be one of {sorted(VALID_SIZE_MODES)}"})
    if mode is not None and value is None:
        findings.append({"path": "size.value", "level": "error", "message": "size.value is required when size.mode is set"})
    if value is not None:
        if not isinstance(value, (int, float)) or value <= 0:
            findings.append({"path": "size.value", "level": "error", "message": "size.value must be a number > 0"})
        if mode is None:
            findings.append({"path": "size.mode", "level": "error", "message": "size.mode is required when size.value is set"})
    origin_h = size.get("origin_height")
    if origin_h is not None:
        if not isinstance(origin_h, (int, float)) or origin_h < 0:
            findings.append({"path": "size.origin_height", "level": "error", "message": "size.origin_height must be a number >= 0"})
    scale_pct = size.get("scale_pct")
    if scale_pct is not None:
        if not _is_int(scale_pct) or not (10 <= scale_pct <= 500):
            findings.append({"path": "size.scale_pct", "level": "error", "message": "size.scale_pct must be an int in 10..500"})
    offset = size.get("offset")
    if offset is not None:
        if not (isinstance(offset, list) and len(offset) == 3 and all(_is_int(v) for v in offset)):
            findings.append({"path": "size.offset", "level": "error", "message": "size.offset must be a list of 3 ints"})
    center = size.get("center")
    if center is not None and not isinstance(center, bool):
        findings.append({"path": "size.center", "level": "error", "message": "size.center must be a boolean"})
    return findings


def _validate_rig(rig):
    """rig: profile in auto,ue,mixamo,generic; root non-empty str;
    follow list of str matching BONE=SOURCE[@FRACTION]; feet list of str."""
    findings = []
    if not isinstance(rig, dict):
        return findings
    profile = rig.get("profile")
    if profile is not None and profile not in VALID_RIG_PROFILES:
        findings.append({"path": "rig.profile", "level": "error", "message": f"rig.profile must be one of {sorted(VALID_RIG_PROFILES)}"})
    root = rig.get("root")
    if root is not None and not (isinstance(root, str) and root):
        findings.append({"path": "rig.root", "level": "error", "message": "rig.root must be a non-empty string"})
    follow = rig.get("follow")
    if follow is not None:
        if not isinstance(follow, list) or not all(isinstance(f, str) and FOLLOW_PATTERN.match(f) for f in follow):
            findings.append({"path": "rig.follow", "level": "error", "message": "rig.follow must be a list of BONE=SOURCE[@FRACTION] strings"})
    feet = rig.get("feet")
    if feet is not None:
        if not isinstance(feet, list) or not all(isinstance(f, str) for f in feet):
            findings.append({"path": "rig.feet", "level": "error", "message": "rig.feet must be a list of strings"})
    return findings


def _validate_mat(mat):
    """mat: atlas int, power of two, 64..MAX_SIDE (warn above TEXTURE_MAX); no_pbr bool."""
    findings = []
    if not isinstance(mat, dict):
        return findings
    atlas = mat.get("atlas")
    if atlas is not None:
        if not _is_int(atlas) or not (64 <= atlas <= spec.MAX_SIDE):
            findings.append({"path": "mat.atlas", "level": "error", "message": f"mat.atlas must be an int in 64..{spec.MAX_SIDE}"})
        elif (atlas & (atlas - 1)) != 0:
            findings.append({"path": "mat.atlas", "level": "error", "message": "mat.atlas must be a power of two"})
        elif atlas > spec.TEXTURE_MAX:
            findings.append({"path": "mat.atlas", "level": "warn", "message": f"mat.atlas exceeds default texture max {spec.TEXTURE_MAX}"})
    no_pbr = mat.get("no_pbr")
    if no_pbr is not None and not isinstance(no_pbr, bool):
        findings.append({"path": "mat.no_pbr", "level": "error", "message": "mat.no_pbr must be a boolean"})
    return findings


def _validate_acts(acts):
    """acts: keys only from spec.ACTS. Each act is an object.
    "source" is a str (clip name) or object with exactly one key "procedural" (str).
    "strike" list of ints >= 0, at most MAX_STRIKES, allowed only on "attack" (else warn).
    "root_motion" in remove, keep. "loop", "close_loop", "mirror" bool. "speed" number > 0."""
    findings = []
    if not isinstance(acts, dict):
        return findings
    for act_name, act in acts.items():
        prefix = f"acts.{act_name}"
        if act_name not in VALID_ACTS:
            findings.append({"path": prefix, "level": "error", "message": f"act '{act_name}' is not valid; valid acts: {', '.join(spec.ACTS)}"})
        if not isinstance(act, dict):
            findings.append({"path": prefix, "level": "error", "message": "act must be an object"})
            continue
        # source
        source = act.get("source")
        if source is not None:
            if isinstance(source, str):
                pass  # valid clip name string
            elif isinstance(source, dict):
                if set(source.keys()) != {"procedural"}:
                    findings.append({"path": f"{prefix}.source", "level": "error", "message": "act.source object must have exactly one key 'procedural'"})
                elif not isinstance(source.get("procedural"), str):
                    findings.append({"path": f"{prefix}.source.procedural", "level": "error", "message": "act.source.procedural must be a string"})
            else:
                findings.append({"path": f"{prefix}.source", "level": "error", "message": "act.source must be a string or an object with key 'procedural'"})
        # strike
        strike = act.get("strike")
        if strike is not None:
            if not isinstance(strike, list) or not all(_is_int(s) and s >= 0 for s in strike):
                findings.append({"path": f"{prefix}.strike", "level": "error", "message": "act.strike must be a list of ints >= 0"})
            elif len(strike) > spec.MAX_STRIKES:
                findings.append({"path": f"{prefix}.strike", "level": "error", "message": f"act.strike has at most {spec.MAX_STRIKES} entries"})
            elif act_name != "attack":
                findings.append({"path": f"{prefix}.strike", "level": "warn", "message": "act.strike is only meaningful on 'attack'"})
        # root_motion
        root_motion = act.get("root_motion")
        if root_motion is not None and root_motion not in VALID_ROOT_MOTION:
            findings.append({"path": f"{prefix}.root_motion", "level": "error", "message": f"act.root_motion must be one of {sorted(VALID_ROOT_MOTION)}"})
        # loop, close_loop, mirror
        for bool_key in ("loop", "close_loop", "mirror"):
            val = act.get(bool_key)
            if val is not None and not isinstance(val, bool):
                findings.append({"path": f"{prefix}.{bool_key}", "level": "error", "message": f"act.{bool_key} must be a boolean"})
        # speed
        speed = act.get("speed")
        if speed is not None:
            if not isinstance(speed, (int, float)) or speed <= 0:
                findings.append({"path": f"{prefix}.speed", "level": "error", "message": "act.speed must be a number > 0"})
    return findings


def _validate_look(look):
    """look: keys only from spec.LOOK_KEYS (else error); values numbers."""
    findings = []
    if not isinstance(look, dict):
        return findings
    for key, val in look.items():
        if key not in spec.LOOK_KEYS:
            findings.append({"path": f"look.{key}", "level": "error", "message": f"look key '{key}' is not valid; valid keys: {', '.join(spec.LOOK_KEYS)}"})
        elif not isinstance(val, (int, float)):
            findings.append({"path": f"look.{key}", "level": "error", "message": "look values must be numbers"})
    return findings


def _validate_shots(shots):
    """shots: list, at most MAX_SHOTS. Each is an object with "act" in spec.ACTS and ints for
    from, to, yaw, pitch, distance, height, ease within SHOT_RANGES
    (missing optional members are fine except act, from, to); from < to; "other" bool."""
    findings = []
    if not isinstance(shots, list):
        return findings
    if len(shots) > spec.MAX_SHOTS:
        findings.append({"path": "shots", "level": "error", "message": f"shots has at most {spec.MAX_SHOTS} entries"})
        return findings
    for i, shot in enumerate(shots):
        prefix = f"shots[{i}]"
        if not isinstance(shot, dict):
            findings.append({"path": prefix, "level": "error", "message": "shot must be an object"})
            continue
        act = shot.get("act")
        if act is None:
            findings.append({"path": f"{prefix}.act", "level": "error", "message": "shot.act is required"})
        elif act not in spec.ACTS:
            findings.append({"path": f"{prefix}.act", "level": "error", "message": f"shot.act must be one of {', '.join(spec.ACTS)}"})
        from_val = shot.get("from")
        to_val = shot.get("to")
        if from_val is None:
            findings.append({"path": f"{prefix}.from", "level": "error", "message": "shot.from is required"})
        if to_val is None:
            findings.append({"path": f"{prefix}.to", "level": "error", "message": "shot.to is required"})
        # Check range-limited ints (includes from, to)
        for key, (min_v, max_v) in spec.SHOT_RANGES.items():
            val = shot.get(key)
            if val is not None:
                if not _is_int(val):
                    findings.append({"path": f"{prefix}.{key}", "level": "error", "message": f"shot.{key} must be an int"})
                elif not (min_v <= val <= max_v):
                    findings.append({"path": f"{prefix}.{key}", "level": "error", "message": f"shot.{key} must be in {min_v}..{max_v}"})
        if from_val is not None and to_val is not None and _is_int(from_val) and _is_int(to_val):
            if from_val >= to_val:
                findings.append({"path": f"{prefix}.from", "level": "error", "message": "shot.from must be < shot.to"})
        other = shot.get("other")
        if other is not None and not isinstance(other, bool):
            findings.append({"path": f"{prefix}.other", "level": "error", "message": "shot.other must be a boolean"})
    return findings


def _validate_acks(acks):
    """acks: list of objects with "check" (non-empty str) and "value" (any)."""
    findings = []
    if not isinstance(acks, list):
        return findings
    for i, ack in enumerate(acks):
        prefix = f"acks[{i}]"
        if not isinstance(ack, dict):
            findings.append({"path": prefix, "level": "error", "message": "ack must be an object"})
            continue
        check = ack.get("check")
        if not isinstance(check, str) or not check:
            findings.append({"path": f"{prefix}.check", "level": "error", "message": "ack.check must be a non-empty string"})
        # value can be anything
    return findings


def convert_args(recipe) -> dict:
    """Map recipe to native_convert option dests. Returns only keys the recipe sets."""
    result = {}

    # size.mode/value -> one of scale, extent, root_height, height
    size = recipe.get("size")
    if isinstance(size, dict):
        mode = size.get("mode")
        value = size.get("value")
        if mode in VALID_SIZE_MODES and value is not None:
            result[mode] = value
        origin_h = size.get("origin_height")
        if origin_h is not None:
            result["origin_height"] = origin_h
        center = size.get("center")
        if center is False:
            result["no_center"] = True

    timing = recipe.get("timing")
    if isinstance(timing, dict) and timing.get("attack_range") is not None:
        result["attack_range"] = timing["attack_range"]

    # rig.profile -> rig; rig.root -> root; rig.follow -> follow
    rig = recipe.get("rig")
    if isinstance(rig, dict):
        profile = rig.get("profile")
        if profile is not None:
            result["rig"] = profile
        root = rig.get("root")
        if root is not None:
            result["root"] = root
        follow = rig.get("follow")
        if follow is not None:
            result["follow"] = follow

    # mat.atlas -> texture_max; mat.no_pbr True -> no_pbr True
    mat = recipe.get("mat")
    if isinstance(mat, dict):
        atlas = mat.get("atlas")
        if atlas is not None:
            result["texture_max"] = atlas
        no_pbr = mat.get("no_pbr")
        if no_pbr is True:
            result["no_pbr"] = True

    # meta.author -> author; meta.license -> license
    meta = recipe.get("meta")
    if isinstance(meta, dict):
        author = meta.get("author")
        if author is not None:
            result["author"] = author
        license_val = meta.get("license")
        if license_val is not None:
            result["license"] = license_val

    # model.name -> name
    model = recipe.get("model")
    if isinstance(model, dict):
        name = model.get("name")
        if name is not None:
            result["name"] = name

    # library.path -> clips_from (clips taken from another glb, bones matched by name)
    library = recipe.get("library")
    if isinstance(library, dict) and isinstance(library.get("path"), str) and library["path"]:
        result["clips_from"] = library["path"]

    # Any act with root_motion "keep" -> keep_root_motion True
    acts = recipe.get("acts")
    if isinstance(acts, dict):
        keep_root = False
        clip_names = {}
        procedural = []
        for act_name in spec.ACTS:
            act = acts.get(act_name)
            if isinstance(act, dict):
                root_motion = act.get("root_motion")
                if root_motion == "keep":
                    keep_root = True
                source = act.get("source")
                if isinstance(source, str) and source:
                    clip_names[act_name] = source
                elif isinstance(source, dict) and isinstance(source.get("procedural"), str):
                    procedural.append(f"{act_name}={source['procedural']}")
        if keep_root:
            result["keep_root_motion"] = True
        if procedural:
            result["procedural"] = procedural
        if clip_names:
            # comma-joined, de-duplicated clip names in spec.ACTS order
            seen = set()
            ordered = []
            for act_name in spec.ACTS:
                clip = clip_names.get(act_name)
                if clip and clip not in seen:
                    seen.add(clip)
                    ordered.append(clip)
            if ordered:
                result["clips"] = ",".join(ordered)

    return result


def model_json_members(recipe) -> dict:
    """Map recipe to model.json members. Returns only keys the recipe sets."""
    result = {}

    # clips: {act: clip name} for acts whose source is a str
    acts = recipe.get("acts")
    if isinstance(acts, dict):
        clips = {}
        for act_name in spec.ACTS:
            act = acts.get(act_name)
            if isinstance(act, dict):
                source = act.get("source")
                if isinstance(source, str) and source:
                    clips[act_name] = source
        if clips:
            result["clips"] = clips

        # strike: {"attack": [ints]} from acts.attack.strike
        attack = acts.get("attack")
        if isinstance(attack, dict):
            strike = attack.get("strike")
            if isinstance(strike, list) and strike:
                result["strike"] = {"attack": strike}

    # scale: size.scale_pct
    size = recipe.get("size")
    if isinstance(size, dict):
        scale_pct = size.get("scale_pct")
        if scale_pct is not None:
            result["scale"] = scale_pct
        # offset: size.offset
        offset = size.get("offset")
        if offset is not None:
            result["offset"] = offset

    # look: the look object
    look = recipe.get("look")
    if isinstance(look, dict) and look:
        result["look"] = look

    # shots: the shots list (as is)
    shots = recipe.get("shots")
    if isinstance(shots, list) and shots:
        result["shots"] = shots

    # timemaps: list of {"act", "points"} from acts with a timemap
    acts_section = recipe.get("acts")
    if isinstance(acts_section, dict):
        timemap_list = []
        for act_name in spec.ACTS:
            act = acts_section.get(act_name)
            if isinstance(act, dict):
                points = act.get("timemap")
                if points is not None:
                    if not isinstance(points, list):
                        raise ValueError(f"timemap for act {act_name} must be a list")
                    # validate monotonic
                    findings = timemap.check_monotonic(points)
                    if findings:
                        raise ValueError(f"timemap for act {act_name} is not monotonic")
                    timemap_list.append({"act": act_name, "points": points})
        if timemap_list:
            result["timemaps"] = timemap_list

    # author, license: from meta
    meta = recipe.get("meta")
    if isinstance(meta, dict):
        author = meta.get("author")
        if author is not None:
            result["author"] = author
        license_val = meta.get("license")
        if license_val is not None:
            result["license"] = license_val
        # source: meta.url
        url = meta.get("url")
        if url is not None:
            result["source"] = url

    return result