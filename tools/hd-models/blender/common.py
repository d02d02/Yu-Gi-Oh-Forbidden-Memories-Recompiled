import bpy, sys, os, math
from mathutils import Vector
UAL=os.path.abspath("../incoming/ual/Universal Animation Library[Standard]/Unreal-Godot/UAL1_Standard.glb")
def load():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=UAL)
    arm=next(o for o in bpy.data.objects if o.type=="ARMATURE")
    man=bpy.data.objects["Mannequin"]
    ico=bpy.data.objects.get("Icosphere")
    if ico: bpy.data.objects.remove(ico,do_unlink=True)
    return arm,man
def append_angel(path="angel_dec.blend"):
    with bpy.data.libraries.load(os.path.abspath(path)) as (s,d): d.objects=["Angel"]
    ang=d.objects[0]; bpy.context.scene.collection.objects.link(ang); return ang
def setup_render(w=900,h=700):
    sc=bpy.context.scene; sc.render.engine="BLENDER_WORKBENCH"; sc.render.resolution_x=w; sc.render.resolution_y=h
    sh=sc.display.shading; sh.light="STUDIO"; sh.color_type="TEXTURE"; sh.show_cavity=False
    sc.world=bpy.data.worlds.new("w"); sc.world.color=(0.12,0.12,0.14)
    cam=bpy.data.cameras.new("c"); cam.type="ORTHO"; cam.ortho_scale=2.6
    co=bpy.data.objects.new("cam",cam); bpy.context.scene.collection.objects.link(co); sc.camera=co; return co
def shot(co,path,az=0,center=(0,0,0.95),dist=8,elev=0):
    a=math.radians(az); e=math.radians(elev)
    co.location=Vector(center)+Vector((math.sin(a)*math.cos(e)*-dist*-1*-1, -math.cos(a)*math.cos(e)*dist, math.sin(e)*dist))
    d=Vector(center)-co.location; co.rotation_euler=d.to_track_quat("-Z","Y").to_euler()
    bpy.context.scene.render.filepath=os.path.abspath(path); bpy.ops.render.render(write_still=True)
