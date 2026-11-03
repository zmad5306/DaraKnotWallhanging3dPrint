from pathlib import Path
import collections
import json
import sys
import xml.etree.ElementTree as E
import zipfile

ROOT = Path(__file__).resolve().parents[2]
WORK = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / '.work/python-libs'))
import numpy as np
import trimesh
from itertools import product


def maximum_nearest_error(reference, query):
    buckets = collections.defaultdict(list)
    for p, key in zip(reference, np.rint(reference * 1000).astype(int)):
        buckets[tuple(key)].append(p)
    maximum = 0.
    for p, key in zip(query, np.rint(query * 1000).astype(int)):
        candidates = buckets.get(tuple(key), [])
        error = min((float(np.linalg.norm(p - q)) for q in candidates), default=1.)
        if error >= 1e-4:
            for shift in product((-1, 0, 1), repeat=3):
                for q in buckets.get(tuple(key + shift), []):
                    error = min(error, float(np.linalg.norm(p - q)))
        maximum = max(maximum, error)
    return maximum

N = {'m': 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
P = '{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}'


def props(el):
    return {m.get('key'): m.get('value') for m in el.findall('metadata') if m.get('key')}


def transform(s):
    m = np.eye(4)
    m[:3, :] = np.array(list(map(float, s.split()))).reshape(4, 3).T
    return m


result = {'normal_meshes_match_source': True, 'settings_verified': True, 'parts': []}
layout = json.loads((ROOT / 'working/bambu/Dara-Photo-Frame-A1-Jointed/project-validation.json').read_text())
positions = {}
for pi, plate in enumerate(layout['plate_layout']):
    for item in plate['items']:
        positions.setdefault(item['name'], []).append(np.array([item['xy'][0] + (pi % 6) * 307.2,
                                                              item['xy'][1] - (pi // 6) * 307.2, 0]))
with zipfile.ZipFile(WORK / 'validated.3mf') as z:
    assert z.testzip() is None
    config = E.fromstring(z.read('Metadata/model_settings.config'))
    settings = json.loads(z.read('Metadata/project_settings.config'))
    for key, value in [('wall_loops', '4'), ('sparse_infill_density', '15%'), ('sparse_infill_pattern', 'gyroid')]:
        assert settings[key] == value
    root = E.fromstring(z.read('3D/3dmodel.model'))
    objects = {o.get('id'): o for o in root.find('m:resources', N)}
    builds = collections.defaultdict(list)
    for item in root.find('m:build', N):
        builds[item.get('objectid')].append(transform(item.get('transform')))
    modifiers = 0
    for co in config.findall('object'):
        cp = props(co)
        name = cp['name']
        oi = co.get('id')
        comps = {c.get('objectid'): c for c in objects[oi].find('m:components', N)}
        count = len(builds[oi])
        assert count == (32 if name == 'Retainer' else 1), (name, count)
        for key, value in [('wall_loops', '4'), ('sparse_infill_density', '15%'), ('sparse_infill_pattern', 'gyroid')]:
            assert cp.get(key, value) == value, (name, key, cp.get(key))
        for part in co.findall('part'):
            if part.get('subtype') == 'modifier_part':
                modifiers += 1
                assert props(part)['sparse_infill_density'] == '100%'
                continue
            comp = comps[part.get('id')]
            child = E.fromstring(z.read(comp.get(P + 'path').lstrip('/')))
            obj = child.find(f'm:resources/m:object[@id="{part.get("id")}"]', N)
            verts = np.array([[float(v.get(k)) for k in ('x', 'y', 'z')] for v in obj.findall('m:mesh/m:vertices/m:vertex', N)])
            faces = np.array([[int(v.get(k)) for k in ('v1', 'v2', 'v3')] for v in obj.findall('m:mesh/m:triangles/m:triangle', N)])
            mesh = trimesh.Trimesh(verts, faces, process=False)
            mesh.apply_transform(transform(comp.get('transform')))
            mesh.apply_transform(builds[oi][0])
            mesh.apply_translation(-positions[name][0])
            source = trimesh.load_mesh(ROOT / 'working/stl/Dara-Photo-Frame-A1-Jointed' / (name + '.stl'))
            assert len(mesh.faces) == len(source.faces)
            error = max(maximum_nearest_error(mesh.vertices, source.vertices), maximum_nearest_error(source.vertices, mesh.vertices))
            assert error < 1e-4, (name, error)
            centroid_error = maximum_nearest_error(source.triangles_center, mesh.triangles_center)
            assert centroid_error < 1e-4
            assert abs(mesh.volume - source.volume) / source.volume < 1e-5
            for bt in builds[oi]:
                assert np.allclose(bt[:3, :3], np.eye(3))
            assert abs(mesh.bounds[0, 2]) < 1e-5
            result['parts'].append({'name': name, 'quantity': count, 'max_vertex_error_mm': float(error), 'triangles': len(faces)})
    assert modifiers == 73
    assert len(config.findall('plate')) == layout['plates']
    assert sum(len(v) for v in builds.values()) == 70
    assert len([p for p in z.namelist() if p.endswith('.gcode')]) == layout['plates']
    result.update(plates=layout['plates'], pieces=70, modifier_volumes=modifiers)
    result['source_part_count'] = len(result['parts'])
(WORK / 'package-validation.json').write_text(json.dumps(result, indent=2))
print(json.dumps({k: v for k, v in result.items() if k != 'parts'}, indent=2))
