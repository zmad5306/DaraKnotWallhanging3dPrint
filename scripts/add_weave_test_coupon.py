"""Add a full-width F7 weave coupon to the existing AMS fit-test plate.

Run to stage .work/weave-coupon/with-weave.3mf. Open it in Bambu Studio,
slice plate 30 and export that plate's sliced file. Run again with --slices
PATH to combine just that export with the staged editable project. Production
plates 1-29 and project settings must remain byte-identical. Audit the candidate
with validate_print_project.py before publishing it.
"""
import argparse
import copy
import json
import math
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

from append_print_check_plate import PACKAGE, CHECKS, STLS, sha
from build_jointed_bambu_project import ROOT, C, P, R, IDENTITY, tag, meta, model, xml, mesh_object, uid, read_array
from colorize_print_project import weave_modifier, setmeta
from validate_print_project import props
import numpy as np
import trimesh

WORK = ROOT / '.work/weave-coupon'
NAME = 'Test-Weave-Full-Width'


def read_zip(path):
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        return {n: z.read(n) for n in z.namelist()}


def write_zip(path, files):
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        for n, data in files.items():
            z.writestr(n, data)


def stage(source, baseline_path):
    files = read_zip(source)
    base = json.loads(baseline_path.read_text())
    assert sha(source) == base['project_sha256']
    assert not any(p['name'] == NAME for p in base['test_plate']['parts'])
    WORK.mkdir(exist_ok=True)
    (WORK / 'baseline.3mf').write_bytes(source.read_bytes())
    cad = (ROOT / 'working/Dara-Photo-Frame-A1-Jointed.scad').read_text()
    p = read_array(cad, 'frame_placements')[6]
    joint = read_array(cad, 'frame_joints')[0]
    mesh = trimesh.load_mesh(STLS / 'F7.stl')
    mesh.apply_translation([*p[1], -p[3]])
    mesh.apply_transform(trimesh.transformations.rotation_matrix(math.radians(-p[0]), [0, 0, 1]))
    mesh.apply_translation([-joint[2][0], -joint[2][1], 0])
    mesh.apply_transform(trimesh.transformations.rotation_matrix(math.radians(-joint[3]), [0, 0, 1]))
    # Slice along the straight ribbon, well away from the crossing and joints.
    # X clipping faces lie outside both rails: only the two short ends are cut.
    crop = trimesh.creation.box(extents=[140, 24, 40])
    crop.apply_translation([-40, -78, 10])
    mesh = trimesh.boolean.intersection([mesh, crop], engine='manifold')
    assert mesh.bounds[0, 0] > -110 + 5 and mesh.bounds[1, 0] < 30 - 5
    assert mesh.is_volume and len(mesh.split()) == 1
    assert np.allclose(mesh.bounds[:, 2], [0, 13.5], atol=1e-4)
    origin = (mesh.bounds[0] + mesh.bounds[1]) / 2
    origin[2] = mesh.bounds[0, 2]
    mesh.apply_translation(-origin)
    path = CHECKS / (NAME + '.stl')
    mesh.export(path)
    mesh = trimesh.load_mesh(path)
    wood, evidence = weave_modifier(mesh)
    assert mesh.bounds[0, 0] + 10 < wood.bounds[0, 0]
    assert mesh.bounds[1, 0] - 10 > wood.bounds[1, 0]
    root = ET.fromstring(files['3D/3dmodel.model'])
    config = ET.fromstring(files['Metadata/model_settings.config'])
    rels = ET.fromstring(files['3D/_rels/3dmodel.model.rels'])
    plate = config.findall('plate')[-1]
    assert props(plate)['plater_id'] == '30'
    resources = root.find(tag('resources'))
    build = root.find(tag('build'))
    layout = base['plate_layout'][-1]
    # Move only the three small photo coupons to make a clear 68 x 24 mm area.
    lows = {'Test-Photo-Frame': [145, 218], 'Test-Photo-Backer': [174, 222], 'Test-Photo-Tab': [145, 198]}
    for item in layout['items']:
        if item['name'] not in lows:
            continue
        bounds = np.array(item['bounds'])
        delta = np.array(lows[item['name']]) - bounds[0, :2]
        bounds[:, :2] += delta
        item['bounds'] = bounds.tolist()
        item['xy'] = (np.array(item['xy']) + delta).tolist()
        b = next(b for b in build if b.get('objectid') == str(item['object_id']))
        t = b.get('transform').split()
        t[9] = str(float(t[9]) + delta[0]); t[10] = str(float(t[10]) + delta[1])
        b.set('transform', ' '.join(t))
    oid = 30000
    assert all(o.get('id') != str(oid) for o in resources)
    child_path = f'3D/Objects/{NAME}.model'
    child = model(); child_res = ET.SubElement(child, tag('resources'))
    obj = ET.SubElement(resources, tag('object'), id=str(oid), type='model', attrib={'{'+P+'}UUID': uid()})
    comps = ET.SubElement(obj, tag('components'))
    co = ET.Element('object', id=str(oid))
    for k, v in [('name', NAME), ('extruder', 1), ('enable_support', 1),
                 ('support_on_build_plate_only', 0), ('brim_type', 'outer_only')]:
        meta(co, k, v)
    for i, m in enumerate((mesh, wood), 1):
        pid = oid + i
        mesh_object(child_res, pid, m)
        ET.SubElement(comps, tag('component'), objectid=str(pid), transform=IDENTITY,
                      attrib={'{'+P+'}path': '/'+child_path, '{'+P+'}UUID': uid()})
        part = ET.SubElement(co, 'part', id=str(pid), subtype='normal_part' if i == 1 else 'modifier_part')
        meta(part, 'name', NAME if i == 1 else NAME + ' - Wood weave and backing skin')
        meta(part, 'extruder', i)
    files[child_path] = xml(child)
    ET.SubElement(rels, '{'+R+'}Relationship', Target='/'+child_path, Id='weave-test',
                  Type='http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel')
    position = np.array([12, 210]) - mesh.bounds[0, :2]
    ET.SubElement(build, tag('item'), objectid=str(oid), printable='1',
                  transform=f'1 0 0 0 1 0 0 0 1 {position[0]+1536:.9f} {position[1]-1228.8:.9f} 0',
                  attrib={'{'+P+'}UUID': uid()})
    inst = ET.SubElement(plate, 'model_instance')
    for k, v in [('object_id', oid), ('instance_id', 0), ('identify_id', oid + 1)]:
        meta(inst, k, v)
    layout['name'] = 'PRINT FIRST - Hardware, lap and weave tests'
    setmeta(plate, 'plater_name', '30 - ' + layout['name'])
    layout['items'].append({'name': NAME, 'object_id': oid, 'instance_id': 0, 'identify_id': oid + 1,
                            'xy': position.tolist(), 'bounds': (mesh.bounds + [*position, 0]).tolist()})
    # All coupon rectangles are separated by at least 8 mm. The unchanged
    # tower has a separate conservative reserved rectangle including its brim.
    rectangles = [(i['name'], np.array(i['bounds'])[:, :2]) for i in layout['items']]
    for i, (name, a) in enumerate(rectangles):
        assert min(*a[0], *(256-a[1])) > 3
        for other, b in rectangles[i+1:]:
            assert np.any(a[1]+8 < b[0]) or np.any(b[1]+8 < a[0]), (name, other)
        tower = np.array([[95, 210], [133, 248]])
        assert np.any(a[1]+3 < tower[0]) or np.any(tower[1]+3 < a[0]), name
    config[:] = config.findall('object') + [co] + config.findall('plate') + config.findall('assemble')
    # Otherwise Bambu trusts the old embedded thumbnails despite edited XML.
    for md in list(plate.findall('metadata')):
        if md.get('value', '').endswith('.png'):
            files.pop(md.get('value'), None)
            plate.remove(md)
    files.pop('Metadata/plate_30_small.png', None)
    files['3D/3dmodel.model'] = xml(root)
    files['Metadata/model_settings.config'] = xml(config)
    ET.register_namespace('', R); files['3D/_rels/3dmodel.model.rels'] = xml(rels); ET.register_namespace('', C)
    out = WORK / 'with-weave.3mf'
    write_zip(out, files)
    test = base['test_plate']
    test['parts'].append({'name': NAME, 'file': path.name, 'sha256': sha(path), 'triangles': len(mesh.faces),
                          'source': 'F7.stl; frame-joint-1 coordinates X=-110..30, Y=-90..-66; both side rails uncut',
                          'source_stl_sha256': sha(STLS/'F7.stl'), 'dimensions_mm': mesh.extents.tolist(),
                          'modifiers': [], 'color_modifier': {'filament': 2, 'z_mm': wood.bounds[:, 2].tolist(), **evidence},
                          'quantity': 1, 'plate': 30})
    test.update(pieces=10, plate_layout=copy.deepcopy(layout), sliced=False,
                full_width_weave_test=NAME, color_modifier_count=1)
    test['filament_assignment'][NAME] = f'White body; wood weave/backing at Z={wood.bounds[0,2]:g}..{wood.bounds[1,2]:g} mm'
    base.update(pieces=80, distinct_parts=49, test_pieces=10, project_sha256=sha(out))
    (WORK / 'staged-validation.json').write_text(json.dumps(base, indent=2)+'\n')
    print(json.dumps({'project': str(out), 'coupon_dimensions_mm': mesh.extents.tolist()}, indent=2))


def merge(slices, previews=None):
    files = read_zip(WORK / 'with-weave.3mf'); sliced = read_zip(slices)
    base = json.loads((WORK / 'staged-validation.json').read_text())
    config = ET.fromstring(files['Metadata/model_settings.config'])
    sliced_config = ET.fromstring(sliced['Metadata/model_settings.config'])
    stats = ET.fromstring(sliced['Metadata/slice_info.config'])
    assert len(stats.findall('plate')) == 1
    stat = stats.find('plate'); number = props(stat)['index']
    tp = next(p for p in sliced_config.findall('plate') if props(p)['plater_id'] == number)
    plate = config.findall('plate')[-1]
    exported = {o.get('name'): o.get('identify_id') for o in stat.findall('object')}
    names = {o.get('id'): props(o)['name'] for o in config.findall('object')}
    assert set(exported) == {i['name'] for i in base['plate_layout'][-1]['items']}
    gcode = sliced[props(tp)['gcode_file']].decode()
    labels = set(re.search(r'^; model label id: (.*)$', gcode, re.M)[1].split(','))
    assert labels == set(exported.values()), (labels, exported)
    for inst in plate.findall('model_instance'):
        setmeta(inst, 'identify_id', exported[names[props(inst)['object_id']]])
    for item in base['plate_layout'][-1]['items']:
        item['identify_id'] = int(exported[item['name']])
    # Single-plate export may renumber it to plate 1; normalize archive paths.
    prefix = 'Metadata/plate_' + number
    for n, data in sliced.items():
        if n.startswith(prefix + '.') or n.startswith(prefix + '_'):
            files['Metadata/plate_30' + n[len(prefix):]] = data
    for k, v in props(tp).items():
        if k.endswith('_file') and v:
            target = v.replace(prefix, 'Metadata/plate_30')
            files[target] = sliced[v]
            setmeta(plate, k, target)
    sequences = json.loads(files['Metadata/filament_sequence.json'])
    sequences['plate_30'] = json.loads(sliced['Metadata/filament_sequence.json'])['plate_' + number]
    files['Metadata/filament_sequence.json'] = json.dumps(sequences).encode()
    if previews:
        # GUI Save Project As refreshes model thumbnails; a sliced-only export
        # can retain thumbnails loaded from the source archive.
        rendered = read_zip(previews)
        for k, v in props(plate).items():
            if k.endswith('_file') and v.endswith('.png'):
                files[v] = rendered[v]
    si = ET.fromstring(files['Metadata/slice_info.config'])
    old_stat = next(p for p in si.findall('plate') if props(p)['index'] == '30')
    si.remove(old_stat); setmeta(stat, 'index', 30); si.append(stat)
    files['Metadata/slice_info.config'] = xml(si)
    files['Metadata/model_settings.config'] = xml(config)
    out = WORK / 'complete-with-weave.3mf'; write_zip(out, files)
    original = read_zip(WORK / 'baseline.3mf')
    for i in range(1, 30):
        assert original[f'Metadata/plate_{i}.gcode'] == files[f'Metadata/plate_{i}.gcode']
    assert original['Metadata/project_settings.config'] == files['Metadata/project_settings.config']
    base['project_sha256'] = sha(out)
    base['test_plate'].update(sliced=True, production_gcodes_byte_identical=True,
                              plate_layout=copy.deepcopy(base['plate_layout'][-1]))
    base['weave_coupon_workflow'] = {'source_project_sha256': sha(WORK/'baseline.3mf'),
                                    'plate30_export_sha256': sha(slices), 'production_gcodes_byte_identical': True}
    out.with_suffix('.json').write_text(json.dumps(base, indent=2)+'\n')
    print(out)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source', type=Path, default=PACKAGE/'Dara-Photo-Frame-A1-Complete.3mf')
    ap.add_argument('--baseline', type=Path, default=PACKAGE/'project-validation.json')
    ap.add_argument('--slices', type=Path)
    ap.add_argument('--previews', type=Path, help='GUI Save Project As export for refreshed plate thumbnails')
    args = ap.parse_args()
    merge(args.slices, args.previews) if args.slices else stage(args.source, args.baseline)
