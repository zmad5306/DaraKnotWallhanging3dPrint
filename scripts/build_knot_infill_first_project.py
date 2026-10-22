"""Separate A2L knot project with the user-approved r3 support correction.

Extract exact production F1-F10 meshes and settings. Change only infill-first,
support-interface spacing, and packaging for a ten-plate project. Never write
to the original production, M, or A1 files and never send a printer job.
"""
import argparse
import copy
import hashlib
import json
import math
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.work/python-libs'))
import numpy as np
from development_3mf import sha, save_json, props, tag, transform, xml, P, R
from promote_veneer_wall_cradle import read, write, setmeta, EXE

SOURCE = ROOT / 'Dara.3mf'
SOURCE_SHA = '64cd3a8d9a07f55028201c68f8c48ef1ad1fdcf32d4391811a3b5ab7eded5f13'
TEST = ROOT / 'output/Dara-A2L-Photo-Curve-Infill-First-r3'
TEST_SHA = '5fc8fe29ea2993bdceaf690744506bd14bf757982a76b6937e9e7ce4b9192bb0'
PRODUCTION = ROOT / 'working/bambu/Dara-Photo-Frame-A2L'
OUT = ROOT / 'working/bambu/Dara-A2L-Knot-Infill-First'
WORK = ROOT / '.work/knot-infill-first'
EDIT = OUT / 'Dara-A2L-Knot-Infill-First-Editable.3mf'
FINAL = OUT / 'Dara-A2L-Knot-Infill-First.3mf'
NATIVE = WORK / 'native'
LOCKS = dict(sparse_infill_density='8%', sparse_infill_pattern='gyroid',
    layer_height='0.2', initial_layer_print_height='0.2', wall_loops='4',
    top_shell_layers='5', bottom_shell_layers='5', curr_bed_type='Textured PEI Plate')
BOOKKEEPING = {'name', 'matrix', 'source_file', 'source_object_id', 'source_volume_id',
    'source_offset_x', 'source_offset_y', 'source_offset_z', None, 'null'}


def effective(values):
    return {k: v for k, v in values.items() if k not in BOOKKEEPING}


def embedded(path):
    """Decode each child mesh XML once, including every material modifier."""
    from colorize_print_project import read_mesh
    files = read(path)
    cfg = ET.fromstring(files['Metadata/model_settings.config'])
    model = ET.fromstring(files['3D/3dmodel.model'])
    objects = {o.get('id'): o for o in model.find(tag('resources'))}
    configs = {o.get('id'): o for o in cfg.findall('object')}
    items = {o.get('objectid'): o for o in model.find(tag('build'))}
    cols = math.ceil(math.sqrt(len(cfg.findall('plate'))))
    assets, rows = {}, {}
    for i, plate in enumerate(cfg.findall('plate')):
        for instance in plate.findall('model_instance'):
            oid = props(instance)['object_id']
            t = transform(items[oid].get('transform'))
            t[:2, 3] -= [i % cols * 396, -(i // cols) * 384]
            components = {c.get('objectid'): c for c in objects[oid].find(tag('components'))}
            parts = []
            for part in configs[oid].findall('part'):
                co = components[part.get('id')]
                asset = co.get('{' + P + '}path').lstrip('/')
                if asset not in assets:
                    tree = ET.fromstring(files[asset])
                    assets[asset] = {o.get('id'): o for o in tree.find(tag('resources'))}
                mesh = read_mesh(assets[asset][co.get('objectid')])
                mesh.apply_transform(transform(co.get('transform')))
                parts.append(dict(mesh=mesh, subtype=part.get('subtype'), settings=props(part)))
            settings = props(configs[oid])
            rows[settings['name']] = dict(parts=parts, settings=settings, transform=t, plate=i+1)
    return files, rows


def protected():
    paths = [SOURCE, PRODUCTION / 'Dara-A2L-Complete.3mf', PRODUCTION / 'Dara-A2L-Editable.3mf']
    paths += list((ROOT / 'working/bambu/Dara-A1-Companion').rglob('*'))
    paths += [ROOT / 'working/bambu/Dara-Photo-Frame-A1-Jointed/Dara-Photo-Frame-A1-Complete.3mf']
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in paths if p.is_file()}


def build():
    assert sha(SOURCE) == SOURCE_SHA
    assert sha(TEST / (TEST.name + '.3mf')) == TEST_SHA
    OUT.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    before = protected()
    files = read(SOURCE)
    cfg = ET.fromstring(files['Metadata/model_settings.config'])
    model = ET.fromstring(files['3D/3dmodel.model'])
    plates = cfg.findall('plate')
    assert len(plates) == 20
    retained = {props(p.find('model_instance'))['object_id'] for p in plates[:10]}
    assert len(retained) == 10
    assets = set()
    resources = model.find(tag('resources'))
    for obj in list(resources):
        if obj.get('id') not in retained:
            resources.remove(obj)
        else:
            assets.update(c.get('{' + P + '}path').lstrip('/') for c in obj.find(tag('components')))
    for obj in list(cfg.findall('object')):
        if obj.get('id') not in retained:
            cfg.remove(obj)
        else:
            assert 'support_interface_spacing' not in props(obj)
            setmeta(obj, 'support_interface_spacing', '0.2')
    for plate in plates[10:]:
        cfg.remove(plate)
    for plate in plates[:10]:
        for md in list(plate.findall('metadata')):
            if md.get('key') in ['gcode_file', 'thumbnail_file', 'thumbnail_no_light_file', 'top_file', 'pick_file']:
                plate.remove(md)
    plate_index = {props(p.find('model_instance'))['object_id']: i for i, p in enumerate(plates[:10])}
    transforms = []
    for item in list(model.find(tag('build'))):
        oid = item.get('objectid')
        if oid not in retained:
            model.find(tag('build')).remove(item)
            continue
        i = plate_index[oid]
        # Studio displays 20 plates in five columns and 10 plates in four.
        # Change only display-grid offsets, keeping the actual bed pose fixed.
        t = transform(item.get('transform'))
        offset = np.array([i % 4 * 396, -(i // 4) * 384]) - np.array([i % 5 * 396, -(i // 5) * 384])
        t[:2, 3] += offset
        item.set('transform', ' '.join(format(float(v), '.12g') for v in t[:3].T.reshape(-1)))
        transforms.append(dict(plate=i+1, object_id=oid, display_grid_offset_xy_mm=offset.tolist()))
    for name in list(files):
        if name.startswith('3D/Objects/') and name not in assets:
            del files[name]
        elif re.fullmatch(r'Metadata/(?:plate_\d+(?:_small)?|plate_no_light_\d+|top_\d+|pick_\d+)\.(?:png|json|gcode(?:\.md5)?)', name):
            del files[name]
    files.pop('Metadata/slice_info.config', None)
    files.pop('Metadata/filament_sequence.json', None)
    rels = ET.fromstring(files['3D/_rels/3dmodel.model.rels'])
    clean = ET.Element('Relationships', xmlns=R)
    for rel in rels:
        if rel.get('Target').lstrip('/') in assets:
            ET.SubElement(clean, 'Relationship', rel.attrib)
    files['3D/_rels/3dmodel.model.rels'] = xml(clean)
    files['3D/3dmodel.model'] = xml(model)
    files['Metadata/model_settings.config'] = xml(cfg)
    settings = json.loads(files['Metadata/project_settings.config'])
    assert settings['is_infill_first'] == '0'
    settings['is_infill_first'] = '1'
    for key in ['wipe_tower_x', 'wipe_tower_y']:
        assert len(settings[key]) == 20
        settings[key] = settings[key][:10]
    files['Metadata/project_settings.config'] = json.dumps(settings, indent=2).encode()
    # Remove relationships to discarded slices/thumbnails in the editable file.
    for name in [n for n in files if n.endswith('.rels')]:
        clean = ET.Element('Relationships', xmlns=R)
        for rel in ET.fromstring(files[name]):
            if rel.get('TargetMode') == 'External' or rel.get('Target').lstrip('/') in files:
                ET.SubElement(clean, 'Relationship', rel.attrib)
        files[name] = xml(clean)
    write(EDIT, files)
    save_json(OUT / 'source-provenance.json', dict(source='Dara.3mf', source_sha256=SOURCE_SHA,
        source_plates=list(range(1, 11)), full_parts_no_crop=True,
        child_mesh_assets_sha256={n: hashlib.sha256(files[n]).hexdigest() for n in sorted(assets)},
        geometry_changes='None', print_pose_changes='None', display_grid_repack=transforms,
        global_process_change={'is_infill_first': ['0', '1']},
        object_process_change={'support_interface_spacing': ['0.5 inherited', '0.2']},
        packaging_changes=['Remove plates 11-20 and their unused objects/assets',
            '20-to-10 plate display-grid offsets', 'Trim tower position arrays to the same ten retained plates',
            'Remove stale slices/previews and their relationships before native slicing'],
        editable_sha256=sha(EDIT), protected_before=before))
    assert protected() == before
    print('Built separate ten-plate knot project with exact production meshes.', flush=True)


def slice_all():
    NATIVE.mkdir(parents=True, exist_ok=True)
    for attempt in range(3):
        with (WORK / 'slice.log').open('w') as log:
            result = subprocess.run([str(EXE), '--slice', '0', '--export-3mf', 'sliced.3mf',
                '--outputdir', str(NATIVE), str(EDIT)], cwd=EXE.parent, stdout=log,
                stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
        if result.returncode != 3221225477:
            break
    result.check_returncode()
    data = json.loads((NATIVE / 'result.json').read_text())
    assert data['return_code'] == 0 and [p['id'] for p in data['sliced_plates']] == list(range(1, 11))
    print('All ten knot plates sliced natively.', flush=True)


def reopen():
    folder = WORK / 'reopen'
    folder.mkdir(exist_ok=True)
    for attempt in range(3):
        with (folder / 'cli.log').open('w') as log:
            result = subprocess.run([str(EXE), '--info', '--outputdir', str(folder), str(NATIVE / 'sliced.3mf')],
                cwd=EXE.parent, stdout=log, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
        if result.returncode != 3221225477:
            break
    result.check_returncode()
    assert json.loads((folder / 'result.json').read_text())['return_code'] == 0
    save_json(folder / 'input.json', dict(project_sha256=sha(NATIVE / 'sliced.3mf')))


def validate():
    from scipy.spatial import cKDTree
    from shapely.geometry import MultiPoint
    from validate_a2l_project import material_angles
    from validate_print_project import scan_gcode
    from validate_ribbon_bed_datum import segments
    from check_a2l_towers import check_startup_tower, check_tower
    provenance = json.loads((OUT / 'source-provenance.json').read_text())
    assert sha(SOURCE) == SOURCE_SHA and sha(EDIT) == provenance['editable_sha256']
    assert protected() == provenance['protected_before']
    with zipfile.ZipFile(SOURCE) as z:
        keys = set(provenance['child_mesh_assets_sha256']) | {'3D/3dmodel.model', 'Metadata/model_settings.config', 'Metadata/project_settings.config'}
        source = {n: z.read(n) for n in keys}
    edited, erows = embedded(EDIT)
    native, nrows = embedded(NATIVE / 'sliced.3mf')
    assert erows.keys() == nrows.keys() == {f'F{i} A2L knot' for i in range(1, 11)}
    settings = json.loads(native['Metadata/project_settings.config'])
    assert settings == json.loads(edited['Metadata/project_settings.config'])
    original_settings = json.loads(source['Metadata/project_settings.config'])
    expected = copy.deepcopy(original_settings)
    expected['is_infill_first'] = '1'
    expected['wipe_tower_x'] = expected['wipe_tower_x'][:10]
    expected['wipe_tower_y'] = expected['wipe_tower_y'][:10]
    assert settings == expected
    assert settings['nozzle_diameter'] == ['0.4'] and settings['printer_model'] == 'Bambu Lab A2L'
    scfg = ET.fromstring(source['Metadata/model_settings.config'])
    ecfg = ET.fromstring(edited['Metadata/model_settings.config'])
    ncfg = ET.fromstring(native['Metadata/model_settings.config'])
    sroot = ET.fromstring(source['3D/3dmodel.model'])
    eroot = ET.fromstring(edited['3D/3dmodel.model'])
    for name, h in provenance['child_mesh_assets_sha256'].items():
        assert source[name] == edited[name]
        assert hashlib.sha256(edited[name]).hexdigest() == h
    for co in ecfg.findall('object'):
        old = copy.deepcopy(scfg.find(f"object[@id='{co.get('id')}']"))
        setmeta(old, 'support_interface_spacing', '0.2')
        assert ET.tostring(old) == ET.tostring(co)
    # Verify grid repacking independently of the builder's stored offsets.
    for i, plate in enumerate(ecfg.findall('plate')):
        oid = props(plate.find('model_instance'))['object_id']
        st = transform(sroot.find(tag('build')).find(f"{tag('item')}[@objectid='{oid}']").get('transform'))
        et = transform(eroot.find(tag('build')).find(f"{tag('item')}[@objectid='{oid}']").get('transform'))
        st[:2, 3] -= [i % 5 * 396, -(i // 5) * 384]
        et[:2, 3] -= [i % 4 * 396, -(i // 4) * 384]
        assert np.allclose(st, et, atol=1e-8, rtol=0)
    for project_settings, rows in [(settings, erows), (settings, nrows)]:
        for row in rows.values():
            assert effective(row['settings'])['support_interface_spacing'] == '0.2'
            for p in row['parts']:
                e = {**project_settings, **effective(row['settings']), **effective(p['settings'])}
                for key, value in LOCKS.items():
                    if key == 'sparse_infill_density' and p['settings'].get(key) == '100%':
                        value = '100%'
                    assert e[key] == value, (key, e[key])
                assert e['is_infill_first'] == '1' and e['support_top_z_distance'] == '0.2'
    info = ET.fromstring(native['Metadata/slice_info.config'])
    result = json.loads((NATIVE / 'result.json').read_text())
    assert result['return_code'] == 0 and len(result['sliced_plates']) == 10
    plan = json.loads((PRODUCTION / 'production-plan.json').read_text())
    frame = json.loads((PRODUCTION / 'frame-geometry-validation.json').read_text())
    towerplan = json.loads((PRODUCTION / 'tower-placement.json').read_text())
    previous = json.loads((PRODUCTION / 'native-validation.json').read_text())
    records, pad_checks = [], []
    for number in range(1, 11):
        name = f'F{number} A2L knot'
        row, nr = erows[name], nrows[name]
        assert effective(row['settings']) == effective(nr['settings'])
        assert len(row['parts']) == len(nr['parts'])
        errors = []
        for a, b in zip(row['parts'], nr['parts']):
            assert a['subtype'] == b['subtype'] and effective(a['settings']) == effective(b['settings'])
            assert np.array_equal(a['mesh'].faces, b['mesh'].faces)
            av = a['mesh'].vertices @ row['transform'][:3, :3].T + row['transform'][:3, 3]
            bv = b['mesh'].vertices @ nr['transform'][:3, :3].T + nr['transform'][:3, 3]
            error = max(float(cKDTree(av).query(bv)[0].max()), float(cKDTree(bv).query(av)[0].max()))
            assert error < .001
            errors.append(error)
        raw = native[f'Metadata/plate_{number}.gcode']
        assert hashlib.md5(raw).hexdigest() == native[f'Metadata/plate_{number}.gcode.md5'].decode().strip().lower()
        text = raw.decode()
        gc = dict(re.findall(r'^; ([A-Za-z_0-9]+) = (.*)$', text, re.MULTILINE))
        for key, value in LOCKS.items():
            assert gc[key] == value
        assert gc['is_infill_first'] == '1' and gc['nozzle_diameter'] == '0.4'
        assert '; EXECUTABLE_BLOCK_END' in text
        scan = scan_gcode(text)
        low, high = np.array(scan['bead_xy_bounds_mm'])
        clearance = float(min(*low, *(np.array([330, 320]) - high)))
        assert clearance > .5
        heights = scan['model_extrusion_z_by_filament_mm']
        assert set(heights) == {'1', '2', '4'}
        with zipfile.ZipFile(SOURCE) as z:
            old_scan = scan_gcode(z.read(f'Metadata/plate_{number}.gcode').decode())
        old_heights = {k: max(v) for k, v in old_scan['model_extrusion_z_by_filament_mm'].items()}
        assert {k: max(v) for k, v in heights.items()} == old_heights
        height = max(old_heights.values())
        assert height <= 325
        hulls = [MultiPoint((p['mesh'].vertices @ nr['transform'][:3, :3].T + nr['transform'][:3, 3])[:, :2]).convex_hull
            for p in nr['parts'] if p['subtype'] == 'normal_part']
        startup = check_startup_tower(settings, hulls, len(heights), height, number)
        tower = check_tower(text, hulls, towerplan['plates'][number-1]['reserved_envelope_mm'])
        ids = {int(props(i)['identify_id']): name for i in ncfg.findall('plate')[number-1].findall('model_instance')}
        paths = segments(text, ids, single_object='; start printing object, unique label id:' not in text)[name]
        layer = [p for p in paths if abs(p[2][1][2]-2.6) < .001]
        features = [p[1] for p in layer]
        order = None
        if 'Bridge' in features and 'Overhang wall' in features:
            bi, wi = features.index('Bridge'), features.index('Overhang wall')
            order = dict(layer_z_mm=2.6, first_bridge_segment=bi, first_overhang_wall_segment=wi,
                bridge_before_first_overhang_wall=bi < wi)
            assert bi < wi, (number, bi, wi)
        if number == 2:
            assert order and order['bridge_before_first_overhang_wall']
        a = np.array([p[2] for p in paths])
        starts, deltas = a[:, 0, :2], a[:, 1, :2] - a[:, 0, :2]
        length2 = (deltas*deltas).sum(axis=1)
        for k, (joint, proof) in enumerate(zip(plan['frame_joints'], frame['joints'])):
            if joint[0] != number-1:
                continue
            for xy in proof['seating_pads_xy']:
                target = (np.array([*xy, 0]) @ nr['transform'][:3, :3].T + nr['transform'][:3, 3])[:2]
                t = np.clip(((target-starts)*deltas).sum(axis=1)/length2, 0, 1)
                near = np.linalg.norm(starts + t[:, None]*deltas - target, axis=1) < .65
                height = float(a[near, :, 2].max())
                assert abs(height-4.8) < .001
                pad_checks.append(dict(joint=k+1, plate=number, xy_assembly_mm=xy, maximum_model_z_mm=height))
        angles = material_angles(text, plan['frame_fits'][number-1]['rotation_deg'])
        prior_angles = previous['plates'][number-1]['material_surface_angles']
        assert {(a['filament_slot'], a['z_mm']) for a in angles} == {(a['filament_slot'], a['z_mm']) for a in prior_angles}
        for a in angles:
            b = next(b for b in prior_angles if b['filament_slot'] == a['filament_slot'] and b['z_mm'] == a['z_mm'])
            assert abs((a['dominant_assembly_angle_deg'] - b['dominant_assembly_angle_deg'] + 90) % 180 - 90) < 1
        pi = next(p for p in info.findall('plate') if props(p)['index'] == str(number))
        warnings = [w.attrib for w in pi.findall('warning')]
        assert all(w.get('msg') == 'not_support_traditional_timelapse' for w in warnings), warnings
        estimate = next(p for p in result['sliced_plates'] if p['id'] == number)
        scan.pop('model_extrusion_z_by_filament_mm')
        records.append(dict(plate=number, name=name, max_native_mesh_and_pose_error_mm=max(errors),
            gcode_sha256=hashlib.sha256(raw).hexdigest(), gcode_md5_verified=True,
            native_geometry_topology_and_all_effective_volume_settings_preserved=True,
            gcode_locked_constants_verified=True, scan=scan, bed_clearance_mm=clearance,
            unchanged_model_top_z_by_filament_mm=old_heights,
            startup_tower=startup, tower_clearance=tower, first_supported_layer_order=order,
            material_surface_angles=angles, warnings=warnings,
            seconds=estimate['total_predication'], grams=sum(f['total_used_g'] for f in estimate['filaments'])))
        print(f'Plate {number}: geometry, process, path order, tower, finish directions and lap checks passed.', flush=True)
    assert len(pad_checks) == 42
    assert protected() == provenance['protected_before']
    reopened = json.loads((WORK / 'reopen/result.json').read_text())
    assert reopened['return_code'] == 0
    assert json.loads((WORK / 'reopen/input.json').read_text())['project_sha256'] == sha(NATIVE / 'sliced.3mf')
    FINAL.write_bytes((NATIVE / 'sliced.3mf').read_bytes())
    report = dict(revision='r1', source_sha256=SOURCE_SHA, project_sha256=sha(FINAL), editable_sha256=sha(EDIT),
        printer='Bambu Lab A2L 0.4 nozzle', plates=records, removed_pad_toolpath_checks=pad_checks,
        global_settings_differences={'is_infill_first': ['0', '1'], 'wipe_tower_x': 'retained first ten values', 'wipe_tower_y': 'retained first ten values'},
        object_settings_difference={'support_interface_spacing': ['0.5 inherited', '0.2']},
        all_other_process_settings_and_modifiers_preserved=True, full_geometry_no_crop=True,
        protected_before=provenance['protected_before'], protected_after=protected(),
        total_seconds=sum(p['seconds'] for p in records), total_grams=sum(p['grams'] for p in records),
        native_reopen_result=reopened, native_slice_result=result,
        physical_reference=dict(file=(TEST / (TEST.name + '.3mf')).relative_to(ROOT).as_posix(), sha256=TEST_SHA,
            report='User reported r3 worked on 2026-10-22 and requested promotion, commit, push and PR.',
            scope='Supplied A2L test; locally printed file hash not independently read.'),
        user_approved_scope='Keep M settings unchanged; put the corrected knot in a separate project.',
        full_size_physical_confirmation_pending=True, fresh_GUI_review_performed=False, printer_job_sent=False)
    save_json(OUT / 'validation.json', report)
    for number in [2]:
        (OUT / f'saved-plate_{number}.png').write_bytes(native[f'Metadata/plate_{number}.png'])
    print(f'PASS: ten complete knot plates, {report["total_grams"]:.2f} g. Main/M/A1 unchanged.', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['build', 'slice', 'reopen', 'validate'])
    args = parser.parse_args()
    if args.action == 'slice':
        slice_all()
    else:
        globals()[args.action]()
