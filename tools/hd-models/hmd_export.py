#!/usr/bin/env python3
"""Export a disc monster's model to glTF: one skinned mesh, a joint per part.

    hmd_export.py CARD OUT_DIR [--disc DISC.bin] [--preview]   (in hacking/shared/tools/hd-models)

Writes OUT_DIR/model.gltf (+ model.bin), the decoded texture pages as PNG
(texture_row{R}.png, the 384x256 sheet), parts.json (the skeleton and counts) and with
--preview preview_*.png (a quick painter's-order picture, not a render).

The mesh is in the pose the model data stores (the coordinate section), y up,
1 unit = 100 game units. Every vertex is bound 100% to the part it belongs to,
as on the disc (parts are rigid), so Blender shows the same skeleton the game
animates. Quads are split in two triangles. Vertices are not welded (one per
triangle corner); weld by distance in Blender.
"""
import argparse
import json
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent / "vendor"))
import hmd as hmdlib  # noqa: E402
import model_record  # noqa: E402

SECTOR = 2048
TEXTURE_PHASE = 96 * SECTOR
PALETTE_PHASE = TEXTURE_PHASE + 48 * SECTOR
PAGE_W, PAGE_H = 128, 256
SHEET_W = PAGE_W * 3
TPAGE_FIRST, CLUT_FIRST = 0x9A, 0x28
SCALE = 0.01
# The USA disc image of the main checkout (tools here belong to no worktree or branch).
DEFAULT_DISC = Path(__file__).resolve().parents[2].parent / "Yu-Gi-Oh-Forbidden-Memories-Recompiled" / "game" / "ygofm-orig-usa.bin"


def decode_pages(record: bytes):
    """{palette row: RGBA image of the whole 384x256 texture sheet}. The three 128-texel pages
    sit side by side in VRAM; a polygon's page (tpage - 0x9A) offsets its U by 128 per page."""
    sheet = np.zeros((PAGE_H, PAGE_W * 3), np.uint8)
    for page in range(3):
        texels = bytearray()
        for strip in range(16):
            at = TEXTURE_PHASE + (page * 16 + strip) * SECTOR
            texels += record[at:at + SECTOR]
        sheet[:, page * PAGE_W:(page + 1) * PAGE_W] = np.frombuffer(bytes(texels), np.uint8).reshape(PAGE_H, PAGE_W)
    rows = np.frombuffer(record[PALETTE_PHASE:PALETTE_PHASE + 2 * SECTOR], "<u2").reshape(-1, 256)
    out = {}
    for row in range(len(rows)):
        c = rows[row][sheet].astype(np.uint32)
        rgba = np.empty(c.shape + (4,), np.uint8)
        rgba[..., 0] = (c & 31) * 255 // 31
        rgba[..., 1] = ((c >> 5) & 31) * 255 // 31
        rgba[..., 2] = ((c >> 10) & 31) * 255 // 31
        rgba[..., 3] = np.where(c == 0, 0, 255)
        out[row] = Image.fromarray(rgba, "RGBA")
    return out


def decode(low, half):
    """(uvs, normal indices, vertex indices) of one polygon record, by its type's layout:
    0x9 flat triangle, 0xD Gouraud triangle, 0x11 flat quad, 0x15 Gouraud quad."""
    def uv(w):
        return (w & 255, w >> 8)
    if low == 0xD:
        return [uv(half[0]), uv(half[2]), uv(half[4])], [half[6], half[8], half[10]], [half[7], half[9], half[11]]
    if low == 0x15:
        return ([uv(half[0]), uv(half[2]), uv(half[4]), uv(half[6])],
                [half[5], half[8], half[10], half[12]], [half[7], half[9], half[11], half[13]])
    if low == 0x9:
        return [uv(half[0]), uv(half[2]), uv(half[4])], [half[6]] * 3, [half[7], half[8], half[9]]
    return ([uv(half[0]), uv(half[2]), uv(half[4]), uv(half[6])],
            [half[7]] * 4, [half[8], half[9], half[10], half[11]])


def collect(h):
    """Triangles as dicts of world-space (game axes) corners, normals, uvs, bones."""
    world = h.world()
    owner_by_header: dict[tuple, dict[int, int]] = {}
    tris = []

    def vec(section, index):
        return h.vector(section, index)

    def emit(unit_of, positions, normals, uvs, page, row, bones, source):
        corners = []
        for i in range(len(positions)):
            b = bones[i]
            m = world[b]
            p = (m @ np.r_[positions[i], 1])[:3]
            n = m[:3, :3] @ normals[i] if normals[i] is not None else None
            corners.append((p, n, (uvs[i][0] + PAGE_W * page, uvs[i][1]), b,
                            np.asarray(positions[i], float), None if normals[i] is None else np.asarray(normals[i], float)))
        order = [(0, 1, 2)] + ([(1, 3, 2)] if len(corners) == 4 else [])
        for a, b_, c in order:
            tris.append({"c": [corners[a], corners[b_], corners[c]], "page": page, "row": row, "src": source})

    for block in range(1, h.block_count):
        unit = min(block - 1, len(h.units) - 1)
        for element in h.chain(block):
            sec = h.header(element["header"])
            key = tuple(sec)
            owners = owner_by_header.setdefault(key, {})
            for prim in element["prims"]:
                kind = prim["type"]
                hi, low = kind >> 24, kind & 0xFFFF
                if hi == 1 and low == 0 and prim["args"]:
                    count, first = prim["args"][0], prim["args"][1]
                    for i in range(count):
                        owners[first + i] = unit
                elif low in (0x9, 0xD, 0x11, 0x15) and hi in (0, 1):
                    shared = hi == 1
                    stride = {0x9: 0x14, 0xD: 0x18, 0x11: 0x18, 0x15: 0x1C}[low]
                    start = h.section(sec[0]) + prim["args"][0] * 4
                    for n in range(prim["count"]):
                        half = struct.unpack_from("<%dH" % (stride // 2), h.data, start + n * stride)
                        uv, nidx, vidx = decode(low, half)
                        k = len(vidx)
                        # shared polygons index the arrays of the whole model (sections 1 and 3);
                        # the owner is the part whose prepass run holds the vertex.
                        vsec, nsec = (sec[1], sec[3]) if shared else (sec[1], sec[2])
                        bones = [owners.get(v, unit) if shared else unit for v in vidx]
                        emit(None, [vec(vsec, v) for v in vidx],
                             [h.vector(nsec, x) / 4096 for x in nidx], uv,
                             half[3] - TPAGE_FIRST, (half[1] - CLUT_FIRST) // 0x40, bones,
                             "shared" if shared else "plain")
    return tris, world


def fix_winding(tris):
    """Make the triangles run anticlockwise about their normal (glTF's front)."""
    votes = 0
    for t in tris:
        p = [c[0] for c in t["c"]]
        ns = [c[1] for c in t["c"] if c[1] is not None]
        if ns:
            votes += 1 if np.dot(np.cross(p[1] - p[0], p[2] - p[0]), sum(ns)) > 0 else -1
    # game y is down and the conversion below flips y and z (a proper rotation),
    # so orientation carries over unchanged.
    if votes < 0:
        for t in tris:
            t["c"] = [t["c"][0], t["c"][2], t["c"][1]]
    return votes


def to_gltf_axes(p):
    return np.array([p[0], -p[1], -p[2]]) * SCALE


def write_gltf(out: Path, tris, h, world, pages):
    groups: dict[tuple, list] = {}
    for t in tris:
        groups.setdefault(t["row"], []).append(t)
    buffer = bytearray()
    views, accessors, primitives, materials, images, textures = [], [], [], [], [], []

    def add(data: bytes, target=None):
        while len(buffer) % 4:
            buffer.append(0)
        views.append({"buffer": 0, "byteOffset": len(buffer), "byteLength": len(data),
                      **({"target": target} if target else {})})
        buffer.extend(data)
        return len(views) - 1

    def accessor(array, ctype, kind, target=34962, minmax=False):
        a = {"bufferView": add(array.tobytes(), target), "componentType": ctype, "count": len(array), "type": kind}
        if minmax:
            a["min"], a["max"] = array.min(0).tolist(), array.max(0).tolist()
        accessors.append(a)
        return len(accessors) - 1

    for row, group in sorted(groups.items()):
        pos, nor, uv, joints = [], [], [], []
        for t in group:
            p = [c[0] for c in t["c"]]
            face = np.cross(p[1] - p[0], p[2] - p[0])
            face = face / (np.linalg.norm(face) or 1)
            for c in t["c"]:
                pos.append(to_gltf_axes(c[0]))
                n = c[1] if c[1] is not None else face
                n = n / (np.linalg.norm(n) or 1)
                nor.append([n[0], -n[1], -n[2]])
                uv.append([c[2][0] / SHEET_W, c[2][1] / PAGE_H])
                joints.append([c[3], 0, 0, 0])
        count = len(pos)
        name = f"texture_row{row}.png"
        pages[row].save(out / name)
        images.append({"uri": name})
        textures.append({"source": len(images) - 1, "sampler": 0})
        materials.append({"name": f"texture_row{row}", "alphaMode": "MASK", "doubleSided": True,
                          "pbrMetallicRoughness": {"baseColorTexture": {"index": len(textures) - 1},
                                                   "metallicFactor": 0, "roughnessFactor": 1}})
        primitives.append({
            "attributes": {
                "POSITION": accessor(np.array(pos, np.float32), 5126, "VEC3", minmax=True),
                "NORMAL": accessor(np.array(nor, np.float32), 5126, "VEC3"),
                "TEXCOORD_0": accessor(np.array(uv, np.float32), 5126, "VEC2"),
                "JOINTS_0": accessor(np.array(joints, np.uint16), 5123, "VEC4"),
                "WEIGHTS_0": accessor(np.tile(np.array([1, 0, 0, 0], np.float32), (count, 1)), 5126, "VEC4"),
            },
            "material": len(materials) - 1})

    conv = np.diag([SCALE, -SCALE, -SCALE, 1.0])
    inv = np.linalg.inv(conv)
    nodes, children = [], {i: [] for i in range(len(h.units))}
    ibm = []
    for i, (m, t, parent) in enumerate(h.units):
        local = np.eye(4)
        local[:3, :3], local[:3, 3] = m, t
        local = conv @ local @ inv
        nodes.append({"name": f"part{i:02d}", "matrix": local.T.flatten().tolist()})
        if parent >= 0:
            children[parent].append(i)
        ibm.append(np.linalg.inv(conv @ world[i] @ inv).T.astype(np.float32))
    for i, c in children.items():
        if c:
            nodes[i]["children"] = c
    roots = [i for i, (_, _, parent) in enumerate(h.units) if parent < 0]
    ibm_accessor = {"bufferView": add(np.array(ibm).tobytes()), "componentType": 5126,
                    "count": len(ibm), "type": "MAT4"}
    accessors.append(ibm_accessor)
    mesh_node = len(nodes)
    nodes.append({"name": "model", "mesh": 0, "skin": 0})
    doc = {
        "asset": {"version": "2.0", "generator": "hmd_export.py"},
        "scene": 0, "scenes": [{"nodes": roots + [mesh_node]}],
        "nodes": nodes, "meshes": [{"name": "model", "primitives": primitives}],
        "skins": [{"joints": list(range(len(h.units))), "inverseBindMatrices": len(accessors) - 1,
                   "skeleton": roots[0]}],
        "materials": materials, "textures": textures, "images": images,
        "samplers": [{"magFilter": 9728, "minFilter": 9728, "wrapS": 33071, "wrapT": 33071}],
        "buffers": [{"uri": "model.bin", "byteLength": len(buffer)}],
        "bufferViews": views, "accessors": accessors,
    }
    (out / "model.bin").write_bytes(bytes(buffer))
    (out / "model.gltf").write_text(json.dumps(doc, indent=1))


def skin_blends(tris, h, world, radius):
    """For every corner: (part B, weight of B, position in B's local space, normal in B's local space).

    A vertex within `radius` game units of a vertex of its part's parent or child takes part of that neighbour's
    matrix too, up to half at the joint itself, so both sides of a joint move to the same point and the seam
    closes. Only parent/child pairs blend: a part never mixes with a stranger that merely stands close."""
    from scipy.spatial import cKDTree
    count = len(h.units)
    parent = [u[2] for u in h.units]
    neighbours = {i: set() for i in range(count)}
    for i, par in enumerate(parent):
        if par >= 0:
            neighbours[i].add(par)
            neighbours[par].add(i)
    per_part = {i: [] for i in range(count)}
    for t in tris:
        for c in t["c"]:
            per_part[c[3]].append(c[0])
    trees = {i: cKDTree(np.array(v)) for i, v in per_part.items() if v}
    inverse = [np.linalg.inv(m) for m in world]
    out = []
    for t in tris:
        row = []
        for c in t["c"]:
            part = c[3]
            best, best_d = None, radius
            for n in neighbours[part]:
                if n not in trees:
                    continue
                d, _ = trees[n].query(c[0])
                if d < best_d:
                    best, best_d = n, d
            if best is None:
                row.append((part, 0.0, c[4], c[5]))
                continue
            weight = 0.5 * (1.0 - best_d / radius)
            local = (inverse[best] @ np.r_[c[0], 1.0])[:3]
            normal = None
            if c[1] is not None:
                world_normal = c[1]
                normal = inverse[best][:3, :3] @ world_normal
            row.append((best, weight, local, normal))
        out.append(row)
    return out


def write_hdm(out: Path, tris, pages, h=None, world=None, skin_radius=0.0):
    """OUT/model.hdm: what the game's native model pass loads (src/pc/render/native_model.c). Little endian.

    HDM1: "HDM1", u32 vertices, u32 parts, u32 tex_w, u32 tex_h; per vertex (one per triangle corner, part-local game
    units as the HMD stores them) f32 pos[3], f32 normal[3], f32 uv[2] (0..1), u32 part; then tex_w * tex_h RGBA.
    HDM2 (skin_radius > 0): the same header with "HDM2"; per vertex f32 pos[3], normal[3], uv[2], u32 part, then
    u32 part_b, f32 weight_b, f32 pos_b[3], f32 normal_b[3] (17 words): the vertex also sits in part B's local space
    with weight_b (0 = rigid)."""
    import struct as st
    row = sorted({t["row"] for t in tris})[0]
    tex = pages[row]
    parts = max(c[3] for t in tris for c in t["c"]) + 1
    v2 = skin_radius > 0 and h is not None
    blends = skin_blends(tris, h, world, skin_radius) if v2 else None
    blob = bytearray(st.pack("<4sIIII", b"HDM2" if v2 else b"HDM1", len(tris) * 3, parts, tex.width, tex.height))
    blended = 0
    for ti, t in enumerate(tris):
        p = [c[4] for c in t["c"]]
        face = np.cross(p[1] - p[0], p[2] - p[0])
        face = face / (np.linalg.norm(face) or 1)
        for k, c in enumerate(t["c"]):
            n = c[5] if c[5] is not None else face
            n = n / (np.linalg.norm(n) or 1)
            blob += st.pack("<8fI", *c[4].tolist(), *n.tolist(), c[2][0] / SHEET_W, c[2][1] / PAGE_H, c[3])
            if v2:
                part_b, weight, local, normal_b = blends[ti][k]
                nb = normal_b if normal_b is not None else n
                nb = nb / (np.linalg.norm(nb) or 1)
                blended += weight > 0
                blob += st.pack("<If3f3f", part_b, weight, *np.asarray(local, float).tolist(), *np.asarray(nb, float).tolist())
    blob += tex.tobytes()
    (out / "model.hdm").write_bytes(bytes(blob))
    if v2:
        print(f"skin: {blended} of {len(tris) * 3} vertices blend with a neighbour part (radius {skin_radius})")


def preview(out: Path, tris, pages, size=640):
    pts = np.array([c[0] for t in tris for c in t["c"]])
    for name, axes in (("front", (0, 1, 2)), ("side", (2, 1, 0))):
        lo, hi = pts.min(0), pts.max(0)
        span = max(hi[axes[0]] - lo[axes[0]], hi[axes[1]] - lo[axes[1]]) or 1
        k = (size - 40) / span
        img = Image.new("RGB", (size, size), (40, 44, 52))
        d = ImageDraw.Draw(img)
        order = sorted(tris, key=lambda t: -sum(c[0][axes[2]] for c in t["c"]) if name == "front" else
                       sum(c[0][axes[2]] for c in t["c"]))
        for t in order:
            tex = pages.get(t["row"])
            u = sum(c[2][0] for c in t["c"]) / 3
            v = sum(c[2][1] for c in t["c"]) / 3
            colour = tex.getpixel((min(int(u), SHEET_W - 1), min(int(v), PAGE_H - 1)))[:3] if tex else (200, 0, 200)
            poly = [(20 + (c[0][axes[0]] - lo[axes[0]]) * k, 20 + (c[0][axes[1]] - lo[axes[1]]) * k) for c in t["c"]]
            d.polygon(poly, fill=colour)
        img.save(out / f"preview_{name}.png")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("card", type=int)
    ap.add_argument("out", type=Path)
    ap.add_argument("--disc", type=Path, default=DEFAULT_DISC)
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--skin", type=float, default=0.0, metavar="RADIUS",
                    help="smooth skin: blend vertices within RADIUS game units of a parent/child part (HDM2); try 14")
    args = ap.parse_args()
    record = model_record.read_record(args.disc, args.card)
    h = hmdlib.Hmd(record[:96 * SECTOR])
    pages = decode_pages(record)
    tris, world = collect(h)
    votes = fix_winding(tris)
    args.out.mkdir(parents=True, exist_ok=True)
    write_gltf(args.out, tris, h, world, pages)
    write_hdm(args.out, tris, pages, h, world, args.skin)
    uvs = np.array([c[2] for t in tris for c in t["c"]])
    stats = {"card": args.card, "triangles": len(tris),
             "plain": sum(t["src"] == "plain" for t in tris), "shared": sum(t["src"] == "shared" for t in tris),
             "texture_rows_used": sorted({t["row"] for t in tris}), "tpages_used": sorted({t["page"] for t in tris}),
             "uv_max": uvs.max(0).tolist(), "winding_votes": votes,
             "parts": [{"index": i, "parent": p, "rest_translation": t.tolist(),
                        "triangles": sum(1 for tr in tris if tr["c"][0][3] == i)}
                       for i, (m, t, p) in enumerate(h.units)]}
    (args.out / "parts.json").write_text(json.dumps(stats, indent=1))
    if args.preview:
        preview(args.out, tris, pages)
    print({k: v for k, v in stats.items() if k != "parts"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
