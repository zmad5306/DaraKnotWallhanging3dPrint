from pathlib import Path
import sys,re,json
sys.path.insert(0,str(Path('.work/python-libs').resolve()))
import numpy as np,trimesh,manifold3d as md
p=Path('working/Dara-Photo-Frame-A1-Jointed.scad');s=p.read_text()
for owner in [2,4,15,17]:
 m=trimesh.load_mesh(f'.work/wall-blocks-screwed/F{owner+1}-after.stl')
 assert m.is_watertight and m.is_winding_consistent and len(m.split())==1
 pts=np.round(m.vertices,7)
 a=md.Manifold(md.Mesh64(m.vertices,m.faces.astype(np.uint64)));b=md.Manifold(md.Mesh64(pts,m.faces.astype(np.uint64)))
 assert a.status()==b.status()==md.Error.NoError
 assert (a-b).volume()+(b-a).volume()<.005
 block=f'module preview_frame_{owner}() {{\n polyhedron(points='+json.dumps(pts.tolist(),separators=(',',':'))+',\n faces='+json.dumps(m.faces[:,::-1].tolist(),separators=(',',':'))+',convexity=50);\n}'
 s,n=re.subn(r'module preview_frame_'+str(owner)+r'\(\) \{.*?\n\}',lambda _:block,s,flags=re.S);assert n==1
p.write_bytes(s.replace('\n','\r\n').encode())
print('Refreshed F3, F5, F16, F18 preview meshes from the native slots and screw pilots.')
