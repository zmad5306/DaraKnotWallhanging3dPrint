"""Stage plate 30 (nine fit-test pieces) in a copy of the 29-plate project.

The staged project must be sliced/exported in Bambu Studio before publication.
Uses the current production meshes; does not change their CAD or production plates.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

from build_jointed_bambu_project import (ROOT, C, P, R, IDENTITY, tag, meta, model,
                                         xml, mesh_object, cylinder, uid, read_array)
import numpy as np
import trimesh

PACKAGE = ROOT / 'working/bambu/Dara-Photo-Frame-A1-Jointed'
STLS = ROOT / 'working/stl/Dara-Photo-Frame-A1-Jointed'
CHECKS = ROOT / 'working/stl/Dara-Print-Checks'
WORK = ROOT / '.work/print-check-plate'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_parts():
    cad = (ROOT / 'working/Dara-Photo-Frame-A1-Jointed.scad').read_text()
    manifest = json.loads((CHECKS / 'manifest.json').read_text())
    assert manifest['source_sha256'] == sha(ROOT / manifest['source'])
    for entry in manifest['files']:
        assert sha(CHECKS / entry['file']) == entry['sha256']
    records = []

    def add(name, mesh, mods, low_xy, source, rotation=0):
        assert mesh.is_volume and len(mesh.split(only_watertight=False)) == 1
        matrix = trimesh.transformations.rotation_matrix(math.radians(rotation), [0, 0, 1])
        mesh.apply_transform(matrix)
        for _, mod in mods:
            mod.apply_transform(matrix)
        offset = (mesh.bounds[0] + mesh.bounds[1]) / 2
        offset[2] = mesh.bounds[0, 2]
        mesh.apply_translation(-offset)
        for _, mod in mods:
            mod.apply_translation(-offset)
            assert trimesh.boolean.intersection([mesh, mod], engine='manifold').volume > 1
        position = np.array(low_xy) - mesh.bounds[0, :2]
        path = CHECKS / (name + '.stl')
        mesh.export(path)
        mesh = trimesh.load_mesh(path)
        assert mesh.is_volume and abs(mesh.bounds[0, 2]) < 1e-5
        bounds = mesh.bounds + [*position, 0]
        assert min(*bounds[0, :2], *(256 - bounds[1, :2])) > 3
        records.append({'name': name, 'mesh': mesh, 'mods': mods, 'xy': position.tolist(),
                        'bounds': bounds.tolist(), 'source': source, 'file': path.name,
                        'sha256': sha(path), 'triangles': len(mesh.faces)})

    photo = trimesh.load_mesh(CHECKS / 'Photo-Fit-Sample.stl').split(only_watertight=False)
    frame = next(m for m in photo if m.extents[2] > 10)
    backer = next(m for m in photo if m.extents[2] < 2)
    tab = next(m for m in photo if 2 < m.extents[2] < 4)
    add('Test-Photo-Frame', frame, [('100% photo pilot', cylinder([9.5, 0], 14, 13.5))], [12, 210], 'Photo-Fit-Sample.stl')
    add('Test-Photo-Backer', backer, [], [42, 210], 'Photo-Fit-Sample.stl')
    add('Test-Photo-Tab', tab, [('100% photo tab seat', cylinder([9.5, 24], 12, 3))], [68, 210], 'Photo-Fit-Sample.stl')
    wall = trimesh.load_mesh(CHECKS / 'Wall-Fit-Sample-B1.stl').split(only_watertight=False)
    block = next(m for m in wall if m.extents[2] < 13.4)
    socket = next(m for m in wall if m.extents[2] > 13.4)
    mods = [(f'100% B1 screw {i} seat', cylinder([x, -36], 16, 13)) for i, x in enumerate((21, 37), 1)]
    keyhole = trimesh.creation.box(extents=[24, 31, 10]); keyhole.apply_translation([51, -25.5, 5])
    mods.append(('100% B1 keyhole lip', keyhole))
    add('Test-Wall-Block-B1', block, mods, [12, 12], 'Wall-Fit-Sample-B1.stl')
    mods = [(f'100% B1 pilot {i}', cylinder([x, 16], 14, 13.5)) for i, x in enumerate((21, 37), 1)]
    add('Test-Wall-Socket-B1', socket, mods, [12, 62], 'Wall-Fit-Sample-B1.stl')

    def assembly_mesh(name):
        family = 'frame' if name[0] == 'F' else 'M'
        p = read_array(cad, family + '_placements')[int(name[1:]) - 1]
        m = trimesh.load_mesh(STLS / (name + '.stl'))
        m.apply_translation([*p[1], -p[3]])
        m.apply_transform(trimesh.transformations.rotation_matrix(math.radians(-p[0]), [0, 0, 1]))
        return m

    # Preserve M5's actual pin spacing, round/relieved bores, and screw stack.
    crop = trimesh.creation.box(extents=[32, 157, 30]); crop.apply_translation([-29, -106.5, 10])
    for source, name, diameter, height, xy in [
        ('F14', 'Test-M-Frame', 16, 16.5, [12, 112]),
        ('M5', 'Test-M-Letter', 14, 10.5, [12, 157]),
    ]:
        m = trimesh.boolean.intersection([assembly_mesh(source), crop], engine='manifold')
        add(name, m, [('100% M screw zone', cylinder([-29, -62], diameter, height))], xy,
            source + '.stl; native assembly crop X=-45..-13, Y=-185..-28', 90)

    # Exact current F7/F4 lap, including the 13.5 mm production rail thickness.
    joint = read_array(cad, 'frame_joints')[0]
    for index, name, xy in [(joint[0], 'Test-Lap-Tongue', [195, 12]),
                             (joint[1], 'Test-Lap-Socket', [195, 120])]:
        m = assembly_mesh(f'F{index + 1}')
        m.apply_translation([-joint[2][0], -joint[2][1], 0])
        m.apply_transform(trimesh.transformations.rotation_matrix(math.radians(-joint[3]), [0, 0, 1]))
        crop = trimesh.creation.box(extents=[65, joint[4] + 24, 30]); crop.apply_translation([8.5, 0, 10])
        m = trimesh.boolean.intersection([m, crop], engine='manifold')
        add(name, m, [], xy, f'F{index + 1}.stl; native frame joint 1 crop')
    for i, a in enumerate(records):
        for b in records[i + 1:]:
            al, ah = np.array(a['bounds'])[:, :2]; bl, bh = np.array(b['bounds'])[:, :2]
            assert np.any(ah + 8 < bl) or np.any(bh + 8 < al), (a['name'], b['name'])
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=PACKAGE / 'Dara-Photo-Frame-A1-Complete.3mf')
    args = parser.parse_args()
    WORK.mkdir(exist_ok=True)
    with zipfile.ZipFile(args.source) as z:
        files = {n: z.read(n) for n in z.namelist()}
    root = ET.fromstring(files['3D/3dmodel.model'])
    config = ET.fromstring(files['Metadata/model_settings.config'])
    rels = ET.fromstring(files['3D/_rels/3dmodel.model.rels'])
    assert len(config.findall('plate')) == 29, 'Start from the 29 production plates; do not append twice.'
    parts = build_parts()
    resources = root.find(tag('resources')); build = root.find(tag('build'))
    pc = ET.SubElement(config, 'plate')
    for k, v in [('plater_id', 30), ('plater_name', '30 - PRINT FIRST - Hardware and lap fit tests'),
                 ('locked', 'false'), ('filament_map_mode', 'Auto For Flush'),
                 ('filament_maps', 1), ('filament_volume_maps', 0)]:
        meta(pc, k, v)
    items, part_records = [], []
    for i, entry in enumerate(parts):
        name = entry['name']; oid = 1000 + i * 20
        path = f'3D/Objects/{name}.model'
        child = model(); child_res = ET.SubElement(child, tag('resources'))
        obj = ET.SubElement(resources, tag('object'), id=str(oid), type='model', attrib={'{'+P+'}UUID': uid()})
        comps = ET.SubElement(obj, tag('components'))
        co = ET.SubElement(config, 'object', id=str(oid))
        for key, value in [('name', name), ('extruder', 1), ('enable_support', int('Backer' not in name and 'Tab' not in name)),
                           ('support_on_build_plate_only', 0), ('brim_type', 'no_brim' if 'Backer' in name or 'Tab' in name else 'outer_only')]:
            meta(co, key, value)
        for j, (part_name, mesh) in enumerate([(name, entry['mesh'])] + entry['mods'], 1):
            pid = oid + j
            mesh_object(child_res, pid, mesh)
            ET.SubElement(comps, tag('component'), objectid=str(pid), transform=IDENTITY,
                          attrib={'{'+P+'}path': '/'+path, '{'+P+'}UUID': uid()})
            part = ET.SubElement(co, 'part', id=str(pid), subtype='normal_part' if j == 1 else 'modifier_part')
            meta(part, 'name', part_name)
            if j > 1:
                meta(part, 'sparse_infill_density', '100%'); meta(part, 'sparse_infill_pattern', 'cubic')
        files[path] = xml(child)
        ET.SubElement(rels, '{'+R+'}Relationship', Target='/'+path, Id=f'test-{oid}',
                      Type='http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel')
        x, y = entry['xy']; tx, ty = x + 5 * 307.2, y - 4 * 307.2
        ET.SubElement(build, tag('item'), objectid=str(oid), printable='1',
                      transform=f'1 0 0 0 1 0 0 0 1 {tx:.9f} {ty:.9f} 0', attrib={'{'+P+'}UUID': uid()})
        inst = ET.SubElement(pc, 'model_instance')
        for k, v in [('object_id', oid), ('instance_id', 0), ('identify_id', 301 + i)]:
            meta(inst, k, v)
        items.append({'name': name, 'object_id': oid, 'instance_id': 0, 'identify_id': 301 + i,
                      'xy': entry['xy'], 'bounds': entry['bounds']})
        part_records.append({k: v for k, v in entry.items() if k not in ('mesh', 'mods', 'bounds', 'xy')}
                            | {'modifiers': [n for n, _ in entry['mods']], 'quantity': 1, 'plate': 30})
    for md in root.findall(tag('metadata')):
        if md.get('name') == 'Description':
            md.text = '29 production plates plus plate 30 fit tests; 4 walls; 15% gyroid; local solid screw zones.'
    files['3D/3dmodel.model'] = xml(root)
    config[:] = config.findall('object') + config.findall('plate') + config.findall('assemble')
    files['Metadata/model_settings.config'] = xml(config)
    # Bambu's relationships reader expects unprefixed element names.
    ET.register_namespace('', R)
    files['3D/_rels/3dmodel.model.rels'] = xml(rels)
    ET.register_namespace('', C)
    staged = WORK / 'with-tests.3mf'
    with zipfile.ZipFile(staged, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, content in files.items():
            z.writestr(name, content)
    test_report = {'plate': 30, 'pieces': 9, 'production_pieces': 70, 'production_plates': 29,
                   'source_project_sha256': sha(args.source), 'source_cad_sha256': sha(ROOT / 'working/Dara-Photo-Frame-A1-Jointed.scad'),
                   'parts': part_records, 'plate_layout': {'name': 'PRINT FIRST - Hardware and lap fit tests', 'items': items},
                   'modifier_count': sum(len(r['mods']) for r in parts), 'sliced': False}
    (WORK / 'test-plate.json').write_text(json.dumps(test_report, indent=2) + '\n')
    print(json.dumps({'staged_project': str(staged), 'pieces': 9, 'test_modifiers': test_report['modifier_count']}, indent=2))


if __name__ == '__main__':
    main()
