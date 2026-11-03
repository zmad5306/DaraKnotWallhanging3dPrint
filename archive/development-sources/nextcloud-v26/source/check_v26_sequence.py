import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path('work/python-libs').resolve()))
import trimesh,numpy as np,manifold3d as md
p=Path('outputs/Dara-Solid-Joint-Backs-v26');d=json.loads((p/'project-data.json').read_text());solids={}
for r in d['parts']:
 if not ('/knot/' in r['file'] or '/letter/' in r['file']):continue
 t=trimesh.load_mesh(p/r['file']);assert t.is_watertight and len(t.split())==1
 t.apply_transform(r['assembly_transform']);solids[r['part']]=md.Manifold(md.Mesh64(np.array(t.vertices),np.array(t.faces,dtype=np.uint64)))
 assert solids[r['part']].status()==md.Error.NoError
def joined(names):return md.Manifold.batch_boolean([solids[n] for n in names],md.OpType.Add)
checks=[]
def check(fixed,moving,axis,label):
 if not fixed or not moving:return
 a=joined(fixed);b=joined(moving);maximum=0
 for dist in [0,.15,.3,.6,1,2,3,4,5,6,7,8,12]:
  v=(a ^ b.translate(tuple(dist*x for x in axis))).volume();maximum=max(maximum,v)
 checks.append({'step':label,'fixed':fixed,'moving':moving,'withdrawal_direction':axis,'max_overlap_mm3':maximum,'passed':maximum<.02})
 assert maximum<.02,(label,maximum)
k=[n for n in solids if n.startswith('K')]
rows=[]
for row in range(1,6):
 names=sorted(n for n in k if int(n[1])==row);fixed=[]
 for col in range(1,6):
  moving=[n for n in names if int(n[2])==col]
  check(fixed,moving,[1,0,0],f'Knot row {row}, column {col}');fixed+=moving
 rows.append(names)
fixed=rows[0]
for i,moving in enumerate(rows[1:],2):
 check(fixed,moving,[0,-1,0],f'Join knot row {i} below earlier rows');fixed+=moving
fixed=['M_01']
for name,axis in [('M_03',[1,0,0]),('M_02',[1,0,0]),('M_05',[0,-1,0]),('M_04',[0,-1,0]),('M_08',[0,-1,0]),('M_06',[0,-1,0]),('M_07',[0,-1,0])]:
 check(fixed,[name],axis,'Add '+name);fixed.append(name)
(p/'assembly-sequence-validation.json').write_text(json.dumps({'method':'Solid intersection checks at 13 displacement samples along each prescribed withdrawal/insertion path. Checks geometry, not printer tolerance or physical handling.','all_passed':all(r['passed'] for r in checks),'steps':checks},indent=2))
print('Sequence passed:',len(checks),'steps')
