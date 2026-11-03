from pathlib import Path
import sys,json
sys.path.insert(0,str(Path('.work/python-libs').resolve()))
import numpy as np,trimesh,manifold3d as md
D=json.loads(Path('.work/jointed-data.json').read_text())
def solid(m):return md.Manifold(md.Mesh64(m.vertices,m.faces.astype(np.uint64)))
for name,d in D.items():
    raw=solid(trimesh.load_mesh('.work/jointed-original-'+name+'.off'))
    solids=[]
    for i,pl in enumerate(d['placements']):
        fn=f'.work/jointed-{name[0].upper()}{i+1}.stl'
        m=trimesh.load_mesh(fn)
        assert m.is_watertight and m.is_winding_consistent and len(m.split())==1,(fn,'bad mesh')
        assert max(m.extents[:2])<246 and abs(m.bounds[0,2])<1e-5
        shift=3.2 if name=='frame' and m.extents[2]>15 else 0
        s=solid(m).translate([*pl['centre'],-shift]).rotate([0,0,-pl['angle']])
        added=(s-raw).volume()
        print(name,i+1,'added outside raw',round(added,4),flush=True)
        assert added<5,(name,i+1,'added geometry',added)
        solids.append(s)
    for i,s in enumerate(solids):
        for k,t in enumerate(solids[i+1:],i+1):
            volume=(s^t).volume()
            assert volume<.01,(name,'native overlap',i+1,k+1,volume)
    print(name,'all native meshes valid, in original shape, and mutually clear',flush=True)

