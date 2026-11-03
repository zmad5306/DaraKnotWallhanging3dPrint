from pathlib import Path
import ast,re,json,sys
sys.path.insert(0,str(Path('.work/python-libs').resolve()))
import numpy as np,trimesh,manifold3d as md

path=Path('working/Dara-Photo-Frame-A1-Jointed.scad')
out=Path('.work/photo-retainers')
report=json.loads((out/'verification.json').read_text())
assert len(report['parts'])==30 and len(report['pilots'])==32
s=path.read_text()
def value(name):return ast.literal_eval(re.search(r'^'+name+r' = (.*?);',s,re.M).group(1))
def solid(m):
    g=md.Manifold(md.Mesh64(m.vertices,np.array(m.faces,dtype=np.uint64)))
    assert g.status()==md.Error.NoError
    return g
placements=value('frame_placements')
native=[]
affected=[]
for i,p in enumerate(placements):
    m=trimesh.load_mesh(out/f'F{i+1}.stl')
    m.apply_translation([*p[1],0])
    m.apply_transform(trimesh.transformations.rotation_matrix(np.deg2rad(-p[0]),[0,0,1]))
    native.append(m)
    if not value('frame_retainers')[i]:continue
    affected.append(i+1)
    block=f'module preview_frame_{i}() {{\n polyhedron(points='
    block+=json.dumps(np.round(m.vertices,7).tolist(),separators=(',',':'))
    block+=',\n faces='+json.dumps(m.faces[:,::-1].tolist(),separators=(',',':'))+',convexity=50);\n}'
    s,n=re.subn(r'module preview_frame_'+str(i)+r'\(\) \{.*?\n\}',lambda _:block,s,flags=re.S)
    assert n==1
checks=[]
for i,m in enumerate(native):
    body=s.split(f'module preview_frame_{i}() {{')[1].split('\n}')[0]
    a,b=re.search(r'polyhedron\(points=(\[.*?\]),\s*faces=(\[.*?\]),convexity',body,re.S).groups()
    cached=trimesh.Trimesh(vertices=np.array(json.loads(a)),faces=np.array(json.loads(b))[:,::-1],process=False)
    assert cached.is_watertight and cached.is_winding_consistent and cached.bounds[0,2]==0
    c,n=solid(cached),solid(m)
    diff=(c-n).volume()+(n-c).volume()
    assert diff<.002,('cache/native mismatch',i+1,diff)
    checks.append({'part':f'F{i+1}','difference_mm3':diff})
s=s.replace('photo_preview_ready = false; // Enable only after native geometry and cache verification.',
            'photo_preview_ready = true; // Regenerated from verified native flat-back sections.')
path.write_text(s)
report['preview_cache']={'regenerated_sections':affected,'native_comparisons':checks}
(out/'verification.json').write_text(json.dumps(report,indent=2))
print(f'Regenerated {len(affected)} affected frame caches; all 30 match native geometry.')
