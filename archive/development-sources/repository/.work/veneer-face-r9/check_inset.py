import sys
sys.path[:0]=['.work/python-libs','scripts']
import numpy as np
from scipy.interpolate import LinearNDInterpolator
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,axs=plt.subplots(3,1,figsize=(16,9))
for i in (1,2,3):
 d=np.load(f'.work/veneer-face-r9/V{i}-mesh.npz');v=d['v'];f=d['f'];pose=d['pose'];tri=v[f];normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);ids=np.unique(f[(normal[:,2]>1e-10)&(tri[:,:,2].min(1)>10.49)]);vv=v[ids];interp=LinearNDInterpolator(vv[:,:2],vv[:,2])
 p=np.load(f'.work/veneer-face-r9/V{i}-residual.npz')['points'];xy=p[:,1:3].copy();s=pose[0,2];c=pose[0,1]
 # Solve exact intersection of interpolated saved surface with horizontal slice plane.
 dx=np.zeros(len(p))
 for it in range(6):
  q=xy.copy();q[:,1]+=c*dx
  h=interp(q);qy=q.copy();qy[:,1]+=.005;dy=(interp(qy)-h)/.005
  dx+=(h-(p[:,3]+s*dx))/(s-c*dy)
 rows=[]
 for z in np.unique(p[:,0]):
  a=dx[p[:,0]==z];a=a[np.isfinite(a)&(a>.05)&(a<.5)]
  if len(a)>10:rows.append([z,len(a),np.median(a),np.quantile(a,.05),np.quantile(a,.95)])
 a=np.array(rows);np.save(f'.work/veneer-face-r9/V{i}-inset.npy',a)
 axs[i-1].plot(a[:,0],a[:,2]);axs[i-1].fill_between(a[:,0],a[:,3],a[:,4],alpha=.2);axs[i-1].set_ylim(.16,.26);axs[i-1].set_title(f'V{i} outer wall centerline inset from saved surface');axs[i-1].grid()
 jumps=np.diff(a[:,2]);idx=np.argsort(abs(jumps))[-12:];print(i,[(a[n,0],round(jumps[n],5)) for n in idx],flush=True)
fig.tight_layout();fig.savefig('.work/veneer-face-r9/inset.png',dpi=130)
