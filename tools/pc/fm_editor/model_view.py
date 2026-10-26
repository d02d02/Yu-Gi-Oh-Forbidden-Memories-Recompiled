"""Studio model preview: the glb's mesh, skeleton and per-bone weights on a canvas, orbit with the mouse. No game needed."""
import math
import tkinter as tk
from tkinter import ttk

import numpy as np

W, H = 520, 320
MAX_LINES = 3500        # wire edges drawn (a stride over all edges); the mesh shape stays readable
MAX_DOTS = 5000


class ModelView(ttk.Frame):
    def __init__(self, parent, view3d):
        super().__init__(parent)
        self.v = view3d
        self.data = None
        self.yaw, self.pitch, self.zoom = 0.4, 0.2, 1.0
        self.canvas = tk.Canvas(self, width=W, height=H, bg="#1e1e22", highlightthickness=0)
        self.canvas.pack(fill="x")
        row = ttk.Frame(self)
        row.pack(fill="x", pady=(4, 0))
        self.show = {k: tk.BooleanVar(value=v) for k, v in (("mesh", True), ("bones", True), ("box", False))}
        for key, label in (("mesh", "Mesh"), ("bones", "Bones"), ("box", "Box")):
            ttk.Checkbutton(row, text=label, variable=self.show[key], command=self.draw).pack(side="left", padx=(0, 6))
        ttk.Label(row, text="Weights of").pack(side="left", padx=(8, 4))
        self.bone = ttk.Combobox(row, state="readonly", width=24, values=["(none)"])
        self.bone.current(0)
        self.bone.pack(side="left")
        self.bone.bind("<<ComboboxSelected>>", lambda e: self.draw())
        for name, v in (("Front", (0, 0.1)), ("Side", (math.pi / 2, 0.1)), ("Back", (math.pi, 0.1)), ("Top", (0, 1.4))):
            ttk.Button(row, text=name, width=6, command=lambda v=v: self.view(*v)).pack(side="left", padx=1)
        clip = ttk.Frame(self)
        clip.pack(fill="x", pady=(4, 0))
        ttk.Label(clip, text="Clip").pack(side="left", padx=(0, 4))
        self.clip = ttk.Combobox(clip, state="readonly", width=28, values=["(bind pose)"])
        self.clip.current(0)
        self.clip.pack(side="left")
        self.clip.bind("<<ComboboxSelected>>", lambda e: self.pick_clip())
        self.play_button = ttk.Button(clip, text="Play", width=6, command=self.toggle_play)
        self.play_button.pack(side="left", padx=4)
        self.t = tk.DoubleVar(value=0.0)
        self.scale = ttk.Scale(clip, from_=0.0, to=1.0, variable=self.t, command=lambda v: self.pose())
        self.scale.pack(side="left", fill="x", expand=True)
        self.sources, self.model, self.length, self.playing = {}, None, 0.0, False
        self.note = ttk.Label(self, wraplength=W)
        self.note.pack(anchor="w")
        self.canvas.bind("<B1-Motion>", self.drag)
        self.canvas.bind("<Button-1>", lambda e: setattr(self, "last", (e.x, e.y)))
        self.canvas.bind("<MouseWheel>", lambda e: self.wheel(1.1 if e.delta < 0 else 1 / 1.1))

    def load(self, model, library=None):
        """Show `model` (an audit.Model), or clear the view when it is None. Its own clips and the library's can be played."""
        self.playing = False
        self.play_button.configure(text="Play")
        self.model = model
        self.data = None if model is None else self.v.model_arrays(model)
        d = self.data
        self.sources = {}
        for src, tag in ((model, ""), (library, "lib: ")):
            for i, an in enumerate(src.doc.get("animations", []) if src is not None else []):
                self.sources[tag + an.get("name", f"clip{i}")] = (src, an.get("name", f"clip{i}"))
        self.clip.configure(values=["(bind pose)"] + sorted(self.sources))
        self.clip.current(0)
        if d is not None:
            self.cur_pos, self.cur_bones = d["pos"], d["bones"]
            self.target, self.dist = self.v.fit_camera(d["lo"], d["hi"])
            self.edges = self.v.wire_edges(d["idx"])
            step = max(1, len(self.edges) // MAX_LINES)
            self.edges = self.edges[::step]
            self.dead = self.v.unweighted_bones(d["joints"], d["weights"], len(d["bones"]))
            self.bone.configure(values=["(none)"] + d["names"])
            self.bone.current(0)
        self.draw()

    def view(self, yaw, pitch):
        self.yaw, self.pitch = yaw, pitch
        self.draw()

    def drag(self, e):
        x0, y0 = self.last
        self.last = (e.x, e.y)
        self.yaw -= (e.x - x0) * 0.01
        self.pitch = max(-1.5, min(1.5, self.pitch + (e.y - y0) * 0.01))
        self.draw()

    def wheel(self, factor):
        self.zoom = max(0.2, min(5.0, self.zoom * factor))
        self.draw()

    def project(self, pts):
        view = self.v.orbit_view(self.yaw, self.pitch, self.dist * self.zoom, self.target)
        return self.v.project(pts, view, 40.0, W, H)

    def draw(self):
        c = self.canvas
        c.delete("all")
        d = self.data
        if d is None:
            c.create_text(W // 2, H // 2, text="Open a glb to see it here", fill="#888888")
            self.note.configure(text="")
            return
        p = self.project(self.cur_pos)
        front = p[:, 2] > 0
        pick = self.bone.current() - 1
        if self.show["mesh"].get():
            if pick >= 0:
                self.dots(p, front, self.v.vertex_weight(d["joints"], d["weights"], pick))
            for a, b in self.edges:
                if front[a] and front[b]:
                    c.create_line(p[a, 0], p[a, 1], p[b, 0], p[b, 1], fill="#4a4f5a" if pick < 0 else "#2c2f36")
        if self.show["box"].get():
            self.box()
        if self.show["bones"].get() and len(d["bones"]):
            self.bones(pick)
        self.caption(pick)

    def dots(self, p, front, w):
        step = max(1, len(p) // MAX_DOTS)
        rgb = self.v.heat_color(w)
        for i in range(0, len(p), step):
            if front[i]:
                r, g, b = rgb[i]
                c = f"#{r:02x}{g:02x}{b:02x}"
                self.canvas.create_rectangle(p[i, 0] - 1.5, p[i, 1] - 1.5, p[i, 0] + 1.5, p[i, 1] + 1.5, fill=c, outline="")

    def box(self):
        lo, hi = self.data["lo"], self.data["hi"]
        pts = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
        q = self.project(pts)
        for a in range(8):
            for b in range(a + 1, 8):
                if bin(a ^ b).count("1") == 1 and q[a, 2] > 0 and q[b, 2] > 0:
                    self.canvas.create_line(q[a, 0], q[a, 1], q[b, 0], q[b, 1], fill="#8a8a30", dash=(3, 3))

    def bones(self, pick):
        d = self.data
        q = self.project(self.cur_bones)
        for par, ch in self.v.bone_segments(d["bones"], d["parents"]):
            if q[par, 2] > 0 and q[ch, 2] > 0:
                self.canvas.create_line(q[par, 0], q[par, 1], q[ch, 0], q[ch, 1], fill="#e6e6e6", width=2)
        for i, (x, y, z) in enumerate(q):
            if z > 0:
                dead, sel = i in self.dead, i == pick
                col = "#ff3b30" if dead else "#ffd60a" if sel else "#e6e6e6"
                r = 5 if (dead or sel) else 3
                self.canvas.create_oval(x - r, y - r, x + r, y + r, fill=col, outline="")
        if pick >= 0 and q[pick, 2] > 0:
            self.canvas.create_text(q[pick, 0] + 8, q[pick, 1] - 8, text=d["names"][pick], fill="#ffd60a", anchor="w")

    def caption(self, pick):
        d = self.data
        n = len(d["bones"])
        text = f"{len(d['pos'])} vertices, {len(d['idx']) // 3} triangles, {n} bones."
        if n == 0:
            text += " No skeleton found: nothing can animate."
        elif self.dead:
            text += f" Red bones carry no weight ({len(self.dead)}): they move nothing."
        if pick >= 0:
            text += " Blue = no weight, green = half, red = full for the chosen bone."
        self.note.configure(text=text)

    # --- clips ---------------------------------------------------------------------------------
    def pick_clip(self):
        name = self.clip.get()
        self.playing = False
        self.play_button.configure(text="Play")
        if name not in self.sources:
            self.cur_pos, self.cur_bones = self.data["pos"], self.data["bones"]
            self.draw()
            return
        from studio import clipdata
        src, clip = self.sources[name]
        self.length = max(clipdata.clip_length(src, clip), 1e-3)
        self.scale.configure(to=self.length)
        self.t.set(0.0)
        self.pose()

    def pose(self):
        name = self.clip.get()
        if self.data is None or name not in self.sources:
            return
        src, clip = self.sources[name]
        d = self.data
        mats, self.cur_bones = self.v.pose_data(self.model, src, clip, float(self.t.get()))
        self.cur_pos = self.v.skin_points(d["pos"], d["joints"], d["weights"], mats)
        self.draw()

    def toggle_play(self):
        if self.clip.get() not in self.sources:
            return
        self.playing = not self.playing
        self.play_button.configure(text="Pause" if self.playing else "Play")
        if self.playing:
            self.step()

    def step(self):
        if not self.playing:
            return
        t = self.t.get() + 0.06
        self.t.set(t if t < self.length else 0.0)
        self.pose()
        self.after(60, self.step)
