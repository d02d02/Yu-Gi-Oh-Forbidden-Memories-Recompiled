"""A mod's "native_models" (src/pc/render/native_registry.c, notes/native-models.md): the checks the port makes of the
entries when it reads the manifest, and whether the files they name are in the mod. The models themselves (the HDM4
file, model.json, the PNGs) are tools/hd-models/native_check.py's to check: it reads them as the game does."""
from __future__ import annotations

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
