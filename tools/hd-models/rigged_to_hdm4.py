#!/usr/bin/env python3
"""A RIGGED glTF (Quaternius UAL, Mixamo...) -> a model.hdm of kind HDM4: the model keeps its OWN skeleton and clips.

    rigged_to_hdm4.py MODEL.glb OUT.hdm --card 364 [--clips Sword_Attack,Sword_Idle,...|all] [--keep-root-motion] [--texture T.png]

Unlike HDM3 (game rotations on the model's joints) nothing is retargeted: the game only gives the root pose, the state and the timing.
The model is moved into the disc model's space (same similarity as rigged_to_hdm.py: legs fitted to BLS's, hips on BLS's pelvis,
glTF y-up -> disc axes) so the game's root matrix places it. Every clip is baked at 30 fps as LOCAL translation + rotation per bone
(already in disc space); the game side does the forward kinematics.
File (little endian, 4-byte words):
  "HDM4", nverts, nindices, nbones, tex_w, tex_h, nclips, 0
  bones   : nbones x 16 words: i32 parent (-1 = none), f32 ibm[12] (3x4 row major: disc-space model -> bone), 3 pad
  vertices: nverts x 13 words: f32 pos[3], nrm[3], uv[2], u32 joints (4 x u8), f32 weights[4]
  indices : nindices x u32
  texture : tex_w x tex_h RGBA8, then (header word 7: bit0 normal map, bit1 metal-roughness map) each u32 w, u32 h, RGBA8
  clips   : per clip 12 words (char name[32], u32 nframes, f32 fps, 2 pad) then nframes x nbones x 7 f32 (t[3], q[4] xyzw)
In-place clips: the pelvis' horizontal travel is removed (the game's root carries the motion) unless --keep-root-motion."""
import argparse
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE / "vendor"))
import gltf_to_hdm as base  # noqa: E402
import hmd as hmdlib  # noqa: E402
import model_record  # noqa: E402

SCALE = base.SCALE
FLIP = np.diag([1.0, -1.0, -1.0])
FPS = 30.0


def quat_to_mat(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def mat_to_quat(m):
    t = np.trace(m)
    if t > 0:
        s = np.sqrt(t + 1.0) * 2; q = [(m[2, 1] - m[1, 2]) / s, (m[0, 2] - m[2, 0]) / s, (m[1, 0] - m[0, 1]) / s, 0.25 * s]
    elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        s = np.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2; q = [0.25 * s, (m[0, 1] + m[1, 0]) / s, (m[0, 2] + m[2, 0]) / s, (m[2, 1] - m[1, 2]) / s]
    elif m[1, 1] > m[2, 2]:
        s = np.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2; q = [(m[0, 1] + m[1, 0]) / s, 0.25 * s, (m[1, 2] + m[2, 1]) / s, (m[0, 2] - m[2, 0]) / s]
    else:
        s = np.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2; q = [(m[0, 2] + m[2, 0]) / s, (m[1, 2] + m[2, 1]) / s, 0.25 * s, (m[1, 0] - m[0, 1]) / s]
    q = np.array(q); return q / np.linalg.norm(q)


def slerp(a, b, t):
    d = float(a @ b)
    if d < 0: b = -b; d = -d
    if d > 0.9995:
        r = a + (b - a) * t; return r / np.linalg.norm(r)
    th = np.arccos(d); return (np.sin((1 - t) * th) * a + np.sin(t * th) * b) / np.sin(th)


def sample_channel(times, values, path, t):
    i = int(np.searchsorted(times, t, side="right") - 1)
    if i < 0: return values[0]
    if i >= len(times) - 1: return values[-1]
    f = (t - times[i]) / max(times[i + 1] - times[i], 1e-9)
    if path == "rotation": return slerp(values[i], values[i + 1], f)
    return values[i] * (1 - f) + values[i + 1] * f


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("gltf", type=Path); ap.add_argument("out", type=Path); ap.add_argument("--card", type=int, required=True)
    ap.add_argument("--disc", type=Path, default=base.DEFAULT_DISC); ap.add_argument("--texture", type=Path, default=None)
    ap.add_argument("--clips", default="Sword_Attack,Sword_Idle,Hit_Chest,Death01,Idle_Loop")
    ap.add_argument("--clips-from", type=Path, default=None, help="take the clips from this glb (bone names matched; default: the model's own)")
    ap.add_argument("--wing-follow", type=float, default=0.8, help="derived bones wing_a_*/wing_b_* follow the arm's motion relative to its parent by this fraction")
    ap.add_argument("--no-pbr", action="store_true", help="do not write the normal / metal-roughness maps")
    ap.add_argument("--keep-root-motion", action="store_true"); ap.add_argument("--height", type=float, default=1.0)
    a = ap.parse_args()

    record = model_record.read_record(a.disc, a.card); h = hmdlib.Hmd(record[:96 * base.SECTOR]); world = h.world()
    tb = np.array([w[:3, 3] for w in world]); tbg = (tb @ FLIP.T) * SCALE

    g = base.Gltf(a.gltf); doc = g.doc; nodes = doc["nodes"]
    skin = doc["skins"][0]; jn = skin["joints"]; nb = len(jn)
    if nb > 128: sys.exit("more than 128 bones")
    ibm = g.accessor(skin["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
    node_parent = {}
    for i, n in enumerate(nodes):
        for c in n.get("children", []): node_parent[c] = i
    jindex = {n: i for i, n in enumerate(jn)}
    bone_parent = []
    for n in jn:
        p = node_parent.get(n, None)
        while p is not None and p not in jindex: p = node_parent.get(p, None)
        bone_parent.append(jindex[p] if p is not None else -1)
    names = [nodes[n].get("name", "") for n in jn]

    def rest_trs(n):
        nd = nodes[n]
        if "matrix" in nd:
            m = np.array(nd["matrix"], float).reshape(4, 4).T
            lin = m[:3, :3]; s = np.linalg.norm(lin, axis=0)
            return m[:3, 3].copy(), mat_to_quat(lin / s), s
        return (np.array(nd.get("translation", [0, 0, 0]), float), np.array(nd.get("rotation", [0, 0, 0, 1]), float), np.array(nd.get("scale", [1, 1, 1]), float))

    def local_matrix(t, q, s):
        m = np.eye(4); m[:3, :3] = quat_to_mat(q / np.linalg.norm(q)) * s; m[:3, 3] = t; return m

    def world_of(trs):                       # trs: node index -> (t, q, s); returns node index -> 4x4 world
        cache = {}
        def w(i):
            if i not in cache:
                m = local_matrix(*trs[i]); cache[i] = w(node_parent[i]) @ m if i in node_parent else m
            return cache[i]
        return w

    rest = {i: rest_trs(i) for i in range(len(nodes))}
    wrest = world_of(rest)
    dev = max(np.abs(wrest(n) @ ibm[k] - np.eye(4)).max() for k, n in enumerate(jn))
    print(f"{nb} bones; rest world x inverse bind deviates from identity by at most {dev:.4f}")
    bind_pos = np.array([np.linalg.inv(ibm[k])[:3, 3] for k in range(nb)])

    # the mesh (skinned primitives only), in the bind space
    P_, N_, U_, J_, W_, I_ = [], [], [], [], [], []
    off = 0
    first_tex = None; first_color = None; normal_img = None; mr_img = None
    for node in nodes:
        if "mesh" not in node: continue
        for prim in doc["meshes"][node["mesh"]]["primitives"]:
            at = prim["attributes"]
            if "JOINTS_0" not in at: continue
            p = g.accessor(at["POSITION"]); n = g.accessor(at["NORMAL"]) if "NORMAL" in at else np.zeros_like(p)
            uv = g.accessor(at["TEXCOORD_0"]) if "TEXCOORD_0" in at else np.zeros((len(p), 2))
            P_.append(p); N_.append(n); U_.append(uv); J_.append(g.accessor(at["JOINTS_0"]).astype(int)); W_.append(g.accessor(at["WEIGHTS_0"]))
            I_.append(g.accessor(prim["indices"]).astype(np.int64).reshape(-1) + off if "indices" in prim else np.arange(len(p)) + off); off += len(p)
            if "material" in prim and first_tex is None and first_color is None:
                pbr = doc["materials"][prim["material"]].get("pbrMetallicRoughness", {})
                tx = pbr.get("baseColorTexture")
                mat = doc["materials"][prim["material"]]
                uv1_same = "TEXCOORD_1" in at and np.allclose(g.accessor(at["TEXCOORD_1"]), g.accessor(at["TEXCOORD_0"]))   # the maps may name UV set 1: fine when it equals set 0
                ok_uv = lambda ti: ti.get("texCoord", 0) == 0 or uv1_same
                if mat.get("normalTexture") and ok_uv(mat["normalTexture"]) and not a.no_pbr: normal_img = g.image(mat["normalTexture"]["index"])
                if pbr.get("metallicRoughnessTexture") and ok_uv(pbr["metallicRoughnessTexture"]) and not a.no_pbr: mr_img = g.image(pbr["metallicRoughnessTexture"]["index"])
                if tx: first_tex = g.image(tx["index"])
                else: first_color = pbr.get("baseColorFactor", [0.8, 0.8, 0.82, 1.0])
    pos = np.vstack(P_); nrm = np.vstack(N_); uvs = np.vstack(U_); jj = np.vstack(J_); ww = np.vstack(W_); idx = np.concatenate(I_)
    ww = ww / np.maximum(ww.sum(1, keepdims=True), 1e-9)
    print(f"{len(pos)} vertices, {len(idx) // 3} triangles")

    # the similarity glTF (rest world) -> disc space: legs fitted to the disc's, hips on its pelvis, y-up -> disc axes
    def key(name): return name.lower()
    by_name = {key(n): i for i, n in enumerate(names)}
    hips = by_name["pelvis"]; thigh = [i for i, n in enumerate(names) if n.lower().startswith("thigh_")]; foot = [i for i, n in enumerate(names) if n.lower().startswith("foot_")]
    right = lambda lst: min(lst, key=lambda i: bind_pos[i][0])
    hip_p, ankle_p = bind_pos[right(thigh)], bind_pos[right(foot)]
    s_fit = np.linalg.norm(tbg[14] - tbg[16]) / np.linalg.norm(hip_p - ankle_p) * a.height
    origin = bind_pos[hips]
    A = FLIP * (s_fit / SCALE); b = (FLIP @ (-origin * s_fit)) / SCALE   # hips at the ORIGIN: the game's root matrix carries the position (the disc's own coordinates include the root's world position)
    if a.height != 1.0:   # a smaller (or bigger) model keeps its soles on the same ground: the hips (origin) move down by the sole height lost
        sole = float((pos @ A.T + b)[:, 1].max()); b = b + np.array([0.0, sole * (1.0 - a.height) / a.height, 0.0])
        print(f"height x{a.height}: hips moved {b[1] - 0:.1f} disc units so the feet stay on the ground")
    T = np.eye(4); T[:3, :3] = A; T[:3, 3] = b
    Ti = np.linalg.inv(T)
    print(f"scale x{s_fit:.3f}; model {(pos[:, 1].max() - pos[:, 1].min()) * s_fit:.2f} m tall")

    ibm_d = np.array([(T @ ibm[k] @ Ti) for k in range(nb)])
    pos_d = pos @ A.T + b; nrm_d = nrm @ (FLIP).T; nrm_d /= np.maximum(np.linalg.norm(nrm_d, axis=1, keepdims=True), 1e-9)

    # texture
    if a.texture: tex = Image.open(a.texture).convert("RGBA")
    elif first_tex is not None: tex = first_tex.convert("RGBA")
    else:
        c = [200, 200, 205]; tex = Image.new("RGBA", (16, 16), tuple(c[:3]) + (255,))

    # clips
    gc = base.Gltf(a.clips_from) if a.clips_from else g; cdoc = gc.doc
    name_to_node = {nodes[n].get("name", ""): n for n in range(len(nodes))}
    cnode = {i: name_to_node.get(cn.get("name", "")) for i, cn in enumerate(cdoc["nodes"])}
    DERIVED = [(f"wing_{x}_{sd}", par, src) for sd in "lr" for x, par, src in (("a", "spine_03", f"upperarm_{sd}"), ("b", f"wing_a_{sd}", f"lowerarm_{sd}"))]
    DERIVED = [(w, par, src) for w, par, src in DERIVED if w in name_to_node]
    if DERIVED: print("derived bones (follow the arm x%.2f):" % a.wing_follow, [d[0] for d in DERIVED])
    anims = {an["name"]: an for an in cdoc.get("animations", [])}
    want = list(anims) if a.clips == "all" else [c for c in a.clips.split(",") if c]
    if len(want) > 16: sys.exit(f"{len(want)} clips: the game takes at most 16 (pick them with --clips)")
    for c in want:
        if c not in anims: sys.exit(f"no clip {c}; has {sorted(anims)}")
    clip_blobs = []
    for cname in want:
        an = anims[cname]; chans = {}
        dur = 0.0
        for ch in an["channels"]:
            tgt = ch["target"]; smp = an["samplers"][ch["sampler"]]
            times = gc.accessor(smp["input"]).reshape(-1); vals = gc.accessor(smp["output"])
            mine = cnode.get(tgt["node"])
            if mine is None: continue
            chans[(mine, tgt["path"])] = (times, vals); dur = max(dur, float(times[-1]))
        nf = int(round(dur * FPS)) + 1
        data = np.zeros((nf, nb, 7), np.float32)
        p0 = None
        for f in range(nf):
            t = min(f / FPS, dur); trs = {}
            for i in range(len(nodes)):
                tt, qq, ss = rest[i]
                for path in ("translation", "rotation", "scale"):
                    c = chans.get((i, path))
                    if c is not None:
                        v = sample_channel(c[0], c[1], path, t)
                        if path == "translation": tt = v
                        elif path == "rotation": qq = v
                        else: ss = v
                trs[i] = (tt, qq, ss)
            wf = world_of(trs)
            for wname, pname, sname in DERIVED:      # extra bones that copy the arm's motion (relative to its parent) at a fraction
                wn, pn, sn = name_to_node[wname], name_to_node[pname], name_to_node[sname]
                spn = node_parent[sn]
                def rw(x, trs_=trs): return world_of(trs_)(x)[:3, :3] / np.linalg.norm(world_of(trs_)(x)[:3, 0])
                def rrest(x): return wrest(x)[:3, :3] / np.linalg.norm(wrest(x)[:3, 0])
                dw = (rw(sn) @ rrest(sn).T) @ np.linalg.inv(rw(spn) @ rrest(spn).T)      # the source's rotation beyond its parent's, world axes
                q = mat_to_quat(dw); q = q if q[3] >= 0 else -q
                qk = slerp(np.array([0, 0, 0, 1.0]), q, a.wing_follow); dk = quat_to_mat(qk)
                rpar = rw(pn); rl = quat_to_mat(rest[wn][1] / np.linalg.norm(rest[wn][1]))
                newl = np.linalg.inv(rpar) @ dk @ rpar @ rl
                trs[wn] = (rest[wn][0], mat_to_quat(newl), rest[wn][2])
            wf = world_of(trs)
            W = {n: wf(n) for n in jn}
            if not a.keep_root_motion:
                pw = W[jn[hips]][:3, 3]
                if p0 is None: p0 = pw.copy()
                d = np.array([pw[0] - p0[0], 0.0, pw[2] - p0[2]])
                for n in jn: W[n] = W[n].copy(); W[n][:3, 3] -= d
            Wd = {n: T @ W[n] @ Ti for n in jn}
            for k, n in enumerate(jn):
                par = bone_parent[k]
                loc = Ti @ Ti if False else (np.linalg.inv(Wd[jn[par]]) @ Wd[n] if par >= 0 else Wd[n])
                lin = loc[:3, :3]; u, _, vt = np.linalg.svd(lin); r = u @ vt
                if np.linalg.det(r) < 0: r = u @ np.diag([1, 1, -1]) @ vt
                q = mat_to_quat(r)
                if f > 0 and float(q @ data[f - 1, k, 3:7]) < 0: q = -q
                data[f, k, :3] = loc[:3, 3]; data[f, k, 3:] = q
        clip_blobs.append((cname, nf, data))
        print(f"clip {cname}: {nf} frames ({dur:.2f} s)")

    # write
    blob = bytearray(struct.pack("<4sIIIIIII", b"HDM4", len(pos), len(idx), nb, tex.width, tex.height, len(clip_blobs), (1 if normal_img is not None else 0) | (2 if mr_img is not None else 0)))
    for k in range(nb):
        blob += struct.pack("<i12f3f", bone_parent[k], *ibm_d[k][:3, :].reshape(-1).tolist(), 0, 0, 0)
    vb = np.zeros((len(pos), 13), np.float32)
    vb[:, 0:3] = pos_d; vb[:, 3:6] = nrm_d; vb[:, 6:8] = uvs
    packed = (jj[:, 0].astype(np.uint32) & 255) | ((jj[:, 1].astype(np.uint32) & 255) << 8) | ((jj[:, 2].astype(np.uint32) & 255) << 16) | ((jj[:, 3].astype(np.uint32) & 255) << 24)
    vb[:, 8] = packed.view(np.float32); vb[:, 9:13] = ww
    blob += vb.tobytes()
    blob += idx.astype("<u4").tobytes()
    blob += tex.tobytes()
    for extra in (normal_img, mr_img):      # header word 7 bit 0 = normal map, bit 1 = metal(B)/roughness(G) map: each w, h, RGBA
        if extra is not None:
            extra = extra.convert("RGBA"); blob += struct.pack("<II", extra.width, extra.height) + extra.tobytes()
    for cname, nf, data in clip_blobs:
        blob += struct.pack("<32sIfII", cname.encode()[:31], nf, FPS, 0, 0)
        blob += data.astype("<f4").tobytes()
    a.out.write_bytes(bytes(blob))
    print(f"{a.out}: {len(blob) / 1e6:.1f} MB, {len(clip_blobs)} clips")


if __name__ == "__main__":
    main()
