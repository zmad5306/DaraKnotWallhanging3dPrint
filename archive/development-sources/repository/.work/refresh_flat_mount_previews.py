from pathlib import Path
import sys,json,re
sys.path.insert(0,str(Path('.work/python-libs').resolve()))
import trimesh,numpy as np
path=Path('working/Dara-Photo-Frame-A1-Jointed.scad');s=path.read_text()
D=json.loads(Path('.work/jointed-data.json').read_text())
A=json.loads(Path('.work/flat-mount-affected.json').read_text())
assert Path('.work/flat-mounts-verification.json').exists()
for family,ids in A.items():
    for i in ids:
        label=f'{family[0].upper()}{i+1}'
        pl=D[family]['placements'][i]
        old=trimesh.load_mesh(f'.work/jointed-{label}.stl')
        zshift=3.2 if family=='frame' and old.extents[2]>15 else 0
        m=trimesh.load_mesh(f'.work/flat-mounted-{label}.stl')
        m.apply_translation([*pl['centre'],-zshift])
        m.apply_transform(trimesh.transformations.rotation_matrix(np.deg2rad(-pl['angle']),[0,0,1]))
        assert m.is_watertight and len(m.split())==1
        block=f'module preview_{family}_{i}() {{\n polyhedron(points='
        block+=json.dumps(np.round(m.vertices,7).tolist(),separators=(',',':'))
        block+=',\n faces='+json.dumps(m.faces[:,::-1].tolist(),separators=(',',':'))+',convexity=50);\n}'
        s,n=re.subn(r'module preview_'+family+'_'+str(i)+r'\(\) \{.*?\n\}',lambda _:block,s,flags=re.S)
        assert n==1,(family,i,n)
s=s.replace('mount_preview_ready = false; // Rebuild after native flat-back verification.','mount_preview_ready = true; // Refreshed from the validated native sections with mounts.')
path.write_text(s)
print('Refreshed 16 flat-back section previews. CAD bytes:',path.stat().st_size)
