import sys,json
sys.path[:0]=['.work/python-libs','scripts']
from pathlib import Path
import numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from develop_m_veneer import texture
from add_blue_ribbon_edge import artwork
outline=artwork(Path('working/Dara-Photo-Frame-A1-Jointed.scad').read_text(),'letter_outline'); roof=texture(outline)
fig,axes=plt.subplots(1,3,figsize=(15,12))
for i,ax in enumerate(axes,1):
 d=np.load(f'.work/veneer-face-r9/V{i}-mesh.npz');v=d['v'];f=d['f'];t=v[f];n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);ids=np.unique(f[(n[:,2]>1e-8)&(t[:,:,2].min(1)>10.49)])
 vv=v[ids];grid=np.all(np.abs(vv[:,:2]*2-np.round(vv[:,:2]*2))<.001,axis=1);v0=vv[grid];err=v0[:,2]-roof(v0[:,:2]);print(i,'front error min max',np.min(err),np.max(err), 'outliers',v0[abs(err)>.001][:20],flush=True)
 a=np.load(f'.work/veneer-face-r9/V{i}-residual.npz')['points'];ax.scatter(a[::2,1],a[::2,2],s=.05,c=a[::2,4],vmin=.1,vmax=.25,cmap='coolwarm');ax.set_aspect('equal');ax.set_title(f'V{i} outer wall offset to saved surface');ax.set_xlabel('Assembly X mm');ax.set_ylabel('Assembly Y mm')
fig.tight_layout();fig.savefig('.work/veneer-face-r9/face-offsets.png',dpi=150)
