"""Cap only Knot's solid screw modifiers below the continuous top skin.

Revision-specific migration from the saved production project. No printer job
is sent. Build/slice in .work, validate native toolpaths, then publish explicitly.
"""
import argparse
import copy
import hashlib
import json
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / '.work/python-libs'), str(ROOT / 'scripts')]
import numpy as np
from organize_root_projects import (rows, compare, dump, sha, ASSET,
    clean_relations, BOOKKEEPING)
from development_3mf import props, tag, transform, P
from promote_veneer_wall_cradle import read, write, EXE

WORK = ROOT / '.work/knot-reinforcement-skin-r1'
REPORT = ROOT / 'release/knot-reinforcement-skin-r1'
BASE = WORK / 'Knot-before.3mf'
EDIT = WORK / 'Knot-editable.3mf'
NATIVE = WORK / 'native'
FINAL = WORK / 'Knot-final.3mf'
SOURCE_SHA = '2510f6f9bd0139155d7aea0603b0e24c3e5c9ac414f946abf9aadf1464f9c356'
CAP = 12.4


def protected():
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in
            [*ROOT.glob('*.3mf'), *ROOT.glob('Letter STL/*.stl'),
             *ROOT.glob('Small Parts* STL/*.stl'),
             ROOT / 'release/samples/Dara-A2L-Hammered-Finish-ERYONE-r4.3mf']
            if p.name != 'Knot.3mf'}


def build():
    assert sha(ROOT / 'Knot.3mf') == SOURCE_SHA
    WORK.mkdir(parents=True, exist_ok=True)
    REPORT.mkdir(parents=True, exist_ok=True)
    if not BASE.exists():
        shutil.copyfile(ROOT / 'Knot.3mf', BASE)
        for name in ['AGENTS.md', 'release/root-projects/catalog.json',
                     'release/root-projects/gcode-sha256.json',
                     'release/root-projects/README.md']:
            target = WORK / 'initial' / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
    assert sha(BASE) == SOURCE_SHA
    files = read(BASE)
    cfg = ET.fromstring(files['Metadata/model_settings.config'])
    model = ET.fromstring(files['3D/3dmodel.model'])
    trees, changed = {}, []
    for obj in cfg.findall('object'):
        parent = model.find(tag('resources')).find(f"{tag('object')}[@id='{obj.get('id')}']")
        components = {c.get('objectid'): c for c in parent.find(tag('components'))}
        for part in obj.findall('part'):
            if props(part).get('sparse_infill_density') != '100%':
                continue
            assert part.get('subtype') == 'modifier_part'
            assert props(part)['name'] == 'Local solid screw reinforcement'
            co = components[part.get('id')]
            t = transform(co.get('transform'))
            assert np.array_equal(t[:3, :3], np.eye(3))
            asset = co.get('{' + P + '}path').lstrip('/')
            if asset not in trees:
                trees[asset] = ET.fromstring(files[asset])
            node = trees[asset].find(tag('resources')).find(f"{tag('object')}[@id='{part.get('id')}']")
            vertices = node.find(tag('mesh')).find(tag('vertices'))
            z = np.array([float(v.get('z')) + t[2, 3] for v in vertices])
            assert set(z) == {0., 17.}
            for v, oldz in zip(vertices, z):
                if oldz == 17.:
                    v.set('z', format(CAP - t[2, 3], '.12g'))
            changed.append(dict(object=props(obj)['name'], volume_id=part.get('id'),
                                asset=asset, old_z_mm=[0, 17], new_z_mm=[0, CAP]))
    assert len(changed) == 50
    # Patch only the affected object blocks to preserve all normal/color meshes
    # and their XML (including support paint) exactly.
    for asset, tree in trees.items():
        text = files[asset].decode()
        for item in [c for c in changed if c['asset'] == asset]:
            pid = item['volume_id']
            pattern = rf'(<object\b[^>]*\bid="{pid}"[^>]*>)(.*?)(</object>)'
            hit = re.search(pattern, text, re.S)
            assert hit
            body = hit[2]
            def vertex(match):
                value = float(match[1])
                return 'z="3.9"' if value == 8.5 else match[0]
            assert len(re.findall(r'z="8\.5"', body)) == 64
            replacement = re.sub(r'z="([^"]+)"', vertex, body)
            text = text[:hit.start(2)] + replacement + text[hit.end(2):]
        files[asset] = text.encode()
    for name in list(files):
        if ASSET.fullmatch(name) or name in ['Metadata/slice_info.config', 'Metadata/filament_sequence.json']:
            del files[name]
    for plate in cfg.findall('plate'):
        for md in list(plate.findall('metadata')):
            if md.get('key', '').endswith('_file'):
                plate.remove(md)
    files['Metadata/model_settings.config'] = ET.tostring(cfg, encoding='utf-8', xml_declaration=True)
    clean_relations(files)
    write(EDIT, files)
    dump(REPORT / 'provenance.json', dict(source='Knot.3mf', source_sha256=SOURCE_SHA,
         editable_sha256=sha(EDIT), changes=changed, protected_before=protected(),
         process_changes={}, normal_geometry_changes=False, material_boundary_changes=False,
         pose_changes=False, physical_qualification='Pending physical print/finish confirmation'))
    print('Built 50 capped modifiers; top 17.0 -> 12.4 mm; all process settings preserved.', flush=True)


def native(info=False):
    folder = WORK / 'reopen' if info else NATIVE
    folder.mkdir(parents=True, exist_ok=True)
    args = ['--info'] if info else ['--slice', '0', '--export-3mf', 'sliced.3mf']
    source = FINAL if info else EDIT
    for attempt in range(3):
        with (folder / 'run.log').open('w') as log:
            result = subprocess.run([str(EXE), *args, '--outputdir', str(folder), str(source)],
                cwd=EXE.parent, stdout=log, stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW)
        if result.returncode != 3221225477:
            break
    result.check_returncode()
    data = json.loads((folder / 'result.json').read_text())
    assert data['return_code'] == 0
    if not info:
        assert [p['id'] for p in data['sliced_plates']] == list(range(1, 11))
    print('Native reopen passed.' if info else 'Ten native plates sliced.', flush=True)


def shell_paths(text):
    from validate_ribbon_bed_datum import segments
    paths = segments(text, {1: 'knot'}, single_object=True)['knot']
    return [p for p in paths if 12.79 <= p[2][1][2] <= 13.61]


def crossings(paths, center, radius):
    a = np.asarray([p[2] for p in paths])
    delta = a[:, 1, :2] - a[:, 0, :2]
    fraction = np.clip(((center - a[:, 0, :2]) * delta).sum(axis=1) /
                       (delta * delta).sum(axis=1), 0, 1)
    near = np.linalg.norm(a[:, 0, :2] + fraction[:, None] * delta - center, axis=1)
    far = np.linalg.norm(a[:, :, :2] - center, axis=2).max(axis=1)
    fill = np.array([p[1] in ['Top surface', 'Internal solid infill', 'Bridge',
                             'Floating vertical shell'] for p in paths])
    cross = fill & (near < radius - .4) & (far > radius + .4)
    return {str(z): int((cross & (abs(a[:, 1, 2] - z) < .001)).sum())
            for z in [12.8, 13.0, 13.2, 13.4, 13.6]}


def validate():
    from shapely.geometry import Point, Polygon, MultiPoint
    from shapely import union_all
    from validate_print_project import scan_gcode
    from check_a2l_towers import check_startup_tower, check_tower
    from validate_a2l_project import material_angles
    assert sha(BASE) == SOURCE_SHA
    proof = json.loads((REPORT / 'provenance.json').read_text())
    assert sha(EDIT) == proof['editable_sha256']
    assert protected() == proof['protected_before']
    oldfiles, editfiles, nativefiles = read(BASE), read(EDIT), read(NATIVE / 'sliced.3mf')
    settings, oldrows = rows(BASE)
    edited_settings, editrows = rows(EDIT)
    assert settings == edited_settings
    native_check = compare(EDIT, NATIVE / 'sliced.3mf')
    # No effective global settings, tower positions or process overrides change.
    assert not native_check['settings_changes'], native_check['settings_changes']
    assert oldfiles['3D/3dmodel.model'] == editfiles['3D/3dmodel.model']
    assert oldfiles['Metadata/project_settings.config'] == editfiles['Metadata/project_settings.config']
    original_cfg = ET.fromstring(oldfiles['Metadata/model_settings.config'])
    edit_cfg = ET.fromstring(editfiles['Metadata/model_settings.config'])
    assert [ET.tostring(o) for o in original_cfg.findall('object')] == [ET.tostring(o) for o in edit_cfg.findall('object')]
    locks = dict(sparse_infill_density='8%', sparse_infill_pattern='gyroid',
                 layer_height='0.2', initial_layer_print_height='0.2', wall_loops='4',
                 top_shell_layers='5', bottom_shell_layers='5', curr_bed_type='Textured PEI Plate',
                 is_infill_first='1', support_top_z_distance='0.2')
    for k, v in locks.items():
        assert settings[k] == v, (k, settings[k])
    assert settings['printer_model'] == 'Bambu Lab A2L' and settings['nozzle_diameter'] == ['0.4']
    geometry = []
    for old, new in zip(oldrows, editrows):
        assert old['settings'] == new['settings']
        assert np.array_equal(old['transform'], new['transform'])
        surfaces = []
        for part in old['parts']:
            if part['subtype'] == 'normal_part':
                m = part['mesh']; triangles = m.triangles
                up = m.face_normals[:, 2] > .999
                for z in np.unique(np.round(triangles[up, :, 2].mean(axis=1), 4)):
                    chosen = triangles[up & (abs(triangles[:, :, 2].mean(axis=1) - z) < .0001)]
                    surfaces.append((float(z), union_all([Polygon(t[:, :2]) for t in chosen])))
        for i, (a, b) in enumerate(zip(old['parts'], new['parts'])):
            assert a['settings'] == b['settings'] and a['subtype'] == b['subtype'] and a['paint'] == b['paint']
            assert np.array_equal(a['mesh'].faces, b['mesh'].faces)
            expected = a['mesh'].vertices.copy()
            reinforcement = a['settings'].get('sparse_infill_density') == '100%'
            effective = {**settings, **old['settings'], **a['settings']}
            for k, v in locks.items():
                assert effective[k] == ('100%' if reinforcement and k == 'sparse_infill_density' else v)
            assert effective['support_interface_spacing'] == '0.2'
            if reinforcement:
                expected[expected[:, 2] == 17., 2] = CAP
                assert b['mesh'].is_watertight and b['mesh'].is_volume
                bounds = a['mesh'].bounds
                xy = bounds.mean(axis=0)[:2]
                radius = (bounds[1, 0] - bounds[0, 0]) / 2
                disc = Point(xy).buffer(radius, quad_segs=32)
                heights = sorted({z for z, g in surfaces if g.intersection(disc).area > .0001})
                assert heights == [13.5], (old['name'], i, heights)
                geometry.append(dict(plate=old['plate'], volume=i+1, xy_assembly_mm=xy.tolist(),
                    radius_mm=radius, visible_top_z_mm=13.5, new_modifier_top_z_mm=CAP,
                    nominal_continuous_skin_clearance_mm=1.1))
            assert np.max(abs(expected - b['mesh'].vertices)) < 1e-9
        # Verify byte-for-byte preservation of every non-reinforcement XML object.
    for asset in {c['asset'] for c in proof['changes']}:
        a, b = oldfiles[asset].decode(), editfiles[asset].decode()
        ids = {c['volume_id'] for c in proof['changes'] if c['asset'] == asset}
        pattern = r'<object\b[^>]*\bid="(\d+)"[^>]*>.*?</object>'
        aa = {m[1]: m[0] for m in re.finditer(pattern, a, re.S)}
        bb = {m[1]: m[0] for m in re.finditer(pattern, b, re.S)}
        assert aa.keys() == bb.keys()
        for pid in aa.keys() - ids:
            assert aa[pid] == bb[pid]
    assert len(geometry) == 50
    dump(REPORT / 'geometry.json', dict(modifiers=geometry, normal_and_color_meshes_byte_identical=True,
         all_transforms_and_all_object_volume_settings_identical=True, native_roundtrip=native_check))
    info = ET.fromstring(nativefiles['Metadata/slice_info.config'])
    results = json.loads((NATIVE / 'result.json').read_text())
    records = []
    for row in editrows:
        number = row['plate']; name = f'Metadata/plate_{number}.gcode'
        raw = nativefiles[name]; text = raw.decode(); oldtext = oldfiles[name].decode()
        assert hashlib.md5(raw).hexdigest().upper() == nativefiles[name+'.md5'].decode().strip().upper()
        gc = dict(re.findall(r'^; ([A-Za-z_0-9]+) = (.*)$', text, re.M))
        for k, v in locks.items():
            assert gc[k] == v, (number, k, gc[k])
        assert gc['nozzle_diameter'] == '0.4' and '; EXECUTABLE_BLOCK_END' in text
        scan, oldscan = scan_gcode(text), scan_gcode(oldtext)
        assert scan['model_extrusion_z_by_filament_mm'] == oldscan['model_extrusion_z_by_filament_mm']
        low, high = np.array(scan['bead_xy_bounds_mm'])
        bed_clearance = float(min(*low, *(np.array([330, 320]) - high)))
        assert bed_clearance > .5
        t = row['transform']
        hulls = [MultiPoint((p['mesh'].vertices @ t[:3, :3].T + t[:3, 3])[:, :2]).convex_hull
                 for p in row['parts'] if p['subtype'] == 'normal_part']
        top = max(max(z) for z in scan['model_extrusion_z_by_filament_mm'].values())
        startup = check_startup_tower(settings, hulls, 3, top, number)
        tower = check_tower(text, hulls, [0, 0, 330, 320])
        angles, oldangles = material_angles(text, 0), material_angles(oldtext, 0)
        assert {(a['filament_slot'], a['z_mm']) for a in angles} == {(a['filament_slot'], a['z_mm']) for a in oldangles}
        for a in angles:
            b = next(b for b in oldangles if b['filament_slot'] == a['filament_slot'] and b['z_mm'] == a['z_mm'])
            assert abs((a['dominant_assembly_angle_deg'] - b['dominant_assembly_angle_deg'] + 90) % 180 - 90) < 1
        before_paths, after_paths = shell_paths(oldtext), shell_paths(text)
        checks = []
        for site in [g for g in geometry if g['plate'] == number]:
            xy = (np.array([*site['xy_assembly_mm'], 0]) @ t[:3, :3].T + t[:3, 3])[:2]
            before = crossings(before_paths, xy, site['radius_mm'])
            after = crossings(after_paths, xy, site['radius_mm'])
            assert min(after.values()) >= 5, (number, site['volume'], before, after)
            checks.append(dict(volume=site['volume'], center_bed_xy_mm=xy.tolist(),
                old_cross_boundary_extrusion_segments=before, new_cross_boundary_extrusion_segments=after))
        pi = next(p for p in info.findall('plate') if props(p)['index'] == str(number))
        warnings = [w.attrib for w in pi.findall('warning')]
        assert all(w.get('msg') == 'not_support_traditional_timelapse' for w in warnings)
        estimate = next(p for p in results['sliced_plates'] if p['id'] == number)
        records.append(dict(plate=number, gcode_sha256=hashlib.sha256(raw).hexdigest(),
            gcode_md5_verified=True, shell_continuity=checks, bed_clearance_mm=bed_clearance,
            startup_tower=startup, tower=tower, model_z_by_filament_mm=scan['model_extrusion_z_by_filament_mm'],
            finish_angles=angles, warnings=warnings, seconds=estimate['total_predication'],
            grams=sum(f['total_used_g'] for f in estimate['filaments'])))
        if number == 3:
            preview(before_paths, after_paths, checks[0]['center_bed_xy_mm'],
                    next(g['radius_mm'] for g in geometry if g['plate'] == 3))
        print(f'Plate {number}: five continuous skin layers over {len(checks)} screw zones; settings, colors and clearances pass.', flush=True)
        dump(WORK / 'toolpath-progress.json', records)
    # Keep exact edited meshes and saved poses; transplant all fresh native plate
    # payloads and their metadata, mapping each native identify_id to its plate.
    final = dict(oldfiles)
    for asset in {c['asset'] for c in proof['changes']}:
        final[asset] = editfiles[asset]
    nc = ET.fromstring(nativefiles['Metadata/model_settings.config'])
    for a, b in zip(original_cfg.findall('plate'), nc.findall('plate')):
        for md in list(a.findall('metadata')):
            a.remove(md)
        for md in b.findall('metadata'):
            a.insert(0, copy.deepcopy(md))
        ai, bi = a.find('model_instance'), b.find('model_instance')
        for md in ai.findall('metadata'):
            if md.get('key') == 'identify_id':
                md.set('value', props(bi)['identify_id'])
    final['Metadata/model_settings.config'] = ET.tostring(original_cfg, encoding='utf-8', xml_declaration=True)
    for name, data in nativefiles.items():
        if ASSET.fullmatch(name) or name in ['Metadata/slice_info.config', 'Metadata/filament_sequence.json']:
            final[name] = data
    write(FINAL, final)
    compare(EDIT, FINAL)
    native(info=True)
    assert protected() == proof['protected_before']
    validation = dict(project='Knot.3mf', project_sha256=sha(FINAL), source_sha256=SOURCE_SHA,
        editable_sha256=sha(EDIT), native_project_sha256=sha(NATIVE / 'sliced.3mf'),
        modifier_count=50, modifier_z_change_mm=[17, CAP], unchanged_process_settings=True,
        normal_geometry_material_boundaries_poses_and_support_paint_preserved=True,
        all_five_top_shell_layers_cross_former_modifier_boundary=True, plates=records,
        total_seconds=sum(p['seconds'] for p in records), total_grams=sum(p['grams'] for p in records),
        protected_after=protected(), native_roundtrip=native_check,
        native_reopen=json.loads((WORK / 'reopen/result.json').read_text()),
        physical_finish_confirmation_pending=True, printer_job_sent=False)
    dump(REPORT / 'validation.json', validation)
    shutil.copyfile(NATIVE / 'result.json', REPORT / 'native-result.json')
    print('Validation passed; publish is a separate explicit command.', flush=True)


def preview(before, after, center, radius):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    fig, axes = plt.subplots(1, 2, figsize=(10, 5), layout='constrained')
    for ax, paths, title in zip(axes, [before, after], ['Before: surface split at cylinder', 'After: continuous top-surface paths']):
        for slot, color in [(1, '#555555'), (4, '#1779ab')]:
            lines = [p[2] for p in paths if p[0] == slot and abs(p[2][1][2] - 13.6) < .001]
            ax.add_collection(LineCollection(np.asarray(lines)[:, :, :2], colors=color, linewidths=.65))
        ax.add_patch(plt.Circle(center, radius, fill=False, color='#c44e52', linestyle='--', linewidth=1))
        ax.set(xlim=(center[0]-radius-3, center[0]+radius+3), ylim=(center[1]-radius-3, center[1]+radius+3),
               xlabel='Bed X (mm)', ylabel='Bed Y (mm)', title=title, aspect='equal')
    fig.suptitle('Knot plate 3 | saved native G-code at Z13.6 mm\nDashed circle marks the former reinforcement boundary')
    fig.savefig(REPORT / 'top-surface-before-after.png', dpi=180)
    plt.close(fig)


def publish():
    report = json.loads((REPORT / 'validation.json').read_text())
    assert sha(FINAL) == report['project_sha256'] and sha(ROOT / 'Knot.3mf') == SOURCE_SHA
    assert protected() == report['protected_after']
    catalog_path = ROOT / 'release/root-projects/catalog.json'
    catalog = json.loads(catalog_path.read_text())
    s, objects = rows(FINAL)
    entry = catalog['Knot']
    assert entry['sha256'] == SOURCE_SHA
    for record, obj in zip(entry['objects'], objects):
        assert record['name'] == obj['name']
        for saved, part in zip(record['parts'], obj['parts']):
            if part['settings'].get('sparse_infill_density') != '100%':
                assert sha(ROOT / saved['file']) == saved['sha256']
                continue
            data = part['mesh'].export(file_type='stl')
            (ROOT / saved['file']).write_bytes(data)
            saved.update(sha256=hashlib.sha256(data).hexdigest(), bounds=part['mesh'].bounds.tolist())
    shutil.copyfile(FINAL, ROOT / 'Knot.3mf')
    entry['sha256'] = sha(ROOT / 'Knot.3mf')
    entry['validation'] = 'release/knot-reinforcement-skin-r1/validation.json'
    dump(catalog_path, catalog)
    hashes_path = ROOT / 'release/root-projects/gcode-sha256.json'
    hashes = json.loads(hashes_path.read_text())
    hashes['Knot'] = {f"plate_{r['plate']}": r['gcode_sha256'] for r in report['plates']}
    dump(hashes_path, hashes)
    shutil.copyfile(REPORT / 'native-result.json', ROOT / 'release/root-projects/Knot-native.json')
    assert protected() == report['protected_after']
    print('Published Knot and its 50 modifier STLs; CAD references remain unchanged.', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['build', 'slice', 'reopen', 'validate', 'publish'])
    args = parser.parse_args()
    if args.action == 'build':
        build()
    elif args.action in ['slice', 'reopen']:
        native(args.action == 'reopen')
    else:
        globals()[args.action]()
