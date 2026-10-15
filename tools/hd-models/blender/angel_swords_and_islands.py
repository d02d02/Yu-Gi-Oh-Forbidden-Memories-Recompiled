import bpy, bmesh, math
from mathutils import Vector, Matrix
ang=bpy.data.objects["Angel"]; arm=bpy.data.objects["Armature"]
names=[g.name for g in ang.vertex_groups]
bm=bmesh.new(); bm.from_mesh(ang.data); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
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
# --- the right sword's missing pieces: pelvis-weighted islands lying on the blade's own axis (the tabard rule had moved them to the pelvis) ---
import numpy as np, os
with bpy.data.libraries.load(os.path.join(os.environ["BASE"],"angel_on_ual_T_rigid.blend")) as (s_,d_): d_.objects=["Angel"]
rig=d_.objects[0]; bpy.context.scene.collection.objects.link(rig)
def isl_info(c):
    vs={v.index for f in c for v in f.verts}; acc={}
    for i in vs:
        for g in ang.data.vertices[i].groups: acc[names[g.group]]=acc.get(names[g.group],0)+g.weight
    return vs,(max(acc,key=acc.get) if acc else None)
sword_isl=[c for c in comps if isl_info(c)[1]=='hand_r' and len(c)>=1000]
assert len(sword_isl)==1, len(sword_isl)
S5=sorted(isl_info(sword_isl[0])[0])
Pr=np.array([rig.data.vertices[i].co[:] for i in S5]); Pc=np.array([ang.data.vertices[i].co[:] for i in S5])
mr,mc=Pr.mean(0),Pc.mean(0); Hm=(Pr-mr).T@(Pc-mc); U,Sg,Vt=np.linalg.svd(Hm); Rm=Vt.T@U.T
if np.linalg.det(Rm)<0: Vt[-1]*=-1; Rm=Vt.T@U.T
print("FIT residual",float(np.abs((Pr-mr)@Rm.T+mc-Pc).max()))
u_,s_v,vt_=np.linalg.svd(Pr-mr); axis=vt_[0]; t5=(Pr-mr)@axis
moved=0
for c in comps:
    if c is sword_isl[0] or len(c)<1000: continue   # only the big blade-side pieces move with the sword; the 573-face pommel floats off the handle (the handle lives in the hand mesh), so it is dropped
    vs,top=isl_info(c)
    if top!='pelvis': continue
    P=np.array([rig.data.vertices[i].co[:] for i in vs]); tt=(P-mr)@axis; perp=np.linalg.norm((P-mr)-np.outer(tt,axis),axis=1)
    if (perp<0.07).mean()>0.9 and tt.min()>t5.min()-1.2 and tt.max()<t5.max()+0.2:
        print("FRAGMENT island faces",len(c),"verts",len(vs),"t",tt.min().round(2),tt.max().round(2))
        for i in vs:
            ang.data.vertices[i].co=Vector(((rig.data.vertices[i].co[:]-mr)@Rm.T+mc))
            for ge in list(ang.data.vertices[i].groups): ang.vertex_groups[ge.group].remove([i])
            ang.vertex_groups['hand_r'].add([i],1.0,"REPLACE")
        moved+=len(vs)
print("FRAGMENT verts moved",moved)
Hh=np.array(arm.data.bones['hand_r'].head_local[:]); t_g=float((Hh-mr)@axis); sgn=1.0 if t5.mean()>t_g else -1.0
G_c=Vector(((mr+axis*t_g)-mr)@Rm.T+mc); dir_c=Vector(Rm@(sgn*axis)); RIGHT=(G_c,dir_c.normalized())
print("RIGHT grip t",round(t_g,2),"blade side",sgn,"G",[round(x,2) for x in G_c],"blade dir",[round(x,2) for x in RIGHT[1]])
bpy.data.objects.remove(rig,do_unlink=True)
def info(c):
    vs={v.index for f in c for v in f.verts}
    acc={}
    for i in vs:
        for g in ang.data.vertices[i].groups: acc[names[g.group]]=acc.get(names[g.group],0)+g.weight
    top=max(acc,key=acc.get) if acc else None
    cen=sum((ang.data.vertices[i].co for i in vs),Vector())/len(vs)
    return vs,top,cen
drop=[]; swords={'hand_l':set(),'hand_r':set()}; parts={'hand_l':[],'hand_r':[]}
for c in comps:
    vs,top,cen=info(c)
    if top in swords and len(c)>=300: parts[top].append((c,vs))
    elif len(c)<=600: drop+=[f.index for f in c]   # includes the floating chunk above the head
# a sword piece that floats away from its main blade (>0.08) is dropped (the left sword has a loose 25 cm shard in the asset itself)
for top,lst in parts.items():
    lst.sort(key=lambda p:len(p[0]),reverse=True)
    main=np.array([ang.data.vertices[i].co[:] for i in lst[0][1]]); swords[top]|=lst[0][1]
    for c,vs in lst[1:]:
        P=np.array([ang.data.vertices[i].co[:] for i in vs]); dmin=1e9
        for k in range(0,len(P),400): dmin=min(dmin,float(np.min(np.linalg.norm(P[k:k+400,None,:]-main[None,::4,:],axis=2))))
        if dmin>0.08: print("FLOATING sword piece dropped:",top,"faces",len(c),"min distance",round(dmin,2)); drop+=[f.index for f in c]
        else: swords[top]|=vs
print("DROP faces",len(drop),"sword verts",{k:len(v) for k,v in swords.items()})
# desired blade direction in the Sword_Idle pose (world): up and a little forward (the character faces -Y in Blender) and outward
arm.animation_data_create(); act=bpy.data.actions["Sword_Idle"]; arm.animation_data.action=act
bpy.context.scene.frame_set(int(act.frame_range[0])+5); bpy.context.view_layer.update()
UP=float(__import__("os").environ.get("UP","0.93")); FWD=float(__import__("os").environ.get("FWD","0.30")); OUT=float(__import__("os").environ.get("OUT","0.2"))
for tgt,vs in swords.items():
    sd=1 if tgt.endswith('_l') else -1
    pb=arm.pose.bones[tgt]; bone=arm.data.bones[tgt]
    R_idle=(arm.matrix_world@pb.matrix).to_3x3(); R_rest=(arm.matrix_world@bone.matrix_local).to_3x3()
    want=Vector((sd*OUT,-FWD,UP)).normalized()
    new_ax=R_rest@R_idle.inverted()@want
    co=ang.data.vertices
    H=bone.head_local.copy(); G=H+Vector((sd,0,0))*0.04
    pts=[co[i].co for i in vs]; cen=sum(pts,Vector())/len(pts)
    tip=max(pts,key=lambda p:(p-G).length); ax=(tip-G).normalized()
    if tgt=='hand_r': G=RIGHT[0]; ax=RIGHT[1]; tip=max(pts,key=lambda p:(p-G).dot(ax)); print('RIGHT sword blade length from grip',round((tip-G).dot(ax),2))
    R=ax.rotation_difference(new_ax.normalized()).to_matrix().to_4x4(); M=Matrix.Translation(G)@R@Matrix.Translation(-G)
    for i in vs: co[i].co=M@co[i].co
    print("SWORD",tgt,"axis",[round(x,2) for x in ax],"->",[round(x,2) for x in new_ax.normalized()],"len",round((tip-G).length,2))
arm.animation_data_clear()
# the deletions above were on bm (a copy); redo on the real mesh
bm.free()
bm2=bmesh.new(); bm2.from_mesh(ang.data); bm2.faces.ensure_lookup_table()
idx=set(drop)
bmesh.ops.delete(bm2,geom=[bm2.faces[i] for i in idx],context="FACES_ONLY"); bm2.to_mesh(ang.data); bm2.free()
bpy.ops.wm.save_as_mainfile(filepath=__import__("os").environ["OUTBLEND"])
print("SAVED")
