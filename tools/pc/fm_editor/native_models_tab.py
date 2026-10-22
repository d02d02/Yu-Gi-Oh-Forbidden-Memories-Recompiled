"""The Native models tab: a mod's "native_models" (native_models.py, notes/native-models.md): which cards play a
rigged 3D model of the mod's instead of the disc's in the battle. A package (the model.json a converter made, with its
model and PNGs) is copied into the mod under models/<name>/ and named in an entry with the cards it stands for."""
from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from . import file_dialogs, native_models
from .tabs import Tab
from .widgets import px, scrolled_tree, ui_font


class NativeModelsTab(Tab):
    def __init__(self, notebook, app):
        super().__init__(notebook, app, "Native models")
        left = ttk.Frame(self)
        left.pack(side="left", fill="y")
        frame, self.tree = scrolled_tree(left, [("n", "#"), ("package", "Package"), ("cards", "Cards")], [34, 220, 160], 18,
                                         sort_numeric=("n",))
        frame.pack(fill="both", expand=True, pady=(0, 4))
        self.tree.bind("<<TreeviewSelect>>", lambda e: self.select())
        buttons = ttk.Frame(left)
        buttons.pack(fill="x")
        ttk.Button(buttons, text="Add package...", command=self.add).pack(side="left")
        self.remove_button = ttk.Button(buttons, text="Remove", command=self.remove)
        self.remove_button.pack(side="left", padx=4)

        right = self.right = ttk.Frame(self, padding=(10, 0, 0, 0))
        right.pack(side="left", fill="both", expand=True)
        self.heading = ttk.Label(right, font=ui_font(11))
        self.heading.pack(anchor="w")
        self.how = ttk.Label(right, style="Note.TLabel", wraplength=px(right, 480), justify="left", text=(
            "A package is the folder a converter makes (tools/hd-models/new_native_mod.py): model.json, its model "
            "and PNG textures. Add package copies it into the mod and gives it the cards it plays for, where the "
            "battle draws it instead of the disc's model. Needs Internal 2x or more. Restart the game after a change."))
        self.how.pack(anchor="w", pady=(0, 8))
        row = ttk.Frame(right)
        row.pack(anchor="w", fill="x")
        ttk.Label(row, text="Cards").pack(side="left")
        self.cards = tk.StringVar()
        self.cards_entry = ttk.Entry(row, textvariable=self.cards, width=36)
        self.cards_entry.pack(side="left", padx=4)
        self.apply_button = ttk.Button(row, text="Apply", command=self.apply)
        self.apply_button.pack(side="left")
        self.cards_entry.bind("<Return>", lambda e: self.apply())
        ttk.Label(right, style="Hint.TLabel", text="Card ids, separated by commas or spaces (Black Luster Soldier is 364).").pack(
            anchor="w", pady=(2, 8))
        self.about = ttk.Label(right, justify="left", wraplength=px(right, 480))
        self.about.pack(anchor="w")
        self.status = ttk.Label(right, style="Warning.TLabel", wraplength=px(right, 480), justify="left")
        self.status.pack(anchor="w", pady=6)
        self.refresh()

    @property
    def index(self):
        selection = self.tree.selection()
        return int(selection[0]) if selection else None

    def refresh(self):
        if not hasattr(self, "tree"):
            return
        self.fill(self.index)

    def fill(self, keep=None):
        self.tree.delete(*self.tree.get_children())
        items = native_models.entries(self.project) if self.project is not None and "native_models" in self.project.other \
            else []
        for i, entry in enumerate(items):
            package = entry.get("package") or entry.get("file") if isinstance(entry, dict) else None
            cards = ", ".join(str(c) for c in native_models.entry_cards(entry))
            self.tree.insert("", "end", iid=str(i), values=(i, package if isinstance(package, str) else "(not valid)", cards))
        if keep is not None and self.tree.exists(str(keep)):
            self.tree.selection_set(str(keep))
        elif items:
            self.tree.selection_set("0")
        self.select()

    def select(self):
        i, project = self.index, self.project
        items = project.other.get("native_models") if project is not None else None
        entry = items[i] if i is not None and isinstance(items, list) and i < len(items) else None
        self.status.configure(text="")
        for widget in (self.cards_entry, self.apply_button, self.remove_button):
            widget.state(["!disabled"] if entry is not None else ["disabled"])
        if entry is None:
            self.heading.configure(text="No native models" if project is not None else "")
            self.cards.set("")
            self.about.configure(text="")
            return
        info = native_models.about(project, entry)
        self.heading.configure(text=info["name"] or str(entry.get("package") or entry.get("file") or "A model"))
        self.cards.set(", ".join(str(c) for c in native_models.entry_cards(entry)))
        lines = [f"{label}: {info[key]}" for key, label in (("author", "Author"), ("license", "Licence"), ("source", "Source"))
                 if info[key]]
        self.about.configure(text="\n".join(lines))

    # actions
    def add(self):
        path = file_dialogs.askopenfilename(parent=self, title="A package's model.json",
                                            filetypes=[("model.json", "model.json"), ("All files", "*.*")])
        if path:
            self.use_package(path)

    def use_package(self, path, cards=()) -> bool:
        """Add the package at `path` (the Add button, and tests)."""
        try:
            i = native_models.add_package(self.project, path, cards)
        except (OSError, ValueError) as problem:
            messagebox.showerror("FM Editor", f"Could not add {path}: {problem}", parent=self)
            return False
        self.app.changed()
        self.fill(i)
        self.status.configure(text=f"{Path(path).parent.name} is in the mod. Give it the cards it plays for.")
        self.app.say("Native model added. Save to write it.")
        return True

    def apply(self):
        i = self.index
        if i is None:
            return
        try:
            cards = native_models.parse_cards(self.cards.get())
        except ValueError as problem:
            self.status.configure(text=str(problem))
            return
        native_models.set_cards(self.project, i, cards)
        self.app.changed()
        self.fill(i)

    def remove(self):
        i = self.index
        if i is None:
            return
        native_models.remove_entry(self.project, i)
        self.app.changed()
        self.fill(min(i, len(self.project.other.get("native_models", [])) - 1))
