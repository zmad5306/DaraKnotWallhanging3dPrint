"""Build the complete A1 project from the validated STL exports and joint preset."""
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import uuid
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.work/python-libs'))
import numpy as np
import trimesh

SOURCE = ROOT / 'working/stl/Dara-Photo-Frame-A1-Jointed'
CAD = ROOT / 'working/Dara-Photo-Frame-A1-Jointed.scad'
REFERENCE = ROOT / 'reference/tested-lap-joints/Tested-Joints-One-Plate.3mf'
OUT = ROOT / 'working/bambu/Dara-Photo-Frame-A1-Jointed'
C = 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
P = 'http://schemas.microsoft.com/3dmanufacturing/production/2015/06'
R = 'http://schemas.openxmlformats.org/package/2006/relationships'
ET.register_namespace('', C)
ET.register_namespace('p', P)
IDENTITY = '1 0 0 0 1 0 0 0 1 0 0 0'
PLATE_COUNT = 29
# Lower left, lower right, upper left, upper right; retain the STL rotations.
BACKER_GROUPS = ((3, 1, 5, 7), (4, 2, 6, 8))
BACKER_EDGE_MARGIN = 1.5


def uid():
    return str(uuid.uuid4())


def tag(name):
    return '{' + C + '}' + name


def meta(parent, key, value):
    ET.SubElement(parent, 'metadata', key=key, value=str(value))


def xml(root):
    return ET.tostring(root, encoding='utf-8', xml_declaration=True)


def read_array(text, key):
    return json.loads(re.search(r'^' + key + r'\s*=\s*(\[.*?\]);', text, re.M | re.S)[1])


def model():
    return ET.Element(tag('model'), unit='millimeter', attrib={
        '{http://www.w3.org/XML/1998/namespace}lang': 'en-US',
        'requiredextensions': 'p', 'xmlns:p': P})


def mesh_object(resources, obj_id, mesh):
    obj = ET.SubElement(resources, tag('object'), id=str(obj_id), type='model')
    m = ET.SubElement(obj, tag('mesh'))
    vs = ET.SubElement(m, tag('vertices'))
    for v in mesh.vertices:
        ET.SubElement(vs, tag('vertex'), **dict(zip(('x', 'y', 'z'), (format(float(x), '.10g') for x in v))))
    fs = ET.SubElement(m, tag('triangles'))
    for f in mesh.faces:
        ET.SubElement(fs, tag('triangle'), **dict(zip(('v1', 'v2', 'v3'), map(str, f))))


def cylinder(xy, diameter, height):
    m = trimesh.creation.cylinder(radius=diameter / 2, height=height, sections=64)
    m.apply_translation([*xy, height / 2])
    return m


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    text = CAD.read_text(encoding='utf-8')
    manifest = json.loads((SOURCE / 'manifest.json').read_text())
    assert hashlib.sha256(CAD.read_bytes()).hexdigest() == manifest['source_sha256']
    placements = {k: read_array(text, k + '_placements') for k in ('frame', 'M')}
    screws = read_array(text, 'screw_mounts')
    walls = read_array(text, 'wall_mounts')
    anchors = np.array(read_array(text, 'photo_anchors')).reshape(-1, 2)
    normals = np.array(read_array(text, 'photo_normals')).reshape(-1, 2)
    photo_screws = anchors * .75 + normals * 9.5
    frame_retainers = read_array(text, 'frame_retainers')

    def local(family, index, xy):
        p = placements[family][index]
        a = math.radians(p[0])
        return np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]]) @ xy - p[1]

    with zipfile.ZipFile(REFERENCE) as z:
        preset = json.loads(z.read('Metadata/project_settings.config'))
    preset.update(wall_loops='4', sparse_infill_density='15%', sparse_infill_pattern='gyroid',
                  print_settings_id='Dara complete - 4 walls - 15% gyroid - local solid mounts',
                  print_sequence='by layer')
    root = model()
    # The serializer declares p automatically when attributes use its namespace.
    del root.attrib['xmlns:p']
    for key, value in [('Application', 'BambuStudio-02.08.02.61'), ('BambuStudio:3mfVersion', '1'),
                       ('Title', 'Dara Photo Frame A1 Jointed - Complete 70 Pieces'),
                       ('Description', f'{PLATE_COUNT} plates; 4 walls; 15% gyroid; local 100% screw reinforcement.')]:
        ET.SubElement(root, tag('metadata'), name=key).text = value
    resources = ET.SubElement(root, tag('resources'))
    build = ET.SubElement(root, tag('build'), attrib={'{' + P + '}UUID': uid()})
    config = ET.Element('config')
    relationships = ET.Element('Relationships', xmlns=R)
    files = {}
    records = []
    plates = []
    total = 0

    for entry in manifest['parts']:
        name, family = entry['part'], entry['family']
        path = SOURCE / entry['file']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry['sha256']
        mesh = trimesh.load_mesh(path, process=True)
        assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume > 0
        mods = []

        def add(name, xy, diameter):
            mods.append((name, cylinder(xy, diameter, float(mesh.bounds[1, 2]))))

        if family in ('frame', 'M'):
            index = int(name[1:]) - 1
            for n, (mi, fi, xy) in enumerate(screws, 1):
                if (fi if family == 'frame' else mi) == index:
                    add(f'100% M screw {n} ' + ('seat - D16' if family == 'frame' else 'pilot - D14'),
                        local(family, index, xy), 16 if family == 'frame' else 14)
            if family == 'frame':
                for n in frame_retainers[index]:
                    add(f'100% photo screw {n + 1} - D14', local(family, index, photo_screws[n]), 14)
                for n, w in enumerate(walls, 1):
                    if w[0] == index:
                        for j, x in enumerate(w[5], 1):
                            add(f'100% B{n} screw {j} pilot - D14', local(family, index, np.array(w[1]) + [x, w[4]]), 14)
        elif family == 'wall_block':
            w = walls[int(name[1:]) - 1]
            for j, x in enumerate(w[5], 1):
                add(f'100% block screw {j} seat - D16', [x, w[4]], 16)
            m = trimesh.creation.box(extents=[24, 31, 10])
            m.apply_translation([51, .5, 5])
            mods.append(('100% wall keyhole seat and lip', m))
        elif family == 'retainer':
            add('100% retainer screw seat - D12', [5, 0], 12)

        # Check each modifier intersects real part material, including a ring around its screw.
        for mod_name, mod in mods:
            intersection = trimesh.boolean.intersection([mesh, mod], engine='manifold')
            assert intersection.volume > 1, (name, mod_name, intersection.volume)

        # Bambu resolves mesh IDs globally, even across different component files.
        obj_id = (len(records) + 1) * 1000
        obj_path = f'3D/Objects/{name}.model'
        child = model()
        child_res = ET.SubElement(child, tag('resources'))
        mesh_object(child_res, obj_id + 1, mesh)
        top = ET.SubElement(resources, tag('object'), id=str(obj_id), type='model', attrib={'{' + P + '}UUID': uid()})
        components = ET.SubElement(top, tag('components'))
        conf_obj = ET.SubElement(config, 'object', id=str(obj_id))
        meta(conf_obj, 'name', name)
        meta(conf_obj, 'extruder', 1)
        meta(conf_obj, 'enable_support', int(family in ('frame', 'M', 'wall_block')))
        if family == 'wall_block':
            meta(conf_obj, 'support_on_build_plate_only', 0)
        if family in ('backer', 'retainer'):
            meta(conf_obj, 'brim_type', 'no_brim')
        elif min(entry['minimum_bed_edge_clearance_mm'], 3) < 2.75:
            meta(conf_obj, 'brim_width', 1)
            # Automatic support-base expansion can overrun a nearly full A1 bed.
            meta(conf_obj, 'raft_first_layer_expansion', 0)

        for part_index, (part_name, part_mesh) in enumerate([(name, mesh)] + mods, 1):
            part_id = obj_id + part_index
            if part_index > 1:
                mesh_object(child_res, part_id, part_mesh)
            ET.SubElement(components, tag('component'), objectid=str(part_id), transform=IDENTITY,
                          attrib={'{' + P + '}path': '/' + obj_path, '{' + P + '}UUID': uid()})
            part = ET.SubElement(conf_obj, 'part', id=str(part_id), subtype='normal_part' if part_index == 1 else 'modifier_part')
            meta(part, 'name', part_name)
            if part_index == 1:
                meta(part, 'source_file', entry['file'])
                ET.SubElement(part, 'mesh_stat', face_count=str(len(mesh.faces)),
                              edges_fixed='0', degenerate_facets='0', facets_removed='0', facets_reversed='0', backwards_edges='0')
            else:
                meta(part, 'sparse_infill_density', '100%')
                meta(part, 'sparse_infill_pattern', 'cubic')
        files[obj_path] = xml(child)
        ET.SubElement(relationships, 'Relationship', Target='/' + obj_path, Id=f'rel-{obj_id}',
                      Type='http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel')
        if family in ('frame', 'M'):
            plate_idx = len(plates)
            plates.append({'name': name, 'items': []})
            positions = [(128, 128)]
        elif family == 'backer':
            if len(plates) == 26:
                plates.extend({'name': 'Backers ' + ', '.join(map(str, sorted(group))), 'items': []}
                              for group in BACKER_GROUPS)
            backer = int(name.removeprefix('Backer'))
            group_index = next(i for i, group in enumerate(BACKER_GROUPS) if backer in group)
            corner = BACKER_GROUPS[group_index].index(backer)
            plate_idx = 26 + group_index
            low, high = mesh.bounds[:, :2]
            positions = [tuple(256 - BACKER_EDGE_MARGIN - high[axis] if (corner >> axis) & 1
                               else BACKER_EDGE_MARGIN - low[axis] for axis in (0, 1))]
        else:
            plate_idx = PLATE_COUNT - 1
            if len(plates) == PLATE_COUNT - 1:
                plates.append({'name': 'B1-B4 and 32 Retainers', 'items': []})
            positions = ([(84, 55 + 48 * (int(name[1:]) - 1))] if family == 'wall_block'
                         else [(179 + 26 * (i % 3), 48 + 16 * (i // 3)) for i in range(32)])
        for instance_id, (x, y) in enumerate(positions):
            low, high = mesh.bounds + [x, y, 0]
            assert min(*low[:2], *(256 - high[:2])) >= 1.499
            # Full meshes stay in their authored orientation; only translation is applied.
            tx = x + (plate_idx % 6) * 307.2
            ty = y - (plate_idx // 6) * 307.2
            ET.SubElement(build, tag('item'), objectid=str(obj_id), printable='1',
                          transform=f'1 0 0 0 1 0 0 0 1 {tx:.9f} {ty:.9f} 0',
                          attrib={'{' + P + '}UUID': uid()})
            total += 1
            plates[plate_idx]['items'].append({'name': name, 'object_id': obj_id, 'instance_id': instance_id,
                                              'identify_id': total, 'xy': [x, y], 'bounds': [low.tolist(), high.tolist()]})
        records.append({'name': name, 'file_sha256': entry['sha256'], 'quantity': len(positions),
                        'plate': plate_idx + 1, 'modifiers': [n for n, _ in mods],
                        'bounds_mm': mesh.bounds.tolist(), 'triangles': len(mesh.faces)})

    assert total == 70 and len(plates) == PLATE_COUNT
    for plate_idx, plate in enumerate(plates, 1):
        pc = ET.SubElement(config, 'plate')
        for k, v in [('plater_id', plate_idx), ('plater_name', f'{plate_idx:02d} - {plate["name"]}'),
                     ('locked', 'false'), ('filament_map_mode', 'Auto For Flush'),
                     ('filament_maps', 1), ('filament_volume_maps', 0)]:
            meta(pc, k, v)
        for item in plate['items']:
            inst = ET.SubElement(pc, 'model_instance')
            for k in ('object_id', 'instance_id', 'identify_id'):
                meta(inst, k, item[k])
        for i, a in enumerate(plate['items']):
            for b in plate['items'][i + 1:]:
                al, ah = np.array(a['bounds'])[:, :2]
                bl, bh = np.array(b['bounds'])[:, :2]
                # Backers are flat and printed by layer, with no brim or supports.
                gap = 1.5 if a['name'].startswith('Backer') and b['name'].startswith('Backer') else 4
                assert np.any(ah + gap < bl) or np.any(bh + gap < al), (a, b)

    files['3D/3dmodel.model'] = xml(root)
    files['3D/_rels/3dmodel.model.rels'] = xml(relationships)
    files['Metadata/model_settings.config'] = xml(config)
    files['Metadata/project_settings.config'] = json.dumps(preset, indent=2).encode()
    files['[Content_Types].xml'] = b'''<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/><Default Extension="config" ContentType="application/octet-stream"/></Types>'''
    files['_rels/.rels'] = b'''<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>'''
    target = OUT / 'Dara-Photo-Frame-A1-Complete.3mf'
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as z:
        for path, data in files.items():
            z.writestr(path, data)
    with zipfile.ZipFile(target) as z:
        assert z.testzip() is None
        for name in z.namelist():
            if name.endswith(('.model', '.xml', '.rels')) or name.endswith('model_settings.config'):
                ET.fromstring(z.read(name))
    report = {'project': target.name, 'pieces': total, 'distinct_parts': len(records), 'plates': len(plates),
              'settings': {k: preset[k] for k in ['printer_settings_id', 'filament_settings_id', 'layer_height',
                                                'wall_loops', 'sparse_infill_density', 'sparse_infill_pattern']},
              'modifier_policy': 'D16 screw seats and D14 pilot zones derived from tested local modifiers; no lap infill overrides. Photo and wall screw zones mapped from native CAD.',
              'parts': records, 'plate_layout': plates}
    (OUT / 'project-validation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'path': str(target), 'pieces': total, 'plates': len(plates),
                      'modifier_volumes': sum(len(r['modifiers']) for r in records)}, indent=2))


if __name__ == '__main__':
    main()
