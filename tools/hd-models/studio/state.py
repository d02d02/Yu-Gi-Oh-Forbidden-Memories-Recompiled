"""The Model Studio's stage state machine (UI-free, stdlib only): notes/studio/studio-view.md section 2 and 5.

A Studio holds one recipe (a dict, see recipe.py) and, per stage S0..S9, the findings of the last run of its checks:
  state(stage) -> "todo" | "pass" | "warn" | "fail" | "stale"
    todo   never run
    stale  an input changed since the last run (the knob values are kept)
    fail   a check failed
    warn   a warning nobody acknowledged yet
    pass   no fail, every warn acknowledged
Acknowledgements are stored in the recipe (`acks`: [{"check", "value"}]) and die when the measured value moves.
Knob edits go through edit()/reset_stage(): they are recorded for linear undo/redo, mark the stages that depend on the edit
stale, and flag the recipe unsaved; save() writes it atomically (canonical JSON, a .bak of the previous file).
A finding is a dict: {"id", "level": "info"|"warn"|"fail", "message", "fix", "value", ...}.
"""
import copy
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import recipe as recipe_module  # noqa: E402

STAGES = ("S0", "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9")
GROUPS = (("Prepare", ("S0", "S1", "S2", "S3")), ("Fit", ("S4", "S5", "S6")), ("Judge", ("S7", "S8")), ("Ship", ("S9",)))
# stage -> the stages whose result depends on it (studio-view.md: S1 -> S2 -> S4,S5; S5 -> S6; S4,S5,S6,S3 -> S7 -> S8 -> S9)
DEPENDENTS = {
    "S0": ("S1", "S3"), "S1": ("S2",), "S2": ("S4", "S5"), "S3": ("S7",), "S4": ("S7",), "S5": ("S6", "S7"),
    "S6": ("S7",), "S7": ("S8",), "S8": ("S9",), "S9": (),
}
# the build needs these to be pass (acknowledged warns count as pass)
BUILD_NEEDS = ("S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8")
LEVELS = ("info", "warn", "fail")


def stage_of_path(path):
    """Which stage owns a recipe key, e.g. "rig.root" -> "S2". None for keys that belong to no stage (acks, studio, schema)."""
    top, _, rest = path.partition(".")
    if top in ("source", "model", "meta"):
        return "S0"
    if top == "audit":
        return "S1"
    if top == "rig":
        return "S2"
    if top == "mat":
        return "S3"
    if top == "size":
        return "S4"
    if top == "timing":
        return "S6"
    if top == "acts":
        leaf = path.rsplit(".", 1)[-1]
        return "S6" if leaf in ("strike", "strike_joints", "timemap", "hold") else "S5"
    if top in ("look", "shots"):
        return "S7"
    if top == "runs":
        return "S8"
    if top == "pkg":
        return "S9"
    return None


def get_path(data, path, default=None):
    node = data
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            return default
        node = node[part]
    return node


def set_path(data, path, value):
    """Set (or, for value None, delete) a dotted path, creating objects on the way; empty parents are removed."""
    parts = path.split(".")
    chain = [data]
    for part in parts[:-1]:
        nxt = chain[-1].get(part)
        if not isinstance(nxt, dict):
            if value is None:
                return
            nxt = chain[-1][part] = {}
        chain.append(nxt)
    if value is None:
        chain[-1].pop(parts[-1], None)
        for depth in range(len(parts) - 2, -1, -1):  # an object left empty is removed with its key
            if chain[depth + 1]:
                break
            del chain[depth][parts[depth]]
    else:
        chain[-1][parts[-1]] = value


class Studio:
    def __init__(self, recipe=None):
        self.recipe = copy.deepcopy(recipe) if recipe else {"schema": recipe_module.SCHEMA}
        self.findings = {}      # stage -> list of findings of the last run
        self.inputs = {}        # stage -> the inputs digest of that run
        self.stale = set()      # stages with a result whose inputs changed
        self.undo_stack, self.redo_stack = [], []
        self.save_state = "saved"   # "saved" | "unsaved" | "error"
        self.save_error = ""

    # --- state ------------------------------------------------------------------------------------------------------
    def state(self, stage):
        if stage not in self.findings:
            return "todo"
        if stage in self.stale:
            return "stale"
        levels = [f["level"] for f in self.findings[stage]]
        if "fail" in levels:
            return "fail"
        if self.unacknowledged(stage):
            return "warn"
        return "pass"

    def states(self):
        return {s: self.state(s) for s in STAGES}

    def unacknowledged(self, stage):
        return [f for f in self.findings.get(stage, []) if f["level"] == "warn" and not self._acked(f)]

    def _acked(self, finding):
        return any(a.get("check") == finding["id"] and a.get("value") == finding.get("value") for a in self.recipe.get("acks", []))

    def can_build(self):
        """(ok, reasons): every build stage pass (or only acknowledged warns), none todo/stale/fail/warn."""
        reasons = [f"{s} is {self.state(s)}" for s in BUILD_NEEDS if self.state(s) != "pass"]
        if self.save_state != "saved":
            reasons.append("the recipe is not saved")
        return not reasons, reasons

    # --- findings ---------------------------------------------------------------------------------------------------
    def set_findings(self, stage, findings, inputs=None):
        """Store the result of running a stage's checks. Returns the acknowledgements dropped because the value moved."""
        for f in findings:
            if f.get("level") not in LEVELS:
                raise ValueError(f"finding {f.get('id')}: level must be one of {LEVELS}")
        self.findings[stage] = copy.deepcopy(findings)
        self.inputs[stage] = copy.deepcopy(inputs)
        self.stale.discard(stage)
        current = {f["id"]: f.get("value") for f in findings if f["level"] == "warn"}
        dropped = []
        kept = []
        for a in self.recipe.get("acks", []):
            if a.get("check", "").startswith(stage + ".") and current.get(a["check"], object()) != a.get("value"):
                dropped.append(a)
            else:
                kept.append(a)
        if dropped:
            self._write_acks(kept)
        return dropped

    def unchanged(self, stage, inputs):
        """True when a stale stage's inputs equal the ones of its last run: opening it can restore its old state silently."""
        return stage in self.findings and self.inputs.get(stage) == inputs

    def reopen(self, stage, inputs):
        """Opening a stage: returns True when its checks must run; a stale stage with unchanged inputs just becomes current."""
        if stage not in self.findings:
            return True
        if stage in self.stale and self.unchanged(stage, inputs):
            self.stale.discard(stage)
            return False
        return stage in self.stale

    def acknowledge(self, check_id, value):
        stage = check_id.split(".")[0]
        if not any(f["id"] == check_id and f["level"] == "warn" and f.get("value") == value for f in self.findings.get(stage, [])):
            raise ValueError(f"{check_id} has no warning with value {value!r} to acknowledge")
        acks = [a for a in self.recipe.get("acks", []) if a.get("check") != check_id]
        acks.append({"check": check_id, "value": value})
        self._write_acks(acks)

    def _write_acks(self, acks):
        if acks:
            self.recipe["acks"] = acks
        else:
            self.recipe.pop("acks", None)
        self.save_state = "unsaved"

    # --- edits ------------------------------------------------------------------------------------------------------
    def edit(self, path, value):
        """Set a knob (value None removes it). Returns the stages marked stale. One undo entry."""
        return self._apply([(path, get_path(self.recipe, path), value)], record=True)

    def reset_stage(self, stage):
        """Reset to auto: remove every key the stage owns. One undo entry. Returns the stages marked stale."""
        owned = [p for p in self._leaf_paths(self.recipe) if stage_of_path(p) == stage]
        return self._apply([(p, get_path(self.recipe, p), None) for p in owned], record=True)

    def change_category(self, category):
        """A category change marks everything except S0 stale (studio-view.md section 2)."""
        marked = self._apply([("model.category", get_path(self.recipe, "model.category"), category)], record=True)
        if "S0" in marked:  # S0 holds the category itself: its checks are not stale, only what was built on it
            marked.remove("S0")
            self.stale.discard("S0")
        for s in STAGES[1:]:
            if s in self.findings and s not in self.stale:
                self.stale.add(s)
                marked.append(s)
        return sorted(set(marked))

    def undo(self):
        if not self.undo_stack:
            return []
        entry = self.undo_stack.pop()
        self.redo_stack.append(entry)
        return self._apply([(p, new, old) for p, old, new in entry], record=False)

    def redo(self):
        if not self.redo_stack:
            return []
        entry = self.redo_stack.pop()
        self.undo_stack.append(entry)
        return self._apply(entry, record=False)

    def _apply(self, changes, record):
        changes = [(p, old, new) for p, old, new in changes if old != new]
        if not changes:
            return []
        marked = []
        for path, _old, new in changes:
            set_path(self.recipe, path, copy.deepcopy(new))
            owner = stage_of_path(path)
            if owner:
                for s in (owner, *self.downstream(owner)):
                    if s in self.findings and s not in self.stale:
                        self.stale.add(s)
                        marked.append(s)
        if record:
            self.undo_stack.append([(p, copy.deepcopy(o), copy.deepcopy(n)) for p, o, n in changes])
            self.redo_stack.clear()
        self.save_state = "unsaved"
        return marked

    @staticmethod
    def downstream(stage):
        seen, todo = [], list(DEPENDENTS[stage])
        while todo:
            s = todo.pop(0)
            if s not in seen:
                seen.append(s)
                todo += DEPENDENTS[s]
        return seen

    @staticmethod
    def _leaf_paths(data, prefix=""):
        for key, value in data.items():
            path = f"{prefix}{key}"
            if isinstance(value, dict) and value and key not in ("acts",):
                yield from Studio._leaf_paths(value, path + ".")
            elif isinstance(value, dict) and key == "acts":
                for act, body in value.items():
                    for leaf in body if isinstance(body, dict) else ():
                        yield f"{path}.{act}.{leaf}"
            else:
                yield path

    # --- saving -----------------------------------------------------------------------------------------------------
    def save(self, path):
        """Write the recipe atomically (canonical JSON), keeping the previous file as <path>.bak."""
        path = Path(path)
        try:
            text = recipe_module.canonical_json(self.recipe)
            tmp = path.with_name(path.name + ".tmp")
            tmp.write_text(text, encoding="utf-8")
            if path.exists():
                os.replace(path, path.with_name(path.name + ".bak"))
            os.replace(tmp, path)
        except OSError as e:
            self.save_state, self.save_error = "error", str(e)
            return False
        self.save_state, self.save_error = "saved", ""
        return True

    # --- report -----------------------------------------------------------------------------------------------------
    def report(self):
        """Everything the UI shows about the stages, as plain data (also what the golden tests compare)."""
        return {
            "states": self.states(),
            "findings": {s: copy.deepcopy(self.findings[s]) for s in STAGES if s in self.findings},
            "build": dict(zip(("ok", "reasons"), self.can_build())),
        }

    def report_json(self):
        return json.dumps(self.report(), indent=2, sort_keys=True, ensure_ascii=False) + "\n"
