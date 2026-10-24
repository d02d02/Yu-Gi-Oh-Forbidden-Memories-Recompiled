"""The Studio tab: S0-S3 of the Model Studio (notes/studio/): open a rigged glb, walk the stage rail, read the checks, set the
knobs. All logic is in tools/hd-models/studio (rail, knobs, checkrows, session); this file only draws it and calls it.
No engine viewport yet (SM4): the stages are judged from their checks."""
from __future__ import annotations

import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from . import file_dialogs
from .tabs import Tab
from .widgets import px, ui_font

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "hd-models"))
try:
    from studio import build, checkrows, knobs, preview, rail, runs, session as session_module
except ImportError:      # the tools are not next to the editor (a frozen build): the tab says so
    build = checkrows = knobs = preview = rail = runs = session_module = None

TICK_MS = 300
CHIP_COLOUR = {"fail": "#b00020", "warn": "#9a6700", "acked": "#555555", "info": "#555555", "pass": "#1a7f37"}


class StudioTab(Tab):
    def __init__(self, notebook, app):
        super().__init__(notebook, app, "Studio")
        self.session = None
        self.stage = "S0"
        self.widgets = {}
        bar = ttk.Frame(self)
        bar.pack(fill="x", pady=(0, 6))
        ttk.Button(bar, text="Open glb...", command=self.open_glb).pack(side="left")
        self.undo_button = ttk.Button(bar, text="Undo", command=lambda: self.history("undo"))
        self.undo_button.pack(side="left", padx=(8, 2))
        self.redo_button = ttk.Button(bar, text="Redo", command=lambda: self.history("redo"))
        self.redo_button.pack(side="left")
        self.saved = ttk.Label(bar, style="Note.TLabel")
        self.saved.pack(side="right")
        self.title = ttk.Label(bar, font=ui_font(11))
        self.title.pack(side="left", padx=12)

        body = ttk.PanedWindow(self, orient="horizontal")
        body.pack(fill="both", expand=True)
        left = ttk.Frame(body)
        self.tree = ttk.Treeview(left, show="tree", selectmode="browse", height=16)
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", lambda e: self.select())
        body.add(left, weight=1)
        self.right = ttk.Frame(body, padding=(10, 0, 0, 0))
        body.add(self.right, weight=4)

        self.heading = ttk.Label(self.right, font=ui_font(11))
        self.heading.pack(anchor="w")
        self.checks = ttk.Frame(self.right)
        self.checks.pack(fill="x", pady=(4, 8))
        self.form = ttk.Frame(self.right)
        self.form.pack(fill="x")
        foot = ttk.Frame(self.right)
        foot.pack(fill="x", side="bottom", pady=(8, 0))
        self.prev_button = ttk.Button(foot, text="Previous", command=lambda: self.go("previous"))
        self.prev_button.pack(side="left")
        self.next_button = ttk.Button(foot, command=lambda: self.go("next"))
        self.next_button.pack(side="right")
        self.reason = ttk.Label(foot, style="Note.TLabel")
        self.reason.pack(side="right", padx=8)
        if session_module is None:
            self.title.configure(text="The studio tools (tools/hd-models/studio) were not found next to the editor.")
        else:
            self.title.configure(text="Open a rigged glb to start.")
        self.after(TICK_MS, self.tick)

    # --- session -----------------------------------------------------------------------------
    def open_glb(self):
        if session_module is None:
            return
        path = file_dialogs.askopenfilename(title="Rigged model", filetypes=[("glTF binary", "*.glb"), ("glTF", "*.gltf")])
        if not path:
            return
        try:
            self.session = session_module.Session.open(path, Path(path).with_suffix(".recipe.json"))
            self.stage = "S0"
            self.session.run_stage("S0")
        except Exception as error:      # a note in the window, never a crash
            self.session = None
            messagebox.showerror("Studio", f"Could not open {Path(path).name}: {error}")
            return
        self.title.configure(text=Path(path).name)
        self.refresh()

    def stage_ids(self):
        return self.stage if isinstance(self.stage, tuple) else (self.stage,)

    def current(self):
        return self.stage_ids()[0]

    def select(self):
        picked = self.tree.selection()
        if not picked or self.session is None or not picked[0].startswith("stage:"):
            return
        ids = tuple(picked[0][6:].split(","))
        if ids != self.stage_ids():
            self.stage = ids if len(ids) > 1 else ids[0]
            self.session.open_stage(ids[0])
            self.draw_stage()

    def go(self, where):
        info = rail.footer(self.session.studio, self.current())
        if info.get(where):
            self.stage = info[where]
            self.session.open_stage(self.current())
            self.refresh()

    def history(self, which):
        if self.session:
            getattr(self.session, which)()
            self.refresh()

    # --- drawing -----------------------------------------------------------------------------
    def refresh(self):
        if self.session is None:
            return
        self.draw_rail()
        self.draw_stage()

    def draw_rail(self):
        keep = ",".join(self.stage_ids())
        self.tree.delete(*self.tree.get_children())
        for item in rail.rail(self.session.studio):
            if item["kind"] == "group":
                self.tree.insert("", "end", iid="group:" + item["label"], text=item["label"].upper(), open=True)
            else:
                iid = "stage:" + ",".join(item["ids"])
                self.tree.insert("", "end", iid=iid, text=f"  [{item['glyph']}] {item['name']}")
        if self.tree.exists("stage:" + keep):
            self.tree.selection_set("stage:" + keep)

    def draw_stage(self):
        studio = self.session.studio
        stage = self.current()
        self.heading.configure(text=f"{stage}  {studio.state(stage)}")
        for frame in (self.checks, self.form):
            for child in frame.winfo_children():
                child.destroy()
        report = checkrows.check_rows(studio, stage)
        for row in report["rows"]:
            line = ttk.Frame(self.checks)
            line.pack(fill="x", anchor="w")
            ttk.Label(line, text=row["chip"], width=9, foreground=CHIP_COLOUR.get(row["level"], "#555555")).pack(side="left")
            text = row["message"] + (f"  ({row['fix']})" if row["fix"] else "")
            ttk.Label(line, text=text, wraplength=px(self.right, 520), justify="left").pack(side="left", anchor="w")
            if row["level"] == "warn" and not row["acknowledged"]:
                ttk.Button(line, text="Accept", command=lambda r=row: self.accept(r)).pack(side="right")
        if stage == "S9":
            self.add_build_button()
        if stage == "S8":
            self.add_run_list()
        self.widgets = {}
        for k in knobs.knobs(stage):
            self.add_knob(k)
        info = rail.footer(studio, stage)
        self.prev_button.state(["!disabled"] if info["previous"] else ["disabled"])
        self.next_button.configure(text=info["next_label"])
        self.next_button.state(["!disabled"] if info["next_enabled"] else ["disabled"])
        self.reason.configure(text="" if info["next_enabled"] else info["next_reason"])
        self.undo_button.state(["!disabled"] if studio.undo_stack else ["disabled"])
        self.redo_button.state(["!disabled"] if getattr(studio, "redo_stack", None) else ["disabled"])
        self.saved.configure(text={"saved": "Saved", "unsaved": "Saving..."}.get(studio.save_state, studio.save_state))

    def add_build_button(self):
        """S9: build the mod twice (new_native_mod.py) in a thread; the findings and pkg.path land when it ends."""
        busy = getattr(self, "building", False)
        button = ttk.Button(self.form, text="Building..." if busy else "Build package", command=self.build_package)
        button.pack(anchor="w", pady=2)
        if busy:
            button.state(["disabled"])
        ttk.Button(self.form, text="Export report", command=self.export_report).pack(anchor="w", pady=2)
        path = knobs.value(self.session.studio.recipe, "pkg.path")
        if path:
            ttk.Label(self.form, text=f"Built: {path}", style="Note.TLabel").pack(anchor="w")

    def export_report(self):
        base = self.session.recipe_path.parent if self.session.recipe_path else self.session.glb.parent
        target = base / "report.md"
        self.session.export_report(target)
        self.heading.configure(text=f"Report saved: {target}")

    def build_package(self):
        base = self.session.recipe_path.parent if self.session.recipe_path else self.session.glb.parent
        self.building = True
        self.draw_stage()

        rec = self.session.studio.recipe
        glb, out = self.session.glb, base / "build"
        cards = [int(c) for c in rec.get("model", {}).get("cards") or []]
        self.build_out = out

        def work():
            try:
                self.build_result = build.run_build_s9(rec, glb, out, cards)
            except (ValueError, OSError) as e:
                self.build_result = {"error": str(e)}
        self.build_thread = threading.Thread(target=work, daemon=True)
        self.build_thread.start()

    def add_run_list(self):
        """S8: one row per scene or act with its status, a Run button (route A: the game is launched per run) and marks."""
        rec = self.session.studio.recipe
        package = knobs.value(rec, "pkg.path")
        cards = rec.get("model", {}).get("cards") or []
        disc = preview.disc_available()
        table = runs.status_table(rec.get("runs", []), self.session._sha256, disc)
        for row in runs.run_rows(disc):
            line = ttk.Frame(self.form)
            line.pack(fill="x", pady=1)
            ttk.Label(line, text=row["label"], width=24).pack(side="left")
            ttk.Label(line, text=table[row["id"]], width=10).pack(side="left")
            scene = row["id"] if row["id"] in preview.SCENES else ("arena" if row["id"].startswith("act:") else None)
            ready = scene and package and cards and (disc or not row["needs_disc"])
            run = ttk.Button(line, text="Run", command=lambda r=row, s=scene: self.run_scene(r, s))
            run.pack(side="left")
            if not ready:
                run.state(["disabled"])
            for text, result in (("Looks right", "seen"), ("Report a problem", "problem")):
                ttk.Button(line, text=text, command=lambda r=row, res=result: self.mark_row(r, res)).pack(side="left", padx=2)
        if not package:
            ttk.Label(self.form, text="Build the package (S9) to enable Run.", style="Note.TLabel").pack(anchor="w")
        elif not disc:
            ttk.Label(self.form, text="Library turntable only; set MEMORIES_DISC for field and arena.", style="Note.TLabel").pack(anchor="w")

    def run_scene(self, row, scene):
        rec = self.session.studio.recipe
        out = Path(self.session.recipe_path.parent if self.session.recipe_path else ".") / "runs" / row["id"].replace(":", "-")
        try:
            preview.install(knobs.value(rec, "pkg.path"), preview.game_mods())   # pkg.path is the built mod folder (S9)
            self.job = preview.start(scene, out, rec["model"]["cards"][0])
        except (RuntimeError, OSError) as e:
            self.heading.configure(text=str(e))

    def mark_row(self, row, result):
        problem = None
        if result == "problem":
            problem = self.ask_problem()
            if problem is None:
                return
        self.session.add_run_mark(row["id"], result, problem)
        self.draw_stage()

    def ask_problem(self):
        from tkinter import simpledialog
        choice = simpledialog.askstring("Report a problem", "One of: " + ", ".join(runs.PROBLEMS), parent=self.right)
        return choice if choice in runs.PROBLEMS else None

    def add_knob(self, k):
        recipe = self.session.studio.recipe
        row = ttk.Frame(self.form)
        row.pack(fill="x", pady=1)
        label = k["label"] + (f" ({k['unit']})" if k.get("unit") else "")
        ttk.Label(row, text=label, width=28).pack(side="left")
        current = knobs.value(recipe, k["path"])
        control = k["control"]
        if control == "toggle":
            var = tk.BooleanVar(value=bool(current) if current is not None else k["auto"] == "on")
            widget = ttk.Checkbutton(row, variable=var, command=lambda: self.set(k, var.get()))
        elif control == "select":
            var = tk.StringVar(value=str(current) if current is not None else str(k["auto"]))
            widget = ttk.Combobox(row, textvariable=var, values=k["choices"] or [], state="readonly", width=18)
            widget.bind("<<ComboboxSelected>>", lambda e: self.set(k, var.get()))
        elif control in ("number", "text", "list", "chips", "ints", "floats", "pairs", "json"):
            shown = knobs.show_text(control, current)
            var = tk.StringVar(value=shown)
            widget = ttk.Entry(row, textvariable=var, width=24)
            widget.bind("<Return>", lambda e: self.commit_knob(k, var.get()))
            widget.bind("<FocusOut>", lambda e: self.commit_knob(k, var.get()))
            if not shown:
                ttk.Label(row, text="auto: " + str(k["auto"]), style="Note.TLabel").pack(side="right")
        else:
            widget = ttk.Label(row, text="(edit in the recipe file)", style="Note.TLabel")
        widget.pack(side="left")
        if knobs.is_changed(recipe, k["path"]):
            ttk.Button(row, text="Back to auto", command=lambda: self.auto(k)).pack(side="left", padx=6)

    # --- actions -----------------------------------------------------------------------------
    def commit_knob(self, k, text):
        text = text.strip()
        if k["control"] == "number":
            try:
                value = float(text) if "." in text else int(text)
            except ValueError:
                return
        elif k["control"] in ("ints", "floats", "pairs", "json"):
            try:
                value = knobs.parse_text(k["control"], text)
            except ValueError:
                return
        elif k["control"] in ("ints", "floats", "pairs", "json"):
            try:
                value = knobs.parse_text(k["control"], text)
            except ValueError:
                return
        elif k["control"] in ("list", "chips"):
            value = [part.strip() for part in text.split(",") if part.strip()]
            if k["control"] == "chips":
                try:
                    value = [int(v) for v in value]
                except ValueError:
                    return
        else:
            value = text
        if text and value != knobs.value(self.session.studio.recipe, k["path"]):
            self.set(k, value)

    def set(self, k, value):
        self.session.edit(k["path"], value)
        self.app.changed() if hasattr(self.app, "changed") else None
        self.draw_stage()

    def auto(self, k):
        knobs.back_to_auto(self.session.studio, k["path"])
        self.draw_stage()

    def accept(self, row):
        self.session.acknowledge(row["id"], row["value"])
        self.draw_stage()

    def tick(self):
        """Every 300 ms: run the stages whose edits settled, autosave, redraw when something ran."""
        try:
            if self.session is not None:
                ran = self.session.run_due()
                self.session.autosave()
                if getattr(self, "building", False) and not self.build_thread.is_alive():
                    self.building = False
                    result = self.build_result
                    if "error" in result:
                        self.heading.configure(text=result["error"])
                    else:
                        self.session.apply_build(result, self.build_out)
                    ran = True
                if ran:
                    self.refresh()
        finally:
            self.after(TICK_MS, self.tick)
