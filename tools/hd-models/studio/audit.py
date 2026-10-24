"""The Model Studio's audit: stages S0-S3 as functions over a glTF (notes/studio/studio-view.md), no UI, no engine, no disc.

    model = load_model(path)                       # numpy arrays of the skin, the meshes, the materials
    audit_stage("S1", model, recipe, clips_from)   # -> {"findings": [...], "data": {...}}
    audit_all(path, recipe, clips_from)            # -> {"S0": ..., "S1": ..., "S2": ..., "S3": ...}

A finding is {"id", "level": info|warn|fail, "message", "fix", "value"}. `value` is the measured number the studio stores
with an acknowledgement. Thresholds are the ones written in studio-view.md; where the document names none (marked HEURISTIC)
the constant is here and says so. Reuses native_convert's glTF reading (accessor, Scene, Channel), so the audit sees the
file as the converter will.
"""
import math
import re
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "vendor"))
import gltf_to_hdm as base  # noqa: E402
import native_convert as nc  # noqa: E402
import native_spec as spec  # noqa: E402

DRIFT_WARN, DRIFT_FAIL = 4.0, 12.0          # S1.bind-vs-rest: percent of the model's height
WEIGHTS_FAIL_PCT = 1.0                       # S1.weights
FLIPPED_WARN_PCT = 1.0                       # S1.normals
MERGE_WEIGHT_PCT = 5.0                       # S1.merge (not measured here: the merge itself is not implemented)
ROOT_OFF_PCT = 15.0                          # S2.root-side
CONFIDENCE_WARN = 60                         # S0.category-confidence
UV_REPEATS = 4                               # S3.uv-repeat: the engine clamps beyond four repeats
TRIANGLES_WARN = 200_000                     # HEURISTIC, S1.size: the document names a budget without a number
TEXTURE_MB_WARN = spec.BUDGET_MB // 8        # HEURISTIC, S3.memory: one model's share of the game's native budget
REGIONS = ("head", "torso", "arm_l", "arm_r", "hands", "legs", "feet", "wings", "tail", "other")
HUMANOID_SLOTS = ("hips", "spine", "head", "arm_l", "arm_r", "hand_l", "hand_r", "leg_l", "leg_r", "foot_l", "foot_r")


class AuditError(Exception):
    pass


def finding(check, level, message, fix="", value=None, **extra):
    out = {"id": check, "level": level, "message": message, "fix": fix}
    if value is not None:
        out["value"] = value
    out.update(extra)
    return out


# --- loading ---------------------------------------------------------------------------------------------------------
class Model:
    """What the audit needs from a glTF, as numpy arrays. Skinned primitives are those of the main skin."""

    def __init__(self, path):
        self.path = Path(path)
        try:
            self.g = base.Gltf(self.path)
        except (OSError, ValueError, KeyError, struct_error()) as e:
            raise AuditError(f"cannot read {self.path.name}: {e}") from e
        self.doc = self.g.doc
        self.scene = nc.Scene(self.g)
        nodes = self.scene.nodes
        skins = self.doc.get("skins") or []
        self.skins = len(skins)
        self.skin_index = max(range(len(skins)), key=lambda i: len(skins[i]["joints"])) if skins else None
        self.joints = skins[self.skin_index]["joints"] if skins else []
        self.names = [nodes[n].get("name", f"bone{i}") for i, n in enumerate(self.joints)]
        jindex = {n: i for i, n in enumerate(self.joints)}
        self.parents = []
        for n in self.joints:
            p = next((x for x in self.scene.ancestors(n) if x in jindex), None)
            self.parents.append(jindex[p] if p is not None else -1)
        if skins and "inverseBindMatrices" in skins[self.skin_index]:
            self.ibm = nc.accessor(self.g, skins[self.skin_index]["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
        elif skins:
            w = self.scene.world(self.scene.rest)
            self.ibm = np.array([np.linalg.inv(w(n)) for n in self.joints])
        else:
            self.ibm = np.zeros((0, 4, 4))
        self.bind = np.array([np.linalg.inv(m) for m in self.ibm]) if len(self.ibm) else np.zeros((0, 4, 4))
        self.prims = []
        for ni, node in enumerate(nodes):
            if "mesh" not in node:
                continue
            for prim in self.doc["meshes"][node["mesh"]]["primitives"]:
                if prim.get("mode", 4) != 4 or "POSITION" not in prim["attributes"]:
                    continue
                at = prim["attributes"]
                pos = nc.accessor(self.g, at["POSITION"])
                idx = (nc.accessor(self.g, prim["indices"]).astype(np.int64).reshape(-1) if "indices" in prim
                       else np.arange(len(pos)))
                own = node.get("skin")
                skinned = own is not None and own == self.skin_index and "JOINTS_0" in at and "WEIGHTS_0" in at
                item = {"node": ni, "name": node.get("name", f"node{ni}"), "pos": pos, "idx": idx, "material": prim.get("material"),
                        "uv": nc.accessor(self.g, at["TEXCOORD_0"]) if "TEXCOORD_0" in at else None,
                        "normal": nc.accessor(self.g, at["NORMAL"]) if "NORMAL" in at else None,
                        "color": "COLOR_0" in at, "skinned": skinned, "joints": None, "weights": None,
                        "extra_weights": "WEIGHTS_1" in at}
                if skinned:
                    item["joints"] = nc.accessor(self.g, at["JOINTS_0"]).astype(int)
                    item["weights"] = nc.accessor(self.g, at["WEIGHTS_0"])
                    if item["extra_weights"]:
                        item["weights1"] = nc.accessor(self.g, at["WEIGHTS_1"])
                elif own is None:
                    world = self.scene.world(self.scene.rest)(ni)
                    item["pos"] = pos @ world[:3, :3].T + world[:3, 3]
                self.prims.append(item)
        if not self.prims:
            raise AuditError("no triangles in the file")
        allpos = np.vstack([p["pos"] for p in self.prims])
        self.lo, self.hi = allpos.min(0), allpos.max(0)
        self.height = float(self.hi[1] - self.lo[1])
        self.triangles = sum(len(p["idx"]) // 3 for p in self.prims)

    @property
    def skinned_prims(self):
        return [p for p in self.prims if p["skinned"]]


def struct_error():
    import struct
    return struct.error


def load_model(path):
    return Model(path)


def read_asset_meta(model):
    """author / license / url from the glb's asset.extras when present (what S0 fills in on intake)."""
    extras = model.doc.get("asset", {}).get("extras", {}) or {}
    out = {}
    for key, name in (("author", "author"), ("license", "license"), ("source", "url")):
        if extras.get(key):
            out[name] = str(extras[key])
    return out


# --- bones -----------------------------------------------------------------------------------------------------------
def classify_bone(name, x=0.0, cx=0.0):
    """(region, slot) of a bone by its name, or ("other", None). Side from the name, else from the bone's x against the centre
    (glTF characters face +z, so their left is +x). slot is a humanoid slot name or None."""
    n = nc.bare(name)
    n = re.sub(r"^(def|mch|org|ctrl)[-_]", "", n)
    side = ("l" if re.search(r"(^|[._\-\s])l($|[._\-\s\d])|left", n) else "r" if re.search(r"(^|[._\-\s])r($|[._\-\s\d])|right", n)
            else ("l" if x > cx else "r"))
    if "wing" in n:
        return "wings", None
    if "tail" in n:
        return "tail", None
    if any(k in n for k in ("finger", "thumb", "index", "middle", "pinky", "ring", "f_")) and "hand" not in n:
        return "hands", None
    if "hand" in n or "palm" in n:
        return "hands", f"hand_{side}"
    if any(k in n for k in ("foot", "toe", "ankle", "ball")):
        return "feet", f"foot_{side}"
    if any(k in n for k in ("thigh", "calf", "shin", "knee", "upleg", "oberschenkel", "lowerleg", "leg")):
        return "legs", f"leg_{side}"
    if any(k in n for k in ("clavicle", "shoulder", "upperarm", "upper_arm", "lowerarm", "forearm", "arm")):
        return "arm_" + side, f"arm_{side}"
    if any(k in n for k in ("head", "neck", "jaw", "eye", "skull", "face")):
        return "head", "head" if "head" in n else None
    if "hip" in n or "pelvis" in n:
        return "torso", "hips"
    if any(k in n for k in ("spine", "chest", "breast", "paunch", "belly", "torso")):
        return "torso", "spine"
    return "other", None


def bone_classes(model):
    cx = float((model.lo[0] + model.hi[0]) / 2)
    return [classify_bone(n, float(model.bind[k][0, 3]), cx) for k, n in enumerate(model.names)]


def detect_root(model, rig="auto", name=None):
    """The body root bone index, as native_convert picks it (a named --root, the profile's names, hip/pelvis, else the bone
    with the most bones under it)."""
    lowered = [nc.bare(n) for n in model.names]
    if name:
        if name not in model.names:
            raise AuditError(f"rig.root {name!r} is not a bone of the model")
        return model.names.index(name)
    if rig == "auto":
        rig = "ue" if "pelvis" in lowered else "mixamo" if any(n.lower().startswith("mixamorig") for n in model.names) else "generic"
    root = next((lowered.index(r) for r in nc.PROFILES[rig]["root"] if r in lowered), None)
    if root is None:
        root = next((k for k, n in enumerate(lowered) if "hip" in n or "pelvis" in n), None)
    if root is None:
        under = [0] * len(model.names)
        for k in range(len(model.names)):
            p = model.parents[k]
            while p >= 0:
                under[p] += 1
                p = model.parents[p]
        root = max(range(len(model.names)), key=lambda k: under[k])
    return root


# --- category --------------------------------------------------------------------------------------------------------
def detect_category(model):
    """HEURISTIC v1: {"category", "confidence" 0-100, "evidence": [...]} from the skeleton's names and shape. Never decisive:
    S0.category-confidence asks the person to choose below 60."""
    ev = []
    dims = model.hi - model.lo
    if not model.joints:
        pieces = len({p["node"] for p in model.prims})
        ev.append(f"not skinned: {pieces} mesh node(s), {model.triangles:,} triangles")
        tall = dims[1] >= 1.2 * max(dims[0], dims[2])
        ev.append(f"bounding box {dims[0]:.2f} x {dims[1]:.2f} x {dims[2]:.2f}: {'upright' if tall else 'not upright'}")
        return {"category": "C3" if tall else "C8", "confidence": 45 if tall else 55,
                "evidence": ev + ["a statue-like shape could be a humanoid to rig (C3), several rigid parts (C7) or a static mesh (C8)"]}
    classes = bone_classes(model)
    slots = {s for _, s in classes if s}
    match = len([s for s in HUMANOID_SLOTS if s in slots]) / len(HUMANOID_SLOTS)
    counts = {r: sum(1 for c, _ in classes if c == r) for r in REGIONS}
    wings, tails, legs = counts["wings"], counts["tail"], counts["legs"] + counts["feet"]
    lowered = [nc.bare(n) for n in model.names]
    lowered = [re.sub(r"^def[-_]", "", n) for n in lowered]   # Rigify's deform bones: DEF-hips
    standard = "pelvis" in lowered or "hips" in lowered or any(n.startswith("mixamorig") for n in model.names)
    ev += [f"{len(model.joints)} bones, {len(model.doc.get('animations', []))} clip(s) in the file",
           f"humanoid slots filled: {match:.0%} ({len([s for s in HUMANOID_SLOTS if s in slots])}/{len(HUMANOID_SLOTS)})",
           f"wing bones {wings}, tail bones {tails}, leg/foot bones {legs}",
           "standard humanoid bone names" if standard else "custom bone names"]
    leg_sides = {s for _, s in classes if s and s.startswith("leg_")}
    if wings >= 2 and match < 0.8:
        return {"category": "C5", "confidence": 85 if tails or not match else 70, "evidence": ev}
    if wings >= 2:
        return {"category": "C2", "confidence": 65, "evidence": ev + ["humanoid with wings: wings need the follow rules (S2)"]}
    if match >= 0.9 and standard:
        return {"category": "C1", "confidence": 92, "evidence": ev}
    if match >= 0.8:
        return {"category": "C2", "confidence": 72, "evidence": ev}
    if legs == 0:
        return {"category": "C6", "confidence": 70, "evidence": ev + ["no leg bones"]}
    if len(leg_sides) <= 2 and legs >= 4 and match < 0.5:
        return {"category": "C4", "confidence": 60, "evidence": ev + ["four-limbed, not humanoid"]}
    return {"category": "C2", "confidence": 40, "evidence": ev + ["no clear match; check the skeleton"]}


# --- S0 --------------------------------------------------------------------------------------------------------------
def s0(model, recipe):
    out = []
    meta = recipe.get("meta") or {}
    fill = read_asset_meta(model)
    license_text = (meta.get("license") or "").strip()
    if not license_text:
        suggestion = f" The file says: {fill['license']}" if fill.get("license") else ""
        out.append(finding("S0.licence", "info", "The licence is empty.",
                           "Optional: add the licence so it is stored in the package and shown in the Library." + suggestion))
    elif re.search(r"\bby\b", license_text, re.I) and not (meta.get("author") or "").strip():
        out.append(finding("S0.attribution", "warn", "The licence requires attribution but the author is empty.", "Add the author name.", value=license_text))
    cat = detect_category(model)
    chosen = (recipe.get("model") or {}).get("category")
    if not chosen:
        out.append(finding("S0.category", "fail", "No category is chosen.",
                           f"Choose a category; the detection suggests {cat['category']}.", suggested=cat["category"]))
    if cat["confidence"] < CONFIDENCE_WARN and not chosen:
        out.append(finding("S0.category-confidence", "warn", f"The detected category {cat['category']} has {cat['confidence']}% confidence.",
                           "Check the evidence panel and choose the category.", value=cat["confidence"]))
    if model.skins > 1 and ((recipe.get("source") or {}).get("skin") is None):
        out.append(finding("S0.skins", "warn", f"{model.skins} skins and none chosen.", "Choose the skin to use.", value=model.skins))
    if not out:
        out.append(finding("S0.ok", "info", "The file opened and the intake is complete.", ""))
    return {"findings": out, "data": {"category": cat, "meta_from_file": fill, "skins": model.skins, "joints": len(model.joints),
                                      "meshes": len({p["node"] for p in model.prims}), "triangles": model.triangles,
                                      "clips": [a.get("name", "") for a in model.doc.get("animations", [])]}}


# --- S1 --------------------------------------------------------------------------------------------------------------
def skin_positions(model, world_of_joint):
    """The skinned vertices of every skinned primitive for a pose: world_of_joint(k) is joint k's world matrix."""
    sm = np.array([world_of_joint(k) @ model.ibm[k] for k in range(len(model.joints))])
    out = []
    for p in model.skinned_prims:
        h = np.hstack([p["pos"], np.ones((len(p["pos"]), 1))])
        res = np.zeros_like(p["pos"])
        for c in range(4):
            res += p["weights"][:, c, None] * np.einsum("nij,nj->ni", sm[p["joints"][:, c]], h)[:, :3]
        out.append(res)
    return out


def pose_function(model, clips_doc, clip_name, t):
    """World matrices of the model's joints in the pose of one clip at time t (a clip of another file is matched by node name)."""
    gc, cscene = clips_doc
    nodes = model.scene.nodes
    by_name = {nd.get("name", ""): i for i, nd in enumerate(nodes)}
    same = gc is model.g
    target = {i: i for i in range(len(nodes))} if same else {i: by_name.get(nd.get("name", "")) for i, nd in enumerate(cscene.nodes)}
    anims = {an.get("name", f"clip{i}"): an for i, an in enumerate(gc.doc.get("animations", []))}
    an = anims[clip_name]
    chans = {}
    for ch in an["channels"]:
        tgt, smp = ch["target"], an["samplers"][ch["sampler"]]
        mine = target.get(tgt.get("node"))
        if mine is None or tgt["path"] not in ("translation", "rotation", "scale"):
            continue
        times = nc.accessor(gc, smp["input"]).reshape(-1)
        chans[(mine, tgt["path"])] = nc.Channel(times, nc.accessor(gc, smp["output"]), tgt["path"], smp.get("interpolation", "LINEAR"))
    trs = {}
    for i in range(len(nodes)):
        tt, qq, ss = model.scene.rest[i]
        c = chans.get((i, "translation"))
        tt = c.at(t) if c else tt
        c = chans.get((i, "rotation"))
        qq = c.at(t) if c else qq
        c = chans.get((i, "scale"))
        ss = c.at(t) if c else ss
        trs[i] = (tt, qq, ss)
    wf = model.scene.world(trs)
    return lambda k: wf(model.joints[k])


def vertex_regions(model):
    """Region name per vertex of each skinned primitive: the region of the vertex's strongest joint."""
    classes = bone_classes(model)
    names = np.array([c for c, _ in classes])
    return [names[p["joints"][np.arange(len(p["joints"])), np.argmax(p["weights"], axis=1)]] for p in model.skinned_prims]


def s1(model, recipe, clips_from=None):
    out, data = [], {}
    nb = len(model.joints)
    if not model.joints:
        return {"findings": [finding("S1.skin", "fail", "The model has no skin (no armature).", "Rig it in Blender, or choose a static category.")],
                "data": {}}
    if nb > spec.MAX_BONES:
        out.append(finding("S1.bones", "fail", f"{nb} bones; the game takes at most {spec.MAX_BONES}.",
                           "Too many bones. Allow more merging, or drop the tail/hair chain.", value=nb))
    # weights
    total = sum(len(p["weights"]) for p in model.skinned_prims)
    bare_weights = sum(int((p["weights"].sum(1) < 0.01).sum()) for p in model.skinned_prims)
    pct = 100.0 * bare_weights / max(total, 1)
    if bare_weights:
        out.append(finding("S1.weights", "fail" if pct > WEIGHTS_FAIL_PCT else "warn",
                           f"{bare_weights} of {total} vertices have no weight ({pct:.2f}%).",
                           "Fix weights in Blender (button), or let auto-smooth fill them.", value=bare_weights))
    cut = sum(int(((p["weights"] > 0).sum(1) + ((p.get("weights1", np.zeros((len(p["weights"]), 4))) > 0).sum(1))).__gt__(4).sum())
              for p in model.skinned_prims)
    if cut:
        out.append(finding("S1.influences", "info", f"{cut} vertices have more than 4 influences; the 4 strongest are kept.", "", value=cut))
    # scale
    odd = []
    for n in {p["node"] for p in model.prims} | set(model.joints):
        for i in (n, *model.scene.ancestors(n)):
            s = np.abs(model.scene.rest[i][2])
            if np.allclose(s, s[0], rtol=1e-3) is False or (not np.allclose(s, 1.0, atol=1e-3) and
                                                           (abs(s[0] - 0.01) < 1e-3 or abs(s[0] - 100) < 1e-1 or not np.allclose(s, s[0], rtol=1e-3))):
                odd.append(model.scene.nodes[i].get("name", str(i)))
    if odd:
        out.append(finding("S1.scale", "warn", f"Node scale of 0.01, 100 or non-uniform on: {', '.join(sorted(set(odd))[:4])}.",
                           "Apply scale on export, or accept the auto fix.", value=len(set(odd))))
    # normals
    flipped = faces = 0
    for p in model.skinned_prims:
        if p["normal"] is None:
            continue
        tri = p["idx"].reshape(-1, 3)
        fn = np.cross(p["pos"][tri[:, 1]] - p["pos"][tri[:, 0]], p["pos"][tri[:, 2]] - p["pos"][tri[:, 0]])
        vn = p["normal"][tri].sum(1)
        flipped += int(((fn * vn).sum(1) < 0).sum())
        faces += len(tri)
    if faces and 100.0 * flipped / faces > FLIPPED_WARN_PCT:
        out.append(finding("S1.normals", "warn", f"{flipped} of {faces} faces point against their normals ({100.0 * flipped / faces:.1f}%).",
                           "Fix in Blender or turn on auto-flip.", value=round(100.0 * flipped / faces, 1)))
    if model.triangles > TRIANGLES_WARN:
        out.append(finding("S1.size", "warn", f"{model.triangles:,} triangles (over {TRIANGLES_WARN:,}).", "Reduce in Blender (decimate).",
                           value=model.triangles))
    # bind vs rest
    table, drift = bind_vs_rest(model, clips_from)
    data["regions"] = table
    data["best_pose"] = drift["pose"]
    worst = max(table, key=lambda r: r["drift_pct"]) if table else None
    if worst and worst["drift_pct"] > DRIFT_WARN:
        level = "fail" if worst["drift_pct"] > DRIFT_FAIL else "warn"
        out.append(finding("S1.bind-vs-rest", level,
                           f"The mesh and the rig rest in different poses: {worst['region']} moves {worst['drift_pct']}% of the height "
                           f"even in the closest pose ({drift['pose']}).",
                           f"Re-pose {worst['region']} in Blender, or choose another rig.", value=worst["drift_pct"],
                           region=worst["region"]))
    out.append(finding("S1.merge", "info", "Bone merging is not measured in this version (the merge itself runs in Blender).", ""))
    if not [f for f in out if f["level"] != "info"]:
        out.insert(0, finding("S1.ok", "info", "The mesh and skin are sound.", ""))
    data["bones"] = nb
    return {"findings": out, "data": data}


def bind_vs_rest(model, clips_from=None):
    """Per region, the largest vertex drift (percent of height) between the mesh as stored and the same mesh posed, taken in
    the CLOSEST available pose: the node rest pose, or frame 0 of any clip (of this file, or of clips_from matched by node
    name). A rig whose best pose still moves a region more than 4% rests in another pose than its mesh."""
    regions = vertex_regions(model)
    rest_world = model.scene.world(model.scene.rest)
    candidates = [("rest pose", lambda k: rest_world(model.joints[k]))]
    sources = [(model.g, model.scene)]
    if clips_from:
        sources = [(base.Gltf(Path(clips_from)), None)]
        sources[0] = (sources[0][0], nc.Scene(sources[0][0]))
    for gc, cscene in sources:
        for i, an in enumerate(gc.doc.get("animations", [])):
            name = an.get("name", f"clip{i}")
            candidates.append((name, ("clip", (gc, cscene), name)))
    best = None
    for label, pose in candidates:
        if isinstance(pose, tuple):
            first = None
            _, doc, name = pose
            an = [a for j, a in enumerate(doc[0].doc.get("animations", [])) if a.get("name", f"clip{j}") == name][0]
            t0 = min((float(nc.accessor(doc[0], s["input"]).min()) for s in an["samplers"]), default=0.0)
            try:
                fn = pose_function(model, doc, name, t0)
            except (KeyError, IndexError, ValueError):
                continue
        else:
            fn = pose
        moved = skin_positions(model, fn)
        per = {}
        for p, new, reg in zip(model.skinned_prims, moved, regions):
            d = np.linalg.norm(new - p["pos"], axis=1)
            for r in np.unique(reg):
                sel = reg == r
                e = per.setdefault(str(r), {"vertices": 0, "worst": 0.0})
                e["vertices"] += int(sel.sum())
                e["worst"] = max(e["worst"], float(d[sel].max()))
        score = max(e["worst"] for e in per.values())
        if best is None or score < best[0]:
            best = (score, label, per)
    _, label, per = best
    weights = weight_issues(model, regions)
    table = [{"region": r, "vertices": per[r]["vertices"], "drift_pct": round(100.0 * per[r]["worst"] / max(model.height, 1e-9), 1),
              "weight_issues": weights.get(r, 0)} for r in REGIONS if r in per]
    return table, {"pose": label}


def weight_issues(model, regions):
    out = {}
    for p, reg in zip(model.skinned_prims, regions):
        bad = p["weights"].sum(1) < 0.01
        for r in np.unique(reg[bad]):
            out[str(r)] = out.get(str(r), 0) + int((bad & (reg == r)).sum())
    return out


# --- S2 --------------------------------------------------------------------------------------------------------------
def s2(model, recipe):
    out = []
    rig = recipe.get("rig") or {}
    if not model.joints:
        return {"findings": [finding("S2.skin", "fail", "The model has no skeleton.", "Rig it, or choose a static category.")], "data": {}}
    root = detect_root(model, rig.get("profile", "auto"), rig.get("root"))
    nb = len(model.joints)
    roots = [k for k in range(nb) if model.parents[k] < 0]

    def top(k):
        while model.parents[k] >= 0:
            k = model.parents[k]
        return k
    apart = [k for k in range(nb) if top(k) != top(root)]
    if apart:  # the game accepts several parentless bones (native_format.c): they are fine, but they do not follow the root
        names = [model.names[k] for k in apart][:4]
        out.append(finding("S2.chains", "warn", f"{len(apart)} bone(s) are in {len(roots) - 1} separate tree(s) from the root "
                           f"{model.names[root]} and will not follow it: {', '.join(names)}.",
                           "Parent them under the body in Blender if they should move with it, or accept.", value=len(apart)))
    classes = bone_classes(model)
    filled = {}
    for k, (_, slot) in enumerate(classes):
        if slot and slot not in filled:
            filled[slot] = model.names[k]
    for slot, bone in (rig.get("humanoid") or {}).items():
        if bone in model.names:
            filled[slot] = bone
    category = (recipe.get("model") or {}).get("category")
    missing = [s for s in HUMANOID_SLOTS if s not in filled]
    if category in ("C1", "C2", "C3") and missing:
        out.append(finding("S2.map", "fail", f"Humanoid slots empty: {', '.join(missing)}.",
                           f"Pick a bone for {missing[0]}, or switch to non-humanoid.", value=len(missing)))
    centre = (model.lo + model.hi) / 2
    off = float(np.linalg.norm((model.bind[root][:3, 3] - centre)[[0, 2]])) / max(model.height, 1e-9) * 100.0
    if off > ROOT_OFF_PCT:
        out.append(finding("S2.root-side", "warn", f"The root {model.names[root]} is {off:.0f}% of the height off the body's centre.",
                           "Choose a bone closer to the pelvis.", value=round(off)))
    neg = [model.names[k] for k, n in enumerate(model.joints) if (model.scene.rest[n][2] < 0).any() or np.linalg.det(model.ibm[k][:3, :3]) < 0]
    if neg:
        out.append(finding("S2.reversed-scale", "fail", f"Negative scale on: {', '.join(neg[:4])}.", "Fix in Blender (apply scale).", value=len(neg)))
    used = np.zeros(nb, bool)
    for p in model.skinned_prims:
        for c in range(4):
            used[np.unique(p["joints"][p["weights"][:, c] > 0, c])] = True
    for bone in (e if isinstance(e, str) else e.get("bone") for e in (rig.get("extras") or [])):
        if bone in model.names and not used[model.names.index(bone)]:
            out.append(finding("S2.extras-weights", "warn", f"The extra bone {bone} carries no weights.",
                               "Nothing will move; cut it or paint weights.", value=bone))
    if not out:
        out.append(finding("S2.ok", "info", "The skeleton is connected and mapped.", ""))
    return {"findings": out, "data": {"root": model.names[root], "roots": [model.names[k] for k in roots], "slots": filled,
                                      "missing": missing}}


# --- S3 --------------------------------------------------------------------------------------------------------------
def s3(model, recipe):
    out = []
    doc = model.doc
    mats = doc.get("materials", [])
    lost = []
    for i, m in enumerate(mats):
        ext = set(m.get("extensions", {})) - {"KHR_materials_emissive_strength"}
        pbr = m.get("pbrMetallicRoughness", {})
        infos = [pbr.get("baseColorTexture"), pbr.get("metallicRoughnessTexture"), m.get("normalTexture")]
        why = []
        if ext:
            why.append("extension " + ", ".join(sorted(ext)))
        if any(x and x.get("texCoord", 0) != 0 for x in infos):
            why.append("UV set other than 0")
        if any(x and "KHR_texture_transform" in x.get("extensions", {}) for x in infos):
            why.append("texture transform")
        if why:
            lost.append((m.get("name", f"material {i}"), "; ".join(why)))
    for name, why in lost:
        out.append(finding("S3.dropped", "warn", f"Material {name} uses {why}; it is not applied.",
                           "Bake to a texture in Blender, or give it a replacement file.", value=name))
    colours = sum(1 for p in model.prims if p["color"])
    if colours:
        out.append(finding("S3.vertex-colour", "warn", f"{colours} primitive(s) carry vertex colours; they are not drawn.",
                           "Bake them into the texture.", value=colours))
    glow = [m.get("name", str(i)) for i, m in enumerate(mats) if m.get("emissiveTexture") or any(m.get("emissiveFactor", [0, 0, 0]))]
    if glow:
        out.append(finding("S3.emissive", "warn", f"Emissive on {', '.join(glow[:3])}; the engine may not draw it (unconfirmed).",
                           "Bake glow into the base colour.", value=len(glow)))
    span = 0
    for p in model.prims:
        if p["uv"] is not None and len(p["uv"]):
            lo, hi = np.floor(p["uv"].min(0) + 1e-4), np.ceil(p["uv"].max(0) - 1e-4)
            if ((hi - lo) > UV_REPEATS).any():
                span += 1
    if span:
        out.append(finding("S3.uv-repeat", "warn", f"{span} primitive(s) have UVs beyond {UV_REPEATS} repeats; the engine clamps them.",
                           "Bake the tiling into the texture.", value=span))
    cap = int((recipe.get("mat") or {}).get("atlas") or spec.TEXTURE_MAX)
    no_pbr = bool((recipe.get("mat") or {}).get("no_pbr"))
    uv = np.vstack([p["uv"] if p["uv"] is not None else np.zeros((len(p["pos"]), 2)) for p in model.prims])
    mat = np.concatenate([np.full(len(p["pos"]), -1 if p["material"] is None else p["material"]) for p in model.prims])
    groups = {None if m < 0 else int(m): np.nonzero(mat == m)[0] for m in np.unique(mat)}
    notes = []
    size = None
    try:
        b, n, m = nc.build_textures(model.g, groups, uv.copy(), cap, no_pbr, notes)
        size = list(b.size)
        mb = sum(img.size[0] * img.size[1] * 4 for img in (b, n, m) if img is not None) * 1.34 / 1048576
        if mb > TEXTURE_MB_WARN:
            out.append(finding("S3.memory", "warn", f"Textures take about {mb:.0f} MB (over {TEXTURE_MB_WARN} MB).", "Lower the atlas size.", value=round(mb)))
    except Exception as e:  # noqa: BLE001 - the converter's own refusal text is the message
        out.append(finding("S3.atlas", "fail", f"The textures cannot be built at {cap}: {e}", "Raise the atlas size or lower texture sizes."))
    if not out:
        out.append(finding("S3.ok", "info", "Materials and textures are fine.", ""))
    return {"findings": out, "data": {"atlas": size, "materials": len(mats), "notes": notes}}


# --- runner ----------------------------------------------------------------------------------------------------------
def audit_stage(stage, model, recipe=None, clips_from=None):
    recipe = recipe or {}
    if stage == "S0":
        return s0(model, recipe)
    if stage == "S1":
        return s1(model, recipe, clips_from)
    if stage == "S2":
        return s2(model, recipe)
    if stage == "S3":
        return s3(model, recipe)
    raise ValueError(f"the audit covers S0-S3, not {stage}")


def audit_all(path, recipe=None, clips_from=None):
    """S0-S3 for one file. A file that does not open gives S0.load as the only finding."""
    try:
        model = load_model(path)
    except AuditError as e:
        return {"S0": {"findings": [finding("S0.load", "fail", f"This file did not open: {e}",
                                            "Re-export as glb 2.0, or convert .blend/.fbx through Blender.")], "data": {}}}
    return {s: audit_stage(s, model, recipe, clips_from) for s in ("S0", "S1", "S2", "S3")}


def apply_to_studio(studio, results, inputs=None):
    """Store an audit_all() result in a state.Studio."""
    for stage, res in results.items():
        studio.set_findings(stage, res["findings"], (inputs or {}).get(stage))
