"""Apply the selected SUNLU Silk 2.0 copper finish without changing geometry.

Usage: python scripts/tune_silk_project.py stage
       python scripts/tune_silk_project.py slice 31 21 22 23 24 25 26
       python scripts/tune_silk_project.py merge
       python scripts/tune_silk_project.py verify
       python scripts/validate_print_project.py --project .work/copper-production-c/complete.3mf --baseline .work/copper-production-c/complete.json --report .work/copper-production-c/audit.json
       python scripts/tune_silk_project.py publish
The candidate is independently audited before publication.
"""
import argparse
import collections
import copy
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / '.work/copper-production-c'
PACKAGE = ROOT / 'working/bambu/Dara-Photo-Frame-A1-Jointed'
PLATES = [21, 22, 23, 24, 25, 26, 31]
OBJECT_SETTINGS = {
    'outer_wall_speed': '40', 'top_surface_speed': '30',
    'internal_solid_infill_speed': '50', 'top_shell_layers': '8',
    'top_shell_thickness': '1.6', 'top_surface_pattern': 'monotonicline',
    'top_solid_infill_flow_ratio': '1',
    'ironing_type': 'no ironing',
}
FILAMENT_SETTINGS = {
    'filament_flow_ratio': '0.96', 'filament_z_hop': '0.6',
    'filament_z_hop_types': 'Normal Lift', 'filament_wipe': '0',
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_zip(path):
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        return {n: z.read(n) for n in z.namelist()}


def write_zip(path, files):
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        for n, d in files.items():
            z.writestr(n, d)


def props(el):
    return {m.get('key'): m.get('value') for m in el.findall('metadata')}


def setmeta(el, key, value):
    item = next((m for m in el.findall('metadata') if m.get('key') == key), None)
    if item is None:
        item = ET.SubElement(el, 'metadata', key=key)
    item.set('value', str(value))


def xml(el):
    return ET.tostring(el, encoding='utf-8', xml_declaration=True)


def stage():
    WORK.mkdir(parents=True, exist_ok=True)
    baseline_path = WORK / 'baseline.3mf'
    assert not baseline_path.exists(), 'Preserve existing evidence; do not overwrite its baseline.'
    source = PACKAGE / 'Dara-Photo-Frame-A1-Complete.3mf'
    assert sha(source) == sha(ROOT / 'Dara.3mf')
    shutil.copy2(source, baseline_path)
    shutil.copy2(PACKAGE / 'project-validation.json', WORK / 'baseline.json')
    files = read_zip(source)
    settings = json.loads(files['Metadata/project_settings.config'])
    assert settings['wall_loops'] == '4'
    assert settings['top_one_wall_type'] == 'all top'
    assert settings['sparse_infill_density'] == '15%' and settings['sparse_infill_pattern'] == 'gyroid'
    old_settings = copy.deepcopy(settings)
    for key, value in FILAMENT_SETTINGS.items():
        assert len(settings[key]) == 4
        settings[key][2] = value
    files['Metadata/project_settings.config'] = json.dumps(settings, indent=2).encode()
    model = ET.fromstring(files['Metadata/model_settings.config'])
    changed = []
    for obj in model.findall('object'):
        name = props(obj)['name']
        if re.fullmatch(r'M[1-6]', name) or name == 'Test-M-Letter':
            before = props(obj)
            for key, value in OBJECT_SETTINGS.items():
                setmeta(obj, key, value)
            changed.append({'name': name, 'prior_overrides': before})
    assert len(changed) == 7
    for plate in model.findall('plate'):
        if int(props(plate)['plater_id']) in PLATES:
            for md in list(plate.findall('metadata')):
                if md.get('key', '').endswith('_file'):
                    plate.remove(md)
    files['Metadata/model_settings.config'] = xml(model)
    info = ET.fromstring(files['Metadata/slice_info.config'])
    for plate in list(info.findall('plate')):
        if int(props(plate)['index']) in PLATES:
            info.remove(plate)
    files['Metadata/slice_info.config'] = xml(info)
    for name in list(files):
        m = re.match(r'Metadata/(?:plate_|top_|pick_|plate_no_light_)(\d+)(?:[_.])', name)
        if m and int(m[1]) in PLATES:
            del files[name]
    write_zip(WORK / 'staged.3mf', files)
    baseline = json.loads((WORK / 'baseline.json').read_text())
    previous_selection = copy.deepcopy(baseline.get('silk_finish_trial', {}).get('selection'))
    comparison = ROOT / 'Dara-Copper-Diagnostic-Test.3mf'
    comparison_report = json.loads((PACKAGE / 'copper-diagnostic-test.json').read_text())
    assert comparison_report['project_sha256'] == sha(comparison)
    selected = next(s for s in comparison_report['samples'] if s['label'] == 'C')
    assert selected['speed'] == 30 and selected['flow'] == 1 and selected['density'] == '15%'
    baseline['silk_finish_trial'] = {
        'date': '2026-10-14', 'material': 'SUNLU Silk 2.0 PLA Copper Red',
        'product_url': 'https://www.amazon.com/dp/B0H8SC8RXP',
        'prior_project_sha256': sha(source), 'affected_plates': PLATES,
        'sample_plate': 31, 'physical_test_passed': False,
        'status': 'user_selected_for_production',
        'selection': {
            'date': '2026-10-14',
            'sample': 'C - Middle left - 30 mm/s - 100% top flow - 15% gyroid',
            'comparison_project_sha256': sha(comparison),
            'user_instruction': 'lets go with C. update the project.',
            'coupon_finish_accepted': True,
            'full_geometry_print_with_selected_settings_verified': False,
            'wall_layout': 'Original four walls; one perimeter on top surfaces. No upper-1-mm wall modifier.',
            'observations': 'The user selected coupon C from the five-coupon diagnostic plate. This supersedes the earlier 104% choice; no new full-geometry physical result was reported.',
        },
        'previous_selection': previous_selection,
        'object_settings': OBJECT_SETTINGS, 'filament_slot': 3,
        'filament_settings': FILAMENT_SETTINGS,
        'prior_filament_settings': {k: old_settings[k][2] for k in FILAMENT_SETTINGS},
        'objects': changed,
        'note': '100% applies to top solid infill only; filament flow remains 0.96. This is a user-selected finish, not a measured spool calibration. The diagnostic pause is not transferred to production. Wipe is disabled to remove the sideways pre-lift wipe; short unretracted moves and extrusion still occur at layer height.',
    }
    baseline['settings'].update({k: settings[k] for k in FILAMENT_SETTINGS})
    (WORK / 'staged.json').write_text(json.dumps(baseline, indent=2) + '\n')
    print('Staged seven copper objects; all model resources unchanged.', flush=True)


def slice_plates(plates):
    executable = Path('C:/Program Files/Bambu Studio/bambu-studio.exe')
    for plate in plates:
        assert plate in PLATES
        folder = WORK / f'plate-{plate}'
        folder.mkdir(exist_ok=True)
        assert not (folder / 'sliced.3mf').exists(), f'Existing slice: {folder}'
        command = [str(executable), '--slice', str(plate), '--export-3mf',
                   'sliced.3mf', '--outputdir', str(folder), str(WORK / 'staged.3mf')]
        print(f'Slicing plate {plate}', flush=True)
        with (folder / 'cli.log').open('w') as log:
            result = subprocess.run(command, cwd=executable.parent, stdout=log,
                                    stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
        assert result.returncode == 0, (plate, result.returncode)
        status = json.loads((folder / 'result.json').read_text())
        assert status['return_code'] == 0 and status['plate_index'] == plate, status
        assert (folder / 'sliced.3mf').exists()
        print(f'Plate {plate} sliced successfully', flush=True)


def merge():
    original = read_zip(WORK / 'baseline.3mf')
    files = read_zip(WORK / 'staged.3mf')
    model = ET.fromstring(files['Metadata/model_settings.config'])
    info = ET.fromstring(files['Metadata/slice_info.config'])
    original_model = ET.fromstring(original['Metadata/model_settings.config'])
    names = {o.get('id'): props(o)['name'] for o in model.findall('object')}
    for number in PLATES:
        sliced = read_zip(WORK / f'plate-{number}/sliced.3mf')
        sc = ET.fromstring(sliced['Metadata/model_settings.config'])
        si = ET.fromstring(sliced['Metadata/slice_info.config'])
        sp = next(p for p in sc.findall('plate') if int(props(p)['plater_id']) == number)
        p = next(p for p in model.findall('plate') if int(props(p)['plater_id']) == number)
        assert len(si.findall('plate')) == 1
        stat = si.find('plate')
        assert int(props(stat)['index']) == number
        assert {o.get('name') for o in stat.findall('object')} == {names[props(i)['object_id']] for i in p.findall('model_instance')}
        for md in sp.findall('metadata'):
            if md.get('key', '').endswith('_file'):
                setmeta(p, md.get('key'), md.get('value'))
                path = md.get('value')
                if path:
                    files[path] = sliced[path]
        for name, data in sliced.items():
            if re.match(rf'Metadata/plate_{number}(?:\.|_)', name):
                files[name] = data
        # CLI keeps instance IDs but omits the printer ID in slice metadata.
        old_info = ET.fromstring(original['Metadata/slice_info.config'])
        old_stat = next(p for p in old_info.findall('plate') if int(props(p)['index']) == number)
        old_ids = {o.get('name'): o.get('identify_id') for o in old_stat.findall('object')}
        for obj in stat.findall('object'):
            assert obj.get('identify_id') == old_ids[obj.get('name')]
        setmeta(stat, 'printer_model_id', props(old_stat)['printer_model_id'])
        info.append(stat)
    info[:] = sorted(info.findall('plate'), key=lambda p: int(props(p)['index']))
    files['Metadata/model_settings.config'] = xml(model)
    files['Metadata/slice_info.config'] = xml(info)
    assert len(model.findall('plate')) == len(info.findall('plate')) == 31
    for name, data in original.items():
        if name.startswith('3D/'):
            assert files[name] == data, name
    assert files.get('Metadata/custom_gcode_per_layer.xml') == original.get('Metadata/custom_gcode_per_layer.xml')
    for n in range(1, 32):
        if n not in PLATES:
            assert files[f'Metadata/plate_{n}.gcode'] == original[f'Metadata/plate_{n}.gcode']
    for old_obj, obj in zip(original_model.findall('object'), model.findall('object')):
        assert old_obj.get('id') == obj.get('id')
        assert [xml(p) for p in old_obj.findall('part')] == [xml(p) for p in obj.findall('part')]
        if props(obj)['name'] not in {f'M{i}' for i in range(1, 7)} | {'Test-M-Letter'}:
            assert xml(old_obj) == xml(obj)
    output = WORK / 'complete.3mf'
    write_zip(output, files)
    baseline = json.loads((WORK / 'staged.json').read_text())
    baseline['project_sha256'] = sha(output)
    baseline['silk_finish_trial'].update(geometry_byte_identical=True, unaffected_plate_gcodes_byte_identical=True)
    for key in ('bambu_studio_slice', 'bambu_studio_round_trip', 'bambu_studio_slice_warnings'):
        baseline.pop(key, None)
    (WORK / 'complete.json').write_text(json.dumps(baseline, indent=2) + '\n')
    print(output, flush=True)


def verify_paths():
    candidate = WORK / 'complete.3mf'
    checks = []
    with zipfile.ZipFile(candidate) as z, zipfile.ZipFile(WORK / 'baseline.3mf') as old:
        old_config = ET.fromstring(old.read('Metadata/model_settings.config'))
        old_settings = json.loads(old.read('Metadata/project_settings.config'))
        old_objects = {o.get('id'): props(o) for o in old_config.findall('object')}
        for plate in PLATES:
            old_plate = next(p for p in old_config.findall('plate') if int(props(p)['plater_id']) == plate)
            instance = old_plate.findall('model_instance')
            assert len(instance) == 1
            prior_object = old_objects[props(instance[0])['object_id']]
            prior_top_value = prior_object.get('top_solid_infill_flow_ratio', old_settings.get('top_solid_infill_flow_ratio', '1'))
            if isinstance(prior_top_value, list):
                assert len(prior_top_value) in (1, 4)
                prior_top_value = prior_top_value[0 if len(prior_top_value) == 1 else int(prior_object['extruder']) - 1]
            prior_top_flow = float(prior_top_value)
            data = z.read(f'Metadata/plate_{plate}.gcode')
            lines = data.decode().splitlines()
            prior_lines = old.read(f'Metadata/plate_{plate}.gcode').decode().splitlines()
            assert lines.count('M400 U1') == prior_lines.count('M400 U1'), 'Production pause count changed'
            feature, feed, layer, position_z = '', 0, None, 0
            speeds = collections.defaultdict(set)
            hops, solid_z = collections.Counter(), set()
            for line in lines:
                if line.startswith('; FEATURE:'):
                    feature = line.split(':', 1)[1].strip()
                if line.startswith('; Z_HEIGHT:'):
                    layer = float(line.split(':', 1)[1])
                if not line.startswith('G1 '):
                    continue
                values = {k: float(n) for k, n in re.findall(r'([XYZEF])([+-]?(?:\d+(?:\.\d*)?|\.\d+))', line.split(';')[0])}
                if 'F' in values:
                    feed = values['F'] / 60
                if 'Z' in values:
                    if layer is not None and values['Z'] > position_z and abs(values['Z'] - layer - .6) < .001 and not any(k in values for k in 'XY'):
                        hops[round(values['Z'] - layer, 3)] += 1
                    position_z = values['Z']
                if values.get('E', 0) > 0 and any(k in values for k in 'XY'):
                    if feature in ('Top surface', 'Internal solid infill'):
                        speeds[feature].add(round(feed, 3))
                    if feature == 'Internal solid infill' and layer is not None and layer >= 9:
                        solid_z.add(layer)
            assert speeds['Top surface'] == {30}, (plate, speeds['Top surface'])
            assert max(speeds['Internal solid infill']) <= 50.001
            assert sum(hops.values()) > 0 and '; WIPE_START' not in lines
            current_extrusion = feature_extrusion(lines)
            prior_extrusion = feature_extrusion(prior_lines)
            assert 'Ironing' not in current_extrusion
            assert current_extrusion.keys() == prior_extrusion.keys()
            feature_ratios = {}
            move_count_changes = {}
            for feature, current in current_extrusion.items():
                prior = prior_extrusion[feature]
                # Bambu may split/merge support strokes differently on a re-slice.
                # Keep model stroke counts exact and compare support extrusion too.
                if current['moves'] != prior['moves']:
                    assert feature == 'Support', (plate, feature, current, prior)
                    move_count_changes[feature] = {'prior': prior['moves'], 'current': current['moves']}
                ratio = current['extrusion_mm'] / prior['extrusion_mm']
                expected = float(OBJECT_SETTINGS['top_solid_infill_flow_ratio']) / prior_top_flow if feature == 'Top surface' else 1.0
                assert abs(ratio - expected) < 0.0001, (plate, feature, ratio)
                feature_ratios[feature] = round(ratio, 6)
            for key, value in FILAMENT_SETTINGS.items():
                saved = next(l.split(' = ', 1)[1] for l in lines if l.startswith('; ' + key + ' = '))
                assert saved.split(',')[2] == value, (plate, key, saved)
            checks.append(dict(plate=plate, top_speed_mm_s=sorted(speeds['Top surface']),
                solid_speed_mm_s=sorted(speeds['Internal solid infill']), vertical_hop_counts=dict(hops),
                extrusion_ratio_vs_prior_by_feature=feature_ratios, ironing_moves=0,
                feature_move_count_changes=move_count_changes,
                pause_count_unchanged=True,
                sideways_wipes=0, solid_layer_heights_near_top=sorted(solid_z), gcode_sha256=hashlib.sha256(data).hexdigest()))
    report = dict(passed=True, checks=checks, physical_test_passed=False, project_sha256=sha(candidate))
    (WORK / 'toolpath-verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Seven copper toolpaths verified: 100% top extrusion, unchanged other-feature extrusion, speeds, vertical hops, no ironing or pre-lift wipes.')


def feature_extrusion(lines):
    """Measure deposited filament by feature, excluding travel and priming."""
    feature = 'Custom'
    relative_e = False
    totals = {}
    for line in lines:
        if line.startswith('; FEATURE:'):
            feature = line.split(':', 1)[1].strip()
        code = line.split(';', 1)[0].strip()
        command = code.split(' ', 1)[0]
        if command == 'M83':
            relative_e = True
        elif command == 'M82':
            relative_e = False
        elif command in ('G1', 'G2', 'G3') and feature != 'Custom':
            values = {k: float(n) for k, n in re.findall(r'([XYZEFIJ])([+-]?(?:\d+(?:\.\d*)?|\.\d+))', code)}
            if values.get('E', 0) > 0 and any(k in values for k in 'XYIJ'):
                assert relative_e, 'This comparison requires relative extrusion.'
                record = totals.setdefault(feature, {'moves': 0, 'extrusion_mm': 0.0})
                record['moves'] += 1
                record['extrusion_mm'] += values['E']
    assert totals.get('Top surface', {}).get('extrusion_mm', 0) > 0
    return totals


def publish():
    candidate = WORK / 'complete.3mf'
    baseline = json.loads((WORK / 'complete.json').read_text())
    audit = json.loads((WORK / 'audit.json').read_text())
    paths = json.loads((WORK / 'toolpath-verification.json').read_text())
    summary = audit['summary']
    assert summary['digital_checks_passed'] and summary['plates'] == 31
    assert paths['passed'] and [p['plate'] for p in paths['checks']] == PLATES
    assert audit['project_sha256'] == baseline['project_sha256'] == paths['project_sha256'] == sha(candidate)
    with zipfile.ZipFile(candidate) as z:
        for check in paths['checks']:
            assert hashlib.sha256(z.read(f"Metadata/plate_{check['plate']}.gcode")).hexdigest() == check['gcode_sha256']
    target = PACKAGE / 'Dara-Photo-Frame-A1-Complete.3mf'
    assert sha(target) == baseline['silk_finish_trial']['prior_project_sha256']
    production = audit['plates'][:29]
    baseline['bambu_studio_slice'] = dict(
        all_plates_sliced=True, plate_count=31, all_extrusions_within_bed=True,
        **{k: summary[k] for k in ('total_weight_g', 'total_estimated_seconds',
                                  'minimum_edge_clearance_mm', 'extrusion_moves_checked', 'filament_weights_g')},
        production_weight_g=round(sum(p['weight_g'] for p in production), 2),
        production_estimated_seconds=sum(p['estimated_seconds'] for p in production),
        production_filament_weights_g=[round(sum(p['filament_weights_g'][i] if i < len(p['filament_weights_g']) else 0
                                                for p in production), 2) for i in range(4)],
        validation_note='Copper plates 21-26 and 31 re-sliced with coupon C settings: 100% top-fill multiplier, 30 mm/s top speed, original wall layout and no ironing; other toolpaths and all geometry unchanged. All 31 plates audited.',
        plates=audit['plates'])
    baseline['bambu_studio_round_trip'] = dict(normal_meshes_match_source=True, settings_verified=True,
        solid_modifiers_verified=audit['solid_modifiers_verified'], color_modifiers_verified=audit['color_modifiers_verified'],
        comparisons=audit['normal_mesh_comparisons'])
    baseline['bambu_studio_slice_warnings'] = [{'plate': p['plate'], **n} for p in audit['plates'] for n in p.get('slicer_notices', [])]
    baseline['silk_finish_trial']['toolpath_verification'] = paths
    baseline['ams_color_workflow']['audit'] = 'Passed; matching project SHA256 and all 31 plates in final-review.json.'
    baseline['test_plate']['sliced'] = True
    shutil.copy2(candidate, target)
    shutil.copy2(candidate, ROOT / 'Dara.3mf')
    (PACKAGE / 'project-validation.json').write_text(json.dumps(baseline, indent=2) + '\n')
    (PACKAGE / 'final-review.json').write_text(json.dumps(audit, indent=2) + '\n')
    checks = ROOT / 'working/stl/Dara-Print-Checks'
    for number in (30, 31):
        record = dict(plate=number, pieces=1, source_cad_sha256=audit['source_sha256'], project_sha256=sha(candidate),
                      parts=[p for p in baseline['test_plate']['parts'] if p['plate'] == number],
                      plate_layout=baseline['plate_layout'][number-1], sliced=True, audit=audit['plates'][number-1])
        (checks / f'plate-{number}-manifest.json').write_text(json.dumps(record, indent=2) + '\n')
    with zipfile.ZipFile(candidate) as z:
        (PACKAGE / 'copper-test-plate.png').write_bytes(z.read('Metadata/plate_31.png'))
    (PACKAGE / 'copper-finish-settings.json').write_text(json.dumps({
        'project_sha256': sha(candidate), **baseline['silk_finish_trial']}, indent=2) + '\n')
    print(json.dumps({'project': str(target), 'test': audit['plates'][30], 'summary': summary}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['stage', 'slice', 'merge', 'verify', 'publish'])
    parser.add_argument('plates', type=int, nargs='*')
    args = parser.parse_args()
    if args.action == 'stage':
        stage()
    elif args.action == 'slice':
        slice_plates(args.plates or PLATES)
    elif args.action == 'merge':
        merge()
    elif args.action == 'verify':
        verify_paths()
    else:
        publish()
