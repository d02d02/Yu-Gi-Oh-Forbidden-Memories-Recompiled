#!/usr/bin/env python3
"""Check native models the way the game reads them, without the game (plain Python: nothing to install).

    native_check.py PATH [PATH ...]

PATH is a mod folder (its mod.json's "native_models"), a package's model.json, or an .hdm file. Every problem the
game would note beside the mod is printed with the same reason, then what each model is: its size, clips, the clip
each act plays, the strike frames, its textures and the memory it takes. Exit status 1 when a model would not be
drawn (an entry the game leaves out, a file it refuses); 0 otherwise, warnings included."""
import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import native_spec as spec  # noqa: E402


class Report:
    def __init__(self):
        self.errors = 0
        self.warnings = 0

    def error(self, where, text):
        self.errors += 1
        print(f"error: {where}: {text}")

    def warn(self, where, text):
        self.warnings += 1
        print(f"warning: {where}: {text}")


def describe(where, info, extra=""):
    low, high = info["low"], info["high"]
    print(f"{where}: {info['vertices']} vertices, {info['triangles']} triangles, {info['bones']} bones, "
          f"{len(info['clips'])} clips, {info['bytes'] / 1e6:.1f} MB{extra}")
    print(f"  bind pose: {high[1] - low[1]:.0f} game units tall, soles {high[1]:.0f} below the root, "
          f"{high[0] - low[0]:.0f} wide, {high[2] - low[2]:.0f} deep")
    for clip in info["clips"]:
        print(f"  clip {clip['name']}: {clip['frames']} frames at {clip['fps']:g} fps")


def check_hdm(path, report, where=None):
    where = where or str(path)
    try:
        data = Path(path).read_bytes()
    except OSError as e:
        report.error(where, f"{path} cannot be read ({e.strerror})")
        return None
    try:
        return spec.parse_hdm4(data)
    except spec.Hdm4Error as e:
        report.error(where, f"{path} is not a usable HDM4 model: {e}")
        return None


def act_clip(package, info, act):
    """The clip an act plays (NativeAnim_ActClip): the package's, else the default name, else the first clip."""
    names = [c["name"] for c in info["clips"]]
    mapped = (package.get("clips") or {}).get(act) if isinstance(package.get("clips"), dict) else None
    if mapped in names:
        return mapped
    if spec.DEFAULT_CLIPS[act] in names:
        return spec.DEFAULT_CLIPS[act]
    return names[0] if names else None


def check_package(path, report, where=None):
    """A model.json and what it names; the bytes it takes, or None when the game would not draw it."""
    path = Path(path)
    where = where or str(path)
    try:
        package = spec.read_json(path)
    except (OSError, ValueError) as e:
        report.error(where, f"model.json: {e}")
        return None
    if not isinstance(package, dict):
        report.error(where, "model.json is not an object")
        return None
    if package.get("format", 1) != 1:
        report.error(where, f"model.json is format {package.get('format')}; this build reads format 1")
        return None
    for key in package:
        if key not in spec.PACKAGE_KEYS:
            report.warn(where, f"model.json: \"{key}\" is not read")
    model = package.get("model", "")
    if not isinstance(model, str) or not model or not spec.paths_contained(model):
        report.error(where, f"model.json: \"model\" names the .hdm file beside it (\"{model}\" is not a file inside the mod)")
        return None
    info = check_hdm(path.parent / model, report, where)
    if not info:
        return None
    total = info["bytes"]
    textures = package.get("textures", {})
    shown = {}
    if not isinstance(textures, dict):
        report.warn(where, "\"textures\" is an object: {\"base\": \"base.png\"}")
        textures = {}
    for key, name in textures.items():
        if key not in spec.TEXTURE_KEYS:
            continue  # the game does not look at other keys
        if not isinstance(name, str) or not name or not spec.paths_contained(name):
            report.warn(where, f"textures.{key}: \"{name}\" is not a file inside the mod")
            continue
        try:
            w, h = spec.png_size(path.parent / name)
        except (OSError, ValueError) as e:
            report.warn(where, f"textures.{key}: {name}: {getattr(e, 'strerror', None) or e} (the model's own is used)")
            continue
        if w > spec.MAX_SIDE or h > spec.MAX_SIDE:
            report.warn(where, f"textures.{key}: {name}: {w}x{h} is too large (each side at most {spec.MAX_SIDE})")
            continue
        while w > spec.TEXTURE_MAX or h > spec.TEXTURE_MAX:
            w, h = max(1, w // 2), max(1, h // 2)
        if (w, h) != spec.png_size(path.parent / name):
            report.warn(where, f"textures.{key}: {name} is halved to {w}x{h} (MEMORIES_NATIVE_TEXTURE_MAX, default {spec.TEXTURE_MAX})")
        total += w * h * 4
        shown[key] = f"{name} {w}x{h}"
    if "base" not in shown:
        shown["base"] = f"the model file's {info['texture'][0]}x{info['texture'][1]}"
        if info["texture"] == (1, 1):
            report.warn(where, "no base texture: the model is drawn in one colour")
    names = [c["name"] for c in info["clips"]]
    clips = package.get("clips", {})
    if clips and not isinstance(clips, dict):
        report.warn(where, "\"clips\" maps acts to the model's clips: {\"attack\": \"Sword_Attack\"}")
    elif clips:
        for act, clip in clips.items():
            if act not in spec.ACTS:
                report.warn(where, f"clips: \"{act}\" is not an act ({', '.join(spec.ACTS)})")
            elif clip not in names:
                report.warn(where, f"clips.{act}: the model has no clip \"{clip}\"")
    strike = package.get("strike")
    frames_ok = []
    if strike is not None:
        attack = act_clip(package, info, "attack")
        frames = [c["frames"] for c in info["clips"] if c["name"] == attack]
        given = strike.get("attack") if isinstance(strike, dict) else None
        if not isinstance(given, list):
            report.warn(where, "\"strike\" lists the attack clip's frames where its blows land: {\"attack\": [11, 30]}")
        else:
            last = -1
            for frame in given[:spec.MAX_STRIKES]:
                if not isinstance(frame, int) or frame <= last or not frames or frame >= frames[0]:
                    report.warn(where, f"strike.attack: {frame} is not a frame of the attack clip ({attack}, "
                                       f"{frames[0] if frames else 0} frames) after the one before")
                    frames_ok = []
                    break
                frames_ok.append(frame)
                last = frame
            if len(given) > spec.MAX_STRIKES:
                report.warn(where, f"strike.attack: at most {spec.MAX_STRIKES} blows")
    scale = package.get("scale")
    if scale is not None and (not isinstance(scale, int) or not 10 <= scale <= 1000):
        report.warn(where, "\"scale\" is a percentage, 10 to 1000")
    offset = package.get("offset")
    if offset is not None and not (isinstance(offset, list) and len(offset) == 3 and
                                   all(isinstance(v, int) and not isinstance(v, bool) and -2000 <= v <= 2000 for v in offset)):
        report.warn(where, "\"offset\" is [x, y, z]: whole numbers from -2000 to 2000 (x right, y down, z forward)")
    shots = package.get("shots")
    if shots is not None:
        if not isinstance(shots, list):
            report.warn(where, "\"shots\" is a list: [{\"act\": \"attack\", \"from\": 0, \"to\": 60, \"yaw\": 40}]")
        else:
            if len(shots) > spec.MAX_SHOTS:
                report.warn(where, f"shots: at most {spec.MAX_SHOTS} shots")
            for i, shot in enumerate(shots[:spec.MAX_SHOTS]):
                if not isinstance(shot, dict) or shot.get("act") not in spec.ACTS:
                    report.warn(where, f"shots[{i}]: an object whose \"act\" is one of {', '.join(spec.ACTS)}")
                    continue
                bad = [k for k, (lo, hi) in spec.SHOT_RANGES.items()
                       if k in shot and not (isinstance(shot[k], int) and not isinstance(shot[k], bool) and lo <= shot[k] <= hi)]
                if bad or shot.get("to", 0) < shot.get("from", 0):
                    report.warn(where, f"shots[{i}]: {', '.join(bad) or 'to < from'} out of range (whole numbers; "
                                       + ", ".join(f"{k} {lo}..{hi}" for k, (lo, hi) in spec.SHOT_RANGES.items()) + ")")
                else:
                    print(f"  shot {i}: {shot['act']}{' (the other monster)' if shot.get('other') else ''} "
                          f"frames {shot.get('from', 0)}-{shot.get('to', 0)}")
    look = package.get("look", {})
    if not isinstance(look, dict):
        report.warn(where, "\"look\" is an object: {\"ambient\": 20, \"light_gain\": 100}")
    else:
        for key, value in look.items():
            if key not in spec.LOOK_KEYS:
                report.warn(where, f"look: \"{key}\" is not read ({', '.join(spec.LOOK_KEYS)})")
            elif not isinstance(value, int) or value < 0:
                report.warn(where, f"look.{key}: a whole number (percent; camera_near in game units)")
    describe(where, info, f", {total / 1e6:.1f} MB in memory with its textures")
    for act in spec.ACTS:
        print(f"  {act:9} -> {act_clip(package, info, act)}")
    if frames_ok:
        print(f"  blows of the attack at frames {frames_ok}")
    print("  textures: " + ", ".join(f"{k} {v}" for k, v in shown.items()))
    if isinstance(scale, int) and 10 <= scale <= 1000 and scale != 100:
        print(f"  drawn at {scale}% about its soles")
    if isinstance(offset, list) and offset != [0, 0, 0]:
        print(f"  moved by {offset} (x right, y down, z forward)")
    return total


def check_mod(folder, report):
    folder = Path(folder)
    manifest_path = folder / "mod.json"
    try:
        manifest = spec.read_json(manifest_path)
    except (OSError, ValueError) as e:
        report.error(str(manifest_path), f"cannot be read: {e}")
        return
    mod = manifest.get("id", folder.name) if isinstance(manifest, dict) else folder.name
    entries = manifest.get("native_models") if isinstance(manifest, dict) else None
    if entries is None:
        report.error(mod, "mod.json has no \"native_models\"")
        return
    if not isinstance(entries, list):
        report.error(mod, "native_models is a list: [{\"cards\": [364], \"package\": \"angel/model.json\"}]")
        return
    if len(entries) > spec.REGISTRY_MAX:
        report.error(mod, f"native_models[{spec.REGISTRY_MAX}] and after: at most {spec.REGISTRY_MAX} native models in all the mods")
    total, seen = 0, {}
    for i, entry in enumerate(entries[:spec.REGISTRY_MAX]):
        where = f"{mod}: native_models[{i}]"
        if not isinstance(entry, dict):
            report.error(where, "needs a \"package\" (a model.json) or a \"file\" (an .hdm model), one of the two")
            continue
        package, file = entry.get("package", ""), entry.get("file", "")
        named = package or file
        if not named or (package and file) or not isinstance(named, str):
            report.error(where, "needs a \"package\" (a model.json) or a \"file\" (an .hdm model), one of the two")
            continue
        if not spec.paths_contained(named):
            report.error(where, f"{named} is not a file inside the mod")
            continue
        cards = []
        for key, values in (("card", [entry["card"]] if "card" in entry else []), ("cards", entry.get("cards", []))):
            if not isinstance(values, list):
                report.warn(where, "\"cards\" is a list of card ids: [364]")
                continue
            for card in values:
                if not isinstance(card, int) or isinstance(card, bool) or not 1 <= card <= 65535:
                    report.warn(where, f"{key}: a card is a card id (1 to 65535)")
                elif len(cards) >= spec.REGISTRY_CARDS:
                    report.warn(where, f"{key}: at most {spec.REGISTRY_CARDS} cards per entry (another entry can name more)")
                else:
                    cards.append(card)
        model = entry.get("model")
        if model is not None and (not isinstance(model, int) or not 0 <= model <= 65535):
            report.warn(where, "\"model\" is a disc model id (the card id - 1)")
            model = None
        if not cards and model is None:
            report.error(where, "names no card (\"cards\": [364]) and no disc model (\"model\": 363)")
            continue
        if "setting" in entry:
            print(f"{where}: drawn only while the mod's setting {entry['setting']!r} allows it")
        for card in cards:
            if card in seen:
                report.warn(where, f"card {card} is also in native_models[{seen[card]}]: this later one is drawn")
            seen[card] = i
        target = f"cards {cards}" if cards else f"disc model {model}"
        if package:
            bytes_ = check_package(folder / package, report, where)
        else:
            info = check_hdm(folder / file, report, where)
            bytes_ = info["bytes"] if info else None
            if info:
                describe(where, info)
        if bytes_ is None:
            continue
        total += bytes_
        print(f"  for {target}")
    print(f"{mod}: {total / 1e6:.1f} MB for all its models, if they all show (the game's budget: {spec.BUDGET_MB} MB)")
    if total > spec.BUDGET_MB * 1024 * 1024:
        report.warn(mod, "past the memory budget: the models read last are not drawn (smaller textures help)")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+", type=Path)
    a = ap.parse_args(argv)
    report = Report()
    for path in a.paths:
        if path.is_dir():
            check_mod(path, report)
        elif path.suffix.lower() == ".json":
            check_package(path, report)
        else:
            info = check_hdm(path, report)
            if info:
                describe(str(path), info)
    print(f"{report.errors} errors, {report.warnings} warnings")
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
