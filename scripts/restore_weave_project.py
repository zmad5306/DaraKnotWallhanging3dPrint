"""Stage the restored crossing texture and two dedicated test plates.

Export the revised native CAD first with export_jointed_stls.py. This replaces
only frame meshes/color masks, crops the new F7 test, and removes already printed
hardware tests from the project. The archived STL coupons remain available.
Slice the candidate in Bambu Studio before publishing and run the full audit.
"""
import argparse
import copy
import json
import math
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from add_weave_test_coupon import read_zip, write_zip, NAME
from build_jointed_bambu_project import ROOT, tag, P, R, mesh_object, xml, read_array
from colorize_print_project import weave_modifier, setmeta
from validate_print_project import transform, props, digest
from export_jointed_stls import verify
import numpy as np
import trimesh

WORK = ROOT / '.work/weave-restore'
STLS = ROOT / 'working/stl/Dara-Photo-Frame-A1-Jointed'
CHECKS = ROOT / 'working/stl/Dara-Print-Checks'
CAD = ROOT / 'working/Dara-Photo-Frame-A1-Jointed.scad'


def crop_weave(cad):
    p = read_array(cad, 'frame_placements')[6]
    j = read_array(cad, 'frame_joints')[0]
    m = trimesh.load_mesh(STLS / 'F7.stl')
    m.apply_translation([*p[1], -p[3]])
    m.apply_transform(trimesh.transformations.rotation_matrix(math.radians(-p[0]), [0, 0, 1]))
    m.apply_translation([-j[2][0], -j[2][1], 0])
    m.apply_transform(trimesh.transformations.rotation_matrix(math.radians(-j[3]), [0, 0, 1]))
    box = trimesh.creation.box(extents=[140, 24, 40])
    box.apply_translation([-40, -78, 10])
    m = trimesh.boolean.intersection([m, box], engine='manifold')
    origin = m.bounds.mean(axis=0); origin[2] = m.bounds[0, 2]
    m.apply_translation(-origin)
    m.export(CHECKS / (NAME + '.stl'))
    verify(CHECKS / (NAME + '.stl'))
    return trimesh.load_mesh(CHECKS / (NAME + '.stl'))


def refresh_preview_cache():
    cad = CAD.read_text()
    for i in range(20):
        m = trimesh.load_mesh(STLS / f'F{i+1}.stl')
        block = (f'module preview_frame_{i}() {{\n polyhedron(points=' +
                 json.dumps(np.round(m.vertices, 7).tolist(), separators=(',', ':')) +
                 ',\n faces=' + json.dumps(m.faces[:, ::-1].tolist(), separators=(',', ':')) +
                 ',convexity=50);\n}')
        cad, n = re.subn(r'module preview_frame_' + str(i) + r'\(\) \{.*?\n\}', lambda _: block, cad, flags=re.S)
        assert n == 1
    CAD.write_text(cad)
    manifest = json.loads((STLS / 'manifest.json').read_text())
    manifest['source_sha256'] = digest(CAD)
    (STLS / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


def stage(source, baseline):
    files = read_zip(source)
    base = json.loads(baseline.read_text())
    assert base['project_sha256'] == digest(source)
    root = ET.fromstring(files['3D/3dmodel.model'])
    config = ET.fromstring(files['Metadata/model_settings.config'])
    settings = json.loads(files['Metadata/project_settings.config'])
    resources = root.find(tag('resources')); build = root.find(tag('build'))
    objects = {o.get('id'): o for o in resources}
    children = {n: ET.fromstring(d) for n, d in files.items() if n.startswith('3D/Objects/') and n.endswith('.model')}
    coupon = crop_weave(CAD.read_text())
    removed = set()
    evidence = []
    for obj in list(config.findall('object')):
        name = props(obj)['name']; oid = obj.get('id')
        if name.startswith('Test-') and name not in (NAME, 'Test-M-Letter'):
            removed.add(oid); config.remove(obj); resources.remove(objects[oid])
            for b in list(build):
                if b.get('objectid') == oid: build.remove(b)
            continue
        if not (re.fullmatch(r'F\d+', name) or name == NAME):
            continue
        m = coupon if name == NAME else trimesh.load_mesh(STLS / (name + '.stl'))
        wood, proof = weave_modifier(m)
        evidence.append({'part': name, **proof})
        comps = {c.get('objectid'): c for c in objects[oid].find(tag('components'))}
        for part in obj.findall('part'):
            is_color = props(part).get('extruder') == '2'
            if part.get('subtype') != 'normal_part' and not is_color: continue
            comp = comps[part.get('id')]
            res = children[comp.get('{'+P+'}path').lstrip('/')].find(tag('resources'))
            old = next(o for o in res if o.get('id') == part.get('id'))
            replacement = (wood if is_color else m).copy()
            replacement.apply_transform(np.linalg.inv(transform(comp.get('transform'))))
            res.remove(old); mesh_object(res, part.get('id'), replacement)
            stat = part.find('mesh_stat')
            if stat is not None: stat.set('face_count', str(len(replacement.faces)))
    # Existing production placements/settings are retained. The tests each
    # occupy one plate, centered and clear of the white/wood prime tower.
    old_plate = config.findall('plate')[-1]
    config.remove(old_plate)
    layouts = base['plate_layout'][:29]
    tests = {p['name']: copy.deepcopy(p) for p in base['test_plate']['parts'] if p['name'] in (NAME, 'Test-M-Letter')}
    names = {o.get('id'): props(o)['name'] for o in config.findall('object')}
    moved = {}
    for pi, name, title in [(29, NAME, 'White and wood weave test'), (30, 'Test-M-Letter', 'Copper silk test')]:
        oid = next(oid for oid, n in names.items() if n == name)
        mesh = coupon if name == NAME else trimesh.load_mesh(CHECKS / (name + '.stl'))
        xy = np.array([128., 128.]) - mesh.bounds.mean(axis=0)[:2]
        position = xy + [pi % 6 * 307.2, -(pi // 6) * 307.2]
        b = next(b for b in build if b.get('objectid') == oid)
        b.set('transform', f'1 0 0 0 1 0 0 0 1 {position[0]:.9f} {position[1]:.9f} 0')
        moved[oid] = b.get('transform')
        plate = ET.Element('plate')
        for key, value in [('plater_id', pi+1), ('plater_name', f'{pi+1:02d} - {title}'), ('locked', 'false'),
                           ('filament_map_mode', 'Auto For Flush'), ('filament_maps', '1 1 1'), ('filament_volume_maps', '0 0 0')]:
            setmeta(plate, key, value)
        inst = copy.deepcopy(next(i for i in old_plate.findall('model_instance') if props(i)['object_id'] == oid))
        plate.append(inst); config.append(plate)
        item = {'name': name, **{k: int(v) for k, v in props(inst).items()}, 'xy': xy.tolist(),
                'bounds': (mesh.bounds + [*xy, 0]).tolist()}
        layouts.append({'plate': pi+1, 'name': title, 'items': [item]})
        tests[name]['plate'] = pi+1
    asm = config.find('assemble')
    if asm is not None:
        for a in list(asm):
            if a.get('object_id') in removed: asm.remove(a)
            elif a.get('object_id') in moved and a.get('instance_id') is not None:
                a.set('transform', moved[a.get('object_id')])
    tests[NAME].update(sha256=digest(CHECKS/(NAME+'.stl')), triangles=len(coupon.faces),
                       source_stl_sha256=digest(STLS/'F7.stl'), dimensions_mm=coupon.extents.tolist(),
                       color_modifier={'filament': 2, 'z_mm': [8.4, 9.9], 'follows_surface_relief': True})
    settings['wipe_tower_x'] = settings['wipe_tower_x'][:29] + ['180', '15']
    settings['wipe_tower_y'] = settings['wipe_tower_y'][:29] + ['180', '190']
    assert settings['textured_plate_temp'] == ['65', '65', '55']
    config[:] = config.findall('object') + config.findall('plate') + config.findall('assemble')
    # No stale toolpaths or thumbnails for revised geometry/layout.
    for p in config.findall('plate'):
        for md in list(p.findall('metadata')):
            if md.get('key', '').endswith('_file'): p.remove(md)
    files = {n:d for n,d in files.items() if not n.startswith('Metadata/') or n in
             ('Metadata/model_settings.config', 'Metadata/project_settings.config')}
    files['3D/3dmodel.model'] = xml(root)
    files['Metadata/model_settings.config'] = xml(config)
    files['Metadata/project_settings.config'] = json.dumps(settings, indent=2).encode()
    active_paths = {c.get('{'+P+'}path').lstrip('/') for o in resources for c in o.findall(f'{tag("components")}/{tag("component")}')}
    for n, child in children.items():
        if n in active_paths: files[n] = xml(child)
        else: files.pop(n, None)
    rels = ET.fromstring(files['3D/_rels/3dmodel.model.rels'])
    for rel in list(rels):
        if rel.get('Target', '').lstrip('/') not in active_paths: rels.remove(rel)
    ET.register_namespace('', R); files['3D/_rels/3dmodel.model.rels'] = xml(rels); ET.register_namespace('', tag('model')[1:].split('}')[0])
    output = WORK / 'restored.3mf'; write_zip(output, files)
    manifest = json.loads((STLS/'manifest.json').read_text())
    for part in base['parts']:
        src = next(p for p in manifest['parts'] if p['part'] == part.get('part', part.get('name')))
        for k in ('sha256', 'triangles', 'bounds_mm', 'size_mm', 'volume_mm3'):
            if k in part: part[k] = src[k]
        part['file_sha256'] = src['sha256']
    test_meta = {'plates': [30,31], 'pieces': 2, 'parts': list(tests.values()),
                 'modifier_count': len(tests['Test-M-Letter']['modifiers']), 'color_modifier_count': 1,
                 'full_width_weave_test': NAME, 'sliced': False,
                 'source_cad_sha256': digest(CAD), 'plate_layouts': layouts[29:],
                 'already_printed_tests_removed': True}
    base.update(project='Dara-Photo-Frame-A1-Complete.3mf', project_sha256=digest(output),
                pieces=72, distinct_parts=41, plates=31, test_pieces=2, plate_layout=layouts, test_plate=test_meta)
    for key in ('bambu_studio_slice','bambu_studio_round_trip','bambu_studio_slice_warnings','weave_coupon_workflow'):
        base.pop(key, None)
    base['weave_restoration'] = {'prior_project_sha256': digest(source), 'crossing_depth_mm': .3,
                                  'crossing_size_mm': [3.3, 1.5], 'pitch_mm': 6,
                                  'wood_z_mm': [8.4, 9.9], 'surface_masks': evidence}
    (WORK/'staged.json').write_text(json.dumps(base, indent=2)+'\n')
    print(output, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh-preview-cache', action='store_true')
    parser.add_argument('--source', type=Path, default=WORK/'baseline.3mf')
    parser.add_argument('--baseline', type=Path, default=WORK/'baseline.json')
    args = parser.parse_args()
    if args.refresh_preview_cache: refresh_preview_cache()
    stage(args.source, args.baseline)
