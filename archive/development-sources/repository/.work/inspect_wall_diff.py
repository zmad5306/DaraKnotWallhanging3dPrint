from pathlib import Path
import sys
sys.path.insert(0,str(Path('.work/python-libs').resolve()))
import numpy as np,trimesh,manifold3d as md
out=Path('.work/wall-blocks-screwed')
def load(n):
 m=trimesh.load_mesh(out/(n+'.stl'));return md.Manifold(md.Mesh64(m.vertices,m.faces.astype(np.uint64)))
a=load('F18-after');o=load('F18-before');s=load('slots-3');d=(o-a)-s
print('volume',d.volume(),'bounds',d.bounding_box())
print('parts',[(x.volume(),x.bounding_box()) for x in d.decompose()])
