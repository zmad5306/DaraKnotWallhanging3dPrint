from pathlib import Path
import sys,json,re,ast
sys.path.insert(0,str(Path('.work/python-libs').resolve()))
import numpy as np,trimesh,manifold3d as md
OUT=Path('.work/repartition');N=OUT/'native';CAD=Path('working/Dara-Photo-Frame-A1-Jointed.scad')
report=json.loads((N/'verification.json').read_text());assert report['all_pass']
D=json.loads((OUT/'jointed-data.json').read_text());s=CAD.read_text();blocks=[];checks=[]
for kind,d in D.items():
 dimensions=[]
 for i,pl in enumerate(d['placements']):
  m=trimesh.load_mesh(N/f'{kind[0].upper()}{i+1}.stl');dimensions.append(m.extents.tolist())
  m.apply_translation([*pl[1],0]);m.apply_transform(trimesh.transformations.rotation_matrix(np.deg2rad(-pl[0]),[0,0,1]))
  vertices=np.round(m.vertices,7);cached=trimesh.Trimesh(vertices=vertices,faces=m.faces,process=False);assert cached.is_watertight and cached.is_winding_consistent
  a=md.Manifold(md.Mesh64(m.vertices,m.faces.astype(np.uint64)));b=md.Manifold(md.Mesh64(vertices,m.faces.astype(np.uint64)));assert a.status()==b.status()==md.Error.NoError
  diff=(a-b).volume()+(b-a).volume();assert diff<.005,(kind,i,diff)
  checks.append({'part':f'{kind[0].upper()}{i+1}','difference_mm3':diff})
  blocks.append(f'module preview_{kind}_{i}() {{\n polyhedron(points='+json.dumps(vertices.tolist(),separators=(',',':'))+',\n faces='+json.dumps(m.faces[:,::-1].tolist(),separators=(',',':'))+',convexity=50);\n}\n')
 s,n=re.subn(r'^'+kind+r'_print_footprints = .*?;',lambda _:kind+'_print_footprints = '+json.dumps(dimensions,separators=(',',':'))+';',s,flags=re.M);assert n==1
s=s[:s.index('// Preview tessellations are regenerated after native geometry validation.')]
s+='// Exact native section tessellations, verified 2026-10-12. F6 uses the CSG.\n'+''.join(blocks)
s+='module preview_section(kind,i) {\n'
for kind,d in D.items():
 for i in range(len(d['parts'])):s+=f'    if(kind=="{kind}" && i=={i}) preview_{kind}_{i}();\n'
s+='}\n';s=s.replace('mount_preview_ready = false;','mount_preview_ready = true;').replace('photo_preview_ready = false;','photo_preview_ready = true;')
s=s.replace('// All sections fit a 253 mm square including tongues at the saved flat rotations.','// All 26 native-rendered sections fit a 253 mm square including tongues at the saved flat rotations.\n// Largest native footprint: F6, 252.392 x 252.470 mm; minimum placed edge clearance 1.758 mm.\n// No neighboring pair can be combined into one 253 mm piece, including retained lap extensions.\n// Partition search minimizes joints first, then pieces; no claim of a proven global minimum.')
CAD.write_text(s);report['preview_cache_checks']=checks;(N/'verification.json').write_text(json.dumps(report,indent=2));print('Refreshed all 26 native preview caches and measured footprints.')
