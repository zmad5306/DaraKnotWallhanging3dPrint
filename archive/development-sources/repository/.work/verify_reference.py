import ast, hashlib, json, re, sys
from pathlib import Path
sys.path.insert(0,str(Path('.work/python-libs').resolve()))
import numpy as np
import trimesh
import manifold3d as md
from shapely.geometry import Polygon

root=Path(__file__).resolve().parents[1]
source=root/'reference/Dara-Clean-Reference.scad'
scad=source.read_text()
entries=re.findall(r'polygon\(points = (\[.*?\]), paths = (\[.*?\]), convexity',scad,flags=re.S)
for a,b in entries:
    pts=ast.literal_eval(a); paths=ast.literal_eval(b)
    poly=Polygon([pts[j] for j in paths[0]],[[pts[j] for j in path] for path in paths[1:]])
    assert poly.is_valid

renders=[]
for mode in ('front','angle','back','svg','bare','mesh'):
    r=json.loads((root/'.work'/f'render-{mode}.json').read_text())
    assert r['returncode']==0 and r['output_exists']
    assert 'ERROR:' not in r['stderr'] and 'WARNING:' not in r['stderr'], r['stderr']
    renders.append({'mode':mode,'passed':True,'seconds':r['seconds'],'log':r['stderr']})

full=trimesh.load_mesh(root/'.work/reference-render.stl')
bare=trimesh.load_mesh(root/'.work/reference-bare.stl')
assert full.is_watertight and full.is_winding_consistent and full.volume>0
assert bare.is_watertight and bare.is_winding_consistent
assert np.allclose(full.bounds,[[-457.2,-457.2,0],[457.2,457.2,24]],atol=.001)
previous=trimesh.load_mesh(root/'.work/reference-before-scale.stl')
assert np.allclose(full.extents,previous.extents*.75,atol=.001)
volume_ratio=full.volume/previous.volume
assert abs(volume_ratio-.75**3)<1e-5

def solid(mesh):
    result=md.Manifold(md.Mesh64(np.array(mesh.vertices),np.array(mesh.faces,dtype=np.uint64)))
    assert result.status()==md.Error.NoError, result.status()
    return result

full_solid=solid(full); bare_solid=solid(bare)
components=full_solid.decompose()
assert len(components)==1, len(components)
sections=[]
for master_z in (1,6,11.9,12.4,13,17.9,20,31.9):
    z=master_z*.75
    extra=full_solid.slice(z)-bare_solid.slice(z)
    extra_area=extra.area()
    if master_z==12.4:assert extra_area>1000
    else:assert abs(extra_area)<.1,(z,extra_area)
    sections.append({'z_mm':z,'fabric_only_area_mm2':round(extra_area,5)})

report={
    'date':'2026-10-11',
    'scad_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
    'openscad_version':'2021.01',
    'saved_polygons_valid':True,
    'external_scad_dependencies':False,
    'uniform_scaling':{
        'factor_xyz':[0.75,0.75,0.75],
        'overall_width_inches':36,
        'measured_extents_mm':full.extents.tolist(),
        'volume_ratio_to_previous':float(volume_ratio),
        'expected_volume_ratio':0.75**3,
    },
    'renders':renders,
    'full_render_mesh':{
        'watertight':bool(full.is_watertight),'consistent_winding':bool(full.is_winding_consistent),
        'connected_components':len(components),'bounds_mm':full.bounds.tolist(),
        'faces':len(full.faces),'positive_volume':bool(full.volume>0),
    },
    'fabric_support_check':{
        'method':'Compare horizontal sections of the full render with the knot-and-M-only render.',
        'result':'Fabric geometry exists only at its designated thin decorative layer; no lower support structures.',
        'sections':sections,
    },
    'visual_review':['front','angle','back'],
}
(root/'reference/verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
