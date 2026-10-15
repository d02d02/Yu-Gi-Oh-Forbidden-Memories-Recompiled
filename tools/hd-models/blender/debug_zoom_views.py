import bpy, os
from mathutils import Vector
sc=bpy.context.scene; sc.render.engine="BLENDER_WORKBENCH"; sc.render.resolution_x=900; sc.render.resolution_y=700
sc.display.shading.light="STUDIO"; sc.display.shading.color_type="TEXTURE"
sc.world=bpy.data.worlds.new("w"); sc.world.color=(0.1,0.1,0.12)
cam=bpy.data.cameras.new("c"); cam.type="ORTHO"; cam.ortho_scale=1.6
co=bpy.data.objects.new("cam",cam); sc.collection.objects.link(co); sc.camera=co
for o in bpy.data.objects:
    if o.name=="Mannequin": o.hide_render=True
out=os.environ["OUTDIR"]; c=Vector((-0.15,-0.1,1.5))
for name,loc in (("front",(c.x,-8,c.z)),("side",(-8+c.x,c.y,c.z)),("back",(c.x,8,c.z))):
    co.location=Vector(loc); d=c-co.location; co.rotation_euler=d.to_track_quat("-Z","Y").to_euler()
    sc.render.filepath=os.path.join(out,"zoom_"+name+".png"); bpy.ops.render.render(write_still=True)
print("DONE")
