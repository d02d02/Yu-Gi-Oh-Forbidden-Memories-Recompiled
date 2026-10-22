"""The native model formats as the game reads them, in plain Python (no numpy, no Pillow), for the converter and the checker.

Mirrors src/pc/render/native_format.c (the HDM4 file), src/pc/render/native_registry.c (manifest entries and model.json)
and src/pc/platform/paths.c (Paths_Contained): what the game refuses, these refuse with the same reason."""
import json
import struct
import zlib
from pathlib import Path

MAX_BONES = 128
MAX_CLIPS = 16
MAX_SIDE = 16384          # NATIVE_FORMAT_MAX_SIDE
MAX_STRIKES = 4           # NATIVE_MAX_STRIKES
REGISTRY_MAX = 64         # NATIVE_REGISTRY_MAX: entries in all the mods
REGISTRY_CARDS = 64       # NATIVE_REGISTRY_CARDS: cards per entry
TEXTURE_MAX = 2048        # MEMORIES_NATIVE_TEXTURE_MAX default
BUDGET_MB = 512           # MEMORIES_NATIVE_BUDGET_MB default
FPS = 30.0

ACTS = ("idle", "enter", "attack", "hit", "destroyed", "win", "guard")   # NativeAct, in order
# The runtime's clip names for an act model.json does not map (NativeAnim_ActClip).
DEFAULT_CLIPS = {"idle": "Sword_Idle", "enter": "Idle_Loop", "attack": "Sword_Attack", "hit": "Hit_Chest", "destroyed": "Death01",
                 "win": "Sword_Idle", "guard": "Sword_Idle"}
PACKAGE_KEYS = ("format", "name", "model", "textures", "clips", "strike", "scale", "look", "author", "license", "source", "converter")
TEXTURE_KEYS = ("base", "normal", "metal_roughness")
LOOK_KEYS = ("camera_near", "camera_keep", "camera_scale", "ambient", "light_gain", "normal_strength", "highlight", "flip_green")


def paths_contained(relative):
    """Paths_Contained: a relative path that stays inside its folder (no "..", ".", empty parts, backslashes, drives)."""
    if not isinstance(relative, str) or not relative or relative[0] in "/\\" or "\\" in relative:
        return False
    if len(relative) > 1 and relative[1] == ":":
        return False
    return all(part not in ("", ".", "..") for part in relative.split("/"))


class Hdm4Error(ValueError):
    pass


def parse_hdm4(data):
    """The HDM4 file checked whole, as NativeFormat_ParseHdm4: a dict of its counts, clips and bind-pose extent,
    or Hdm4Error with the game's reason."""
    if len(data) < 32 or len(data) % 4:
        raise Hdm4Error("too short, or not whole 4-byte words")
    if data[:4] in (b"HDM1", b"HDM2", b"HDM3"):
        raise Hdm4Error("an HDM1-3 file: those part-posed formats are no longer drawn (native_convert.py makes an HDM4)")
    if data[:4] != b"HDM4":
        raise Hdm4Error("not an HDM4 file")
    words = len(data) // 4
    vertices, index_count, bones, tex_w, tex_h, clip_count, flags = struct.unpack_from("<7I", data, 4)
    if not 1 <= bones <= MAX_BONES:
        raise Hdm4Error(f"{bones} bones (it takes 1 to {MAX_BONES})")
    if vertices < 1:
        raise Hdm4Error("no vertices")
    if index_count < 3 or index_count % 3:
        raise Hdm4Error(f"{index_count} indices (triangles: a multiple of 3)")
    if clip_count > MAX_CLIPS:
        raise Hdm4Error(f"{clip_count} animation clips (at most {MAX_CLIPS})")
    if flags & ~3:
        raise Hdm4Error(f"unknown flags 0x{flags:x}")

    def side_ok(side):
        return 1 <= side <= MAX_SIDE

    if not side_ok(tex_w) or not side_ok(tex_h):
        raise Hdm4Error(f"texture {tex_w}x{tex_h} (each side 1 to {MAX_SIDE})")
    at = 8

    def take(count, what):
        nonlocal at
        if at > words or count > words - at:
            raise Hdm4Error(f"cut short in {what}")
        start = at
        at += count
        return start

    bone_at = take(bones * 16, "the bones")
    vertex_at = take(vertices * 13, "the vertices")
    index_at = take(index_count, "the triangles")
    take(tex_w * tex_h, "the texture")
    maps = {}
    for bit, name in ((1, "normal map"), (2, "metal/roughness map")):
        if not flags & bit:
            continue
        start = take(2, f"the {name}")
        mw, mh = struct.unpack_from("<2I", data, start * 4)
        if not side_ok(mw) or not side_ok(mh):
            raise Hdm4Error(f"{name} {mw}x{mh} (each side 1 to {MAX_SIDE})")
        take(mw * mh, f"the {name}")
        maps[name] = (mw, mh)
    clips = []
    for k in range(clip_count):
        start = take(12, f"clip {k}")
        raw = data[start * 4:start * 4 + 32]
        name = raw[:31].split(b"\0", 1)[0].decode("utf-8", "replace")
        frames, fps = struct.unpack_from("<If", data, start * 4 + 32)
        if frames < 1:
            raise Hdm4Error(f"clip {name} has no frames")
        if not 0.0 < fps <= 240.0:
            raise Hdm4Error(f"clip {name}: frame rate out of range")
        offset = take(frames * bones * 7, f"clip {name}")
        clips.append({"name": name, "frames": frames, "fps": fps, "offset": offset})
    if at != words:
        raise Hdm4Error(f"{words - at} words left over after the last clip")
    parents = [struct.unpack_from("<i", data, (bone_at + b * 16) * 4)[0] for b in range(bones)]
    for b, parent in enumerate(parents):
        if parent < -1 or parent >= bones or parent == b:
            raise Hdm4Error(f"bone {b} has parent {parent}")
    for b in range(bones):
        up, steps = b, 0
        while up >= 0:
            steps += 1
            if steps > bones:
                raise Hdm4Error(f"bone {b} is its own ancestor")
            up = parents[up]
    low = [float("inf")] * 3
    high = [float("-inf")] * 3
    for k in range(vertices):
        base = (vertex_at + k * 13) * 4
        position = struct.unpack_from("<3f", data, base)
        joints = struct.unpack_from("<I", data, base + 32)[0]
        for j in range(4):
            if (joints >> (8 * j)) & 255 >= bones:
                raise Hdm4Error(f"vertex {k} names joint {(joints >> (8 * j)) & 255} of {bones}")
        for c in range(3):
            low[c] = min(low[c], position[c])
            high[c] = max(high[c], position[c])
    indices = struct.unpack_from(f"<{index_count}I", data, index_at * 4)
    for k, index in enumerate(indices):
        if index >= vertices:
            raise Hdm4Error(f"triangle corner {k} is vertex {index} of {vertices}")
    return {"vertices": vertices, "triangles": index_count // 3, "bones": bones, "texture": (tex_w, tex_h), "maps": maps,
            "clips": clips, "low": low, "high": high, "bytes": len(data), "parents": parents, "vertex_offset": vertex_at}


def png_size(path):
    """(width, height) of a PNG whose chunks are whole and check out, else ValueError with why."""
    data = Path(path).read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    at, size, ended = 8, None, False
    while at + 12 <= len(data):
        length, kind = struct.unpack_from(">I4s", data, at)
        body = data[at + 8:at + 8 + length]
        if len(body) != length or at + 12 + length > len(data):
            raise ValueError("cut short")
        crc = struct.unpack_from(">I", data, at + 8 + length)[0]
        if zlib.crc32(kind + body) & 0xffffffff != crc:
            raise ValueError(f"a damaged {kind.decode('latin-1')} chunk")
        if kind == b"IHDR":
            size = struct.unpack(">II", body[:8])
        if kind == b"IEND":
            ended = True
            break
        at += 12 + length
    if not size or not ended:
        raise ValueError("cut short")
    return size


def _whole_only(text):
    raise ValueError(f"a number must be whole (the game's JSON reader takes no fraction or exponent): {text}")


def read_json(path):
    """A JSON file as the game reads it (src/pc/mods/json.c): numbers are whole, anywhere in the file."""
    with open(path, encoding="utf-8") as file:
        return json.load(file, parse_float=_whole_only)
