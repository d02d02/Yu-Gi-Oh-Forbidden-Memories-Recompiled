"""A mod's "native_models" (src/pc/render/native_registry.c, notes/native-models.md): the checks the port makes of the
entries when it reads the manifest, and whether the files they name are in the mod. The models themselves (the HDM4
file, model.json, the PNGs) are tools/hd-models/native_check.py's to check: it reads them as the game does."""
from __future__ import annotations

import json
import re
from pathlib import Path

from .art import contained

REGISTRY_MAX = 64   # NATIVE_REGISTRY_MAX: entries in all the mods
CARDS_MAX = 64      # NATIVE_REGISTRY_CARDS: cards per entry


def _whole(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def check(project, has_file) -> list:
    """(level, where, message) for each thing the game would note; has_file(name) says whether the mod holds a file."""
    out = []
    entries = project.other.get("native_models")
    if entries is None:
        return out
    if not isinstance(entries, list):
        return [("error", "native_models", "native_models is a list: [{\"cards\": [364], \"package\": \"angel/model.json\"}]")]
    if len(entries) > REGISTRY_MAX:
        out.append(("error", f"native_models[{REGISTRY_MAX}]", f"at most {REGISTRY_MAX} native models in all the mods"))
    settings = {s.get("key") for s in project.info.settings if isinstance(s, dict)}
    seen = {}
    for i, entry in enumerate(entries[:REGISTRY_MAX]):
        where = f"native_models[{i}]"
        if not isinstance(entry, dict):
            out.append(("error", where, "needs a \"package\" (a model.json) or a \"file\" (an .hdm model), one of the two"))
            continue
        package, file = entry.get("package", ""), entry.get("file", "")
        named = package or file
        if not isinstance(named, str) or not named or (package and file):
            out.append(("error", where, "needs a \"package\" (a model.json) or a \"file\" (an .hdm model), one of the two"))
            continue
        if not contained(named):
            out.append(("error", where, f"{named} is not a file inside the mod"))
            continue
        if not has_file(named):
            out.append(("error", where, f"{named} is not in the mod: the monster keeps its disc model"))
        cards = []
        values = ([entry["card"]] if "card" in entry else []) + (entry.get("cards") if isinstance(entry.get("cards"), list) else [])
        if "cards" in entry and not isinstance(entry["cards"], list):
            out.append(("warning", where, "\"cards\" is a list of card ids: [364]"))
        for card in values:
            if not _whole(card) or not 1 <= card <= 65535:
                out.append(("warning", where, f"{card!r} is not a card id (1 to 65535): left out"))
            elif len(cards) >= CARDS_MAX:
                out.append(("warning", where, f"at most {CARDS_MAX} cards per entry (another entry can name more)"))
                break
            else:
                cards.append(card)
                if card not in project.cards:
                    out.append(("warning", where, f"card {card} is neither a card of the game nor one this mod adds"))
        model = entry.get("model")
        if model is not None and (not _whole(model) or not 0 <= model <= 65535):
            out.append(("warning", where, "\"model\" is a disc model id (the card id - 1): left out"))
            model = None
        if not cards and model is None:
            out.append(("error", where, "names no card (\"cards\": [364]) and no disc model (\"model\": 363)"))
            continue
        setting = entry.get("setting")
        if setting is not None and setting not in settings:
            out.append(("warning", where, f"\"setting\" {setting!r} is not one of the mod's settings: the entry is always used"))
        for card in cards:
            if card in seen:
                out.append(("warning", where, f"card {card} is also in native_models[{seen[card]}]: this later one is drawn"))
            seen[card] = i
    return out


# --- editing (the Native models tab) ------------------------------------------------------------------

PACKAGE_FILE_MAX = 64 * 1024 * 1024     # bytes of one file copied into the mod
PACKAGE_SUFFIXES = (".json", ".hdm", ".png")


def entries(project) -> list:
    """The mod's native_models list (made on first use)."""
    value = project.other.get("native_models")
    if not isinstance(value, list):
        value = project.other["native_models"] = []
    return value


def parse_cards(text: str) -> list:
    """Card ids from "364, 1 2": whole numbers 1..65535, in order, once each; ValueError names the first bad word."""
    cards = []
    for word in re.split(r"[\s,;]+", text.strip()):
        if not word:
            continue
        if not word.isdigit() or not 1 <= int(word) <= 65535:
            raise ValueError(f"{word!r} is not a card id (1 to 65535)")
        if int(word) not in cards:
            cards.append(int(word))
    if len(cards) > CARDS_MAX:
        raise ValueError(f"at most {CARDS_MAX} cards per entry")
    return cards


def entry_cards(entry) -> list:
    """The cards an entry names ("card" and "cards"), as the game reads them."""
    if not isinstance(entry, dict):
        return []
    cards = ([entry["card"]] if _whole(entry.get("card")) else []) + \
            [c for c in (entry.get("cards") if isinstance(entry.get("cards"), list) else []) if _whole(c)]
    return cards


def package_folder(model_json: str) -> str:
    """The folder of a mod-relative package path ("models/angel/model.json" -> "models/angel/")."""
    return model_json.rsplit("/", 1)[0] + "/" if "/" in model_json else ""


def add_package(project, model_json, cards=()) -> int:
    """Copy the package whose model.json is at `model_json` (and every .json/.hdm/.png beside it) into the mod under
    models/<folder>/ and name it in a new entry for `cards`; the entry's index. OSError/ValueError when the folder
    holds no usable package."""
    source = Path(model_json)
    if source.name != "model.json" or not source.is_file():
        raise ValueError("choose a package's model.json")
    try:
        meta = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as problem:
        raise ValueError(f"{source.name} cannot be read: {problem}")
    if not isinstance(meta, dict) or not isinstance(meta.get("model"), str) or not meta["model"]:
        raise ValueError("model.json names no \"model\" file")
    held = sorted(p for p in source.parent.iterdir() if p.is_file() and p.suffix.lower() in PACKAGE_SUFFIXES)
    if not any(p.name == meta["model"] for p in held):
        raise ValueError(f"{meta['model']} is not beside model.json")
    for p in held:
        if p.stat().st_size > PACKAGE_FILE_MAX:
            raise ValueError(f"{p.name} is too big to put in a mod")
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", source.parent.name).strip("-.") or "model"
    folder, n = f"models/{slug}/", 2
    taken = {e.get("package") for e in entries(project) if isinstance(e, dict)}
    while any(name.startswith(folder) for name in project.files) or \
            (project.source_dir and (Path(project.source_dir) / folder).exists()) or f"{folder}model.json" in taken:
        folder, n = f"models/{slug}-{n}/", n + 1
    for p in held:
        project.files[folder + p.name] = p.read_bytes()
    entries(project).append({"cards": list(cards), "package": folder + "model.json"})
    return len(entries(project)) - 1


def remove_entry(project, index: int) -> None:
    """Drop entry `index`; the copied files of its package go too unless another entry uses the folder."""
    items = entries(project)
    entry = items.pop(index)
    if not items:
        project.other.pop("native_models", None)
    package = entry.get("package") if isinstance(entry, dict) else None
    if isinstance(package, str) and package_folder(package):
        folder = package_folder(package)
        if not any(isinstance(e, dict) and isinstance(e.get("package"), str) and e["package"].startswith(folder)
                   for e in items):
            for name in [n for n in project.files if n.startswith(folder)]:
                del project.files[name]


def set_cards(project, index: int, cards: list) -> None:
    """The entry's cards: "cards" (and no "card"), which the game reads the same."""
    entry = entries(project)[index]
    entry.pop("card", None)
    entry["cards"] = list(cards)


def about(project, entry) -> dict:
    """name/author/license/source of an entry's package, from the model.json in the mod ('' when unknown)."""
    out = {"name": "", "author": "", "license": "", "source": ""}
    package = entry.get("package") if isinstance(entry, dict) else None
    if not isinstance(package, str):
        return out
    blob = project.files.get(package)
    if blob is None and project.source_dir and contained(package):
        try:
            blob = (Path(project.source_dir) / package).read_bytes()
        except OSError:
            blob = None
    try:
        meta = json.loads(blob.decode("utf-8")) if blob else {}
    except (UnicodeError, ValueError):
        meta = {}
    for key in out:
        if isinstance(meta, dict) and isinstance(meta.get(key), str):
            out[key] = meta[key]
    return out
