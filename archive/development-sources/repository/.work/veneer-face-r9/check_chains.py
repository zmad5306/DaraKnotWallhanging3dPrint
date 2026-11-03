import sys,re,json
sys.path[:0]=['.work/python-libs','scripts']
from pathlib import Path
import numpy as np
TOKEN=re.compile(r'([XYZEF])\s*(-?(?:\d*\.\d+|\d+\.?\d*))')
for i in (1,2,3):
 d=np.load(f'.work/veneer-face-r9/V{i}-mesh.npz');pose=d['pose'];v=np.zeros(3);e=0;rel=False;feature='Custom';zlayer=0;chains=[];cur=[];speed=0;last=None
 def finish():
  if cur:chains.append(np.array(cur));cur.clear()
 for line in Path(f'.work/veneer-face-r9/V{i}.gcode').read_text().splitlines():
  if line.startswith('; FEATURE: '):feature=line[11:]
  if line.startswith('M83'):rel=True
  if line.startswith('M82'):rel=False
  code=line.split(';')[0].strip();cmd=code.split()[0] if code else ''
  if cmd=='G92':
   a={k:float(n) for k,n in TOKEN.findall(code)};e=a.get('E',e)
  if cmd not in ['G0','G1']:continue
  a={k:float(n) for k,n in TOKEN.findall(code)};end=np.array([a.get(k,old) for k,old in zip('XYZ',v)]);de=a.get('E',0) if rel else a.get('E',e)-e;speed=a.get('F',speed)
  if de>0 and np.linalg.norm(end[:2]-v[:2])>1e-8 and feature=='Outer wall':
   q=((v+end)/2-pose[:3,3])@pose[:3,:3]
   if q[2]>10.25:
    cur.append([*v,*end,speed,de])
   else:finish()
  else:finish()
  v=end;e=e+a.get('E',0) if rel else a.get('E',e)
 finish();stats=[]
 for c in chains:
  z=c[0,2];length=np.linalg.norm(c[:,3:5]-c[:,:2],axis=1);dir=np.sum(c[:,4]-c[:,1]);stats.append([z,len(c),length.sum(),np.sign(dir),c[0,0],c[0,1],c[-1,3],c[-1,4],np.min(c[:,6]),np.max(c[:,6])])
 np.savez_compressed(f'.work/veneer-face-r9/V{i}-chains.npz',stats=np.array(stats),**{f'c{k}':c for k,c in enumerate(chains)})
 a=np.array(stats);a=a[a[:,2]>20];ids=np.where(np.diff(a[:,3])!=0)[0];print(i,'direction transitions',a[ids].tolist(),flush=True)
