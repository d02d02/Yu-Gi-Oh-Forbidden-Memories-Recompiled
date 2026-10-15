import bpy, os
arm=[o for o in bpy.data.objects if o.type=="ARMATURE"]
print("ARMS",[a.name for a in arm],"OBJS",[(o.name,o.type,o.parent.name if o.parent else None) for o in bpy.data.objects])
keep=set()
for o in bpy.data.objects:
    if o.type=="ARMATURE" or o.name=="Angel": keep.add(o.name)
for o in list(bpy.data.objects):
    if o.name not in keep: bpy.data.objects.remove(o,do_unlink=True)
for o in bpy.data.objects:
    if o.animation_data: o.animation_data_clear()
a=arm[0]
for pb in a.pose.bones:
    for c in list(pb.constraints): pb.constraints.remove(c)
for o in bpy.data.objects: o.select_set(True)
out=os.environ["OUTGLB"]
bpy.ops.export_scene.gltf(filepath=out,export_format="GLB",use_selection=True,export_animations=False,export_skins=True,export_apply=False,export_image_format="JPEG",export_yup=True)
print("EXPORTED",out,os.path.getsize(out))
