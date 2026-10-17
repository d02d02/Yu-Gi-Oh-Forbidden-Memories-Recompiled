"""A small rigged glb made from nothing, for the native model tools' tests: an Unreal-named skeleton (pelvis 1 m up,
spine, right arm and hand, right leg), a body of two materials (a textured lower box, a colour-only upper box whose
UVs repeat twice), a sword that is not skinned (under the hand), and five clips: Idle, Sword_Attack (the arm swings
fastest between 0.3 and 0.4 s), Death01 (cubic spline keys), Victory (step keys) and Walk (the pelvis travels 1 m)."""
import io
import json
import math
import struct

from PIL import Image

POSITION, NORMAL, TEXCOORD, JOINTS, WEIGHTS = range(5)


class Builder:
    def __init__(self):
        self.buf = bytearray()
        self.views, self.accessors = [], []

    def view(self, data):
        while len(self.buf) % 4:
            self.buf.append(0)
        self.views.append({"buffer": 0, "byteOffset": len(self.buf), "byteLength": len(data)})
        self.buf += data
        return len(self.views) - 1

    def accessor(self, values, kind, component=5126):
        code = {5126: "f", 5125: "I", 5121: "B", 5123: "H"}[component]
        flat = [v for item in values for v in (item if isinstance(item, (list, tuple)) else [item])]
        data = struct.pack(f"<{len(flat)}{code}", *flat)
        a = {"bufferView": self.view(data), "componentType": component, "count": len(values), "type": kind}
        if kind == "VEC3" and component == 5126:
            a["min"] = [min(v[i] for v in values) for i in range(3)]
            a["max"] = [max(v[i] for v in values) for i in range(3)]
        self.accessors.append(a)
        return len(self.accessors) - 1


def box(x0, x1, y0, y1, z0, z1, u_repeat=1.0):
    corners = [(x, y, z) for y in (y0, y1) for z in (z0, z1) for x in (x0, x1)]
    faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    positions, normals, uvs, indices = [], [], [], []
    for face in faces:
        a, b, c = (corners[face[k]] for k in range(3))
        u = [b[i] - a[i] for i in range(3)]
        v = [c[i] - a[i] for i in range(3)]
        n = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]
        length = math.sqrt(sum(x * x for x in n)) or 1.0
        start = len(positions)
        for k, corner in enumerate(face):
            positions.append(corners[corner])
            normals.append([x / length for x in n])
            uvs.append([(1.0 if k in (1, 2) else 0.0) * u_repeat, 1.0 if k >= 2 else 0.0])
        indices += [start, start + 1, start + 2, start, start + 2, start + 3]
    return positions, normals, uvs, indices


def quat(axis, degrees):
    h = math.radians(degrees) / 2
    s = math.sin(h)
    return [axis[0] * s, axis[1] * s, axis[2] * s, math.cos(h)]


def png_bytes(size, colour):
    out = io.BytesIO()
    Image.new("RGBA", size, colour).save(out, "PNG")
    return out.getvalue()


def write(path):
    b = Builder()
    # nodes: 0 Armature, 1 pelvis, 2 spine_01, 3 upperarm_r, 4 hand_r, 5 thigh_r, 6 foot_r, 7 Body, 8 Sword
    nodes = [
        {"name": "Armature", "children": [1, 7]},
        {"name": "pelvis", "translation": [0, 1, 0], "children": [2, 5]},
        {"name": "spine_01", "translation": [0, 0.4, 0], "children": [3]},
        {"name": "upperarm_r", "translation": [-0.3, 0.3, 0], "children": [4]},
        {"name": "hand_r", "translation": [-0.4, 0, 0], "children": [8]},
        {"name": "thigh_r", "translation": [-0.1, -0.1, 0], "children": [6]},
        {"name": "foot_r", "translation": [0, -0.8, 0]},
        {"name": "Body", "mesh": 0, "skin": 0},
        {"name": "Sword", "mesh": 1, "translation": [-0.1, 0, 0]},
    ]
    world = {1: (0, 1, 0), 2: (0, 1.4, 0), 3: (-0.3, 1.7, 0), 4: (-0.7, 1.7, 0), 5: (-0.1, 0.9, 0), 6: (-0.1, 0.1, 0)}
    joints = [1, 2, 3, 4, 5, 6]
    ibm = []
    for j in joints:
        x, y, z = world[j]
        ibm.append([1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, -x, -y, -z, 1])  # column major
    skin = {"joints": joints, "inverseBindMatrices": b.accessor(ibm, "MAT4")}

    primitives = []
    for (y0, y1, material, repeat) in ((0.0, 1.0, 0, 1.0), (1.0, 1.6, 1, 2.0)):
        p, n, uv, idx = box(-0.2, 0.2, y0, y1, -0.1, 0.1, repeat)
        jt = [[5 if v[1] < 0.5 else (0 if v[1] <= 1.0 else 1), 0, 0, 0] for v in p]  # foot, pelvis, spine
        wt = [[1.0, 0, 0, 0] for _ in p]
        primitives.append({"attributes": {"POSITION": b.accessor(p, "VEC3"), "NORMAL": b.accessor(n, "VEC3"),
                                          "TEXCOORD_0": b.accessor(uv, "VEC2"), "JOINTS_0": b.accessor(jt, "VEC4", 5123),
                                          "WEIGHTS_0": b.accessor(wt, "VEC4")},
                           "indices": b.accessor(idx, "SCALAR", 5125), "material": material})
    sword = {"attributes": {"POSITION": b.accessor([(0, 0, 0), (-0.5, 0.05, 0), (-0.5, -0.05, 0)], "VEC3"),
                            "TEXCOORD_0": b.accessor([(0.1, 0.1), (0.9, 0.1), (0.9, 0.9)], "VEC2")},
             "indices": b.accessor([0, 1, 2], "SCALAR", 5125), "material": 0}

    def channel(node, path, times, values, interpolation="LINEAR"):
        kind = "VEC4" if path == "rotation" else "VEC3"
        return {"input": b.accessor(times, "SCALAR"), "output": b.accessor(values, kind), "interpolation": interpolation}, node, path

    def animation(name, channels):
        samplers, chans = [], []
        for sampler, node, path in channels:
            chans.append({"sampler": len(samplers), "target": {"node": node, "path": path}})
            samplers.append(sampler)
        return {"name": name, "samplers": samplers, "channels": chans}

    z = (0, 0, 1)
    cubic = []
    for angle in (0, 90):  # in-tangent, value, out-tangent per key
        cubic += [[0, 0, 0, 0], quat((1, 0, 0), angle), [0, 0, 0, 0]]
    animations = [
        animation("Idle", [channel(2, "rotation", [0, 1], [quat(z, 0), quat(z, 3)])]),
        animation("Sword_Attack", [channel(3, "rotation", [0, 0.3, 0.4, 1.0],
                                           [quat(z, 0), quat(z, -10), quat(z, -100), quat(z, -110)])]),
        animation("Death01", [channel(1, "rotation", [0, 1], cubic, "CUBICSPLINE")]),
        animation("Victory", [channel(2, "rotation", [0, 0.5], [quat(z, 0), quat(z, 20)], "STEP")]),
        animation("Walk", [channel(1, "translation", [0, 1], [[0, 1, 0], [0, 1, 1]])]),
    ]
    images = [{"bufferView": b.view(png_bytes((8, 8), (220, 30, 30, 255))), "mimeType": "image/png"}]
    doc = {
        "asset": {"version": "2.0"}, "scene": 0, "scenes": [{"nodes": [0]}], "nodes": nodes,
        "meshes": [{"primitives": primitives}, {"primitives": [sword]}], "skins": [skin],
        "materials": [{"name": "red", "pbrMetallicRoughness": {"baseColorTexture": {"index": 0}}},
                      {"name": "blue", "pbrMetallicRoughness": {"baseColorFactor": [0, 0, 1, 1]}}],
        "textures": [{"source": 0}], "images": images, "animations": animations,
        "buffers": [{"byteLength": 0}], "bufferViews": b.views, "accessors": b.accessors,
    }
    while len(b.buf) % 4:
        b.buf.append(0)
    doc["buffers"][0]["byteLength"] = len(b.buf)
    text = json.dumps(doc).encode()
    text += b" " * (-len(text) % 4)
    body = struct.pack("<II", len(text), 0x4E4F534A) + text + struct.pack("<II", len(b.buf), 0x004E4942) + bytes(b.buf)
    with open(path, "wb") as file:
        file.write(struct.pack("<4sII", b"glTF", 2, 12 + len(body)) + body)
