"""Audit the saved production artifacts without exporting or re-slicing them.

Requires numpy, trimesh and manifold3d. Run from any working directory.
The report covers digital geometry/toolpaths, not physical fit or load testing.
"""
import collections
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.work/python-libs'))
import numpy as np
import trimesh
import manifold3d
from export_jointed_stls import verify
from mesh_sections import mesh_cross_section

PACKAGE = ROOT / 'working/bambu/Dara-Photo-Frame-A1-Jointed'
STLS = ROOT / 'working/stl/Dara-Photo-Frame-A1-Jointed'
CAD = ROOT / 'working/Dara-Photo-Frame-A1-Jointed.scad'
REPORT = PACKAGE / 'final-review.json'
N = {'m': 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
P = '{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}'
# Bambu emits E.0123, X-.5 and I.123; a leading digit is NOT required.
TOKEN = re.compile(r'([XYZEFIJP])([+-]?(?:\d+(?:\.\d*)?|\.\d+))')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def props(el):
    return {m.get('key'): m.get('value') for m in el.findall('metadata')}


def transform(value):
    matrix = np.eye(4)
    if value:
        matrix[:3, :] = np.array(list(map(float, value.split()))).reshape(4, 3).T
    return matrix


def arc_points(start, end, values, ccw):
    cx, cy = start[0] + values.get('I', 0), start[1] + values.get('J', 0)
    radius = math.hypot(start[0] - cx, start[1] - cy)
    a, b = math.atan2(start[1] - cy, start[0] - cx), math.atan2(end[1] - cy, end[0] - cx)
    span = ((b - a) if ccw else (a - b)) % (2 * math.pi)
    if math.dist(start, end) < 1e-8:
        span = 2 * math.pi
    points = [start, end]
    for q in (0, math.pi / 2, math.pi, math.pi * 1.5):
        distance = ((q - a) if ccw else (a - q)) % (2 * math.pi)
        if distance <= span + 1e-6:
            points.append((cx + radius * math.cos(q), cy + radius * math.sin(q)))
    return points


def scan_gcode(text):
    """Bounds include bead widths and arc extrema; exclude printer custom routines."""
    feature, width = 'Custom', .5
    x = y = z = e = 0.
    relative_e, relative_xyz = False, False
    low, high = [math.inf] * 2, [-math.inf] * 2
    bead_low, bead_high = [math.inf] * 2, [-math.inf] * 2
    features = collections.Counter()
    tool = None
    model_z = collections.defaultdict(set)
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith('; FEATURE: '):
            feature = line.split(': ', 1)[1]
        elif line.startswith('; LINE_WIDTH: '):
            width = float(line.split(': ', 1)[1])
        code = line.split(';', 1)[0].strip()
        if not code:
            continue
        command = code.split()[0]
        if re.fullmatch(r'T[0-3]', command):
            tool = int(command[1:]) + 1
        elif command == 'M83':
            relative_e = True
        elif command == 'M82':
            relative_e = False
        elif command in ('G90', 'G91'):
            relative_xyz = command == 'G91'
        elif command == 'G92':
            v = {k: float(n) for k, n in TOKEN.findall(code)}
            x, y, z, e = v.get('X', x), v.get('Y', y), v.get('Z', z), v.get('E', e)
        elif command in ('G0', 'G1', 'G2', 'G3'):
            v = {k: float(n) for k, n in TOKEN.findall(code)}
            nx, ny, nz = [old + v.get(k, 0) if relative_xyz else v.get(k, old)
                          for k, old in zip('XYZ', (x, y, z))]
            de = v.get('E', 0) if relative_e else v.get('E', e) - e
            if de > 0 and feature != 'Custom' and any(k in v for k in ('X', 'Y', 'I', 'J')):
                if command in ('G2', 'G3'):
                    if 'R' in code:
                        raise ValueError('Radius-form arcs require explicit handling')
                    points = arc_points((x, y), (nx, ny), v, command == 'G3')
                else:
                    points = [(x, y), (nx, ny)]
                for point in points:
                    for axis in (0, 1):
                        low[axis] = min(low[axis], point[axis])
                        high[axis] = max(high[axis], point[axis])
                        bead_low[axis] = min(bead_low[axis], point[axis] - width / 2)
                        bead_high[axis] = max(bead_high[axis], point[axis] + width / 2)
                features[feature] += 1
                if tool is not None and feature not in ('Prime tower', 'Support', 'Support interface', 'Brim', 'Skirt'):
                    model_z[tool].add(round(nz, 4))
            x, y, z = nx, ny, nz
            e = e + v.get('E', 0) if relative_e else v.get('E', e)
    assert features, 'No model extrusion found'
    return {'extrusion_moves_checked': sum(features.values()), 'features': dict(features),
            'model_extrusion_z_by_filament_mm': {str(t): sorted(v) for t, v in model_z.items()},
            'extruding_xy_bounds_mm': [low, high],
            'bead_xy_bounds_mm': [bead_low, bead_high],
            'conservative_bed_edge_clearance_mm': min(*bead_low, *(256 - n for n in bead_high))}


def nearest_error(reference, query):
    # Bambu reorders mesh vertices; spatial buckets allow a symmetric comparison.
    buckets = collections.defaultdict(list)
    for p, key in zip(reference, np.floor(reference * 100).astype(int)):
        buckets[tuple(key)].append(p)
    maximum = 0.
    from itertools import product
    for p in query:
        key = np.floor(p * 100).astype(int)
        candidates = buckets.get(tuple(key), [])
        error = min((float(np.linalg.norm(p - q)) for q in candidates), default=math.inf)
        if error >= 1e-4:
            for shift in product((-1, 0, 1), repeat=3):
                for q in buckets.get(tuple(key + shift), []):
                    error = min(error, float(np.linalg.norm(p - q)))
        maximum = max(maximum, error)
    return maximum


def filament_weights(gcode):
    values = re.search(r'^; total filament weight \[g\] : ([^\n]+)', gcode, re.M)
    assert values, 'Missing filament weight header'
    weights = [float(n.strip()) for n in values[1].split(',')]
    ids = re.search(r'^; filament: ([^\n]+)', gcode, re.M)
    if not ids:
        return weights
    slots = [int(n) for n in ids[1].split(',')]
    assert len(slots) == len(weights)
    mapped = [0.] * max(slots)
    for slot, weight in zip(slots, weights):
        mapped[slot - 1] = weight
    return mapped


def assembly_checks(meshes, array):
    assembled = {}
    for family, prefix, count in [('frame', 'F', 20), ('M', 'M', 6)]:
        placements = array(family + '_placements')
        order = array(family + '_assembly_order')
        assert sorted(order) == list(range(1, count + 1))
        for joint in array(family + '_joints'):
            assert order.index(joint[0] + 1) < order.index(joint[1] + 1)
        for i, p in enumerate(placements):
            m = meshes[prefix + str(i + 1)].copy()
            m.apply_translation([*p[1], -p[3]])
            m.apply_transform(trimesh.transformations.rotation_matrix(math.radians(-p[0]), [0, 0, 1]))
            if family == 'M':
                m.apply_translation([0, 0, 13.5])
            assembled[prefix + str(i + 1)] = m
    for i, xy in enumerate(array('photo_centres'), 1):
        m = meshes[f'Backer{i}'].copy()
        m.apply_translation([xy[0] * .75, xy[1] * .75, 0])
        assembled[f'Backer{i}'] = m
    for i, wall in enumerate(array('wall_mounts'), 1):
        m = meshes[f'B{i}'].copy()
        m.apply_translation([*wall[1], -10])
        assembled[f'B{i}'] = m
    anchors = np.array(array('photo_anchors')).reshape(-1, 2)
    normals = np.array(array('photo_normals')).reshape(-1, 2)
    for i, (anchor, normal) in enumerate(zip(anchors, normals), 1):
        m = meshes['Retainer'].copy()
        m.apply_translation([4.5, 0, -3])
        m.apply_transform(trimesh.transformations.rotation_matrix(math.atan2(normal[1], normal[0]), [0, 0, 1]))
        m.apply_translation([*(anchor * .75), 0])
        assembled[f'Tab{i}'] = m
    overlaps = []
    items = list(assembled.items())
    pairs = 0
    for i, (name, a) in enumerate(items):
        for other, b in items[i + 1:]:
            if np.any(np.minimum(a.bounds[1], b.bounds[1]) - np.maximum(a.bounds[0], b.bounds[0]) <= 1e-5):
                continue
            pairs += 1
            with np.errstate(invalid='ignore', divide='ignore'):
                volume = abs(float(trimesh.boolean.intersection([a, b], engine='manifold').volume))
            assert math.isfinite(volume), (name, other)
            if volume > 1e-5:
                overlaps.append({'parts': [name, other], 'volume_mm3': volume})
    worst = max((p['volume_mm3'] for p in overlaps), default=0.)
    # STL coordinates have micrometre-level roundoff at a 914 mm assembly scale.
    assert worst < .01, overlaps
    return {'assembled_pieces': len(assembled), 'intersecting_bounds_pairs_checked': pairs,
            'maximum_overlap_mm3': worst, 'overlaps_above_1e_5_mm3': overlaps,
            'overlap_tolerance_mm3': .01, 'lap_assembly_orders_valid': True,
            'frame_assembly_order': array('frame_assembly_order'), 'M_assembly_order': array('M_assembly_order')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path)
    parser.add_argument('--baseline', type=Path, default=PACKAGE / 'project-validation.json')
    parser.add_argument('--report', type=Path, default=REPORT)
    args = parser.parse_args()
    baseline = json.loads(args.baseline.read_text())
    manifest = json.loads((STLS / 'manifest.json').read_text())
    project = args.project or PACKAGE / baseline['project']
    assert digest(project) == baseline['project_sha256']
    assert digest(CAD) == manifest['source_sha256']
    cad = CAD.read_text()

    def array(key):
        return json.loads(re.search(r'^' + key + r'\s*=\s*(\[.*?\]);', cad, re.M | re.S)[1])

    meshes, mesh_records = {}, []
    for entry in manifest['parts']:
        path = STLS / entry['file']
        record = verify(path)
        assert record['sha256'] == entry['sha256']
        meshes[entry['part']] = trimesh.load_mesh(path)
        mesh_records.append({'part': entry['part'], **record})
    print('39 source meshes and hashes verified', flush=True)
    assembly = assembly_checks(meshes, array)
    print('70 assembled pieces checked for interference and lap ordering', flush=True)
    test_plate = baseline.get('test_plate', {})
    test_parts = test_plate.get('parts', [])
    expected_quantities = {e['part']: e['print_quantity'] for e in manifest['parts']}
    for entry in test_parts:
        path = ROOT / 'working/stl/Dara-Print-Checks' / entry['file']
        record = verify(path)
        assert record['sha256'] == entry['sha256']
        meshes[entry['name']] = trimesh.load_mesh(path)
        mesh_records.append({'part': entry['name'], 'test_coupon': True, **record})
        expected_quantities[entry['name']] = entry['quantity']
    expected_modifiers = 73 + test_plate.get('modifier_count', 0)
    expected_plate_count = 29 + (len(test_plate.get('plates', [30])) if test_parts else 0)
    wood_top = baseline.get('weave_restoration', {}).get('wood_z_mm', [8.4, 9.6])[1]
    report = {'project_sha256': digest(project), 'source_sha256': digest(CAD),
              'scope': 'Digital checks only. No physical fit, strength or wall-load qualification.',
              'source_meshes': mesh_records, 'assembly': assembly, 'plates': []}
    with zipfile.ZipFile(project) as archive:
        assert archive.testzip() is None
        config = ET.fromstring(archive.read('Metadata/model_settings.config'))
        root = ET.fromstring(archive.read('3D/3dmodel.model'))
        assert root.get('unit') == 'millimeter'
        settings = json.loads(archive.read('Metadata/project_settings.config'))
        expected_settings = {'printer_model': 'Bambu Lab A1', 'nozzle_diameter': ['0.4'],
                             'wall_loops': '4', 'sparse_infill_density': '15%',
                             'sparse_infill_pattern': 'gyroid', 'layer_height': '0.2', 'print_sequence': 'by layer'}
        for key, value in expected_settings.items():
            assert settings[key] == value, (key, settings[key])
        blue_edge = 'blue_ribbon_edge' in baseline
        colored = len(settings['filament_colour']) in (3, 4)
        if blue_edge:
            from add_blue_ribbon_edge import artwork, in_print_coordinates, coupon_shape, section, WIDTH, GAP
            spec = baseline['blue_ribbon_edge']
            assert spec['source_cad_sha256'] == digest(CAD)
            assert spec['width_mm'] == WIDTH and spec['white_gap_to_weave_mm'] == GAP
            fabric = artwork(cad, 'fabric_outline').buffer(.1125, quad_segs=16)
            blue_path = (fabric.buffer(GAP + WIDTH, quad_segs=16) - fabric.buffer(GAP, quad_segs=16)).intersection(artwork(cad, 'knot_outline'))
            blue_path = blue_path.simplify(.001, preserve_topology=True)
        if colored:
            for key, value in {
                'filament_colour': ['#FFFFFF', '#C2AB84', '#B87333'] + (['#295D8A'] if blue_edge else []),
                'filament_settings_id': ['Generic PLA @BBL A1', 'Generic PLA @BBL A1', 'Generic PLA Silk @BBL A1'] + (['Generic PLA @BBL A1'] if blue_edge else []),
                'enable_prime_tower': '1', 'flush_into_infill': '0',
                'flush_into_objects': '0', 'flush_into_support': '0',
            }.items():
                assert settings[key] == value, (key, settings[key])
                expected_settings[key] = value
        report['settings'] = expected_settings
        objects = {o.get('id'): o for o in root.find('m:resources', N)}
        builds = collections.defaultdict(list)
        for item in root.find('m:build', N):
            assert item.get('printable') == '1'
            builds[item.get('objectid')].append(transform(item.get('transform')))
        source_positions = collections.defaultdict(list)
        for pi, plate in enumerate(baseline['plate_layout']):
            for item in plate['items']:
                source_positions[item['name']].append(np.array([item['xy'][0] + (pi % 6) * 307.2,
                                                               item['xy'][1] - (pi // 6) * 307.2, 0]))
        names, normal_errors, modifier_count, color_modifiers = {}, [], 0, []
        for obj in config.findall('object'):
            oid, op = obj.get('id'), props(obj)
            name = names[oid] = op['name']
            for key in ('wall_loops', 'sparse_infill_density', 'sparse_infill_pattern', 'layer_height'):
                assert op.get(key, expected_settings[key]) == expected_settings[key], (name, key, op)
            assert len(builds[oid]) == (32 if name == 'Retainer' else 1)
            components = {c.get('objectid'): c for c in objects[oid].find('m:components', N)}
            assert len(obj.findall("part[@subtype='normal_part']")) == 1
            expected_slot = '3' if name.startswith('M') or name == 'Test-M-Letter' else '1'
            if colored:
                assert op['extruder'] == expected_slot, (name, op)
                if expected_slot == '3':
                    assert op['outer_wall_speed'] == op['top_surface_speed'] == '40'
            for part in obj.findall('part'):
                comp = components[part.get('id')]
                child = ET.fromstring(archive.read(comp.get(P + 'path').lstrip('/')))
                assert child.get('unit') == 'millimeter'
                mo = child.find(f'm:resources/m:object[@id="{part.get("id")}"]', N)
                verts = [[float(v.get(k)) for k in ('x', 'y', 'z')] for v in mo.findall('m:mesh/m:vertices/m:vertex', N)]
                faces = [[int(f.get(k)) for k in ('v1', 'v2', 'v3')] for f in mo.findall('m:mesh/m:triangles/m:triangle', N)]
                # Preserve the archive's indexed topology. Bambu rounds some
                # sub-micrometre vertices to coincident coordinates; automatic
                # re-welding would create non-manifold edges during this audit.
                # Symmetric geometry comparisons below bound that rounding.
                mesh = trimesh.Trimesh(verts, faces, process=False)
                assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume > 0, name
                mesh.apply_transform(transform(comp.get('transform')))
                mesh.apply_transform(builds[oid][0])
                mesh.apply_translation(-source_positions[name][0])
                if part.get('subtype') == 'modifier_part':
                    if blue_edge and props(part).get('extruder') == '4':
                        spec = baseline['blue_ribbon_edge']
                        record = next(r for r in spec['masks'] if r['part'] == name)
                        assert np.allclose(mesh.bounds[:, 2], spec['z_mm'], atol=1e-4)
                        assert abs(mesh.volume - record['volume_mm3']) < .02
                        assert 'sparse_infill_density' not in props(part)
                        mask_solid = manifold3d.Manifold(manifold3d.Mesh64(mesh.vertices, mesh.faces.astype(np.uint64)))
                        source_solid = manifold3d.Manifold(manifold3d.Mesh64(meshes[name].vertices, meshes[name].faces.astype(np.uint64)))
                        local = (coupon_shape(blue_path, cad) if name == test_plate.get('full_width_weave_test') else
                                 in_print_coordinates(blue_path, array('frame_placements')[int(name[1:]) - 1]))
                        expected_blue = section(local) ^ mesh_cross_section(meshes[name],13.2)
                        actual_blue = mesh_cross_section(mesh,13.2)
                        path_error = abs((actual_blue - expected_blue).area()) + abs((expected_blue - actual_blue).area())
                        assert path_error < .05, (name, path_error)
                        for height in (12.901, 13.2, 13.499):
                            outside = (mesh_cross_section(mesh,height) - mesh_cross_section(meshes[name],height).offset(.0001)).area()
                            assert abs(outside) < .02, (name, height, outside)
                        color_modifiers.append({'part': name, 'filament': 4, 'z_mm': mesh.bounds[:, 2].tolist(),
                                                'volume_mm3': float(mesh.volume), 'path_error_mm2': path_error, 'flush': True})
                        continue
                    if colored and props(part).get('extruder') == '2':
                        assert name.startswith('F') or name == test_plate.get('full_width_weave_test')
                        assert np.allclose(mesh.bounds[:, 2], [8.4, wood_top], atol=1e-4)
                        assert 'sparse_infill_density' not in props(part)
                        mask_solid = manifold3d.Manifold(manifold3d.Mesh64(mesh.vertices, mesh.faces.astype(np.uint64)))
                        source_solid = manifold3d.Manifold(manifold3d.Mesh64(meshes[name].vertices, meshes[name].faces.astype(np.uint64)))
                        overlap = (mask_solid ^ source_solid).volume()
                        assert overlap > 100
                        if 'weave_restoration' in baseline:
                            # The modifier must follow the recesses and caps;
                            # reject a filled prism that visually hides them.
                            # Avoid subtracting exactly coincident 3D faces.
                            # The weave is piecewise constant across these
                            # three bands; test the cross-sections directly.
                            for height in (8.7, 9.3, 9.75):
                                outside = (mesh_cross_section(mesh,height) - mesh_cross_section(meshes[name],height).offset(.0001)).area()
                                assert abs(outside) < .02, (name, height, outside)
                        color_modifiers.append({'part': name, 'filament': 2, 'z_mm': mesh.bounds[:, 2].tolist()})
                        continue
                    assert props(part)['sparse_infill_density'] == '100%'
                    assert trimesh.boolean.intersection([mesh, meshes[name]], engine='manifold').volume > 1
                    modifier_count += 1
                else:
                    for key in ('wall_loops', 'sparse_infill_density', 'sparse_infill_pattern', 'layer_height'):
                        assert props(part).get(key, expected_settings[key]) == expected_settings[key], (name, key)
                    ref = meshes[name]
                    if colored:
                        # Bambu omits redundant part-level assignments for
                        # some single-volume objects; they inherit the object.
                        slot = props(part).get('extruder', op['extruder'])
                        assert slot == expected_slot, (name, slot)
                    assert len(mesh.faces) == len(ref.faces)
                    error = max(nearest_error(ref.vertices, mesh.vertices), nearest_error(mesh.vertices, ref.vertices),
                                nearest_error(ref.triangles_center, mesh.triangles_center))
                    assert error < 1e-4, (name, error)
                    normal_errors.append({'part': name, 'maximum_geometry_error_mm': error})
            for bt, position in zip(builds[oid], source_positions[name]):
                assert np.allclose(bt[:3, :3], np.eye(3), atol=1e-7)
                assert np.allclose(bt[:3, 3] - builds[oid][0][:3, 3], position - source_positions[name][0], atol=1e-5)
        assert len(normal_errors) == len(meshes) and modifier_count == expected_modifiers
        report['normal_mesh_comparisons'] = normal_errors
        report['solid_modifiers_verified'] = modifier_count
        if colored:
            expected_color_parts = [f'F{i}' for i in range(1, 21)]
            if test_plate.get('full_width_weave_test'):
                expected_color_parts.append(test_plate['full_width_weave_test'])
            for slot in ([2, 4] if blue_edge else [2]):
                assert sorted(p['part'] for p in color_modifiers if p['filament'] == slot) == sorted(expected_color_parts)
            report['color_modifiers_verified'] = color_modifiers
        print(f'3MF meshes, all instance placements, {modifier_count} solid modifiers and '
              f'{len(color_modifiers)} color modifiers verified', flush=True)
        plates = config.findall('plate')
        assert len(plates) == expected_plate_count
        slice_info = ET.fromstring(archive.read('Metadata/slice_info.config'))
        sliced_plates = {int(props(p)['index']): p for p in slice_info.findall('plate')}
        quantity = collections.Counter()
        for plate in plates:
            pp = props(plate)
            number = int(pp['plater_id'])
            actual = collections.Counter(names[props(i)['object_id']] for i in plate.findall('model_instance'))
            expected = collections.Counter(i['name'] for i in baseline['plate_layout'][number - 1]['items'])
            assert actual == expected
            quantity.update(actual)
            gcode = archive.read(pp['gcode_file']).decode()
            assert '; EXECUTABLE_BLOCK_END' in gcode
            labels = re.search(r'^; model label id: (.*)$', gcode, re.M)
            if labels:
                assert len(labels[1].strip().split(',')) == sum(actual.values())
                heights = list(map(float, re.search(r'^; object max height: (.*)$', gcode, re.M)[1].split(',')))
                expected_heights = sorted(float(meshes[name].bounds[1, 2]) for name in actual.elements())
                # Headers contain sliced heights: e.g. a 13.5 mm model reaches
                # 13.6 mm on the saved 0.2 mm layer grid.
                assert np.allclose(sorted(heights), expected_heights,
                                   atol=float(expected_settings['layer_height']) + .001)
            else:
                assert sum(actual.values()) == 1
            maximum_z = float(re.search(r'^; max_z_height: (.*)$', gcode, re.M)[1])
            assert abs(maximum_z - max(meshes[name].bounds[1, 2] for name in actual)) <= .201
            for key in ('wall_loops', 'sparse_infill_density', 'sparse_infill_pattern', 'layer_height'):
                assert f'; {key} = {expected_settings[key]}\n' in gcode
            scan = scan_gcode(gcode)
            assert scan['conservative_bed_edge_clearance_mm'] >= 0, (number, scan)
            weights = filament_weights(gcode)
            mass = sum(weights)
            color_info = {}
            if colored:
                stat = sliced_plates[number]
                slots = {int(f.get('id')) for f in stat.findall('filament')}
                frame_slots = {1, 2, 4} if blue_edge else {1, 2}
                test_slots = (frame_slots if number == 30 else {3}) if 'plates' in test_plate else ({1, 2, 3} if test_plate.get('full_width_weave_test') else {1, 3})
                expected_slots = frame_slots if number <= 20 else {3} if number <= 26 else {1} if number <= 29 else test_slots
                assert slots == expected_slots, (number, slots)
                for filament in stat.findall('filament'):
                    slot = int(filament.get('id'))
                    assert filament.get('color') == settings['filament_colour'][slot - 1]
                    assert abs(float(filament.get('used_g')) - weights[slot - 1]) < .02
                layers = [dict(p.attrib) for p in stat.findall('layer_filament_lists/layer_filament_list')]
                if number <= 20 or (number == 30 and test_plate.get('full_width_weave_test')):
                    wood_layers = [p for p in layers if '1' in p['filament_list'].split()]
                    expected_range = '42 49' if wood_top == 9.9 else '42 47'
                    assert len(wood_layers) == 1 and wood_layers[0]['layer_ranges'] == expected_range, (number, wood_layers)
                    if blue_edge:
                        blue_layers = [p for p in layers if '3' in p['filament_list'].split()]
                        assert len(blue_layers) == 1 and blue_layers[0]['layer_ranges'] == '65 67', (number, blue_layers)
                        assert all('1' not in p['filament_list'].split() for p in blue_layers)
                        assert scan['model_extrusion_z_by_filament_mm']['4'] == [13.2, 13.4, 13.6], (number, scan['model_extrusion_z_by_filament_mm'])
                color_info = {'filament_slots': sorted(slots), 'layer_filament_lists': layers,
                              'filament_changes': len(re.findall(r'^; CP TOOLCHANGE START', gcode, re.M)),
                              'slicer_notices': [dict(w.attrib) for w in stat.findall('warning')]}
                if number <= 20 or (blue_edge and number == 30):
                    # Tall M locating pins continue in white above the rail face.
                    blue_changes = (3 + int(maximum_z > 13.601)) if blue_edge else 0
                    assert color_info['filament_changes'] == (8 if wood_top == 9.9 else 6) + blue_changes, (number, color_info)
                if 'plates' in test_plate and number >= 30:
                    bed_temps = [float(v) for v in re.findall(r'^M1[49]0 S([\d.]+)', gcode, re.M) if float(v) > 0]
                    expected_bed = 65 if number == 30 else 55
                    assert bed_temps and set(bed_temps) == {expected_bed}, (number, bed_temps)
                    if number == 31:
                        assert color_info['filament_changes'] == 0
                    color_info['bed_temperatures_c'] = bed_temps
            duration = re.search(r'total estimated time: ([^\n]+)', gcode)[1]
            seconds = sum(int(n) * {'h': 3600, 'm': 60, 's': 1}[u] for n, u in re.findall(r'(\d+)([hms])', duration))
            report['plates'].append({'plate': number, 'parts': dict(actual), 'weight_g': mass,
                                     'filament_weights_g': weights,
                                     'estimated_seconds': seconds, 'settings_verified': True, **color_info, **scan})
            print(f'Plate {number}: {scan["extrusion_moves_checked"]} extrusion moves; edge {scan["conservative_bed_edge_clearance_mm"]:.3f} mm', flush=True)
        assert dict(quantity) == expected_quantities
    report['summary'] = {'digital_checks_passed': True, 'distinct_meshes': len(meshes),
                         'pieces': sum(expected_quantities.values()), 'plates': expected_plate_count,
                         'production_pieces': 70, 'test_pieces': len(test_parts),
                         'minimum_edge_clearance_mm': min(p['conservative_bed_edge_clearance_mm'] for p in report['plates']),
                         'extrusion_moves_checked': sum(p['extrusion_moves_checked'] for p in report['plates']),
                         'total_weight_g': round(sum(p['weight_g'] for p in report['plates']), 2),
                         'total_estimated_seconds': sum(p['estimated_seconds'] for p in report['plates'])}
    report['summary']['filament_weights_g'] = [round(sum(p['filament_weights_g'][i] if i < len(p['filament_weights_g']) else 0
                                                       for p in report['plates']), 2)
                                                for i in range(len(settings['filament_colour']))]
    args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report['summary'], indent=2))


if __name__ == '__main__':
    main()
