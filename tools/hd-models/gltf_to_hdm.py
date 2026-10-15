#!/usr/bin/env python3
"""A skinned glTF model of your own -> a model.hdm the game's native model pass draws.

    gltf_to_hdm.py MODEL.gltf|.glb OUT.hdm --card 364 [--disc DISC.bin]

The mesh is skinned to the game's skeleton: joints named part00 .. partNN, the 30 parts of the card's disc model
(hmd_export.py writes that skeleton, with the disc's own mesh, as model.gltf: open it in Blender, model your own mesh
around it, skin it to the armature, export). Rules:

  * Leave the armature as it is (its rest pose is the game's rest pose; the game moves the parts, so your mesh moves
    with them). Do not rename, move, scale or re-parent the joints.
  * Units: as exported (y up, 1 unit = 100 game units). The mesh is read in the bind pose.
  * Each vertex follows its two strongest joints (weights are renormalised): that is the game's smooth skin.
  * One texture (the first material's base colour image, any size), UV set 0, origin top left (glTF's).
  * Triangles only; any number (the game draws them natively, not as PS1 packets).
"""
import argparse
import base64
import json
import struct
import sys
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent / "vendor"))
import hmd as hmdlib  # noqa: E402
import model_record  # noqa: E402

SECTOR = 2048
DEFAULT_DISC = Path(__file__).resolve().parents[2].parent / "Yu-Gi-Oh-Forbidden-Memories-Recompiled" / "game" / "ygofm-orig-usa.bin"
SCALE = 0.01  # glTF units per game unit (hmd_export.py)
COMPONENT = {5120: ("b", 1), 5121: ("B", 1), 5122: ("h", 2), 5123: ("H", 2), 5125: ("I", 4), 5126: ("f", 4)}
TYPE_SIZE = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


class Gltf:
    def __init__(self, path: Path):
        self.path = path
        data = path.read_bytes()
        self.glb_bin = None
        if data[:4] == b"glTF":
            length = struct.unpack_from("<I", data, 8)[0]
            at = 12
            while at < length:
                size, kind = struct.unpack_from("<II", data, at)
                chunk = data[at + 8:at + 8 + size]
                if kind == 0x4E4F534A:
                    self.doc = json.loads(chunk)
                elif kind == 0x004E4942:
                    self.glb_bin = chunk
                at += 8 + size
        else:
            self.doc = json.loads(data)
        self.buffers = []
        for b in self.doc.get("buffers", []):
            uri = b.get("uri")
            if uri is None:
                self.buffers.append(self.glb_bin)
            elif uri.startswith("data:"):
                self.buffers.append(base64.b64decode(uri.split(",", 1)[1]))
            else:
                self.buffers.append((path.parent / uri).read_bytes())

    def view(self, index: int) -> bytes:
        v = self.doc["bufferViews"][index]
        start = v.get("byteOffset", 0)
        return self.buffers[v["buffer"]][start:start + v["byteLength"]]

    def accessor(self, index: int) -> np.ndarray:
        a = self.doc["accessors"][index]
        code, size = COMPONENT[a["componentType"]]
        n = TYPE_SIZE[a["type"]]
        count = a["count"]
        if "bufferView" not in a:
            return np.zeros((count, n))
        v = self.doc["bufferViews"][a["bufferView"]]
        stride = v.get("byteStride") or n * size
        raw = self.view(a["bufferView"])
        offset = a.get("byteOffset", 0)
        out = np.empty((count, n), dtype=np.float64)
        for i in range(count):
            out[i] = struct.unpack_from("<" + code * n, raw, offset + i * stride)
        if a.get("normalized"):
            out /= {5121: 255.0, 5123: 65535.0, 5120: 127.0, 5122: 32767.0}[a["componentType"]]
        return out

    def image(self, texture_index: int) -> Image.Image:
        source = self.doc["textures"][texture_index]["source"]
        image = self.doc["images"][source]
        if "uri" in image:
            uri = image["uri"]
            if uri.startswith("data:"):
                return Image.open(BytesIO(base64.b64decode(uri.split(",", 1)[1]))).convert("RGBA")
            return Image.open(self.path.parent / uri).convert("RGBA")
        return Image.open(BytesIO(self.view(image["bufferView"]))).convert("RGBA")


def joint_part_numbers(g: Gltf) -> list[int]:
    skins = g.doc.get("skins") or []
    if not skins:
        sys.exit("the glTF has no skin: skin the mesh to the part00..partNN armature")
    names = [g.doc["nodes"][j].get("name", "") for j in skins[0]["joints"]]
    numbers = []
    for k, name in enumerate(names):
        digits = "".join(ch for ch in name if ch.isdigit())
        if not name.lower().startswith("part") or not digits:
            sys.exit(f"joint {k} is called '{name}': the skeleton must keep the names part00 .. partNN")
        numbers.append(int(digits))
    return numbers


def node_world_positions(g: Gltf) -> dict[int, np.ndarray]:
    """glTF node index -> world position (the node's origin), from matrix or translation/rotation/scale down the hierarchy."""
    nodes = g.doc["nodes"]
    parent = {}
    for i, n in enumerate(nodes):
        for c in n.get("children", []):
            parent[c] = i
    def local(n):
        if "matrix" in n:
            return np.array(n["matrix"], float).reshape(4, 4).T
        t = np.array(n.get("translation", [0, 0, 0]), float)
        x, y, z, w = n.get("rotation", [0, 0, 0, 1])
        r = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                      [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                      [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
        sc = np.array(n.get("scale", [1, 1, 1]), float)
        m = np.eye(4); m[:3, :3] = r * sc; m[:3, 3] = t
        return m
    cache = {}
    def world(i):
        if i not in cache:
            m = local(nodes[i]); cache[i] = world(parent[i]) @ m if i in parent else m
        return cache[i]
    return {i: world(i)[:3, 3] for i in range(len(nodes))}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("gltf", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--card", type=int, required=True, help="the card whose disc skeleton the mesh is skinned to")
    ap.add_argument("--disc", type=Path, default=DEFAULT_DISC)
    args = ap.parse_args()

    record = model_record.read_record(args.disc, args.card)
    h = hmdlib.Hmd(record[:96 * SECTOR])
    world = h.world()
    inverse = [np.linalg.inv(m) for m in world]
    g = Gltf(args.gltf)
    parts_of_joint = joint_part_numbers(g)
    flip = np.diag([1.0, -1.0, -1.0])  # glTF (y up, z toward the viewer) -> the game's axes, a proper rotation

    positions, normals, uvs, joints, weights = [], [], [], [], []
    triangle_corners = []
    texture = None
    for mesh in g.doc["meshes"]:
        for prim in mesh["primitives"]:
            if prim.get("mode", 4) != 4:
                sys.exit("only triangle lists are supported")
            at = prim["attributes"]
            for need in ("POSITION", "JOINTS_0", "WEIGHTS_0", "TEXCOORD_0"):
                if need not in at:
                    sys.exit(f"a primitive has no {need}: the mesh must be skinned and UV mapped")
            p = g.accessor(at["POSITION"])
            n = g.accessor(at["NORMAL"]) if "NORMAL" in at else np.zeros_like(p)
            base = len(positions)
            positions.extend(p)
            normals.extend(n)
            uvs.extend(g.accessor(at["TEXCOORD_0"]))
            joints.extend(g.accessor(at["JOINTS_0"]).astype(int))
            weights.extend(g.accessor(at["WEIGHTS_0"]))
            idx = g.accessor(prim["indices"]).astype(int).reshape(-1) if "indices" in prim else np.arange(len(p))
            triangle_corners.extend((idx + base).tolist())
            if texture is None and "material" in prim:
                m = g.doc["materials"][prim["material"]]
                tex = m.get("pbrMetallicRoughness", {}).get("baseColorTexture")
                if tex:
                    texture = g.image(tex["index"])
    if texture is None:
        sys.exit("no base colour texture on the material")
    positions = np.array(positions)
    normals = np.array(normals)
    uvs = np.array(uvs)
    joints = np.array(joints)
    weights = np.array(weights)

    # per source vertex: its two strongest joints, as the game's part numbers
    top = np.argsort(-weights, axis=1)[:, :2]
    part_a = np.array([parts_of_joint[joints[i, top[i, 0]]] for i in range(len(positions))])
    part_b = np.array([parts_of_joint[joints[i, top[i, 1]]] for i in range(len(positions))])
    wa = weights[np.arange(len(positions)), top[:, 0]]
    wb = weights[np.arange(len(positions)), top[:, 1]]
    total = np.maximum(wa + wb, 1e-9)
    weight_b = np.where(part_b == part_a, 0.0, wb / total)

    # the skeleton's own joint positions (the RETARGET): J[a] in game units; the disc's own (world translation) when the glTF has none
    P = len(world)
    tb = np.array([w[:3, 3] for w in world]); Rb = [w[:3, :3] for w in world]
    J = tb.copy()
    skin_joints = g.doc["skins"][0]["joints"]
    wp = node_world_positions(g)
    for k, node in enumerate(skin_joints):
        pn = parts_of_joint[k]
        if pn < P: J[pn] = flip @ (wp[node] / SCALE)
    print("joint offsets from the disc skeleton (game units): max %.1f" % np.abs(J - tb).max())
    parent = np.array([h.units[i][2] for i in range(P)])
    game_p = (positions / SCALE) @ flip.T          # the bind pose in game units
    game_n = normals @ flip.T
    corners = np.array(triangle_corners)
    count = (len(corners) // 3) * 3
    corners = corners[:count]
    blob = bytearray(struct.pack("<4sIIII", b"HDM3", count, P, texture.width, texture.height))
    for a_ in range(P):   # joint table: parent, J[3], disc joint tb[3], INVERSE of the disc bind rotation Rbi[9] (the renderer: posed joint = parent's + R_rel * (J - J_parent))
        blob += struct.pack("<i3f3f9f", int(parent[a_]), *J[a_].tolist(), *tb[a_].tolist(), *np.linalg.inv(Rb[a_]).reshape(-1).tolist())
    for v in corners:
        a, b = int(part_a[v]), int(part_b[v])
        pa = np.linalg.inv(Rb[a]) @ (game_p[v] - J[a])     # part frame, origin at the model's own joint
        pb = np.linalg.inv(Rb[b]) @ (game_p[v] - J[b])
        na = inverse[a][:3, :3] @ game_n[v]
        nb = inverse[b][:3, :3] @ game_n[v]
        na = na / (np.linalg.norm(na) or 1.0)
        nb = nb / (np.linalg.norm(nb) or 1.0)
        blob += struct.pack("<8fI", *pa.tolist(), *na.tolist(), float(uvs[v][0]), float(uvs[v][1]), a)
        blob += struct.pack("<If3f3f", b, float(weight_b[v]), *pb.tolist(), *nb.tolist())
    blob += texture.tobytes()
    args.out.write_bytes(bytes(blob))
    print(f"{args.out}: {count // 3} triangles, {count} vertices, texture {texture.width}x{texture.height}, "
          f"{int((weight_b[corners] > 0).sum())} blended vertices")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
