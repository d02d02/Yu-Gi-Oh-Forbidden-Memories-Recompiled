"""Vendored from upstream feat/model-replace tools/pc/model_import.py (the Hmd reader only),
so tools here work without that unmerged branch. Remove when it lands."""
import struct
import numpy as np

MAP_COORDINATES = 0x00800000
UNMAPPED = 0x80000000


def words(data: bytes) -> np.ndarray:
    return np.frombuffer(data[:len(data) // 4 * 4], dtype="<u4")


class Hmd:
    """The model data of a record: an HMD whose id word holds its size."""

    def __init__(self, data: bytes):
        self.data = bytes(data)
        w = self.w = words(self.data)
        self.size, _, self.header_section, self.block_count = (int(x) for x in w[:4])
        at = self.header_section
        count = int(w[at])
        at += 1
        self.headers: list[tuple[int, list[int]]] = []
        for _ in range(count):
            entries = int(w[at])
            self.headers.append((at, [int(x) for x in w[at + 1:at + 1 + entries]]))
            at += 1 + entries
        self.blocks = [int(x) for x in w[4:4 + self.block_count]]
        self.coordinates = None
        for block in range(self.block_count):
            for element in self.chain(block):
                if any(p["type"] & MAP_COORDINATES for p in element["prims"]):
                    self.coordinates = self.header(element["header"])[-1] & 0x7FFFFFFF
                    break
            if self.coordinates is not None:
                break
        if self.coordinates is None:
            raise SystemExit("the template has no coordinate section")
        self.units = []
        c = self.coordinates
        for i in range(int(w[c])):
            base = (c + 1 + i * 20) * 4
            m = np.array(struct.unpack_from("<9h", self.data, base + 4), float).reshape(3, 3) / 4096
            t = np.array(struct.unpack_from("<3i", self.data, base + 24), float)
            parent = struct.unpack_from("<I", self.data, base + 76)[0]
            self.units.append((m, t, (parent - (c + 1)) // 20 if parent else -1))

    def header(self, at: int) -> list[int]:
        for position, entries in self.headers:
            if position == at:
                return entries
        raise SystemExit(f"no primitive header at word {at}")

    def chain(self, block: int) -> list[dict]:
        out, p, w = [], self.blocks[block], self.w
        while p:
            following, header, count = int(w[p]), int(w[p + 1]), int(w[p + 2])
            c, prims = p + 3, []
            for _ in range(count & 0xFFFF):
                size = int(w[c + 1]) & 0xFFFF
                prims.append({"type": int(w[c]), "count": (int(w[c + 1]) >> 16) & 0x7FFF,
                              "args": [int(x) for x in w[c + 2:c + 1 + size]]})
                c += 1 + size
            out.append({"at": p, "header": header, "prims": prims})
            if following == 0xFFFFFFFF:
                break
            p = following & 0x7FFFFFFF
        return out

    def world(self) -> list[np.ndarray]:
        done: dict[int, np.ndarray] = {}

        def get(i: int) -> np.ndarray:
            if i not in done:
                m, t, parent = self.units[i]
                matrix = np.eye(4)
                matrix[:3, :3], matrix[:3, 3] = m, t
                done[i] = get(parent) @ matrix if parent >= 0 else matrix
            return done[i]
        return [get(i) for i in range(len(self.units))]

    def section(self, pointer: int) -> int:
        return (pointer & 0x7FFFFFFF) * 4

    def vector(self, pointer: int, index: int) -> np.ndarray:
        return np.array(struct.unpack_from("<3h", self.data, self.section(pointer) + index * 8), float)

    def bone_points(self) -> list[tuple[int, np.ndarray]]:
        """Every vertex the template draws, in world space, with its bone:
        the ordinary polygons' vertices and the shared-vertex runs."""
        world, out = self.world(), []
        for block in range(1, self.block_count - 1):
            unit = block - 1
            for element in self.chain(block):
                sections = self.header(element["header"])
                for prim in element["prims"]:
                    kind = prim["type"]
                    if kind >> 24 == 1 and kind & 0xFFFF == 0 and prim["args"]:
                        count, first = prim["args"][0], prim["args"][1]
                        for i in range(count):
                            out.append((unit, (world[unit] @ np.r_[self.vector(sections[1], first + i), 1])[:3]))
                    elif kind >> 24 == 0 and kind & 0xFFFF in (0x9, 0xD, 0x11, 0x15):
                        low = kind & 0xFFFF
                        quad, gouraud = low in (0x11, 0x15), low in (0xD, 0x15)
                        stride = {0x9: 0x14, 0xD: 0x18, 0x11: 0x18, 0x15: 0x1C}[low]
                        start = self.section(sections[0]) + prim["args"][0] * 4
                        for n in range(prim["count"]):
                            half = struct.unpack_from("<%dH" % (stride // 2), self.data, start + n * stride)
                            corners = 4 if quad else 3
                            vertices = ([half[7 + i * 2] for i in range(corners)] if gouraud
                                        else [half[(8 if quad else 7) + i] for i in range(corners)])
                            for v in vertices:
                                out.append((unit, (world[unit] @ np.r_[self.vector(sections[1], v), 1])[:3]))
        return out

    def shared_winding(self) -> int:
        """+1 when the template's shared triangles run v0, v1, v2 anticlockwise
        about their normal, -1 when clockwise: the order a new one keeps."""
        votes = 0
        # The runs' world positions are only known through their bones; the
        # ordinary polygons, which also cull, are enough to decide.
        world = self.world()
        for block in range(1, self.block_count - 1):
            unit = block - 1
            for element in self.chain(block):
                sections = self.header(element["header"])
                for prim in element["prims"]:
                    if prim["type"] >> 24 != 0 or prim["type"] & 0xFFFF != 0xD:
                        continue
                    start = self.section(sections[0]) + prim["args"][0] * 4
                    for n in range(prim["count"]):
                        half = struct.unpack_from("<12H", self.data, start + n * 0x18)
                        p = [world[unit][:3, :3] @ self.vector(sections[1], half[7 + i * 2]) for i in range(3)]
                        normal = sum(world[unit][:3, :3] @ self.vector(sections[2], half[6 + i * 2]) for i in range(3))
                        votes += 1 if np.dot(np.cross(p[1] - p[0], p[2] - p[0]), normal) > 0 else -1
        return 1 if votes >= 0 else -1
