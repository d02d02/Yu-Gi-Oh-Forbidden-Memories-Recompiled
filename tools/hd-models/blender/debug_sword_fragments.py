import bpy, bmesh, os, numpy as np
from mathutils import Vector
base=os.environ["BASE"]
ang=bpy.data.objects["Angel"]
with bpy.data.libraries.load(os.path.join(base,"angel_on_ual_T_rigid.blend")) as (s,d): d.objects=["Angel"]
rig=d.objects[0]; bpy.context.scene.collection.objects.link(rig)
print("NAMES",ang.name,rig.name,len(ang.data.vertices),len(rig.data.vertices))
names=[g.name for g in ang.vertex_groups]
# islands of the carry mesh
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
isl_of={}
for k,c in enumerate(comps):
    for f in c:
        for v in f.verts: isl_of[v.index]=k
# right sword island = hand_r weighted, >1000 faces
def top_group(i):
    gs=ang.data.vertices[i].groups
    return names[max(gs,key=lambda g:g.weight).group] if gs else None
S5=[i for i in set(isl_of) if isl_of[i]==5]
print("island5 verts",len(S5),"top group",top_group(S5[0]))
Pr=np.array([rig.data.vertices[i].co[:] for i in S5]); Pc=np.array([ang.data.vertices[i].co[:] for i in S5])
# Kabsch rigid fit rigid->carry
mr,mc=Pr.mean(0),Pc.mean(0); H=(Pr-mr).T@(Pc-mc); U,S,Vt=np.linalg.svd(H); Rm=Vt.T@U.T
if np.linalg.det(Rm)<0: Vt[-1]*=-1; Rm=Vt.T@U.T
res=np.linalg.norm((Pr-mr)@Rm.T+mc-Pc,axis=1); print("rigid fit residual max/mean",res.max(),res.mean())
# axis of the sword in the rigid blend
u,s,vt=np.linalg.svd(Pr-mr); ax=vt[0]; t=(Pr-mr)@ax; print("axis",ax.round(2),"extent",t.min().round(2),t.max().round(2),"width",np.sqrt(s[1]**2/len(Pr)).round(3))
allr=np.array([v.co[:] for v in rig.data.vertices])
tt=(allr-mr)@ax; perp=np.linalg.norm((allr-mr)-np.outer(tt,ax),axis=1)
for rad in (0.06,0.1):
    cand=[i for i in range(len(allr)) if perp[i]<rad and t.min()-0.9<tt[i]<t.max()+0.2 and i not in set(S5)]
    from collections import Counter
    print("radius",rad,"candidates",len(cand),Counter((isl_of.get(i,-1),top_group(i)) for i in cand).most_common(8))
    if rad==0.06:
        ct=np.array([tt[i] for i in cand]); print(" t range",ct.min().round(2),ct.max().round(2))
