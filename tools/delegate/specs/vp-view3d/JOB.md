# Job vp-view3d

## Goal
One UI-free module `tools/hd-models/studio/view3d.py` and tests: the math behind the Studio's model preview (camera, projection, wireframe, bones, weight colours). Pure Python 3.12 + numpy, stdlib `unittest`, no tkinter, no glb files. Tests: `tools/hd-models/tests/test_studio_view3d.py`, one class per item, built on tiny hand-written arrays.

## Facts (do NOT read other studio modules)
- Run: `python3 tools/hd-models/tests/test_studio_view3d.py -k TestOrbit` from the repo root. Test header: `HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))`, then `from studio import view3d`. The file MUST end with `if __name__ == "__main__":\n    unittest.main()`.
- Conventions: right-handed, Y up, the model faces +Z. Points are numpy float arrays of shape (N, 3). Triangle indices are a flat int array (3 per triangle). Bones: `positions` (B, 3) and `parents` list of B ints (-1 = root). Skin data per vertex: `joints` (N, 4) int and `weights` (N, 4) float (the 4 strongest bones and their weights).
- Yaw turns the camera around Y (0 = looking down -Z at the model's front, +yaw moves the camera toward +X). Pitch is elevation in radians (positive = camera above). Camera sits at `target + dist * (sin(yaw)cos(pitch), sin(pitch), cos(yaw)cos(pitch))` looking at `target`.

## Items (see progress.md)
1. `orbit_view(yaw, pitch, dist, target)` returns the 4x4 world-to-camera matrix (camera looks down its own -Z). Test: the target maps to (0, 0, -dist); a point at the camera position maps to the origin.
2. `project(points, view, fov_deg, width, height)` returns an (N, 3) array: pixel x, pixel y (y down, origin top-left, centre = width/2, height/2) and depth (distance along the view axis, positive in front). A point behind the camera gets depth <= 0. Test: the target lands in the image centre; a point right of the target lands right of centre.
3. `fit_camera(lo, hi, fov_deg=40.0)` returns `(target, dist)`: target = box centre, dist so the box's bounding sphere fits the vertical field of view with 10% margin. Test: a bigger box gives a bigger dist; target is the centre.
4. `wire_edges(indices)` returns a sorted (E, 2) int array of the unique undirected edges of the triangles (a < b in each row). Test: two triangles sharing an edge give 5 edges.
5. `bone_segments(positions, parents)` returns an (S, 2) int array of `(parent, child)` index pairs, one per bone with a parent >= 0, in bone order. Test: a 3-bone chain gives 2 segments; two roots give none for them.
6. `vertex_weight(joints, weights, bone)` returns an (N,) float array: the total weight of `bone` in each vertex's 4 slots. `heat_color(w)` maps an array in 0..1 to an (N, 3) uint8 RGB array: 0 = blue (0,0,255), 0.5 = green (0,255,0), 1 = red (255,0,0), linear between, clipped outside. Tests: a vertex with the bone in slot 2 gets that weight; the three anchor colours.
7. `depth_order(points_projected, indices)` returns triangle numbers sorted far to near by the mean depth of their 3 vertices (painter's order). Test: two triangles at different depths come back far first.

## Constraints
One item per session; WRITE small: a new file at most 60 lines per write, grow it by edits of at most 60 lines. Edit only `studio/view3d.py` and `tests/test_studio_view3d.py`. Never edit any other file, README included.

## Acceptance
`bash verify.sh` exits 0.
