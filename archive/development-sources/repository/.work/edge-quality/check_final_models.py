import sys,json,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from validate_print_project import *
from scipy.spatial import cKDTree
base=json.loads((ROOT/'.work/edge-quality/staged.json').read_text())
with zipfile.ZipFile(ROOT/'.work/edge-quality/models-final.3mf') as z:
    config=ET.fromstring(z.read('Metadata/model_settings.config'))
    root=ET.fromstring(z.read('3D/3dmodel.model'))
    for obj in config.findall('object'):
        name=props(obj)['name']

        oid=obj.get('id');part=obj.find("part[@subtype='normal_part']")
        parent=root.find(f"m:resources/m:object[@id='{oid}']",N)
        comp=next(c for c in parent.find('m:components',N) if c.get('objectid')==part.get('id'))
        child=ET.fromstring(z.read(comp.get(P+'path').lstrip('/')))
        mo=child.find(f"m:resources/m:object[@id='{part.get('id')}']",N)
        verts=[[float(v.get(k)) for k in ('x','y','z')] for v in mo.findall('m:mesh/m:vertices/m:vertex',N)]
        faces=[[int(f.get(k)) for k in ('v1','v2','v3')] for f in mo.findall('m:mesh/m:triangles/m:triangle',N)]
        mesh=trimesh.Trimesh(verts,faces,process=False)
        mesh.apply_transform(transform(comp.get('transform')))
        build=next(b for b in root.find('m:build',N) if b.get('objectid')==oid)
        mesh.apply_transform(transform(build.get('transform')))
        position=None
        for pi,plate in enumerate(base['plate_layout']):
            for item in plate['items']:
                if item['name']==name and position is None:position=np.array([item['xy'][0]+(pi%6)*307.2,item['xy'][1]-(pi//6)*307.2,0])
        mesh.apply_translation(-position)
        ref=trimesh.load_mesh((ROOT/'working/stl/Dara-Print-Checks' if name.startswith('Test-') else STLS)/(name+'.stl'))
        assert len(mesh.faces)==len(ref.faces),name
        for label,a,b in [('vertices',ref.vertices,mesh.vertices),('centers',ref.triangles_center,mesh.triangles_center)]:
            d,i=cKDTree(a).query(b);ix=d.argmax()
            assert d.max()<1e-4,(name,label,d.max()); print(name,label,round(d.max(),8))


