import sys,json,zipfile,collections,re
from pathlib import Path
sys.path[:0]=['.work/python-libs','scripts']
import numpy as np
from validate_production_split import Project
p=Project(Path('Letter.3mf'))
geom=json.loads(Path('release/veneer-nub-cleanup-r8/Letter-geometry.json').read_text())
for g in geom['objects']:
 row=p.rows[g['name']];m=row['parts'][0]['mesh'].copy();m.apply_transform(row['T']); pose=np.array(g['pose']);m.apply_transform(np.linalg.inv(pose))
 np.savez_compressed('.work/veneer-face-r9/'+g['name'][:2]+'-mesh.npz',v=m.vertices,f=m.faces,pose=pose)
 print(g['name'][:2],row['plate'],m.bounds.tolist(),flush=True)
 text=p.z.read(f"Metadata/plate_{row['plate']}.gcode").decode()
 Path('.work/veneer-face-r9/'+g['name'][:2]+'.gcode').write_text(text)
 print(text[:3000],flush=True)
 print('layers',collections.Counter(re.findall(r'; LAYER_HEIGHT: ([^\n]+)',text)),flush=True)
