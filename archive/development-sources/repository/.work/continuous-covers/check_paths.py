import sys,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'.work'),str(ROOT/'scripts'),str(ROOT/'.work/python-libs')]
import analyze_cover_marks as a
import rebuild_continuous_covers as g
import numpy as np
W=ROOT/'.work/continuous-covers'
stage=json.loads((W/'stage.json').read_text())
variant=sys.argv[1] if len(sys.argv)>1 else 'slice'
with zipfile.ZipFile(W/variant/'sliced.3mf') as z:
    keys=[k for k in z.namelist() if k.endswith('.gcode')];print('Gcodes',keys)
    text=z.read(keys[0]).decode()
    print('Labels',[l for l in text.splitlines() if 'start printing object' in l][:5])
moves=a.parse(text);rows=[];plots=[]
for i,row in enumerate(stage['geometry'],1):
    saved=np.load(W/(row['name']+'.npz'));mesh=g.trimesh.Trimesh(saved['vertices'],saved['faces'],process=False)
    region=g.footprint(mesh,mesh.faces[mesh.face_normals[:,2]>.1])
    undo=np.linalg.inv(row['build_transform']);prev=None;joins=[];front=[];segments=[];partial=[]
    for m in moves:
        if m['object']!=i+6:continue
        p=a.sample(m);xyz=g.trimesh.transform_points(p,undo)
        uv=xyz[:,:2]-row['origin_xy'];u=uv@row['u_axis'];v=uv@row['v_axis']
        edge=g.shapely.distance(g.shapely.points(xyz[:,:2]),region.boundary)
        top=g.crown(row['parameters'],u,v,row['sin_t'],row['cos_t'])-.25*(1-np.clip(edge/.25,0,1))
        onface=(xyz[:,2]-top>-.4)&(edge>.6)
        if onface.any():
            front.append(m)
            for s,k in zip(np.stack([np.column_stack([v,u])[:-1],np.column_stack([v,u])[1:]],axis=1),onface[:-1]&onface[1:]):
                if k:segments.append(s)
            if onface[0] and prev is not None and prev['chain']==m['chain']:
                va,vb=a.tangent(prev,True),a.tangent(m)
                angle=float(np.degrees(np.arccos(np.clip(va@vb/np.linalg.norm(va)/np.linalg.norm(vb),-1,1))))
                joins.append(dict(uv=[float(u[0]),float(v[0])],line=m['line'],angle_deg=angle))
            prev=m if onface[-1] else None
        else:prev=None
    result=dict(name=row['name'],front_moves=len(front),arc_moves=sum(m['arc'] is not None for m in front),
        interior_joins=len(joins),maximum_join_angle_deg=max([j['angle_deg'] for j in joins],default=0),joins=joins)
    rows.append(result);plots.append((row,segments,joins));print(result,flush=True)
(W/(variant+'-paths.json')).write_text(json.dumps(rows,indent=2))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
fig,axs=plt.subplots(5,1,figsize=(12,10),layout='constrained')
for ax,(r,segs,joins) in zip(axs,plots):
    ax.add_collection(LineCollection(segs,linewidths=.6,color='#98602d'));ax.autoscale();ax.set_aspect('equal')
    if joins:ax.scatter([j['uv'][1] for j in joins],[j['uv'][0] for j in joins],c='red',s=12)
    ax.set_title(r['name']+' — '+str(len(joins))+' interior G-code junctions')
fig.suptitle('New continuous crowns: actual native outer-wall paths')
fig.savefig(W/'new-paths.png',dpi=160)
