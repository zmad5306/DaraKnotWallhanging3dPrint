import sys
sys.path[:0]=['.work/python-libs']
import numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
for i in (1,):
 d=np.load(f'.work/veneer-face-r9/V{i}-mesh.npz');pose=d['pose'];data=np.load(f'.work/veneer-face-r9/V{i}-chains.npz');segs=[]
 for k in data.files:
  if k=='stats':continue
  a=data[k];xyz=a[:,:6].reshape(-1,2,3);asm=(xyz-pose[:3,3])@pose[:3,:3];segs.extend(asm[:,:,:2])
 fig,axs=plt.subplots(1,4,figsize=(20,16));segs=np.array(segs)
 for ax,(lo,hi) in zip(axs,[(80,160),(0,80),(-80,0),(-160,-80)]):
  keep=(segs[:,:,1].max(1)>lo)&(segs[:,:,1].min(1)<hi);ax.add_collection(LineCollection(segs[keep],linewidths=.45,color='#b87333'));ax.set_ylim(lo,hi);ax.set_xlim(-305,-195);ax.set_aspect('equal');ax.grid(False)
 fig.tight_layout();fig.savefig('.work/veneer-face-r9/V1-path-overview.png',dpi=200)
