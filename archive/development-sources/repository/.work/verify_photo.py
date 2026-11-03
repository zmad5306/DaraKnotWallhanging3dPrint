import sys,hashlib,re,ast,json
from pathlib import Path
sys.path.insert(0,'.work/python-libs')
import numpy as np,trimesh,manifold3d as md
from shapely.geometry import Polygon
from shapely import affinity
ref=Path('reference/Dara-Clean-Reference.scad');cad=Path('working/Dara-Photo-Frame.scad')
assert hashlib.sha256(ref.read_bytes()).hexdigest()=='d214952476c9a398b54235cc27edc35c7365a6b085cf850d1e967f29ffa2a237'
a=ref.read_text();b=cad.read_text()
assert b[b.index('module knot_outline()'):b.index('module photo_loop_1()')].strip()==a[a.index('module knot_outline()'):].strip()
for name in ['slider','backer','frame-sliders']:
 m=trimesh.load_mesh('.work/photo-'+name+'.stl');assert m.is_watertight and m.is_winding_consistent
 assert len(m.split())==1
 print(name,'watertight, one solid',m.bounds.tolist())
frame=trimesh.load_mesh('.work/photo-frame-sliders.stl'); solid=md.Manifold(md.Mesh64(np.array(frame.vertices),np.array(frame.faces,dtype=np.uint64)))
x,y=re.findall(r'polygon\(points = (\[.*?\]), paths = (\[.*?\]), convexity',a,re.S)[0];pts=ast.literal_eval(x);paths=ast.literal_eval(y)
poly=affinity.scale(Polygon([pts[j] for j in paths[0]],[[pts[j] for j in path] for path in paths[1:]]),.75,.75,origin=(0,0))
for z in [2.1,6,13.4]:
 assert abs(solid.slice(z).area()-poly.area)<.1
print('Front rail sections unchanged above rabbet; reference hash and copied artwork identical.')
