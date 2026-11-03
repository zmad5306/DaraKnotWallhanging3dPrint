import sys,json,pickle
from pathlib import Path
sys.path[:0]=['.work/python-libs','scripts']
import numpy as np,shapely
from shapely.strtree import STRtree
from validate_production_split import Project
from audit_veneer_surface_continuity import section
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
out=Path('.work/veneer-full-height')
p=Project(Path('output/Letter Veneers/Letter Veneers.3mf'))
report=[]
fig,axes=plt.subplots(3,3,figsize=(13,11))
for i,obj in enumerate(sorted(p.rows.values(),key=lambda x:x['plate']),1):
 pose=np.load(f'.work/veneer-face-r9/V{i}-mesh.npz')['pose'];m=obj['parts'][0]['mesh'];v=m.vertices@obj['T'][:3,:3].T+obj['T'][:3,3];tri=v[m.faces];lo=tri[:,:,2].min(1);hi=tri[:,:,2].max(1)
 _,model,_=pickle.loads((out/f'plate_{i}.pkl').read_bytes())
 exceptions=[]
 for z in [3.6,3.8,4,4.2,297,297.2]:
  a=np.array([s[:4] for s in model[z] if s[5]=='Outer wall']).reshape(-1,2,2);mid=a.mean(1);asm=(np.column_stack((mid,np.full(len(mid),z-.1)))-pose[:3,3])@pose[:3,:3];a=a[asm[:,2]>10.25]
  n=np.maximum(1,np.ceil(np.linalg.norm(a[:,1]-a[:,0],axis=1)/.5).astype(int));which=np.repeat(np.arange(len(a)),n);along=(np.arange(n.sum())-np.repeat(np.cumsum(n)-n,n)+.5)/n[which];pts=a[which,0]+along[:,None]*(a[which,1]-a[which,0])
  sec=section(tri[(lo<=z-.1)&(hi>=z-.1)],z-.1);tree=STRtree(shapely.linestrings(sec));d=shapely.distance(shapely.points(pts),tree.geometries[tree.nearest(shapely.points(pts))]);exceptions.append(dict(z=z,samples=len(pts),min=float(d.min()),median=float(np.median(d)),max=float(d.max())))
 records=[]
 levels={1:[291,291.2,291.4],2:[270,270.2,270.4],3:[10,10.2,10.4]}[i]
 for j,z in enumerate(levels):
  a=np.array([s[:4] for s in model[z] if s[5]=='Outer wall']).reshape(-1,2,2);mid=a.mean(1);asm=(np.column_stack((mid,np.full(len(mid),z-.1)))-pose[:3,3])@pose[:3,:3];mask=(asm[:,2]>3)&(asm[:,2]<4.6);candidate=a[mask];q=candidate.reshape(-1,2);q=q[np.argmax(q[:,1]) if i==1 else np.argmin(q[:,1])];ax=axes[i-1,j]
  sec=section(tri[(lo<=z-.1)&(hi>=z-.1)],z-.1)
  for lines,color,label in [(sec,'#0072B2','Mesh section'),(a,'#D55E00','Native outer path')]:
   from matplotlib.collections import LineCollection
   ax.add_collection(LineCollection(lines,colors=color,linewidths=1,label=label))
  ax.set_xlim(q[0]-3,q[0]+3);ax.set_ylim(q[1]-3,q[1]+3);ax.set_aspect('equal');ax.grid(alpha=.25);ax.set_title(f'{i}: Z {z:.1f}');ax.legend(fontsize=7)
  # Show the section paths and exact coordinates producing an apparent extrema jump.
  records.append(dict(z=z,extreme_xy=q.tolist()))
 report.append(dict(name=['Left letter veneer','Right letter veneer','Center letter veneer'][i-1],perimeter_closure_against_complete_mesh=exceptions,carrier_end_transition=records))
 print(report[-1],flush=True)
fig.suptitle('Carrier end transitions: complete mesh sections and native outer paths\nPrinting XY coordinates; blue mesh boundary, orange bead centerline');fig.tight_layout(rect=[0,0,1,.94]);fig.savefig(out/'carrier-end-transitions.png',dpi=160)
(out/'transition-inspection.json').write_text(json.dumps(report,indent=2)+'\n')
