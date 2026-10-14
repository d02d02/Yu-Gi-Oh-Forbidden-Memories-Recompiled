"""Render a glTF from the front and the side, headless:
   blender -b --python blender_render.py -- model.gltf OUT_PREFIX [size]"""
import sys, math
import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
src, prefix = argv[0], argv[1]
size = int(argv[2]) if len(argv) > 2 else 800
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
for o in meshes:
    for m in o.data.materials:   # nearest-neighbour texels, as the sheet is tiny
        for n in m.node_tree.nodes:
            if n.type == "TEX_IMAGE":
                n.interpolation = "Closest"
pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
mid, span = (lo + hi) / 2, max((hi - lo).x, (hi - lo).y, (hi - lo).z)
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE" if "BLENDER_EEVEE" in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items] else "BLENDER_EEVEE_NEXT"
scene.render.resolution_x = scene.render.resolution_y = size
scene.render.film_transparent = False
scene.world = bpy.data.worlds.new("w"); scene.world.use_nodes = True
scene.world.node_tree.nodes["Background"].inputs[0].default_value = (0.16, 0.17, 0.2, 1)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); scene.collection.objects.link(cam)
cam.data.type = "ORTHO"; cam.data.ortho_scale = span * 1.15; scene.camera = cam
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); scene.collection.objects.link(sun)
sun.data.energy = 3
for name, yaw in (("front", 0), ("side", 90), ("back", 180)):
    d = span * 3
    cam.location = mid + Vector((math.sin(math.radians(yaw)) * d, -math.cos(math.radians(yaw)) * d, 0))
    cam.rotation_euler = (math.radians(90), 0, math.radians(yaw))
    sun.rotation_euler = (math.radians(50), 0, math.radians(yaw - 30))
    scene.render.filepath = f"{prefix}_{name}.png"
    bpy.ops.render.render(write_still=True)
