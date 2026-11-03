import sys,re,json
sys.path[:0]=['.work/python-libs','scripts']
from pathlib import Path
import numpy as np
from check_veneer_layer_overlap import parse
for i in (1,2,3):
 d=np.load(f'.work/veneer-face-r9/V{i}-mesh.npz');pose=d['pose'];mod,sup=parse(Path(f'.work/veneer-face-r9/V{i}.gcode').read_text());rows=[]
 for z,segs in mod.items():
  a=np.array([r[:5] for r in segs if r[5]=='Outer wall'])
  if not len(a):continue
  # all segment endpoints on front half, including edge contour
  xy=a[:,:4].reshape(-1,2);xyz=np.column_stack([xy,np.full(len(xy),z-.1)]);asm=(xyz-pose[:3,3])@pose[:3,:3];q=asm[asm[:,2]>10.25]
  if len(q):rows.append([z,*q[:,:2].min(0),*q[:,:2].max(0)])
 a=np.array(rows);np.save(f'.work/veneer-face-r9/V{i}-edges.npy',a)
 b=np.diff(a[:,[1,3]],axis=0);dd=np.diff(b,axis=0);ids=np.argsort(np.max(abs(dd),axis=1))[-15:];print(i,[(a[j:j+3].tolist(),dd[j].tolist()) for j in ids],flush=True)
