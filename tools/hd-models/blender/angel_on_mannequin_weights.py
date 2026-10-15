import sys; sys.path.insert(0,".")
from common import *
from mathutils import Matrix
th=75.0
FAR=float(sys.argv[sys.argv.index('--')+1]) if '--' in sys.argv else 0.10
RIGID='--rigid' in sys.argv
OUT=os.path.abspath(('angel_on_ual_T_align.blend' if '--align' in sys.argv else 'angel_on_ual_T_rigid.blend') if RIGID else 'angel_on_ual_T.blend')
arm,man=load(); ang=append_angel(); arm.animation_data_clear()
S=1.83/0.852; ang.scale=(S,)*3; ang.location=(0,0,0)
def sel(o):
    for x in bpy.context.view_layer.objects: x.select_set(False)
    o.select_set(True); bpy.context.view_layer.objects.active=o
sel(ang); bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
def rot_world(pb,axis,deg):
    R=Matrix.Rotation(math.radians(deg),4,axis); h=pb.head.copy()
    pb.matrix=Matrix.Translation(h)@R@Matrix.Translation(-h)@pb.matrix; bpy.context.view_layer.update()
# helper armature (dup), posed to the angel's A-pose
dup=arm.copy(); dup.data=arm.data.copy(); dup.name="dup"; bpy.context.scene.collection.objects.link(dup)
mc=man.copy(); mc.data=man.data.copy(); bpy.context.scene.collection.objects.link(mc)
mc.modifiers["Armature"].object=dup if "Armature" in mc.modifiers else None
for m in mc.modifiers:
    if m.type=="ARMATURE": m.object=dup
mc.parent=dup
sel(dup); bpy.ops.object.mode_set(mode="POSE")
for s,sg in (("l",1),("r",-1)): rot_world(dup.pose.bones["upperarm_"+s],"Y",sg*th)
bpy.ops.object.mode_set(mode="OBJECT"); bpy.context.view_layer.update()
SEG=[(dup.matrix_world@dup.pose.bones[n].head,dup.matrix_world@dup.pose.bones[n].tail) for n in dup.pose.bones.keys() if n.split('_')[0] in ('upperarm','lowerarm','hand','clavicle')]
mev=mc.evaluated_get(bpy.context.evaluated_depsgraph_get())
proxy=bpy.data.objects.new("proxy",bpy.data.meshes.new_from_object(mev)); bpy.context.scene.collection.objects.link(proxy)
for g in proxy.vertex_groups: ang.vertex_groups.new(name=g.name)
sel(ang)
dt=ang.modifiers.new("dt","DATA_TRANSFER"); dt.object=proxy; dt.use_vert_data=True; dt.data_types_verts={"VGROUP_WEIGHTS"}
dt.vert_mapping="POLYINTERP_NEAREST"; dt.layers_vgroup_select_src="ALL"; dt.layers_vgroup_select_dst="NAME"
bpy.ops.object.modifier_apply(modifier="dt")
print('DBG weighted verts',sum(1 for v in ang.data.vertices if v.groups),len(ang.data.vertices),'proxy vg',len(proxy.vertex_groups),sum(1 for v in proxy.data.vertices if v.groups))

SW={}; WG={}; TAB=[]; SSET={}
if RIGID:
    from mathutils.bvhtree import BVHTree
    import bmesh
    bv=BVHTree.FromObject(proxy,bpy.context.evaluated_depsgraph_get())
    bm=bmesh.new(); bm.from_mesh(ang.data); bm.verts.ensure_lookup_table()
    far=[bv.find_nearest(v.co)[3]>FAR for v in bm.verts]
    print("DBG far verts",sum(far))
    seen=set(); comps=[]
    for v in bm.verts:
        if not far[v.index] or v.index in seen: continue
        st=[v]; seen.add(v.index); c=[]
        while st:
            x=st.pop(); c.append(x.index)
            for e in x.link_edges:
                o=e.other_vert(x)
                if far[o.index] and o.index not in seen: seen.add(o.index); st.append(o)
        comps.append(c)
    comps.sort(key=len,reverse=True)
    names=[g.name for g in ang.vertex_groups]
    for c in comps[:12]:
        if len(c)<300: break
        # attachment = the 3% of verts nearest to the proxy; dominant bone there
        c2=sorted(c,key=lambda i: bv.find_nearest(bm.verts[i].co)[3])[:max(10,len(c)//30)]
        acc={}
        for i in c2:
            for ge in ang.data.vertices[i].groups: acc[ge.group]=acc.get(ge.group,0)+ge.weight
        gi=max(acc,key=acc.get)
        cx=sum((bm.verts[i].co for i in c),Vector())/len(c)
        tgt='spine_03' if (cx.y>0.15 and cx.z>1.0) else ('hand_l' if cx.x>0 else 'hand_r'); gi=names.index(tgt)
        print("DBG comp",len(c),"->",names[gi],[round(x,2) for x in cx])
        if tgt.startswith('hand'): SW.setdefault(tgt,[]).extend(c)
        if tgt=='spine_03': WG['l' if cx.x>0 else 'r']=list(c)
        for i in c:
            for ge in list(ang.data.vertices[i].groups): ang.vertex_groups[ge.group].remove([i])
            ang.vertex_groups[gi].add([i],1.0,"REPLACE")
    if '--align' in sys.argv:
        def segd(p,a,b):
            ab=b-a; t=max(0,min(1,(p-a).dot(ab)/max(ab.dot(ab),1e-9))); return (p-(a+ab*t)).length
        armg={ang.vertex_groups[n].index for n in names if n.split('_')[0] in ('upperarm','lowerarm','hand','clavicle','index','middle','ring','pinky','thumb')}
        rigidset=set(i for c in SW.values() for i in c)|set(i for c in WG.values() for i in c)
        pg=ang.vertex_groups['pelvis'].index; ntab=0
        for v in ang.data.vertices:
            if v.index in rigidset or not v.groups: continue
            dom=max(v.groups,key=lambda g:g.weight).group
            if dom in armg and bm.verts[v.index].co.z<1.15 and min(segd(bm.verts[v.index].co,a,b) for a,b in SEG)>0.14:
                for ge in list(v.groups): ang.vertex_groups[ge.group].remove([v.index])
                ang.vertex_groups[pg].add([v.index],1.0,"REPLACE"); ntab+=1; TAB.append(v.index)
        print("DBG tabard verts ->pelvis",ntab)
bpy.data.objects.remove(proxy,do_unlink=True)
sel(ang); bpy.ops.object.mode_set(mode="WEIGHT_PAINT")
bpy.ops.object.vertex_group_limit_total(group_select_mode="ALL",limit=4); bpy.ops.object.vertex_group_normalize_all(group_select_mode="ALL",lock_active=False)
bpy.ops.object.mode_set(mode="OBJECT")
# dup: apply the A-pose as ITS rest, then make it follow the original (T-pose) bones in world space -> angel deformed into the T-pose
sel(dup); bpy.ops.object.mode_set(mode="POSE"); bpy.ops.pose.select_all(action="SELECT"); bpy.ops.pose.armature_apply(selected=False)
for pb in dup.pose.bones:
    c=pb.constraints.new("COPY_TRANSFORMS"); c.target=arm; c.subtarget=pb.name; c.target_space="WORLD"; c.owner_space="WORLD"
bpy.ops.object.mode_set(mode="OBJECT"); bpy.context.view_layer.update()
import mathutils
print('DBG dup rest hand_l',dup.data.bones['hand_l'].head_local[:],'pose hand_l',(dup.matrix_world@dup.pose.bones['hand_l'].head)[:], 'orig',arm.pose.bones['hand_l'].head[:])
print('DBG ang x extent before',max(v.co.x for v in ang.data.vertices))
mod=ang.modifiers.new("Armature","ARMATURE"); mod.object=dup
sel(ang); bpy.ops.object.modifier_apply(modifier="Armature")
print('DBG ang x extent after',max(v.co.x for v in ang.data.vertices))

if RIGID and '--align' in sys.argv:
    for tgt,idx in SW.items():
        hb=arm.data.bones[tgt]; H=hb.head_local.copy(); direction=Vector((1,0,0)) if tgt.endswith('_l') else Vector((-1,0,0))
        co=ang.data.vertices
        near=sorted(idx,key=lambda i:(co[i].co-H).length)[:max(10,len(idx)//100)]; G=sum((co[i].co for i in near),Vector())/len(near)
        tip=max(idx,key=lambda i:(co[i].co-G).length); T=co[tip].co.copy(); ax=(T-G).normalized()
        seg_len=(T-G).length; sset=set(idx)
        for v in co:   # grip/hilt: verts close to the hand->tip segment
            d=v.co-G; t=d.dot(ax)
            if 0<=t<=seg_len and (d-ax*t).length<0.05 and any(ang.vertex_groups[g.group].name.split('_')[0] in ('hand','lowerarm','index','middle','ring','pinky','thumb') for g in v.groups): sset.add(v.index)
        R=ax.rotation_difference(direction).to_matrix().to_4x4(); M=Matrix.Translation(H+direction*0.04)@R@Matrix.Translation(-G)
        gi=ang.vertex_groups[tgt].index
        for i in sset:
            co[i].co=M@co[i].co
            for ge in list(co[i].groups): ang.vertex_groups[ge.group].remove([i])
            ang.vertex_groups[gi].add([i],1.0,"REPLACE")
        SSET[tgt]=sset
        print("DBG sword",tgt,len(sset),"axis",[round(x,2) for x in ax])

if RIGID and '--align' in sys.argv:
    sel(arm); bpy.ops.object.mode_set(mode="EDIT"); eb=arm.data.edit_bones; WB={}
    for sd,idx in WG.items():
        sg=1 if sd=='l' else -1; P=[ang.data.vertices[i].co.copy() for i in idx]
        sp=eb['spine_03'].head
        near=sorted(P,key=lambda p:(p-sp).length)[:max(10,len(P)//50)]; R=sum(near,Vector())/len(near)
        tip=max(P,key=lambda p:(p-R).length); d=(tip-R); L=d.length; d.normalize()
        for nm,par,src in (('wing_a_'+sd,'spine_03','upperarm_'+sd),('wing_b_'+sd,'wing_a_'+sd,'lowerarm_'+sd)):
            b=eb.new(nm); b.head=R if nm.startswith('wing_a') else R+d*L*0.4; b.tail=b.head+Vector((sg*0.3,0,0)); b.roll=eb[src].roll; b.parent=eb[par]; b.use_connect=False
        WB[sd]=(R,d,L,idx)
    bpy.ops.object.mode_set(mode="OBJECT")
    sel(arm); bpy.ops.object.mode_set(mode="POSE")
    for sd in WB:
        for nm,src in (('wing_a_'+sd,'upperarm_'+sd),('wing_b_'+sd,'lowerarm_'+sd)):
            c=arm.pose.bones[nm].constraints.new('COPY_ROTATION'); c.target=arm; c.subtarget=src; c.target_space='LOCAL'; c.owner_space='LOCAL'; c.influence=0.8
    bpy.ops.object.mode_set(mode="OBJECT")
    for sd,(R,d,L,idx) in WB.items():
        ga=ang.vertex_groups.new(name='wing_a_'+sd); gb=ang.vertex_groups.new(name='wing_b_'+sd)
        for i in idx:
            t=max(0,min(1,((ang.data.vertices[i].co-R).dot(d)/L-0.2)/0.4)); w=t*t*(3-2*t)
            for ge in list(ang.data.vertices[i].groups): ang.vertex_groups[ge.group].remove([i])
            ga.add([i],1-w,"REPLACE"); gb.add([i],w,"REPLACE") if w>0 else None
    print("DBG wing bones",list(WB))

if RIGID and '--align' in sys.argv:
    import bmesh
    cls={}
    for k,(sd,idx) in enumerate(WG.items()):
        for i in idx: cls[i]=10+k
    for k,(tg,st) in enumerate(SSET.items()):
        for i in st: cls[i]=20+k
    for i in TAB: cls.setdefault(i,30)
    bm2=bmesh.new(); bm2.from_mesh(ang.data); bm2.faces.ensure_lookup_table()
    bad=[f for f in bm2.faces if len({cls.get(v.index,0) for v in f.verts})>1]
    print("DBG cut bridge faces",len(bad),"of",len(bm2.faces))
    bmesh.ops.delete(bm2,geom=bad,context="FACES_ONLY"); bm2.to_mesh(ang.data); bm2.free()
# now bind to the real armature (rest = T-pose)
mod=ang.modifiers.new("Armature","ARMATURE"); mod.object=arm; ang.parent=arm
for o in (dup,mc): bpy.data.objects.remove(o,do_unlink=True)
for x in bpy.data.actions: x.use_fake_user=True
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("BUILD OK vgroups",len(ang.vertex_groups))
