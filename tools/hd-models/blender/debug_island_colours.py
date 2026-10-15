import bpy, bmesh, math, os
from mathutils import Vector
ang=bpy.data.objects["Angel"]
names=[g.name for g in ang.vertex_groups]
bm=bmesh.new(); bm.from_mesh(ang.data); bm.faces.ensure_lookup_table()
seen=set(); comps=[]
for f in bm.faces:
    if f.index in seen: continue
    st=[f]; seen.add(f.index); c=[]
    while st:
        x=st.pop(); c.append(x)
        for e in x.edges:
            for o in e.link_faces:
                if o.index not in seen: seen.add(o.index); st.append(o)
    comps.append(c)
comps.sort(key=len,reverse=True)
# vertex colours by role: right sword island = red, left sword = blue, body-island verts weighted to right leg/pelvis = grey, others textured
col=ang.data.color_attributes.new("role","FLOAT_COLOR","POINT")
vals={}
for k,c in enumerate(comps):
    vs={v.index for f in c for v in f.verts}
    acc={}
    for i in vs:
        for g in ang.data.vertices[i].groups: acc[names[g.group]]=acc.get(names[g.group],0)+g.weight
    top=max(acc,key=acc.get) if acc else ''
    color=(0.7,0.7,0.7,1)
    if top=='hand_r' and len(c)>1000: color=(1,0,0,1)
    elif top=='hand_l' and len(c)>1000: color=(0,0.3,1,1)
    elif k==0: color=(0.3,0.9,0.3,1)
    elif top.startswith('wing'): color=(0.9,0.7,0.1,1)
    else: color=(1,0,1,1)
    for i in vs: vals[i]=color
for i,v in vals.items(): col.data[i].color=v
sc=bpy.context.scene; sc.render.engine="BLENDER_WORKBENCH"; sc.render.resolution_x=900; sc.render.resolution_y=700
sc.display.shading.light="FLAT"; sc.display.shading.color_type="VERTEX"
sc.world=bpy.data.worlds.new("w"); sc.world.color=(0.1,0.1,0.12)
cam=bpy.data.cameras.new("c"); cam.type="ORTHO"; cam.ortho_scale=3.3
co=bpy.data.objects.new("cam",cam); sc.collection.objects.link(co); sc.camera=co
for o in bpy.data.objects:
    if o.name=="Mannequin": o.hide_render=True
out=os.environ["OUTDIR"]
for name,loc,center in (("front",(0,-8,1.0),(0,0,1.0)),("side_r",(-8,0,1.0),(0,0,1.0)),("top",(0,0,9),(0,0,0))):
    co.location=Vector(loc); d=Vector(center)-co.location; co.rotation_euler=d.to_track_quat("-Z","Y").to_euler()
    sc.render.filepath=os.path.join(out,"sword_"+name+".png"); bpy.ops.render.render(write_still=True)
print("DONE")
