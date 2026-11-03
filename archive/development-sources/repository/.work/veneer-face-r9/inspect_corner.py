import sys,pickle
sys.path[:0]=['.work/python-libs','scripts']
import numpy as np,trimesh
from development_3mf import solid
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
r=Path('.work/veneer-face-r9');d=np.load(r/'V1-mesh.npz');pose=d['pose'];m=trimesh.Trimesh(d['v'],d['f'],process=False);m.apply_transform(pose);body=solid(m);mod,sup=pickle.loads((r/'V1-parsed.pkl').read_bytes())
fig,axs=plt.subplots(2,3,figsize=(15,9))
for ax,z in zip(axs.flat,[138.0,138.2,138.4,138.6,138.8,139.0]):
 shift=(z-.1-pose[2,3])*pose[0,1]/pose[0,2]
 for loop in body.slice(z-.1).to_polygons():
  loop=np.array(loop);loop[:,0]+=shift;ax.plot(*np.vstack([loop,loop[:1]]).T,color='black',lw=1)
 a=np.array([s[:5] for s in mod[z] if s[5]=='Outer wall']);lines=a[:,:4].reshape(-1,2,2);lines[:,:,0]+=shift;ax.add_collection(LineCollection(lines,color='red',linewidths=1))
 ax.set_xlim(160.9,162.8);ax.set_ylim(251.3,252.4);ax.set_aspect('equal');ax.grid();ax.set_title(f'Z{z}')
 print(z,'outer segments near corner',[s for s in mod[z] if s[5]=='Outer wall' and min(s[1],s[3])>251 and min(s[0],s[2])+shift<162.8],flush=True)
fig.tight_layout();fig.savefig(r/'corner-exact.png',dpi=140)
