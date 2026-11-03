from pathlib import Path
import sys,json,subprocess,concurrent.futures
sys.path.insert(0,str(Path('.work/python-libs').resolve()))
import numpy as np,trimesh,manifold3d as md
EXE=r'C:\Program Files (x86)\OpenSCAD\openscad.exe'
SCAD='working/Dara-Photo-Frame-A1-Jointed.scad'
D=json.loads(Path('.work/jointed-data.json').read_text())
def solid(m):return md.Manifold(md.Mesh64(m.vertices,m.faces.astype(np.uint64)))
def run(i):
    fn=f'.work/oriented-M{i+1}.stl'
    p=subprocess.run([EXE,'--hardwarnings','--camera=0,0,0,0,0,0,700','-D','view_mode="section"','-D','part_family="M"','-D',f'section_index={i+1}','--export-format=binstl','-o',fn,SCAD],capture_output=True,text=True,timeout=180)
    assert p.returncode==0 and 'WARNING:'not in p.stderr and 'ERROR:'not in p.stderr,p.stderr
    mesh=trimesh.load_mesh(fn)
    assert mesh.is_watertight and len(mesh.split())==1
    assert abs(mesh.bounds[0,2])<1e-5 and max(mesh.extents[:2])<246
    # Undo the new face-down placement and compare with the validated solid.
    pl=D['M']['placements'][i]
    a=solid(mesh).translate([0,0,-10.5]).rotate([180,0,0]).translate([*pl['centre'],0]).rotate([0,0,-pl['angle']])
    old=trimesh.load_mesh(f'.work/mounted-M{i+1}.stl')
    b=solid(old).translate([*pl['centre'],-6.5]).rotate([0,0,-pl['angle']])
    diff=(a-b).volume()+(b-a).volume()
    assert diff<.02,(i,diff)
    print('M'+str(i+1),'front at bed; size',np.round(mesh.extents,3),'solid difference',round(diff,7),flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(run,range(6)))
