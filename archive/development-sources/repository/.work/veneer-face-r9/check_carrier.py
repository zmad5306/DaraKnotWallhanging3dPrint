import sys,pickle
sys.path[:0]=['.work/python-libs','scripts']
from pathlib import Path
import numpy as np
from check_veneer_layer_overlap import parse
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
root=Path('.work/veneer-face-r9')
for i in (1,2,3):
 d=np.load(root/f'V{i}-mesh.npz');pose=d['pose'];cache=root/f'V{i}-parsed.pkl'
 if cache.exists():mod,sup=pickle.loads(cache.read_bytes())
 else:mod,sup=parse((root/f'V{i}.gcode').read_text());cache.write_bytes(pickle.dumps((mod,sup)))
 rows=[]
 fig,axs=plt.subplots(2,3,figsize=(17,8))
 for z,segs in mod.items():
  segs=[r for r in segs if r[5]=='Outer wall']
  if not segs:continue
  a=np.array([r[:5] for r in segs]);xyz=np.column_stack([(a[:,:2]+a[:,2:4])/2,np.full(len(a),z-.1)]);q=(xyz-pose[:3,3])@pose[:3,:3];length=np.linalg.norm(a[:,2:4]-a[:,:2],axis=1)
  # Long straight lines on the inclined carrier wall, away from the end walls.
  keep=(q[:,2]>3)&(q[:,2]<4.6)&(length>2)&(abs(a[:,2]-a[:,0])<.002)
  if keep.any():
   for j in np.where(keep)[0]:rows.append([z,q[j,2],a[j,4],length[j],a[j,0],a[j,1],a[j,2],a[j,3]])
 for ax,z in zip(axs.flat,(138.0,138.2,138.4,138.6,138.8,142.0)):
  segs=mod[z];a=np.array([r[:5] for r in segs]);xyz=np.column_stack([(a[:,:2]+a[:,2:4])/2,np.full(len(a),z-.1)]);q=(xyz-pose[:3,3])@pose[:3,:3]
  k=(q[:,2]>2.8)&(q[:,2]<4.7);a=a[k];segs=[r for r,b in zip(segs,k) if b]
  # Undo the nominal incline so the straight carrier face should stay at a fixed X.
  lines=a[:,:4].reshape(-1,2,2);lines[:,:,0]+=(z-.1-pose[2,3])*pose[0,1]/pose[0,2]
  ax.add_collection(LineCollection(lines,linewidths=1,colors=['red' if r[5]=='Outer wall' else 'gray' for r in segs]));ax.autoscale();ax.set_title(f'V{i} Z{z}');ax.set_xlim(pose[0,3]+3/pose[0,2]-.4,pose[0,3]+4.4/pose[0,2]+.4);ax.set_ylim(lines[:,:,1].min()-1,lines[:,:,1].max()+1);ax.grid()
 fig.tight_layout();fig.savefig(root/f'V{i}-carrier-layers.png',dpi=120);plt.close(fig)
 a=np.array(rows);np.save(root/f'V{i}-carrier-paths.npy',a)
 print('V',i,'carrier outer wall Z=137..140',a[(a[:,0]>=137.8)&(a[:,0]<=139.2)].tolist(),flush=True)
