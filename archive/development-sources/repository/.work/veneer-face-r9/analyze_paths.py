import sys,json
sys.path[:0]=['.work/python-libs','scripts']
import numpy as np
from pathlib import Path
from check_veneer_layer_overlap import parse
from scipy.interpolate import LinearNDInterpolator
for i in (1,2,3):
 d=np.load(f'.work/veneer-face-r9/V{i}-mesh.npz');v=d['v'];f=d['f'];pose=d['pose'];print('pose',i,pose,flush=True)
 # Restrict interpolation to saved front triangles, not support geometry.
 tri=v[f];norm=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);front=(norm[:,2]>1e-10)&(tri[:,:,2].min(1)>10.49)
 ids=np.unique(f[front]);vv=v[ids];interp=LinearNDInterpolator(vv[:,:2],vv[:,2])
 mod,sup=parse(Path(f'.work/veneer-face-r9/V{i}.gcode').read_text())
 rows=[];pts=[]
 for z,segs in mod.items():
  segs=[r for r in segs if r[5]=='Outer wall']
  if not segs:continue
  a=np.array([r[:5] for r in segs]);mid=(a[:,:2]+a[:,2:4])/2;xyz=np.column_stack([mid,np.full(len(mid),z-.1)]);asm=(xyz-pose[:3,3])@pose[:3,:3]
  err=interp(asm[:,:2])-asm[:,2];keep=(asm[:,2]>10.3)&(err<.8)&(err>-.5);err=err[keep]
  if len(err):
   rows.append([z,len(err),float(np.median(err)),float(np.min(err)),float(np.max(err)),float(np.median(a[keep,4]))])
   pts.extend(np.column_stack([np.full(keep.sum(),z),asm[keep],err,a[keep,4]]))
 np.savez_compressed(f'.work/veneer-face-r9/V{i}-residual.npz',layers=np.array(rows),points=np.array(pts))
 a=np.array(rows);jump=np.diff(a[:,2]);ids=np.argsort(abs(jump))[-15:];print('jumps',[(a[n].tolist(),a[n+1].tolist(),jump[n]) for n in ids],flush=True)
