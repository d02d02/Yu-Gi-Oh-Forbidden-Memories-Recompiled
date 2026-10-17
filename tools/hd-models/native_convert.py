#!/usr/bin/env python3
"""A rigged glTF / glb -> a native model package the game draws in place of a monster (no disc needed).

    native_convert.py MODEL.glb OUT_DIR [--clips all|A,B,...] [--clips-from LIBRARY.glb] [--rig auto|ue|mixamo|generic]
                      [--root BONE] [--root-height 300 | --height 560 | --scale S] [--texture-max 2048]
                      [--follow BONE=SOURCE[@FRACTION]] [--keep-root-motion] [--no-pbr] [--name N --author A --license L]

OUT_DIR gets model.hdm (the mesh, skeleton and clips), base.png (+ normal.png, metal_roughness.png when the model has
those maps) and model.json (src/pc/render/native_registry.h): which clip each act plays, where the attack's blows land,
the textures. Edit model.json or swap a PNG without converting again. new_native_mod.py makes the whole mod around it.

What is read:
  * the skin with the most joints (at most 128), every primitive skinned to it (4 influences per vertex), and meshes
    that are not skinned (a sword under the hand bone): they follow the bone above them, else the root;
  * every material: base colour texture x factor, the normal and metal/roughness maps; several materials are packed
    into one texture (an atlas, at most --texture-max a side), UVs past 0..1 tiled into it; MASK alpha is cut;
  * the clips (linear, step and cubic spline keys), baked at 30 fps, in place: the root's horizontal travel is taken
    out (the game moves the monster) unless --keep-root-motion.

The rig: the root bone (the hips) goes to the origin, the game's body root; glTF's y up becomes the game's y down.
Its size: by default the root stands --root-height 300 game units above the soles (Black Luster Soldier's hips);
--height sizes the whole model instead, --scale sets game units per glTF unit. model.json "scale" adjusts it later.
Profiles name the hips and hands: ue (Unreal / Quaternius: pelvis, hand_r), mixamo (Hips, RightHand), generic (--root).

Clips are matched to acts by name (Sword_Attack, Attack, Slash -> attack; Hit, Damage -> hit; Death, Die -> destroyed;
Victory, Win -> win; Block, Guard -> guard; Intro, Spawn -> enter; Idle -> idle); an act without one plays the idle.
The attack's blows are put where the hand (or weapon) moves fastest. Both are in model.json: check them."""
import argparse
import json
import math
import re
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "vendor"))
import gltf_to_hdm as base  # noqa: E402  (its glTF container reader)
import native_spec as spec  # noqa: E402

FLIP = np.diag([1.0, -1.0, -1.0])  # glTF (y up, facing +z) -> the game's model space (y down)
ROOT_HEIGHT = 300.0                # Black Luster Soldier's hips above the arena floor, game units
COMPONENT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NORMALIZED = {5120: 127.0, 5121: 255.0, 5122: 32767.0, 5123: 65535.0}
TYPE_SIZE = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT2": 4, "MAT3": 9, "MAT4": 16}

PROFILES = {
    "ue": {"root": ["pelvis"], "hands": ["hand_r", "hand_l"]},
    "mixamo": {"root": ["hips"], "hands": ["righthand", "lefthand"]},
    "generic": {"root": ["hips", "pelvis", "hip"], "hands": []},
}
# Act -> name fragments, best first (lower case). Idle_Loop is where the angel's enter row has always gone.
ACT_WORDS = {
    "idle": ["sword_idle", "idle", "stand", "breath", "wait"],
    "enter": ["intro", "enter", "spawn", "summon", "appear", "idle_loop"],
    "attack": ["sword_attack", "attack", "slash", "strike", "swing", "punch", "kick", "bite", "cast"],
    "hit": ["hit_chest", "hit", "damage", "hurt", "impact", "flinch"],
    "destroyed": ["death", "die", "dying", "defeat", "dead"],
    "win": ["victory", "win", "cheer", "celebrat", "taunt"],
    "guard": ["block", "guard", "defend", "shield", "parry"],
}
WEAPON_WORDS = ("weapon", "sword", "blade", "axe", "spear", "staff", "wand")


class Problem(Exception):
    pass


def bare(name):
    """A bone name as profiles match it: lower case, without Mixamo's prefix (mixamorig:, mixamorig1_ ...)."""
    return re.sub(r"^mixamorig\d*[:_]", "", name.lower())


# --- glTF reading ---------------------------------------------------------------------------------------------------
def accessor(g, index):
    a = g.doc["accessors"][index]
    kind = np.dtype(COMPONENT[a["componentType"]]).newbyteorder("<")
    n, count = TYPE_SIZE[a["type"]], a["count"]
    out = np.zeros((count, n), np.float64)
    if "bufferView" in a:
        view = g.doc["bufferViews"][a["bufferView"]]
        raw = g.view(a["bufferView"]) + bytes(256)  # the last element needs no stride padding
        offset = a.get("byteOffset", 0)
        stride = view.get("byteStride") or n * kind.itemsize
        layout = np.dtype({"names": ["v"], "formats": [(kind, (n,))], "offsets": [0], "itemsize": stride})
        out[:] = np.frombuffer(raw, layout, count, offset)["v"].reshape(count, n)
    sparse = a.get("sparse")
    if sparse:
        ia, va = sparse["indices"], sparse["values"]
        ik = np.dtype(COMPONENT[ia["componentType"]]).newbyteorder("<")
        where = np.frombuffer(g.view(ia["bufferView"]), ik, sparse["count"], ia.get("byteOffset", 0)).astype(np.int64)
        values = np.frombuffer(g.view(va["bufferView"]), kind, sparse["count"] * n, va.get("byteOffset", 0))
        out[where] = values.reshape(-1, n)
    if a.get("normalized") and a["componentType"] in NORMALIZED:
        out /= NORMALIZED[a["componentType"]]
    return out


def quat_to_mat(q):
    x, y, z, w = q / np.linalg.norm(q)
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def mat_to_quat(m):
    t = np.trace(m)
    if t > 0:
        s = math.sqrt(t + 1.0) * 2
        q = [(m[2, 1] - m[1, 2]) / s, (m[0, 2] - m[2, 0]) / s, (m[1, 0] - m[0, 1]) / s, 0.25 * s]
    elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        s = math.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2
        q = [0.25 * s, (m[0, 1] + m[1, 0]) / s, (m[0, 2] + m[2, 0]) / s, (m[2, 1] - m[1, 2]) / s]
    elif m[1, 1] > m[2, 2]:
        s = math.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2
        q = [(m[0, 1] + m[1, 0]) / s, 0.25 * s, (m[1, 2] + m[2, 1]) / s, (m[0, 2] - m[2, 0]) / s]
    else:
        s = math.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2
        q = [(m[0, 2] + m[2, 0]) / s, (m[1, 2] + m[2, 1]) / s, 0.25 * s, (m[1, 0] - m[0, 1]) / s]
    q = np.array(q)
    return q / np.linalg.norm(q)


def slerp(a, b, t):
    d = float(a @ b)
    if d < 0:
        b, d = -b, -d
    if d > 0.9995:
        r = a + (b - a) * t
        return r / np.linalg.norm(r)
    th = math.acos(min(d, 1.0))
    return (math.sin((1 - t) * th) * a + math.sin(t * th) * b) / math.sin(th)


class Channel:
    def __init__(self, times, values, path, interpolation):
        self.times, self.path, self.interpolation = times, path, interpolation
        if interpolation == "CUBICSPLINE":  # per key: in-tangent, value, out-tangent
            self.values, self.into, self.out = values[1::3], values[0::3], values[2::3]
        else:
            self.values = values

    def at(self, t):
        times, values = self.times, self.values
        i = int(np.searchsorted(times, t, side="right") - 1)
        if i < 0:
            return values[0]
        if i >= len(times) - 1:
            return values[-1]
        span = max(float(times[i + 1] - times[i]), 1e-9)
        f = (t - times[i]) / span
        if self.interpolation == "STEP":
            return values[i]
        if self.interpolation == "CUBICSPLINE":
            f2, f3 = f * f, f * f * f
            v = ((2 * f3 - 3 * f2 + 1) * values[i] + (f3 - 2 * f2 + f) * span * self.out[i] + (-2 * f3 + 3 * f2) * values[i + 1]
                 + (f3 - f2) * span * self.into[i + 1])
            return v / np.linalg.norm(v) if self.path == "rotation" else v
        if self.path == "rotation":
            return slerp(values[i], values[i + 1], f)
        return values[i] * (1 - f) + values[i + 1] * f


class Scene:
    """The node tree of a glTF: rest pose, parents, world matrices of any pose."""

    def __init__(self, g):
        self.g, self.nodes = g, g.doc.get("nodes", [])
        self.parent = {}
        for i, n in enumerate(self.nodes):
            for c in n.get("children", []):
                self.parent[c] = i
        self.rest = {i: self.rest_trs(i) for i in range(len(self.nodes))}

    def rest_trs(self, i):
        nd = self.nodes[i]
        if "matrix" in nd:
            m = np.array(nd["matrix"], float).reshape(4, 4).T
            s = np.linalg.norm(m[:3, :3], axis=0)
            return m[:3, 3].copy(), mat_to_quat(m[:3, :3] / s), s
        return (np.array(nd.get("translation", [0, 0, 0]), float), np.array(nd.get("rotation", [0, 0, 0, 1]), float),
                np.array(nd.get("scale", [1, 1, 1]), float))

    def world(self, trs):
        cache = {}

        def w(i):
            if i not in cache:
                t, q, s = trs[i]
                m = np.eye(4)
                m[:3, :3] = quat_to_mat(q) * s
                m[:3, 3] = t
                cache[i] = w(self.parent[i]) @ m if i in self.parent else m
            return cache[i]
        return w

    def ancestors(self, i):
        while i in self.parent:
            i = self.parent[i]
            yield i


# --- textures -------------------------------------------------------------------------------------------------------
def material_images(g, material, no_pbr, notes):
    """(base RGBA image with its factor and alpha mode applied, normal map or None, metal/roughness or None)."""
    doc = g.doc
    if material is None:
        return Image.new("RGBA", (8, 8), (230, 230, 230, 255)), None, (0.0, 1.0)
    m = doc["materials"][material]
    pbr = m.get("pbrMetallicRoughness", {})
    factor = np.array(pbr.get("baseColorFactor", [1, 1, 1, 1]), float)

    def image(info, what):
        if not info:
            return None
        if info.get("texCoord", 0) != 0:
            notes.append(f"material {m.get('name', material)}: its {what} uses UV set {info['texCoord']}; set 0 is used")
        if "extensions" in info and "KHR_texture_transform" in info["extensions"]:
            notes.append(f"material {m.get('name', material)}: KHR_texture_transform on its {what} is not applied")
        return g.image(info["index"]).convert("RGBA")

    tex = image(pbr.get("baseColorTexture"), "base colour")
    if tex is None:
        c = tuple(int(round(min(max(v, 0.0), 1.0) * 255)) for v in factor)
        tex = Image.new("RGBA", (8, 8), c)
    elif not np.allclose(factor, 1.0):
        a = np.asarray(tex, np.float64) * factor
        tex = Image.fromarray(np.clip(a + 0.5, 0, 255).astype(np.uint8), "RGBA")
    mode = m.get("alphaMode", "OPAQUE")
    a = np.array(tex)
    if mode == "OPAQUE":
        a[:, :, 3] = 255
    elif mode == "MASK":
        a[:, :, 3] = np.where(a[:, :, 3] >= m.get("alphaCutoff", 0.5) * 255, 255, 0)
    tex = Image.fromarray(a, "RGBA")
    if no_pbr:
        return tex, None, None
    normal = image(m.get("normalTexture"), "normal map")
    mr = image(pbr.get("metallicRoughnessTexture"), "metal/roughness map")
    metal, rough = float(pbr.get("metallicFactor", 1.0)), float(pbr.get("roughnessFactor", 1.0))
    if mr is not None and (metal != 1.0 or rough != 1.0):
        a = np.asarray(mr, np.float64).copy()
        a[:, :, 1] *= rough
        a[:, :, 2] *= metal
        mr = Image.fromarray(np.clip(a + 0.5, 0, 255).astype(np.uint8), "RGBA")
    return tex, normal, mr if mr is not None else (metal, rough)


def tiled(img, nx, ny):
    if nx == 1 and ny == 1:
        return img
    out = Image.new(img.mode, (img.width * nx, img.height * ny))
    for y in range(ny):
        for x in range(nx):
            out.paste(img, (x * img.width, y * img.height))
    return out


def padded(img, pad):
    """The image with `pad` texels of its own edges round it (so the atlas' mip levels do not bleed tiles together)."""
    a = np.array(img)
    return Image.fromarray(np.pad(a, ((pad, pad), (pad, pad), (0, 0)), mode="edge"), img.mode)


def pack(sizes, pad):
    """Shelf packing: per tile (x, y) of its padded rectangle, and the atlas' (width, height)."""
    order = sorted(range(len(sizes)), key=lambda i: -sizes[i][1])
    area = sum((w + 2 * pad) * (h + 2 * pad) for w, h in sizes)
    width = max(max(w + 2 * pad for w, _ in sizes), int(math.ceil(math.sqrt(area * 1.15))))
    width = (width + 3) // 4 * 4
    at, x, y, shelf = [None] * len(sizes), 0, 0, 0
    for i in order:
        w, h = sizes[i][0] + 2 * pad, sizes[i][1] + 2 * pad
        if x + w > width:
            x, y, shelf = 0, y + shelf, 0
        at[i] = (x, y)
        x += w
        shelf = max(shelf, h)
    return at, (width, y + shelf)


def fit_side(img, cap):
    if max(img.size) <= cap:
        return img
    f = cap / max(img.size)
    return img.resize((max(1, int(img.width * f)), max(1, int(img.height * f))), Image.LANCZOS)


def build_textures(g, groups, uvs, cap, no_pbr, notes):
    """One texture for the model: the single material's own, or an atlas of all of them; the UVs moved into it.
    groups: material -> vertex index array. Returns (base, normal or None, metal/roughness or None)."""
    tiles = []
    for material, verts in groups.items():
        base_img, normal, mr = material_images(g, material, no_pbr, notes)
        uv = uvs[verts]
        lo, hi = np.floor(uv.min(0) + 1e-4), np.ceil(uv.max(0) - 1e-4)
        n = np.maximum(hi - lo, 1).astype(int)
        if (n > 4).any():
            notes.append(f"material {material}: UVs span {n[0]}x{n[1]} repeats; clamped to one")
            uvs[verts] = np.clip(uv, 0.0, 1.0)
            lo, n = np.zeros(2), np.ones(2, int)
        else:
            uvs[verts] = (uv - lo) / n
        tiles.append({"verts": verts, "n": n, "base": base_img, "normal": normal, "mr": mr})
    has_pbr = any(t["normal"] is not None or isinstance(t["mr"], Image.Image) for t in tiles)
    if len(tiles) == 1 and (tiles[0]["n"] == 1).all():
        t = tiles[0]
        base_img = fit_side(t["base"], cap)
        if not has_pbr:
            return base_img, None, None
        size = base_img.size
        normal = t["normal"].resize(size, Image.BILINEAR) if t["normal"] else Image.new("RGBA", size, (128, 128, 255, 255))
        mr = t["mr"].resize(size, Image.BILINEAR) if isinstance(t["mr"], Image.Image) else mr_fill(size, t["mr"])
        return base_img, normal, mr
    pad = 4
    for t in tiles:
        t["base"] = tiled(t["base"], *t["n"])
    sizes = [t["base"].size for t in tiles]
    at, (width, height) = pack(sizes, pad)
    atlas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    natlas = Image.new("RGBA", (width, height), (128, 128, 255, 255)) if has_pbr else None
    matlas = Image.new("RGBA", (width, height), (0, 160, 0, 255)) if has_pbr else None
    for t, (x, y), (w, h) in zip(tiles, at, sizes):
        atlas.paste(padded(t["base"].resize((w, h), Image.LANCZOS), pad), (x, y))
        if has_pbr:
            normal = tiled(t["normal"], *t["n"]).resize((w, h), Image.BILINEAR) if t["normal"] else Image.new("RGBA", (w, h), (128, 128, 255, 255))
            mr = tiled(t["mr"], *t["n"]).resize((w, h), Image.BILINEAR) if isinstance(t["mr"], Image.Image) else mr_fill((w, h), t["mr"])
            natlas.paste(padded(normal, pad), (x, y))
            matlas.paste(padded(mr, pad), (x, y))
        uv = uvs[t["verts"]]
        uvs[t["verts"]] = np.stack([(x + pad + uv[:, 0] * w) / width, (y + pad + uv[:, 1] * h) / height], 1)
    if max(width, height) > cap:  # the UVs are fractions of the atlas: it can be made smaller whole
        f = cap / max(width, height)
        size = (max(1, int(width * f)), max(1, int(height * f)))
        atlas, natlas, matlas = (img.resize(size, Image.LANCZOS) if img else None for img in (atlas, natlas, matlas))
        width, height = size
    notes.append(f"{len(tiles)} materials packed into one {width}x{height} texture")
    return atlas, natlas, matlas


def mr_fill(size, factors):
    metal, rough = factors if factors else (0.0, 1.0)
    return Image.new("RGBA", size, (0, int(round(rough * 255)), int(round(metal * 255)), 255))


# --- clips ----------------------------------------------------------------------------------------------------------
def guess_acts(names):
    acts = {}
    lower = [n.lower() for n in names]
    for act, words in ACT_WORDS.items():
        for word in words:
            hit = next((names[i] for i, n in enumerate(lower) if word in n), None)
            if hit:
                acts[act] = hit
                break
    if "idle" not in acts and names:
        acts["idle"] = names[0]
    for act in ACT_WORDS:
        acts.setdefault(act, acts.get("idle"))
    return acts


def strike_frames(speed, most=spec.MAX_STRIKES):
    """Frames where the blows land: the speed's peaks over 60% of its largest, at least 6 frames apart."""
    if len(speed) < 3 or speed.max() <= 0:
        return []
    floor = 0.6 * speed.max()
    peaks = [f for f in range(1, len(speed) - 1) if speed[f] >= floor and speed[f] >= speed[f - 1] and speed[f] >= speed[f + 1]]
    chosen = []
    for f in sorted(peaks, key=lambda f: -speed[f]):
        if all(abs(f - c) >= 6 for c in chosen):
            chosen.append(f)
    return sorted(chosen[:most])


# --- the conversion -------------------------------------------------------------------------------------------------
def convert(a):
    notes = []
    g = base.Gltf(a.gltf)
    doc = g.doc
    scene = Scene(g)
    nodes = scene.nodes
    skins = doc.get("skins") or []
    if not skins:
        raise Problem("the model has no skin (no armature): rig it, or export it with its armature")
    skin_index = max(range(len(skins)), key=lambda i: len(skins[i]["joints"]))
    skin = skins[skin_index]
    joints = skin["joints"]
    nb = len(joints)
    if nb > spec.MAX_BONES:
        raise Problem(f"{nb} bones: the game takes at most {spec.MAX_BONES} (remove twist / helper bones)")
    jindex = {n: i for i, n in enumerate(joints)}
    if "inverseBindMatrices" in skin:
        ibm = accessor(g, skin["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
    else:
        w = scene.world(scene.rest)
        ibm = np.array([np.linalg.inv(w(n)) for n in joints])
    parents = []
    for n in joints:
        p = next((x for x in scene.ancestors(n) if x in jindex), None)
        parents.append(jindex[p] if p is not None else -1)
    names = [nodes[n].get("name", f"bone{i}") for i, n in enumerate(joints)]
    wrest = scene.world(scene.rest)
    bind = np.array([np.linalg.inv(ibm[k]) for k in range(nb)])

    # the mesh: skinned primitives, and unskinned ones riding the joint above them (else the root)
    P, N, U, J, W, I, M = [], [], [], [], [], [], []
    count = 0
    dropped_weight = 0.0
    for ni, node in enumerate(nodes):
        if "mesh" not in node:
            continue
        own = node.get("skin")
        rigid = None
        if own is None or own != skin_index:
            if own is not None and not set(skins[own]["joints"]) <= set(joints):
                notes.append(f"mesh {node.get('name', ni)}: skinned to another skeleton; left out")
                continue
            if own is None:
                rigid = next((jindex[x] for x in [ni, *scene.ancestors(ni)] if x in jindex), None)
        remap = None if own is None or own == skin_index else np.array([jindex[j] for j in skins[own]["joints"]])
        for prim in doc["meshes"][node["mesh"]]["primitives"]:
            if prim.get("mode", 4) != 4:
                notes.append(f"mesh {node.get('name', ni)}: a primitive of lines or points left out")
                continue
            at = prim["attributes"]
            p = accessor(g, at["POSITION"])
            n = accessor(g, at["NORMAL"]) if "NORMAL" in at else None
            uv = accessor(g, at["TEXCOORD_0"]) if "TEXCOORD_0" in at else np.zeros((len(p), 2))
            if "COLOR_0" in at:
                notes.append(f"mesh {node.get('name', ni)}: vertex colours are not drawn (bake them into the texture)")
            if own is None:
                world = wrest(ni)
                p = p @ world[:3, :3].T + world[:3, 3]
                if n is not None:
                    n = n @ np.linalg.inv(world[:3, :3])
                j = np.zeros((len(p), 4), int)
                j[:, 0] = rigid if rigid is not None else next((k for k in range(nb) if parents[k] < 0), 0)
                wt = np.zeros((len(p), 4))
                wt[:, 0] = 1.0
            else:
                j = accessor(g, at["JOINTS_0"]).astype(int)
                wt = accessor(g, at["WEIGHTS_0"])
                if remap is not None:
                    j = remap[j]
                if "WEIGHTS_1" in at:
                    dropped_weight = max(dropped_weight, float(accessor(g, at["WEIGHTS_1"]).sum(1).max()))
            idx = accessor(g, prim["indices"]).astype(np.int64).reshape(-1) if "indices" in prim else np.arange(len(p))
            if n is None:  # flat normals from the faces
                n = np.zeros_like(p)
                tri = idx.reshape(-1, 3)
                fn = np.cross(p[tri[:, 1]] - p[tri[:, 0]], p[tri[:, 2]] - p[tri[:, 0]])
                for c in range(3):
                    np.add.at(n, tri[:, c], fn)
            P.append(p); N.append(n); U.append(uv); J.append(j); W.append(wt); I.append(idx + count)
            M.append(np.full(len(p), prim.get("material", -1)))
            count += len(p)
    if not P:
        raise Problem("no triangles in the model")
    pos, nrm, uvs, jj, ww, idx, mat = (np.vstack(P), np.vstack(N), np.vstack(U), np.vstack(J), np.vstack(W),
                                       np.concatenate(I), np.concatenate(M))
    if dropped_weight > 0.05:
        notes.append(f"vertices with more than 4 bones: up to {dropped_weight:.0%} of a vertex's weight dropped (4 strongest kept)")
    ww = ww / np.maximum(ww.sum(1, keepdims=True), 1e-9)
    nrm = nrm / np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-9)

    # the rig: root to the origin, glTF y up -> the game's y down, sized
    rig = a.rig
    lowered = [bare(n) for n in names]
    if rig == "auto":
        rig = "ue" if "pelvis" in lowered else "mixamo" if any(n.lower().startswith("mixamorig") for n in names) else "generic"
    profile = PROFILES[rig]
    if a.root:
        if a.root not in names:
            raise Problem(f"--root {a.root}: no such bone (it has: {', '.join(names[:12])}...)")
        root = names.index(a.root)
    else:
        root = next((lowered.index(r) for r in profile["root"] if r in lowered), None)
        if root is None:
            root = next((k for k, n in enumerate(lowered) if "hip" in n or "pelvis" in n), None)
        if root is None:  # the joint with the most joints under it
            under = [0] * nb
            for k in range(nb):
                p = parents[k]
                while p >= 0:
                    under[p] += 1
                    p = parents[p]
            root = max(range(nb), key=lambda k: under[k])
    origin = bind[root][:3, 3]
    low, high = float(pos[:, 1].min()), float(pos[:, 1].max())
    stature = high - low
    root_height = float(origin[1]) - low
    if a.scale:
        s = a.scale
    elif a.height or root_height < 0.1 * stature:
        if not a.height:
            notes.append(f"the root bone {names[root]} is at the soles: sized by height instead (--height, default 560)")
        s = (a.height or 560.0) / max(stature, 1e-9)
    else:
        s = a.root_height / root_height
    A = FLIP * s
    b = -(FLIP @ origin) * s
    T = np.eye(4)
    T[:3, :3] = A
    T[:3, 3] = b
    Ti = np.linalg.inv(T)
    ibm_d = np.array([T @ ibm[k] @ Ti for k in range(nb)])
    pos_d = pos @ A.T + b
    nrm_d = nrm @ FLIP.T

    # textures
    groups = {}
    for m in np.unique(mat):
        groups[None if m < 0 else int(m)] = np.nonzero(mat == m)[0]
    uvs = uvs.copy()
    base_img, normal_img, mr_img = build_textures(g, groups, uvs, a.texture_max, a.no_pbr, notes)

    # clips
    gc = base.Gltf(a.clips_from) if a.clips_from else g
    cscene = Scene(gc) if a.clips_from else scene
    by_name = {nd.get("name", ""): i for i, nd in enumerate(nodes)}
    target = {i: by_name.get(nd.get("name", "")) for i, nd in enumerate(cscene.nodes)} if a.clips_from else {i: i for i in range(len(nodes))}
    anims = {an.get("name", f"clip{i}"): an for i, an in enumerate(gc.doc.get("animations", []))}
    available = list(anims)
    acts = guess_acts(available)
    if a.clips == "all":
        want = list(dict.fromkeys([c for c in acts.values() if c] + available))
        if len(want) > spec.MAX_CLIPS:
            notes.append(f"{len(want)} clips: the {spec.MAX_CLIPS} kept are the acts' and the first others "
                         f"(left out: {', '.join(want[spec.MAX_CLIPS:])})")
            want = want[:spec.MAX_CLIPS]
    else:
        want = [c for c in a.clips.split(",") if c]
        missing = [c for c in want if c not in anims]
        if missing:
            raise Problem(f"no clip {', '.join(missing)}; the model has: {', '.join(available) or 'none'}")
        if len(want) > spec.MAX_CLIPS:
            raise Problem(f"{len(want)} clips: the game takes at most {spec.MAX_CLIPS}")
    acts = guess_acts(want)
    follow = []
    for rule in a.follow or []:
        m = re.fullmatch(r"([^=]+)=([^@]+)(?:@([0-9.]+))?", rule)
        if not m or m.group(1) not in by_name or m.group(2) not in by_name or \
                by_name[m.group(1)] not in scene.parent or by_name[m.group(2)] not in scene.parent:
            raise Problem(f"--follow {rule}: BONE=SOURCE[@FRACTION] with two bones of the model that have parents")
        follow.append((by_name[m.group(1)], by_name[m.group(2)], float(m.group(3) or 0.8)))
    if not a.follow:  # the angel's wings (derived bones with no constraint in glTF): as rigged_to_hdm4.py did
        for sd in "lr":
            for wing, src in ((f"wing_a_{sd}", f"upperarm_{sd}"), (f"wing_b_{sd}", f"lowerarm_{sd}")):
                if wing in by_name and src in by_name and by_name[wing] in scene.parent and by_name[src] in scene.parent:
                    follow.append((by_name[wing], by_name[src], 0.8))
    hand_names = [k for k, n in enumerate(lowered) if n in profile["hands"] or any(w in n for w in WEAPON_WORDS)]
    if not hand_names:
        children = {p for p in parents if p >= 0}
        hand_names = [k for k in range(nb) if k not in children]

    clip_blobs, strikes = [], []
    for cname in want:
        an = anims[cname]
        chans, dur = {}, 0.0
        for ch in an["channels"]:
            tgt, smp = ch["target"], an["samplers"][ch["sampler"]]
            mine = target.get(tgt.get("node"))
            if mine is None or tgt["path"] not in ("translation", "rotation", "scale"):
                continue
            times = accessor(gc, smp["input"]).reshape(-1)
            chans[(mine, tgt["path"])] = Channel(times, accessor(gc, smp["output"]), tgt["path"], smp.get("interpolation", "LINEAR"))
            dur = max(dur, float(times[-1]))
        frames = int(round(dur * spec.FPS)) + 1
        data = np.zeros((frames, nb, 7), np.float32)
        hands = np.zeros((frames, len(hand_names), 3))
        start = None
        for f in range(frames):
            t = min(f / spec.FPS, dur)
            trs = {}
            for i in range(len(nodes)):
                tt, qq, ss = scene.rest[i]
                c = chans.get((i, "translation"))
                tt = c.at(t) if c else tt
                c = chans.get((i, "rotation"))
                qq = c.at(t) if c else qq
                c = chans.get((i, "scale"))
                ss = c.at(t) if c else ss
                trs[i] = (tt, qq, ss)
            for wing, src, fraction in follow:  # a bone that copies another's turn beyond its parent's, at a fraction
                wf = scene.world(trs)

                def turn(x, w=wf):
                    m = w(x)[:3, :3]
                    return m / np.linalg.norm(m[:, 0])

                def turn0(x):
                    m = wrest(x)[:3, :3]
                    return m / np.linalg.norm(m[:, 0])
                sp = scene.parent[src]
                dw = (turn(src) @ turn0(src).T) @ np.linalg.inv(turn(sp) @ turn0(sp).T)
                q = mat_to_quat(dw)
                q = q if q[3] >= 0 else -q
                dk = quat_to_mat(slerp(np.array([0, 0, 0, 1.0]), q, fraction))
                rp = turn(scene.parent[wing])
                local = np.linalg.inv(rp) @ dk @ rp @ quat_to_mat(scene.rest[wing][1])
                trs[wing] = (scene.rest[wing][0], mat_to_quat(local), scene.rest[wing][2])
            wf = scene.world(trs)
            Wn = {n: wf(n).copy() for n in joints}
            if not a.keep_root_motion:
                at_root = Wn[joints[root]][:3, 3]
                if start is None:
                    start = at_root.copy()
                travel = np.array([at_root[0] - start[0], 0.0, at_root[2] - start[2]])
                for n in joints:
                    Wn[n][:3, 3] -= travel
            Wd = {n: T @ Wn[n] @ Ti for n in joints}
            for k, n in enumerate(joints):
                par = parents[k]
                loc = np.linalg.inv(Wd[joints[par]]) @ Wd[n] if par >= 0 else Wd[n]
                u, _, vt = np.linalg.svd(loc[:3, :3])
                r = u @ vt
                if np.linalg.det(r) < 0:
                    r = u @ np.diag([1, 1, -1]) @ vt
                q = mat_to_quat(r)
                if f > 0 and float(q @ data[f - 1, k, 3:7]) < 0:
                    q = -q
                data[f, k, :3] = loc[:3, 3]
                data[f, k, 3:] = q
            for h, k in enumerate(hand_names):  # the joint itself, in the game's space
                hands[f, h] = A @ Wn[joints[k]][:3, 3] + b
        clip_blobs.append((cname, frames, data))
        if cname == acts.get("attack") and frames > 2:
            speed = np.zeros((frames, len(hand_names)))
            speed[1:-1] = np.linalg.norm(hands[2:] - hands[:-2], axis=2) / 2
            best = int(np.argmax(speed.max(0)))
            strikes = strike_frames(speed[:, best])
            notes.append(f"strike frames from {names[hand_names[best]]}'s speed: {strikes}")
    if not clip_blobs:
        notes.append("no clips: the model stands in its bind pose")

    # write
    a.out.mkdir(parents=True, exist_ok=True)
    flags = 0
    blob = bytearray(struct.pack("<4sIIIIIII", b"HDM4", len(pos), len(idx), nb, 1, 1, len(clip_blobs), flags))
    for k in range(nb):
        blob += struct.pack("<i12f3f", parents[k], *ibm_d[k][:3, :].reshape(-1).tolist(), 0, 0, 0)
    vb = np.zeros((len(pos), 13), np.float32)
    vb[:, 0:3] = pos_d
    vb[:, 3:6] = nrm_d
    vb[:, 6:8] = uvs
    jj = np.clip(jj, 0, nb - 1).astype(np.uint32)
    vb[:, 8] = (jj[:, 0] | (jj[:, 1] << 8) | (jj[:, 2] << 16) | (jj[:, 3] << 24)).astype(np.uint32).view(np.float32)
    vb[:, 9:13] = ww
    blob += vb.tobytes()
    blob += idx.astype("<u4").tobytes()
    blob += bytes([128, 128, 128, 255])  # the file's own 1x1 texture: base.png is drawn over it
    for cname, frames, data in clip_blobs:
        blob += struct.pack("<32sIfII", cname.encode()[:31], frames, spec.FPS, 0, 0)
        blob += data.astype("<f4").tobytes()
    info = spec.parse_hdm4(bytes(blob))  # what the game will say of it
    (a.out / "model.hdm").write_bytes(bytes(blob))
    base_img.save(a.out / "base.png")
    textures = {"base": "base.png"}
    if normal_img is not None:
        normal_img.save(a.out / "normal.png")
        mr_img.save(a.out / "metal_roughness.png")
        textures.update(normal="normal.png", metal_roughness="metal_roughness.png")
    package = {"format": 1, "name": a.name or a.gltf.stem, "model": "model.hdm", "textures": textures,
               "clips": {act: acts[act] for act in spec.ACTS if acts.get(act)}}
    if strikes:
        package["strike"] = {"attack": strikes}
    package.update({"author": a.author or "", "license": a.license or "", "source": a.gltf.name,
                    "converter": {"tool": "native_convert.py", "rig": rig, "root": names[root],
                                  "game_units_per_gltf_unit": round(s, 4), "height": round(stature * s, 1),
                                  "root_height": round(root_height * s, 1)}})
    (a.out / "model.json").write_text(json.dumps(package, indent=2) + "\n", encoding="utf-8")
    return package, info, notes


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("gltf", type=Path, help="the rigged model (.glb or .gltf)")
    ap.add_argument("out", type=Path, help="the package folder to write")
    ap.add_argument("--clips", default="all", help="the clips to keep, comma separated, or all (at most 16)")
    ap.add_argument("--clips-from", type=Path, help="take the clips from this glb instead (bones matched by name)")
    ap.add_argument("--rig", choices=["auto", "ue", "mixamo", "generic"], default="auto")
    ap.add_argument("--root", help="the root (hips) bone, for a rig the profiles do not know")
    ap.add_argument("--root-height", type=float, default=ROOT_HEIGHT, help="game units from the soles to the root (default 300)")
    ap.add_argument("--height", type=float, help="size the model by its height in game units instead (a humanoid: about 560)")
    ap.add_argument("--scale", type=float, help="game units per glTF unit, instead of a fit")
    ap.add_argument("--texture-max", type=int, default=spec.TEXTURE_MAX, help="the texture's largest side (default 2048)")
    ap.add_argument("--follow", action="append", help="BONE=SOURCE[@FRACTION]: BONE turns with SOURCE (beyond SOURCE's parent)")
    ap.add_argument("--keep-root-motion", action="store_true", help="keep the root's horizontal travel in the clips")
    ap.add_argument("--no-pbr", action="store_true", help="leave the normal and metal/roughness maps out")
    ap.add_argument("--name")
    ap.add_argument("--author")
    ap.add_argument("--license")
    a = ap.parse_args(argv)
    try:
        package, info, notes = convert(a)
    except (Problem, spec.Hdm4Error) as e:
        print(f"native_convert: {a.gltf}: {e}", file=sys.stderr)
        return 1
    c = package["converter"]
    print(f"{a.out / 'model.hdm'}: {info['vertices']} vertices, {info['triangles']} triangles, {info['bones']} bones, "
          f"{len(info['clips'])} clips, {info['bytes'] / 1e6:.1f} MB")
    print(f"rig {c['rig']}, root {c['root']}: {c['height']} game units tall, root {c['root_height']} above the soles")
    for act in spec.ACTS:
        print(f"  {act:9} -> {package['clips'].get(act, '(none)')}")
    if "strike" in package:
        print(f"  blows of the attack at frames {package['strike']['attack']}")
    for note in notes:
        print(f"note: {note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
