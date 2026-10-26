"""Studio 3D preview math: camera, projection, wireframe, bones, weights."""
import numpy as np


def orbit_view(yaw: float, pitch: float, dist: float, target: np.ndarray) -> np.ndarray:
    """Return 4x4 world-to-camera matrix. Camera looks down its own -Z.

    Args:
        yaw: Rotation around Y axis (0 = looking down -Z at model front, +yaw -> +X)
        pitch: Elevation in radians (positive = camera above)
        dist: Distance from target
        target: (3,) array, the point the camera looks at

    Returns:
        4x4 matrix: world point -> camera space (camera at origin, looking down -Z)
    """
    target = np.asarray(target, dtype=np.float64)
    # Camera position in world space
    cam_x = np.sin(yaw) * np.cos(pitch)
    cam_y = np.sin(pitch)
    cam_z = np.cos(yaw) * np.cos(pitch)
    cam_pos = target + dist * np.array([cam_x, cam_y, cam_z])

    # Camera forward vector (points from camera to target) = -Z in camera space
    forward = target - cam_pos
    forward = forward / np.linalg.norm(forward)

    # Camera right vector = cross(forward, world_up)
    world_up = np.array([0.0, 1.0, 0.0])
    right = np.cross(forward, world_up)
    right_norm = np.linalg.norm(right)
    if right_norm < 1e-10:
        # Camera looking straight up/down, pick arbitrary right
        right = np.array([1.0, 0.0, 0.0])
    else:
        right = right / right_norm

    # Camera up vector = cross(right, forward)
    up = np.cross(right, forward)

    # World-to-camera rotation (rows are camera axes in world space)
    R = np.stack([right, up, -forward], axis=0)  # 3x3

    # Translation: -R @ cam_pos
    t = -R @ cam_pos

    # Build 4x4 matrix
    M = np.eye(4, dtype=np.float64)
    M[:3, :3] = R
    M[:3, 3] = t
    return M

def project(points: np.ndarray, view: np.ndarray, fov_deg: float, width: int, height: int) -> np.ndarray:
    """Project world points into pixel coordinates.

    Args:
        points: (N,3) world coordinates.
        view: 4x4 world-to-camera matrix.
        fov_deg: vertical field of view in degrees.
        width: image width in pixels.
        height: image height in pixels.

    Returns:
        (N,3) array: [pixel_x, pixel_y, depth]. Depth is distance along view axis (positive in front).
    """
    pts = np.asarray(points, dtype=np.float64)
    if pts.ndim == 1:
        pts = pts.reshape(1, 3)
    N = pts.shape[0]
    # Transform to camera space
    hom = np.hstack([pts, np.ones((N, 1), dtype=np.float64)])
    cam = (view @ hom.T).T[:, :3]
    x = cam[:, 0]
    y = cam[:, 1]
    z = cam[:, 2]
    # Focal length based on vertical fov
    f = (height / 2.0) / np.tan(np.radians(fov_deg) / 2.0)
    # Perspective divide; handle points behind camera (z >= 0) gracefully
    with np.errstate(divide='ignore', invalid='ignore'):
        px = (x * f) / -z + (width / 2.0)
        py = (height / 2.0) - (y * f) / -z
    depth = -z
    result = np.stack([px, py, depth], axis=1)
    return result

# Duplicate orbit_view implementation removed (was redundant)


def fit_camera(lo: np.ndarray, hi: np.ndarray, fov_deg: float = 40.0):
    """Return (target, dist) so the box [lo, hi] fits vertical FOV with 10% margin.

    Args:
        lo: (3,) min corner of box.
        hi: (3,) max corner of box.
        fov_deg: vertical field of view in degrees.

    Returns:
        target: (3,) box centre.
        dist: distance along camera -Z so bounding sphere fits with 10% margin.
    """
    lo = np.asarray(lo, dtype=np.float64)
    hi = np.asarray(hi, dtype=np.float64)
    # Box centre
    target = (lo + hi) / 2.0
    # Half diagonal = radius of bounding sphere
    radius = np.linalg.norm((hi - lo) / 2.0)
    # Vertical half-angle
    half_fov = np.radians(fov_deg) / 2.0
    # With 10% margin: radius = 0.9 * dist * tan(half_fov)
    # => dist = radius / (0.9 * tan(half_fov))
    dist = radius / (0.9 * np.tan(half_fov))
    return target, dist

def wire_edges(indices):
    """Sorted (E, 2) array of the unique undirected edges of the triangles (a < b per row)."""
    tri = np.asarray(indices, dtype=int).reshape(-1, 3)
    e = np.concatenate([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]])
    return np.unique(np.sort(e, axis=1), axis=0)


def bone_segments(positions, parents):
    """(S, 2) array of (parent, child) bone indices, one per bone that has a parent, in bone order."""
    pairs = [(p, c) for c, p in enumerate(parents) if p >= 0]
    return np.array(pairs, dtype=int).reshape(-1, 2)


def vertex_weight(joints, weights, bone):
    """(N,) total weight of `bone` over each vertex's 4 influence slots."""
    return (np.asarray(weights, dtype=float) * (np.asarray(joints) == bone)).sum(axis=1)


def heat_color(w):
    """(N, 3) uint8 RGB: 0 blue, 0.5 green, 1 red, linear between, clipped to 0..1."""
    w = np.clip(np.asarray(w, dtype=float), 0.0, 1.0)
    r = np.clip((w - 0.5) * 2, 0, 1)
    b = np.clip(1 - w * 2, 0, 1)
    g = 1 - r - b
    return np.round(np.stack([r, g, b], axis=1) * 255).astype(np.uint8)


def depth_order(projected, indices):
    """Triangle numbers sorted far to near by the mean depth of their 3 vertices."""
    tri = np.asarray(indices, dtype=int).reshape(-1, 3)
    depth = np.asarray(projected)[:, 2][tri].mean(axis=1)
    return np.argsort(-depth, kind="stable")


def model_arrays(model):
    """Plain arrays for the preview from an audit.Model: stacked mesh, 4-slot skin data (zero weights when unskinned), bones, box."""
    pos, idx, joints, weights, base = [], [], [], [], 0
    for p in model.prims:
        n = len(p["pos"])
        pos.append(np.asarray(p["pos"], dtype=float))
        idx.append(np.asarray(p["idx"], dtype=int) + base)
        if p["skinned"]:
            joints.append(np.asarray(p["joints"], dtype=int)[:, :4])
            weights.append(np.asarray(p["weights"], dtype=float)[:, :4])
        else:
            joints.append(np.zeros((n, 4), dtype=int))
            weights.append(np.zeros((n, 4)))
        base += n
    bones = np.asarray(model.bind, dtype=float)[:, :3, 3] if len(model.bind) else np.zeros((0, 3))
    return {"pos": np.vstack(pos), "idx": np.concatenate(idx), "joints": np.vstack(joints), "weights": np.vstack(weights),
            "bones": bones, "parents": list(model.parents), "names": list(model.names),
            "lo": np.asarray(model.lo, dtype=float), "hi": np.asarray(model.hi, dtype=float)}


def unweighted_bones(joints, weights, count):
    """Indices of bones that carry no weight on any vertex (they move nothing)."""
    used = np.zeros(count, dtype=bool)
    mask = np.asarray(weights) > 0
    used[np.unique(np.asarray(joints)[mask])] = True
    return [i for i in range(count) if not used[i]]


def skin_points(pos, joints, weights, mats):
    """Pose the mesh: each vertex is the weighted sum of its 4 bones' skin matrices (B, 4, 4) applied to it; unweighted vertices stay."""
    pos = np.asarray(pos, dtype=float)
    h = np.concatenate([pos, np.ones((len(pos), 1))], axis=1)
    out = np.zeros_like(pos)
    total = np.zeros(len(pos))
    for k in range(4):
        w = np.asarray(weights)[:, k]
        out += w[:, None] * np.einsum("nij,nj->ni", np.asarray(mats)[np.asarray(joints)[:, k]], h)[:, :3]
        total += w
    free = total <= 1e-9
    out[free] = pos[free]
    return out


def pose_data(model, source, clip, t):
    """(skin matrices (B, 4, 4), posed bone positions (B, 3)) of `model` playing `clip` of `source` (a model; may be the library's) at t seconds."""
    from studio import audit
    world = audit.pose_function(model, (source.g, source.scene), clip, t)
    worlds = np.array([np.asarray(world(k)) for k in range(len(model.joints))])
    return worlds @ np.asarray(model.ibm), worlds[:, :3, 3]
