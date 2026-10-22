import bpy, os, sys
out = os.environ["OUT"]
arm=[o for o in bpy.data.objects if o.type=="ARMATURE"][0]
mesh=[o for o in bpy.data.objects if o.type=="MESH"][0]
w=set()
for v in mesh.data.vertices:
    for g in v.groups:
        if g.weight>0.001: w.add(mesh.vertex_groups[g.group].name)
w={n for n in w if n in arm.data.bones}
keep=set(w)
for n in list(w):
    b=arm.data.bones[n]
    while b.parent: b=b.parent; keep.add(b.name)
LIMIT=int(os.environ.get("LIMIT","120"))
tot={}
for v in mesh.data.vertices:
    for g in v.groups:
        n=mesh.vertex_groups[g.group].name
        if n in arm.data.bones: tot[n]=tot.get(n,0)+g.weight
def kids(n): return [b.name for b in arm.data.bones[n].children if b.name in keep]
while len(keep)>LIMIT:
    leaves=[n for n in keep if not kids(n)]
    n=min(leaves,key=lambda x: tot.get(x,0))
    par=arm.data.bones[n].parent
    while par and par.name not in keep: par=par.parent
    if tot.get(n,0)>0 and par:
        vg=mesh.vertex_groups.get(n); pg=mesh.vertex_groups.get(par.name) or mesh.vertex_groups.new(name=par.name)
        for v in mesh.data.vertices:
            for g in v.groups:
                if g.group==vg.index and g.weight>0: pg.add([v.index], g.weight, 'ADD')
        tot[par.name]=tot.get(par.name,0)+tot[n]
    if mesh.vertex_groups.get(n): mesh.vertex_groups.remove(mesh.vertex_groups[n])
    keep.discard(n)
for b in arm.data.bones: b.use_deform = b.name in keep
print("KEEP", len(keep))

# one material: the colour atlas on the mirrored UV layout (the blend's own are Blender-Internal slots Blender 4.5 drops)
img=bpy.data.images.load(os.environ["TEX"])
mat=bpy.data.materials.new("Dragon"); mat.use_nodes=True
nt=mat.node_tree; bsdf=nt.nodes["Principled BSDF"]; tex=nt.nodes.new("ShaderNodeTexImage"); tex.image=img
nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"]); bsdf.inputs["Roughness"].default_value=0.6
mesh.data.materials.clear(); mesh.data.materials.append(mat)
for p in mesh.data.polygons: p.material_index=0
uv=mesh.data.uv_layers[os.environ.get("UV","UV_mirror")]; uv.active=True; uv.active_render=True
# one NLA/action list: push every action to be exported
for o in list(bpy.data.objects):
    if o not in (arm, mesh): bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.object.select_all(action="DESELECT"); arm.select_set(True); mesh.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", use_selection=True, export_animations=True,
    export_animation_mode="ACTIONS", export_def_bones=True, export_yup=True, export_apply=False, export_image_format="JPEG" if False else "AUTO",
    export_force_sampling=True, export_optimize_animation_size=False)
print("EXPORTED", out)
