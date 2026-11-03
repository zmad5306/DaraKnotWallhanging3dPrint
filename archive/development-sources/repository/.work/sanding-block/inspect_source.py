from pathlib import Path
import json, zipfile, xml.etree.ElementTree as ET
import numpy as np
import trimesh

SRC = Path(r'C:\Users\Zach\Downloads\Sanding_Block.3mf')
OUT = Path(__file__).resolve().parent
C = '{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}'
with zipfile.ZipFile(SRC) as z:
    cfg = ET.fromstring(z.read('Metadata/model_settings.config'))
    names = {p.get('id'): o.find('metadata').get('value')
             for o in cfg.findall('object') for p in o.findall('part')}
    for n in z.namelist():
        if n.endswith('.webp'):
            (OUT / Path(n).name).write_bytes(z.read(n))
        if n.startswith('3D/Objects/'):
            r = ET.fromstring(z.read(n))
            o = r.find(C+'resources/'+C+'object')
            m = o.find(C+'mesh')
            v = [[float(a.get(k)) for k in ('x', 'y', 'z')] for a in m.find(C+'vertices')]
            f = [[int(a.get(k)) for k in ('v1', 'v2', 'v3')] for a in m.find(C+'triangles')]
            tm = trimesh.Trimesh(v, f, process=True)
            name = names[o.get('id')]
            tm.export(OUT/name)
            print(name, 'bounds', tm.bounds.tolist(), 'volume', tm.is_volume)
    s = json.loads(z.read('Metadata/project_settings.config'))
    print({k:v for k,v in s.items() if any(a in k for a in ('support','fuzzy','brim','wall_loops','infill','layer_height'))})
