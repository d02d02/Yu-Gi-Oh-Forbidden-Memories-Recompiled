"""Utilities for generating synthetic GLB files for the corpus tests.

Only the function :func:`write_glb` is required for the first test item. It builds a very
simple glTF binary (GLB) containing:

* An optional armature with the given ``bones``.
* One or more unskinned box meshes (if ``skinned`` is ``False``) or a single box mesh
  attached to the first bone (if ``skinned`` is ``True``).
* An optional ``Idle`` animation that rotates the first bone around the Z axis.

The implementation mirrors the style used in ``tests/synthetic_gltf.py`` so that the
``audit`` module can load the file and report joint information.
"""

from __future__ import annotations

import json
import tempfile
import math
import struct
from pathlib import Path
from typing import List, Tuple, Optional

# Load synthetic_gltf utilities from the tests directory without package import
import importlib.util, pathlib, sys
synthetic_path = pathlib.Path(__file__).resolve().parents[1] / "tests" / "synthetic_gltf.py"
spec = importlib.util.spec_from_file_location("synthetic_gltf", synthetic_path)
synthetic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(synthetic)
Builder = synthetic.Builder
box = synthetic.box
quat = synthetic.quat

# Type alias for clarity
Bone = Tuple[str, Optional[int], Tuple[float, float, float]]


def _build_hierarchy(bones: List[Bone]) -> Tuple[List[dict], List[int], List[Tuple[float, float, float]]]:
    # Existing hierarchy builder

    """Create node entries for the armature and bones.

    Returns a tuple ``(nodes, joint_indices, joint_world_positions)`` where ``nodes`` is a
    list that will become the ``nodes`` array of the glTF, ``joint_indices`` are the indices of
    the bone nodes (used for the skin), and ``joint_world_positions`` are the world‑space
    translations of each bone (required for inverse bind matrices).
    """
    # Start with the root armature node (index 0)
    nodes: List[dict] = [{"name": "Armature", "children": []}]
    joint_indices: List[int] = []
    world_positions: List[Tuple[float, float, float]] = []

    # Helper to add a bone node
    for idx, (name, parent_idx, pos) in enumerate(bones):
        node = {"name": name, "translation": list(pos), "children": []}
        node_index = len(nodes)
        nodes.append(node)
        joint_indices.append(node_index)
        world_positions.append(pos)
        # Attach to parent
        if parent_idx is None:
            # Direct child of armature
            nodes[0]["children"].append(node_index)
        else:
            # parent index refers to index in the bones list, not the node list yet
            parent_node_index = joint_indices[parent_idx]
            nodes[parent_node_index]["children"].append(node_index)
    return nodes, joint_indices, world_positions


def write_glb(
    path: str | Path,
    bones: List[Bone],
    *,
    skinned: bool = True,
    clips: bool = True,
    meshes: int = 1,
) -> None:
    """Write a synthetic GLB file.

    Parameters
    ----------
    path:
        Destination file path.
    bones:
        List of ``(name, parent_index_or_None, (x, y, z))`` defining the skeleton.
    skinned:
        If ``True`` a single box mesh is attached to the first bone and a skin is added.
        If ``False`` the meshes are unskinned nodes.
    clips:
        If ``True`` an ``Idle`` animation rotating the first bone is added.
    meshes:
        Number of unskinned box meshes to create when ``skinned`` is ``False``.
    """
    b = Builder()
    nodes, joint_indices, world_positions = _build_hierarchy(bones)

    # Build a simple box mesh (positions, normals, uvs, indices)
    positions, normals, uvs, indices = box(-0.1, 0.1, 0.0, 0.5, -0.1, 0.1)
    primitives = []
    # Joint/weight attributes are only needed for skinned meshes
    if skinned:
        # Simple skinning: each vertex influenced fully by the first joint
        jt = [[0, 0, 0, 0] for _ in positions]
        wt = [[1.0, 0, 0, 0] for _ in positions]
    else:
        jt = wt = None

    prim = {
        "attributes": {
            "POSITION": b.accessor(positions, "VEC3"),
            "NORMAL": b.accessor(normals, "VEC3"),
            "TEXCOORD_0": b.accessor(uvs, "VEC2"),
        },
        "indices": b.accessor(indices, "SCALAR", 5125),
        "material": 0,
    }
    if skinned:
        prim["attributes"]["JOINTS_0"] = b.accessor(jt, "VEC4", 5123)
        prim["attributes"]["WEIGHTS_0"] = b.accessor(wt, "VEC4")
    primitives.append(prim)

    mesh_node = {
        "mesh": 0,
    }
    if skinned:
        mesh_node["skin"] = 0
        # Add the mesh node as child of the first bone (or armature if no bones)
        target = joint_indices[0] if joint_indices else 0
        nodes[target]["children"] = nodes[target].get("children", []) + [len(nodes)]
    else:
        # Add unskinned mesh nodes as top‑level children of the armature
        for _ in range(meshes):
            nodes[0]["children"].append(len(nodes))
            nodes.append({"mesh": 0})
    nodes.append({"mesh": 0, **({"skin": 0} if skinned else {})})  # placeholder for actual mesh node
    # Replace placeholder with our prepared mesh node (the index is now len(nodes)-1)
    nodes[-1] = mesh_node

    # Build skin if needed
    skin = None
    if skinned:
        # Inverse bind matrices: simple translation to origin
        ibm = []
        for pos in world_positions:
            x, y, z = pos
            ibm.append([1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, -x, -y, -z, 1])
        skin = {"joints": joint_indices, "inverseBindMatrices": b.accessor(ibm, "MAT4")}

    # Animation (Idle) – rotate first bone around Z axis
    animations = []
    if clips and joint_indices:
        def channel(node_idx, path, times, values, interpolation="LINEAR"):
            kind = "VEC4" if path == "rotation" else "VEC3"
            return {
                "input": b.accessor(times, "SCALAR"),
                "output": b.accessor(values, kind),
                "interpolation": interpolation,
            }, node_idx, path

        def animation(name, channels):
            samplers = []
            chans = []
            for sampler, node, path in channels:
                samplers.append(sampler)
                chans.append({"sampler": len(samplers) - 1, "target": {"node": node, "path": path}})
            return {"name": name, "samplers": samplers, "channels": chans}

        z = (0, 0, 1)
        idle = animation(
            "Idle",
            [channel(joint_indices[0], "rotation", [0, 1], [quat(z, 0), quat(z, 3)])],
        )
        animations.append(idle)

    # Assemble glTF document
    doc = {
        "asset": {"version": "2.0"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": nodes,
        "meshes": [{"primitives": primitives}],
        "materials": [{"name": "mat", "pbrMetallicRoughness": {"baseColorFactor": [1, 1, 1, 1]}}],
        "buffers": [{"byteLength": 0}],
        "bufferViews": b.views,
        "accessors": b.accessors,
    }
    if skin:
        doc["skins"] = [skin]
    if animations:
        doc["animations"] = animations

    # Pad buffer to 4‑byte alignment and finalize binary chunk
    while len(b.buf) % 4:
        b.buf.append(0)
    doc["buffers"][0]["byteLength"] = len(b.buf)
    json_text = json.dumps(doc).encode()
    json_text += b" " * (-len(json_text) % 4)
    body = struct.pack("<II", len(json_text), 0x4E4F534A) + json_text + struct.pack("<II", len(b.buf), 0x004E4942) + bytes(b.buf)
    with open(path, "wb") as f:
        f.write(struct.pack("<4sII", b"glTF", 2, 12 + len(body)) + body)

# Humanoid bone definitions for categories C1 and C2

def humanoid_bones() -> List[Bone]:
    """Return a list of bones covering most humanoid slots.
    Includes pelvis, spine chain, head, arms, hands, legs, and feet.
    """
    # (name, parent_index_or_None, (x, y, z))
    # Simple hierarchy: pelvis root
    bones = [
        ("pelvis", None, (0, 1, 0)),
        ("spine_01", 0, (0, 1.2, 0)),
        ("spine_02", 1, (0, 1.4, 0)),
        ("neck_01", 2, (0, 1.6, 0)),
        ("head", 3, (0, 1.8, 0)),
        ("clavicle_l", 2, (-0.1, 1.5, 0)),
        ("upperarm_l", 5, (-0.3, 1.5, 0)),
        ("lowerarm_l", 6, (-0.5, 1.5, 0)),
        ("hand_l", 7, (-0.6, 1.5, 0)),
        ("clavicle_r", 2, (0.1, 1.5, 0)),
        ("upperarm_r", 9, (0.3, 1.5, 0)),
        ("lowerarm_r", 10, (0.5, 1.5, 0)),
        ("hand_r", 11, (0.6, 1.5, 0)),
        ("thigh_l", 0, (-0.2, 0.8, 0)),
        ("calf_l", 13, (-0.2, 0.4, 0)),
        ("foot_l", 14, (-0.2, 0.0, 0)),
        ("thigh_r", 0, (0.2, 0.8, 0)),
        ("calf_r", 16, (0.2, 0.4, 0)),
        ("foot_r", 17, (0.2, 0.0, 0)),
    ]
    return bones

def _drop_bones(bones, names):
    """Remove the named bones and re-index the parents (a plain filter would leave parent indices pointing at the wrong bones)."""
    keep = [i for i, b in enumerate(bones) if b[0] not in names]
    new = {old: n for n, old in enumerate(keep)}
    return [(bones[i][0], None if bones[i][1] is None else new[bones[i][1]], bones[i][2]) for i in keep]


def build(category: str, path: str | Path) -> None:
    """Build a synthetic glb for the given category.
    C1: full humanoid; C2: humanoid with one missing slot (hand_r) to trigger C2.
    """
    """Build a synthetic glb for the given category.
    C1: full humanoid; C2: humanoid with one missing slot (hand_r) to trigger C2.
    """
    if category == "C1":
        bones = humanoid_bones()
    elif category == "C2":
        # Remove the right hand and right foot bones to reduce slot match
        bones = _drop_bones(humanoid_bones(), ("hand_r", "foot_r"))

    elif category == "C3":
        bones = []
        # Unskinned tall box using default dimensions (tall)
        write_glb(path, bones, skinned=False, clips=False, meshes=1)
    elif category == "C8":
        # Existing C8 handling unchanged

        # Unskinned wide box: custom dimensions
        bones = []
        # Build custom glb with a wide box geometry
        b = Builder()
        # wide box: x from -0.5 to 0.5, y 0.0 to 0.2, z -0.1 to 0.1
        positions, normals, uvs, indices = box(-0.5, 0.5, 0.0, 0.2, -0.1, 0.1)
        prim = {
            "attributes": {
                "POSITION": b.accessor(positions, "VEC3"),
                "NORMAL": b.accessor(normals, "VEC3"),
                "TEXCOORD_0": b.accessor(uvs, "VEC2"),
            },
            "indices": b.accessor(indices, "SCALAR", 5125),
            "material": 0,
        }
        # Nodes: armature placeholder with one child mesh node
        nodes = [{"name": "Armature", "children": [1]}, {"mesh": 0}]
        doc = {
            "asset": {"version": "2.0"},
            "scene": 0,
            "scenes": [{"nodes": [0]}],
            "nodes": nodes,
            "meshes": [{"primitives": [prim]}],
            "materials": [{"name": "mat", "pbrMetallicRoughness": {"baseColorFactor": [1, 1, 1, 1]}}],
            "buffers": [{"byteLength": 0}],
            "bufferViews": b.views,
            "accessors": b.accessors,
        }
        # Pad buffer and finalize binary GLB as in write_glb
        while len(b.buf) % 4:
            b.buf.append(0)
        doc["buffers"][0]["byteLength"] = len(b.buf)
        json_text = json.dumps(doc).encode()
        json_text += b" " * (-len(json_text) % 4)
        body = struct.pack("<II", len(json_text), 0x4E4F534A) + json_text + struct.pack("<II", len(b.buf), 0x004E4942) + bytes(b.buf)
        with open(path, "wb") as f:
            f.write(struct.pack("<4sII", b"glTF", 2, 12 + len(body)) + body)
    elif category == "C4":
        # Quadruped: four limbs, spine, head, tail, no humanoid slot names except spine/head
        bones = [
            ("spine_01", None, (0, 1.2, 0)),
            ("head", 0, (0, 1.6, 0)),
            # front left limb
            ("leg_fl", None, (-0.2, 0.8, 0.2)),
            ("leg_fl_lower", 2, (-0.2, 0.4, 0.2)),
            # front right limb
            ("leg_fr", None, (0.2, 0.8, 0.2)),
            ("leg_fr_lower", 4, (0.2, 0.4, 0.2)),
            # back left limb
            ("leg_bl", None, (-0.2, 0.8, -0.2)),
            ("leg_bl_lower", 6, (-0.2, 0.4, -0.2)),
            # back right limb
            ("leg_br", None, (0.2, 0.8, -0.2)),
            ("leg_br_lower", 8, (0.2, 0.4, -0.2)),
            ("tail_01", 0, (0, 1.0, -0.1)),
        ]
        write_glb(path, bones, skinned=True, clips=False, meshes=1)
    elif category == "C5":
        # Winged creature: at least two wing bones, plus some body bone
        bones = [
            ("spine_01", None, (0, 1.2, 0)),
            ("wing_l", 0, (-0.3, 1.4, 0)),
            ("wing_r", 0, (0.3, 1.4, 0)),
        ]
        write_glb(path, bones, skinned=True, clips=False, meshes=1)
    elif category == "C6":
        # Legless: spine chain and head, no leg/foot bones
        bones = [
            ("spine_01", None, (0, 1.2, 0)),
            ("spine_02", 0, (0, 1.4, 0)),
            ("head", 1, (0, 1.6, 0)),
            ("tail_01", 0, (0, 1.0, -0.1)),
        ]
        write_glb(path, bones, skinned=True, clips=False, meshes=1)
    elif category == "C7":
        # Rigid multi-part: several unskinned mesh nodes, not tall
        bones = []
        # Build custom glb with three unskinned box meshes (short height)
        b = Builder()
        # short box: x -0.5..0.5, y 0.0..0.2, z -0.1..0.1
        positions, normals, uvs, indices = box(-0.5, 0.5, 0.0, 0.2, -0.1, 0.1)
        prim = {
            "attributes": {
                "POSITION": b.accessor(positions, "VEC3"),
                "NORMAL": b.accessor(normals, "VEC3"),
                "TEXCOORD_0": b.accessor(uvs, "VEC2"),
            },
            "indices": b.accessor(indices, "SCALAR", 5125),
            "material": 0,
        }
        # Nodes: armature placeholder with three child mesh nodes
        nodes = [{"name": "Armature", "children": []}]
        mesh_node_indices = []
        for _ in range(3):
            mesh_idx = len(nodes)
            mesh_node_indices.append(mesh_idx)
            nodes.append({"mesh": 0})
            nodes[0]["children"].append(mesh_idx)
        doc = {
            "asset": {"version": "2.0"},
            "scene": 0,
            "scenes": [{"nodes": [0]}],
            "nodes": nodes,
            "meshes": [{"primitives": [prim]}],
            "materials": [{"name": "mat", "pbrMetallicRoughness": {"baseColorFactor": [1, 1, 1, 1]}}],
            "buffers": [{"byteLength": 0}],
            "bufferViews": b.views,
            "accessors": b.accessors,
        }
        while len(b.buf) % 4:
            b.buf.append(0)
        doc["buffers"][0]["byteLength"] = len(b.buf)
        json_text = json.dumps(doc).encode()
        json_text += b" " * (-len(json_text) % 4)
        body = struct.pack("<II", len(json_text), 0x4E4F534A) + json_text + struct.pack("<II", len(b.buf), 0x004E4942) + bytes(b.buf)
        with open(path, "wb") as f:
            f.write(struct.pack("<4sII", b"glTF", 2, 12 + len(body)) + body)
    else:
        raise NotImplementedError(f"build not implemented for {category}")
    if category in ("C1", "C2"):
        write_glb(path, bones, skinned=True, clips=True, meshes=1)
EXPECTED_DETECTED = {
    "C1": "C1",
    "C2": "C2",
    "C3": "C3",
    "C4": "C4",
    "C5": "C5",
    "C6": "C6",
    "C7": "C8",
    "C8": "C8",
}

import sys
from pathlib import Path
import json
import argparse
# Ensure local imports work when run as script
module_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(module_dir))
import audit



def golden_of(path: str | Path) -> dict:
    """Return a dict with category and simplified findings for the given GLB file.
    The findings are a mapping stage -> sorted list of "id:level" strings.
    """
    path = Path(path)
    model = audit.load_model(str(path))
    category = audit.detect_category(model)["category"]
    results = audit.audit_all(str(path))
    findings = {}
    for stage, data in results.items():
        items = [f"{f['id']}:{f['level']}" for f in data.get('findings', [])]
        findings[stage] = sorted(items)
    return {"category": category, "findings": findings}


def run_corpus(tmpdir: str | Path, golden_path: str | Path) -> list:
    """Build all categories into tmpdir, compare with golden file, return list of diff strings.
    Empty list means identical.
    """
    tmpdir = Path(tmpdir)
    golden_path = Path(golden_path)
    # Ensure tmpdir exists
    tmpdir.mkdir(parents=True, exist_ok=True)
    diff = []
    # Load existing golden if present
    try:
        with open(golden_path, "r", encoding="utf-8") as f:
            golden = json.load(f)
    except FileNotFoundError:
        golden = {}
    # Build and compare each category
    for cat in ["C1","C2","C3","C4","C5","C6","C7","C8"]:
        out_path = tmpdir / f"{cat.lower()}.glb"
        build(cat, out_path)
        cur = golden_of(out_path)
        gold = golden.get(cat, {})
        if cur != gold:
            diff.append(f"{cat} differs")
    return diff


def _cli():
    parser = argparse.ArgumentParser(description="Corpus utilities")
    parser.add_argument("--check", action="store_true", help="Check against golden and exit with code")
    parser.add_argument("--update", action="store_true", help="Update golden file with current corpus")
    args = parser.parse_args()
    # Define paths
    ref_dir = Path(__file__).resolve().parent / "reference"
    ref_dir.mkdir(parents=True, exist_ok=True)
    golden_path = ref_dir / "corpus_golden.json"
    tmpdir = Path(tempfile.gettempdir()) / "ygofm_corpus_tmp"
    diffs = run_corpus(tmpdir, golden_path)
    if args.update:
        # Write new golden
        new_golden = {}
        for cat in ["C1","C2","C3","C4","C5","C6","C7","C8"]:
            out_path = tmpdir / f"{cat.lower()}.glb"
            new_golden[cat] = golden_of(out_path)
        with open(golden_path, "w", encoding="utf-8") as f:
            json.dump(new_golden, f, indent=1, sort_keys=True)
            f.write("\n")
        return
    if args.check:
        if diffs:
            for d in diffs:
                print(d)
            exit(1)
        else:
            exit(0)

if __name__ == "__main__":
    _cli()



