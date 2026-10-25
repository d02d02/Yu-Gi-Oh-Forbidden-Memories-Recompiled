"""The Model Studio's session: open a glb/recipe, run stages, edit with debounce, undo/redo, autosave.

The Tk tab drives this object; it is UI-free and testable headless.
"""
import copy
import hashlib
import json
import os
import time
from pathlib import Path

from . import audit
from . import build
from . import clipdata
from . import clips
from . import log
from . import look
from . import package
from . import placement
from . import report
from . import provide
from . import resolutions
from . import resolve_actions
from . import runs
from . import timemap
from . import state
import recipe


class Session:
    def __init__(self, glb_path, studio, recipe_path, model):
        self.glb = Path(glb_path)
        self.studio = studio
        self.recipe_path = Path(recipe_path) if recipe_path else None
        self._model = model
        self._library = None
        self._sha256 = self._file_sha256(self.glb)
        self._pending = {}      # stage -> time (monotonic) when edit was made

    @classmethod
    def open(cls, glb_path, recipe_path=None):
        glb_path = Path(glb_path)
        recipe_path = Path(recipe_path) if recipe_path else None

        # Load or create recipe
        if recipe_path and recipe_path.exists():
            rec = recipe.load(recipe_path)
            # source.path in recipe is relative to recipe file; resolve to absolute
            src_path = rec.get("source", {}).get("path")
            if src_path:
                abs_src = (recipe_path.parent / src_path).resolve()
                if abs_src != glb_path.resolve():
                    # glb moved; we'll treat as sha256 change
                    pass
        else:
            # New recipe: store glb path relative to recipe file if recipe_path given, else absolute
            if recipe_path:
                try:
                    rel = glb_path.resolve().relative_to(recipe_path.parent.resolve())
                    src_path = str(rel)
                except ValueError:
                    src_path = str(glb_path.resolve())
            else:
                src_path = str(glb_path.resolve())
            rec = {"schema": recipe.SCHEMA, "source": {"path": src_path}, "model": {"category": "C1"}}

        studio = state.Studio(rec)
        sha256 = cls._file_sha256(glb_path)

        # Load model; if it fails, audit_all will produce S0.load fail
        model = None
        try:
            model = audit.load_model(glb_path)
        except audit.AuditError:
            pass

        session = cls(glb_path, studio, recipe_path, model)
        log.attach(recipe_path.parent if recipe_path else glb_path.parent)
        log.event("open", glb_path.name, f"model={'ok' if model else 'failed'}")
        # Store sha256 in recipe if not present
        if "sha256" not in studio.recipe.get("source", {}):
            state.set_path(studio.recipe, "source.sha256", sha256)

        # If model failed to load, run audit_all to produce S0.load fail
        if model is None:
            results = audit.audit_all(glb_path, studio.recipe)
            audit.apply_to_studio(studio, results, {s: session.stage_inputs(s) for s in ("S0", "S1", "S2", "S3")})

        return session

    @staticmethod
    def _file_sha256(path):
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    def _check_reload(self):
        """Reload model if source.sha256 changed; mark all stages stale."""
        current_sha = self._file_sha256(self.glb)
        stored_sha = state.get_path(self.studio.recipe, "source.sha256")
        if current_sha != stored_sha:
            # File changed; reload model
            self._model = None
            try:
                self._model = audit.load_model(self.glb)
            except audit.AuditError:
                pass
            state.set_path(self.studio.recipe, "source.sha256", current_sha)
            self._sha256 = current_sha
            # Mark all stages that have findings as stale
            for s in state.STAGES:
                if s in self.studio.findings:
                    self.studio.stale.add(s)

    def stage_inputs(self, stage):
        """Return the recipe sections this stage reads, plus sha256, as plain data."""
        self._check_reload()
        rec = self.studio.recipe
        base = {"sha256": self._sha256}
        if stage == "S0":
            base.update({
                "source": copy.deepcopy(rec.get("source", {})),
                "model": copy.deepcopy(rec.get("model", {})),
                "meta": copy.deepcopy(rec.get("meta", {})),
            })
        elif stage == "S1":
            base.update({
                "source": copy.deepcopy(rec.get("source", {})),
                "model": copy.deepcopy(rec.get("model", {})),
                "meta": copy.deepcopy(rec.get("meta", {})),
                "audit": copy.deepcopy(rec.get("audit", {})),
            })
        elif stage == "S2":
            base.update({
                "rig": copy.deepcopy(rec.get("rig", {})),
                "model": {"category": rec.get("model", {}).get("category")},
            })
        elif stage == "S3":
            base.update({
                "mat": copy.deepcopy(rec.get("mat", {})),
            })
        elif stage == "S5":
            base.update({"acts": copy.deepcopy(rec.get("acts", {}))})
        elif stage == "S4":
            base.update({"size": copy.deepcopy(rec.get("size", {}))})
        elif stage == "S8":
            base.update({"runs": copy.deepcopy(rec.get("runs", []))})
        elif stage == "S9":
            base.update({"pkg": copy.deepcopy(rec.get("pkg", {})), "meta": copy.deepcopy(rec.get("meta", {}))})
        elif stage == "S6":
            base.update({
                "acts": copy.deepcopy(rec.get("acts", {})),
                "timing": copy.deepcopy(rec.get("timing", {})),
                "cards": copy.deepcopy(rec.get("model", {}).get("cards", [])),
            })
        elif stage == "S7":
            base.update({
                "look": copy.deepcopy(rec.get("look", {})),
                "shots": copy.deepcopy(rec.get("shots", [])),
                "cards": copy.deepcopy(rec.get("model", {}).get("cards", [])),
            })
        return base

    @staticmethod
    def _arena_rows():
        """Disc reference rows from the SM0 pack (no disc needed); {} when absent."""
        try:
            with open(Path(__file__).parent / "reference" / "arena_rows.json", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            return {}

    def add_run_mark(self, row, result, problem=None, now=None):
        """Record that a scene row was seen or has a problem, against the current source hash. Returns the mark."""
        mark = runs.make_mark(row, result, self._sha256, time.time() if now is None else now, problem)
        self.edit("runs", list(self.studio.recipe.get("runs", [])) + [mark])
        return mark

    def _run_fit_stage(self, stage):
        """S4 reads the glb; S6-S9 read the recipe and the reference pack."""
        rec = self.studio.recipe
        cards = rec.get("model", {}).get("cards") or []
        card_id = str(cards[0]) if cards else ""
        rows = self._arena_rows()
        contact = timemap.contact_for(rows, card_id, "attack")
        if stage == "S4":
            size = dict(rec.get("size", {}))
            if size.get("mode") == "scale":   # the recipe says "scale", the fit says "percent"
                size["mode"] = "percent"
            try:
                return placement.run_s4(str(self.glb), {**rec, "size": size})["findings"]
            except (ValueError, audit.AuditError) as e:
                return [audit.finding("S4.fit", "fail", f"The size could not be fitted: {e}", "Set a size mode and value.")]
        if stage == "S5":
            if self._model is None:
                return [audit.finding("S5.model", "fail", "The model did not open.", "Open a rigged glb.")]
            loops = rec.get("acts", {}).get("idle", {}).get("loop") and ["idle"] or ()
            try:
                cm = self._clip_model(rec)
            except audit.AuditError as e:
                return [audit.finding("S5.library", "fail", f"The library file did not open: {e}", "Pick a glb with clips, or clear the library field.")]
            key = (id(cm), tuple(loops))      # the clips only change with the file or the loop list, not with a knob
            if getattr(self, "_sampled", (None,))[0] != key:
                self._sampled = (key, clipdata.sample_all(cm, loops=loops))
            sampled = self._sampled[1]
            return self._missing_act_findings(rec, cm) + clips.run_s5(sampled, cm.parents, getattr(cm, "names", None))["findings"]
        if stage == "S8":
            disc = bool(os.environ.get("MEMORIES_DISC"))
            return runs.run_s8(rec, self._sha256, disc)["findings"]
        if stage == "S9":   # no build yet: only what the recipe itself can show (provenance)
            return package.run_s9(rec.get("meta", {}), "")["findings"]
        if stage == "S6":
            frames = self._attack_clip_frames(rec)
            return timemap.run_s6(rec, "attack", frames, card_id, rows)["findings"]
        # without a reference row for the card the range cannot be judged: every act in the moves gets no upper bound
        lengths = {s.get("act"): 10 ** 9 for s in rec.get("shots", []) if isinstance(s, dict)}
        if contact:
            lengths["attack"] = contact["row_length"]
        return look.run_s7(rec, lengths)["findings"]

    def _clip_model(self, rec):
        """The model whose clips S5 judges: the library glb when the recipe names one (path relative to the model's folder), else the model."""
        path = (rec.get("library") or {}).get("path")
        if not path:
            return self._model
        lib = Path(path) if Path(path).is_absolute() else Path(self.glb).parent / path
        if self._library is None or self._library[0] != str(lib):
            self._library = (str(lib), audit.load_model(lib))
        return self._library[1]

    def _missing_act_findings(self, rec, model=None):
        """S5.missing-act: an act with no source in the recipe and no clip of the model named for it (the game then plays the idle)."""
        import native_convert
        names = [an.get("name", "") for an in (model or self._model).doc.get("animations", [])]
        lower = [n.lower() for n in names]
        out = []
        for act in native_convert.spec.ACTS:
            if (rec.get("acts", {}).get(act) or {}).get("source"):
                continue
            words = native_convert.ACT_WORDS.get(act, ())
            if act == "idle":
                if not names:
                    out.append(audit.finding("S5.missing-act", "fail", "The model has no clip for idle.", "Choose a clip, a library clip, or a procedural act."))
            elif not any(w in n for w in words for n in lower):
                out.append(audit.finding("S5.missing-act", "warn", f"No clip for {act}: the idle plays instead.", "Choose a clip, a library clip, or a procedural act.", value=act))
        return out

    def _attack_clip_frames(self, rec):
        """Frame count (30 fps) of the clip the attack act names; 30 when no such clip is known."""
        attack = rec.get("acts", {}).get("attack", {})
        name = attack.get("source")
        if self._model is not None and isinstance(name, str):
            try:
                return int(round(clipdata.clip_length(self._clip_model(rec), name) * clipdata.DEFAULT_FPS)) + 1
            except (KeyError, audit.AuditError):
                pass
        return attack.get("clip_frames", 30)

    def build_s9(self, out_dir, runner=None):
        """Build the mod twice into out_dir, then apply_build."""
        rec = self.studio.recipe
        cards = [int(c) for c in rec.get("model", {}).get("cards") or []]
        kw = {"runner": runner} if runner else {}
        return self.apply_build(build.run_build_s9(rec, self.glb, out_dir, cards, **kw), out_dir)

    def preview_key(self):
        return build.preview_key(self.studio.recipe, self._sha256)

    def preview_current(self, out_dir):
        """True when out_dir holds a preview build of the recipe as it is now."""
        stamp = Path(out_dir) / "preview.key"
        try:
            return (Path(out_dir) / "preview").is_dir() and stamp.read_text(encoding="utf-8") == self.preview_key()
        except OSError:
            return False

    def ensure_preview(self, out_dir, runner=None):
        """Build (or reuse) the package the Run rows play; returns build.preview_build's dict. Safe off the main thread."""
        rec = self.studio.recipe
        cards = [int(c) for c in rec.get("model", {}).get("cards") or []]
        kw = {"runner": runner} if runner else {}
        result = build.preview_build(rec, self.glb, out_dir, cards, self.preview_key(), **kw)
        log.event("run", "preview", f"ok={result['ok']} cached={result['cached']}" + ("" if result["ok"] else " " + result["text"]))
        return result

    def apply_build(self, result, out_dir):
        """Store the S9 findings of a build and set pkg.path to the first build ("a"). Main thread only."""
        self.studio.set_findings("S9", result["findings"], self.stage_inputs("S9"))
        log.event("S9", "build", f"ok={result['build'].get('ok')} out={out_dir}")
        self.last_build = result["build"]
        if result["build"]["ok"]:
            self.edit("pkg.path", str(Path(out_dir) / "a"))
        return result

    def export_report(self, path):
        """Write the Markdown report of every stage, the last build and the scene runs to path."""
        rec = self.studio.recipe
        for stage in ("S0", "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9"):
            if stage not in self.studio.findings:
                self.run_stage(stage)
        meta = {"name": rec.get("pkg", {}).get("name") or self.glb.stem, **rec.get("meta", {})}
        text = report.render(self.studio.findings, rec.get("acks", []), meta,
                             getattr(self, "last_build", None), rec.get("runs", []),
                             stand_ins=resolutions.stand_ins(rec))
        Path(path).write_text(text, encoding="utf-8")
        return text

    def run_stage(self, stage):
        """Run audit for the stage, store findings, return them."""
        try:
            findings = self._run_stage(stage)
        except Exception as error:
            log.error(f"stage {stage}", error)
            raise
        log.event(stage, "audit", ", ".join(f"{f.get('level', '?')}:{f.get('id', '?')}" for f in findings) or "no findings")
        return findings

    def _run_stage(self, stage):
        if stage in ("S4", "S5", "S6", "S7", "S8", "S9"):
            findings = self._run_fit_stage(stage)
            self.studio.set_findings(stage, findings, self.stage_inputs(stage))
            return findings
        if self._model is None:
            # Model failed to load; audit_all will produce S0.load fail
            results = audit.audit_all(self.glb, self.studio.recipe)
            audit.apply_to_studio(self.studio, results, {s: self.stage_inputs(s) for s in ("S0", "S1", "S2", "S3")})
            return self.studio.findings.get(stage, [])
        findings = audit.audit_stage(stage, self._model, self.studio.recipe)
        self.studio.set_findings(stage, findings["findings"], self.stage_inputs(stage))
        return findings["findings"]

    def open_stage(self, stage):
        """Open a stage: run checks if needed. Returns True if checks ran."""
        inputs = self.stage_inputs(stage)
        must_run = self.studio.reopen(stage, inputs)
        if must_run:
            self.run_stage(stage)
            return True
        return False

    # --- editing with debounce -------------------------------------------------------------
    def edit(self, path, value, now=None):
        """Edit a knob; record pending debounce for stale stages."""
        if now is None:
            now = time.monotonic()
        marked = self.studio.edit(path, value)
        log.event("edit", path, f"{value!r} stale={sorted(marked)}")
        # Also update pending for stages that were already stale (debounce reset)
        for s in self.studio.stale:
            if s in self._pending:
                self._pending[s] = now
        for s in marked:
            self._pending[s] = now
        return marked

    def due(self, now=None):
        """Stages whose pending time is at least 0.3 s old."""
        if now is None:
            now = time.monotonic()
        return [s for s, t in self._pending.items() if now - t >= 0.3 - 1e-9]

    def run_due(self, now=None):
        """Run all due stages, clear them from pending, return the ids."""
        if now is None:
            now = time.monotonic()
        to_run = self.due(now)
        for s in to_run:
            self.run_stage(s)
            self._pending.pop(s, None)
        return to_run

    # --- persistence -------------------------------------------------------------------------
    def autosave(self):
        """Save to recipe_path if unsaved and path exists. Returns True if wrote."""
        if self.studio.save_state == "unsaved" and self.recipe_path:
            return self.studio.save(self.recipe_path)
        return False

    # --- undo/redo -------------------------------------------------------------------------
    def undo(self):
        if not self.studio.undo_stack:
            return []
        entry = self.studio.undo_stack[-1]
        marked = self.studio.undo()
        # Compute all affected stages from the entry
        affected = set()
        for path, _old, _new in entry:
            owner = state.stage_of_path(path)
            if owner:
                affected.add(owner)
                affected.update(self.studio.downstream(owner))
        affected = [s for s in affected if s in self.studio.findings]
        now = time.monotonic()
        for s in affected:
            self._pending[s] = now
        return affected

    def redo(self):
        if not self.studio.redo_stack:
            return []
        entry = self.studio.redo_stack[-1]
        marked = self.studio.redo()
        affected = set()
        for path, _old, _new in entry:
            owner = state.stage_of_path(path)
            if owner:
                affected.add(owner)
                affected.update(self.studio.downstream(owner))
        affected = [s for s in affected if s in self.studio.findings]
        now = time.monotonic()
        for s in affected:
            self._pending[s] = now
        return affected

    # --- category/acknowledge --------------------------------------------------------------
    def change_category(self, category):
        marked = self.studio.change_category(category)
        now = time.monotonic()
        for s in marked:
            self._pending[s] = now
        return marked

    # The procedural move that stands in for each act a model has no clip for.
    STAND_IN_KIND = {"idle": "idle", "enter": "rise", "attack": "lunge", "hit": "recoil", "destroyed": "collapse", "win": "rise", "guard": "brace"}

    def use_stand_in(self, act):
        """Resolve S5.missing-act for `act` with a tool-made procedural clip: the source goes in the recipe (the converter's
        --procedural) and the choice in recipe["resolutions"] (the report lists it as a stand-in). Two undo entries."""
        kind = self.STAND_IN_KIND[act]
        finding = {"id": "S5.missing-act", "level": "fail" if act == "idle" else "warn", "value": None if act == "idle" else act}
        updated = resolutions.choose(self.studio.recipe, finding, "fallback", source={"procedural": kind}, act=act)
        self.studio.edit(f"acts.{act}.source", {"procedural": kind})
        self.studio.edit("resolutions", updated["resolutions"])

    def clip_names(self, library=None):
        """The clip names of this glb, or of a library glb (a path)."""
        model = audit.load_model(str(library)) if library else self._model
        return [an.get("name", "") for an in model.doc.get("animations", []) if an.get("name")]

    def check_library(self, library):
        """Findings of a library glb against this model's skeleton (bone names and rest pose); [] when they match."""
        return provide.check_provided(self.glb, library)

    def use_clip(self, act, clip):
        return resolve_actions.use_clip(self.studio, act, clip)

    def use_library(self, library, act, clip):
        return resolve_actions.use_library(self.studio, library, act, clip)

    def acknowledge(self, check_id, value):
        self.studio.acknowledge(check_id, value)
        # acknowledging marks recipe unsaved; stage stays same
        return self.studio.undo_stack[-1] if self.studio.undo_stack else []