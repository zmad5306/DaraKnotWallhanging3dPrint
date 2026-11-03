import sys,json,pickle
from pathlib import Path
sys.path[:0]=['.work/python-libs','scripts']
import numpy as np,shapely
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'native-veneers-r9'
fig,axs=plt.subplots(3,2,figsize=(12,10));report=[]
for i in (1,2,3):
 old,_=pickle.loads((ROOT/f'V{i}-parsed.pkl').read_bytes());new,_=pickle.loads((OUT/f'V{i}-parsed.pkl').read_bytes());pose=np.load(ROOT/f'V{i}-mesh.npz')['pose'];traces={}
 def lines(rows,z,front=False):
  a=np.array([s[:4] for s in rows if s[5]=='Outer wall']).reshape(-1,2,2)
  mid=a.mean(axis=1);asm=(np.column_stack((mid,np.full(len(mid),z-.1)))-pose[:3,3])@pose[:3,:3]
  mask=asm[:,2]>10.25 if front else (asm[:,2]>3)&(asm[:,2]<4.6)
  return a[mask]
 limits=(130,154) if i==1 else ((134,143) if i==2 else (.8,9.6))
 for label,mod in [('Original',old),('Candidate',new)]:
  vals=[]
  for z in sorted(mod):
   if not limits[0]<=z<=limits[1]:continue
   a=lines(mod[z],z)
   if len(a):vals.append([z,float(a[:,:,1].min()),float(a[:,:,1].max())])
  traces[label]=np.array(vals)
 for j,ax in enumerate(axs[i-1]):
  for label,v in traces.items():ax.plot(v[:,0],v[:,j+1],label=label,lw=1.6)
  ax.set_title(f'V{i} / '+('front end' if j==0 else 'rear end'));ax.set_xlabel('Print Z (mm)');ax.set_ylabel('Outer-wall path Y (mm)');ax.grid(alpha=.3);ax.legend()
  ax.ticklabel_format(useOffset=False)
  vv=np.concatenate([v[:,j+1] for v in traces.values()]);span=max(float(np.ptp(vv)),.2);ax.set_ylim(vv.min()-span*.1,vv.max()+span*.1)
 # Check the full decorative outside path at every layer through the reported band.
 distances=[]
 for z in sorted(old):
  if not 134<=z<=143:continue
  a=lines(old[z],z,True);b=lines(new[z],z,True)
  if not(len(a) and len(b)):continue
  dist=float(shapely.hausdorff_distance(shapely.multilinestrings(a),shapely.multilinestrings(b)))
  distances.append([z,dist])
 peak=max(distances,key=lambda v:v[1]);print('front comparison peak',i,peak,flush=True)
 assert peak[1]<.03,(i,peak)
 rec=dict(veneer=i,edge_traces={k:v.tolist() for k,v in traces.items()},decorative_front_max_path_difference_134_to_143_mm=max(v[1] for v in distances))
 if i==1:
  for label,v in traces.items():
   band=v[(v[:,0]>=137.8)&(v[:,0]<=139.2)]
   rec[label+'_rear_end_largest_layer_change_mm']=float(np.max(abs(np.diff(band[:,2]))))
  assert rec['Candidate_rear_end_largest_layer_change_mm']<.005,rec
 report.append(rec);print(i,{k:v for k,v in rec.items() if k!='edge_traces'},flush=True)
fig.suptitle('Carrier edge continuity — native toolpaths, before and after\nThe cause of the physical whole-part shift remains unresolved.',fontsize=12);fig.tight_layout(rect=[0,0,1,.95]);fig.savefig(OUT/'carrier-edges-before-after.png',dpi=140)
(OUT/'edge-validation.json').write_text(json.dumps(report,indent=2))
