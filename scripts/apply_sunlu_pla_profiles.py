"""Apply the October 23 user-authorized SUNLU identities without reslicing.

Compare every saved preset option, retain the explicitly approved project
overrides, and prove that all bytes outside identity metadata are preserved.
This revision-specific migration uses local backups and fails on stale input.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / '.work/sunlu-pla-r1'
REPORT = ROOT / 'release/sunlu-pla-r1'
USER = Path(os.environ['APPDATA']) / 'BambuStudio/user/2065895616/filament/base'
IDENTITY = {'filament_settings_id', 'filament_vendor', 'filament_ids'}
META = {'name', 'from', 'version', 'inherits', 'filament_id',
        'filament_settings_id', 'filament_vendor', 'compatible_printers',
        'compatible_printers_condition', 'compatible_prints',
        'compatible_prints_condition', 'default_filament_colour', 'filament_notes'}
DRYER = {'filament_dev_ams_drying_ams_limitations': 2,
         'filament_dev_ams_drying_temperature': 4,
         'filament_dev_ams_drying_time': 4}
COMMENT = rb'(?m)^; filament_(?:settings_id|vendor|ids) = [^\r\n]*'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    return sha(path.read_bytes())


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def read(path):
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        return {n: z.read(n) for n in z.namelist()}


def config(data):
    block = data.split(b'; CONFIG_BLOCK_START', 1)[1].split(b'; CONFIG_BLOCK_END', 1)[0]
    return dict(re.findall(rb'^; ([^\r\n=]+) = ([^\r\n]*)', block, re.M))


def props(node):
    return {m.get('key'): m.get('value') for m in node.findall('metadata')}


def compare(s, preset, slot):
    differences = {}
    compared = []
    for key, expected in preset.items():
        if key in META:
            continue
        assert key in s, ('Missing project option', key)
        actual = s[key]
        if key in DRYER:
            width = DRYER[key]
            # Bambu saves either one shared dryer tuple or one tuple per slot.
            count = len(s['filament_settings_id'])
            if len(actual) == 1 + width * (count - 1):
                # The older transparent-PLA preset contributes one scalar;
                # the following three profiles each contribute a full tuple.
                assert s['filament_settings_id'][0].startswith('SUNLU Transparent PLA') and slot > 0
                start = 1 + (slot - 1) * width
                actual = actual[start:start+width]
            else:
                assert len(actual) in (width, width * count)
                actual = actual if len(actual) == width else actual[slot*width:(slot+1)*width]
        elif isinstance(expected, list):
            assert len(expected) == 1
            assert isinstance(actual, list) and len(actual) in (1, len(s['filament_settings_id']))
            actual = [actual[min(slot, len(actual)-1)]]
        compared.append(key)
        if actual != expected:
            differences[key] = {'project': actual, 'preset': expected}
    return differences, compared


def expected_overrides(title, slot):
    result = {}
    if title == 'Knot':
        result.update({key: {'project': ['65'], 'preset': ['55']}
                       for key in ('textured_plate_temp', 'textured_plate_temp_initial_layer')})
    if slot == 3 and title in ('Knot', 'Small Parts'):
        result['filament_max_volumetric_speed'] = {'project': ['7.5'], 'preset': ['12']}
    return result


def locks(title):
    stencil = 'Stencils' in title
    return dict(sparse_infill_density='0%' if stencil else '8%', sparse_infill_pattern='gyroid',
                nozzle_diameter=['0.4'], layer_height='0.2', initial_layer_print_height='0.2',
                wall_loops='2' if stencil else '4', top_shell_layers='4' if stencil else '5',
                bottom_shell_layers='4' if stencil else '5', curr_bed_type='Textured PEI Plate')


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    catalog_path = ROOT / 'release/root-projects/catalog.json'
    catalog = json.loads(catalog_path.read_text())
    sources_path = WORK / 'sources.json'
    if not sources_path.exists():
        dump(sources_path, catalog)
    source_catalog = json.loads(sources_path.read_text())
    protected_paths = list(ROOT.glob('*.scad')) + list(ROOT.glob('* STL/*.stl'))
    protected_paths += [ROOT / 'Small Parts - Crate Clips PETG.3mf',
                        ROOT / 'release/samples/Dara-A2L-Hammered-Finish-ERYONE-r4.3mf']
    protected = {p.relative_to(ROOT).as_posix(): file_sha(p) for p in protected_paths}
    presets = {}
    for p in sorted(USER.glob('SUNLU PLA*.json')):
        raw = p.read_bytes()
        data = json.loads(raw)
        assert data['inherits'] == ''
        assert data['filament_vendor'] == ['SUNLU']
        (REPORT / 'presets').mkdir(parents=True, exist_ok=True)
        (REPORT / 'presets' / p.name).write_bytes(raw)
        presets[data['name']] = dict(path=str(p), sha256=sha(raw), settings=data)
    assert len(presets) == 4
    reports = {}
    candidates = {}
    for title, row in source_catalog.items():
        source = ROOT / row['project']
        assert file_sha(source) == row['sha256'], ('Source changed', title)
        old = read(source)
        s = json.loads(old['Metadata/project_settings.config'])
        slots = [i for i, name in enumerate(s['filament_settings_id']) if name.startswith('Generic PLA @')]
        if not slots:
            continue
        before = WORK / 'before' / source.name
        before.parent.mkdir(exist_ok=True)
        if not before.exists():
            shutil.copyfile(source, before)
        assert file_sha(before) == row['sha256']
        updated = copy.deepcopy(s)
        assignments = []
        for slot in slots:
            kind = 'Metallic' if slot == 3 else 'Basic'
            name = f'SUNLU PLA {kind} @{s["printer_settings_id"]}'
            p = presets[name]['settings']
            assert p['compatible_printers'] == [s['printer_settings_id']]
            differences, compared = compare(s, p, slot)
            assert differences == expected_overrides(title, slot), (title, slot, differences)
            updated['filament_settings_id'][slot] = name
            updated['filament_ids'][slot] = p['filament_id']
            updated['filament_vendor'][slot] = p['filament_vendor'][0]
            assignments.append(dict(slot=slot+1, before=s['filament_settings_id'][slot],
                                    after=name, profile_sha256=presets[name]['sha256'],
                                    compared_options=compared, preserved_project_overrides=differences))
        assert {k for k in s if s[k] != updated[k]} == IDENTITY
        for key, value in locks(title).items():
            assert s[key] == updated[key] == value, (title, key)
        if title in ('Knot', 'Letter'):
            assert s['is_infill_first'] == ('1' if title == 'Knot' else '0')
        files = dict(old)
        files['Metadata/project_settings.config'] = (json.dumps(updated, indent=2) + '\n').encode()
        # Update AMS material identity in slice metadata without reserializing XML.
        def filament_identity(match):
            tag = match[0]
            slot = int(re.search(rb'\bid="(\d+)"', tag)[1]) - 1
            if slot in slots:
                assert re.search(rb'tray_info_idx="([^"]*)"', tag)[1].decode() == s['filament_ids'][slot]
                tag = re.sub(rb'tray_info_idx="[^"]*"',
                             ('tray_info_idx="' + updated['filament_ids'][slot] + '"').encode(), tag)
            return tag
        files['Metadata/slice_info.config'] = re.sub(rb'<filament\s[^>]*>', filament_identity,
                                                   old['Metadata/slice_info.config'])
        # Every slice XML attribute other than the selected filament IDs must match.
        a, b = [ET.fromstring(v['Metadata/slice_info.config']) for v in (old, files)]
        for tree in (a, b):
            for f in tree.iter('filament'):
                if int(f.get('id'))-1 in slots:
                    f.set('tray_info_idx', 'IDENTITY')
        assert ET.tostring(a) == ET.tostring(b)
        plates = []
        for name in sorted(n for n in old if n.endswith('.gcode')):
            raw = old[name]
            cfg = config(raw)
            for key, value in locks(title).items():
                expected = value[0] if isinstance(value, list) else value
                assert cfg[key.encode()].decode() == expected, (title, name, key)
            for key in sorted(IDENTITY):
                values = updated[key]
                serialized = ';'.join('"' + v + '"' for v in values) if key == 'filament_settings_id' else ';'.join(values)
                replacement = ('; ' + key + ' = ' + serialized).encode()
                raw, count = re.subn(rb'(?m)^; ' + key.encode() + rb' = [^\r\n]*', lambda _: replacement, raw)
                assert count == 1
            assert re.sub(COMMENT, b'', old[name]) == re.sub(COMMENT, b'', raw)
            after_cfg = config(raw)
            assert {k.decode() for k in cfg if cfg[k] != after_cfg[k]} == IDENTITY
            assert hashlib.md5(old[name]).hexdigest().upper() == old[name+'.md5'].decode().strip().upper()
            files[name] = raw
            files[name+'.md5'] = old[name+'.md5'].replace(old[name+'.md5'].strip(), hashlib.md5(raw).hexdigest().upper().encode())
            plates.append(dict(plate=int(re.search(r'plate_(\d+)', name)[1]),
                               source_gcode_sha256=sha(old[name]), gcode_sha256=sha(raw),
                               nonidentity_content_sha256=sha(re.sub(COMMENT, b'', raw)),
                               native_commands_byte_preserved=True, checksum_verified=True))
        assert len(plates) == row['plates']
        changed = sorted(n for n in files if files[n] != old[n])
        allowed = {'Metadata/project_settings.config', 'Metadata/slice_info.config'}
        allowed |= {n for n in files if n.endswith(('.gcode', '.gcode.md5'))}
        assert set(changed) <= allowed
        assert all(files[n] == old[n] for n in old if n not in allowed)
        final = WORK / 'candidates' / source.name
        final.parent.mkdir(exist_ok=True)
        with zipfile.ZipFile(before) as z, zipfile.ZipFile(final, 'w') as out:
            for info in z.infolist():
                out.writestr(info, files[info.filename])
        assert read(final) == files
        reopen = WORK / 'reopen' / title
        reopen.mkdir(parents=True, exist_ok=True)
        exe = Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe')
        with (reopen/'run.log').open('w') as log:
            native = subprocess.run([str(exe), '--info', '--outputdir', str(reopen), str(final)],
                                    cwd=exe.parent, stdout=log, stderr=subprocess.STDOUT,
                                    creationflags=subprocess.CREATE_NO_WINDOW)
        native.check_returncode()
        native_result = json.loads((reopen/'result.json').read_text())
        assert native_result['return_code'] == 0
        estimates = [dict(plate=int(props(p)['index']), seconds=int(props(p)['prediction']),
                          material_g=float(props(p)['weight']))
                     for p in ET.fromstring(files['Metadata/slice_info.config']).findall('plate')]
        reports[title] = dict(project=source.name, source_project_sha256=row['sha256'],
            project_sha256=file_sha(final), assignments=assignments,
            project_setting_changes={k: {'before': s[k], 'after': updated[k]} for k in sorted(IDENTITY)},
            preserved_locks=locks(title), changed_archive_entries=changed,
            preserved_archive_entries_sha256={n: sha(v) for n,v in files.items() if n not in changed},
            geometry_poses_support_paint_object_volume_settings_byte_preserved=True,
            all_print_parameters_preserved=True, plates=plates, estimates=estimates,
            retained_dryer_arrays={k: s[k] for k in DRYER},
            native_reopen=native_result, resliced=False)
        candidates[title] = final
        print(f'{title}: compared presets, retained overrides, preserved {len(plates)} native command streams, reopened successfully.', flush=True)
    # Publish only after every candidate passed and every input still matches.
    for title, row in source_catalog.items():
        assert file_sha(ROOT/row['project']) == row['sha256']
    assert protected == {n: file_sha(ROOT/n) for n in protected}
    for name, p in presets.items():
        assert file_sha(Path(p['path'])) == p['sha256'], ('Preset changed', name)
    for title, final in candidates.items():
        shutil.copyfile(final, ROOT / source_catalog[title]['project'])
    assert protected == {n: file_sha(ROOT/n) for n in protected}
    evidence = dict(date='2026-10-23', authorization='User requested SUNLU identities and explicitly approved retaining existing project overrides.',
                    scope='Six current root PLA production projects; historical samples and PETG unchanged.',
                    presets=presets, projects=reports, protected_files_sha256=protected,
                    protected_files_unchanged=True, physical_qualification_unchanged=True,
                    printer_job_sent=False)
    dump(REPORT / 'validation.json', evidence)
    hashes_path = ROOT / 'release/root-projects/gcode-sha256.json'
    hashes = json.loads(hashes_path.read_text())
    for title, r in reports.items():
        catalog[title].update(sha256=r['project_sha256'], filament_validation='release/sunlu-pla-r1/validation.json',
                              filament_settings_id=r['project_setting_changes']['filament_settings_id']['after'])
        hashes[title] = {f'plate_{p["plate"]}': p['gcode_sha256'] for p in sorted(r['plates'], key=lambda v: v['plate'])}
    dump(catalog_path, catalog)
    dump(hashes_path, hashes)
    print(f'Updated {len(reports)} projects; no printing parameters changed.', flush=True)


def verify_native_roundtrips():
    """Confirm native loading/saving retains all settings, using scratch copies."""
    report_path = REPORT / 'validation.json'
    evidence = json.loads(report_path.read_text())
    exe = Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe')
    for title, r in evidence['projects'].items():
        source = ROOT / r['project']
        assert file_sha(source) == r['project_sha256']
        out = WORK / 'native-roundtrip' / title
        out.mkdir(parents=True, exist_ok=True)
        with (out/'run.log').open('w') as log:
            result = subprocess.run([str(exe), '--export-3mf', 'reopened.3mf',
                                     '--outputdir', str(out), str(source)],
                                    cwd=exe.parent, stdout=log, stderr=subprocess.STDOUT,
                                    creationflags=subprocess.CREATE_NO_WINDOW)
        result.check_returncode()
        native = json.loads((out/'result.json').read_text())
        assert native['return_code'] == 0
        with zipfile.ZipFile(source) as z:
            before = json.loads(z.read('Metadata/project_settings.config'))
        with zipfile.ZipFile(out/'reopened.3mf') as z:
            after = json.loads(z.read('Metadata/project_settings.config'))
        difference = {k: {'before': before.get(k), 'after': after.get(k)}
                      for k in before.keys() | after.keys() if before.get(k) != after.get(k)}
        assert not difference, (title, difference)
        assert file_sha(source) == r['project_sha256']
        r['native_load_save_all_project_settings_equal'] = True
        r['native_load_save_checked_setting_count'] = len(before)
        print(f'{title}: all {len(before)} project settings preserved through native load/save.', flush=True)
    dump(report_path, evidence)


if __name__ == '__main__':
    if sys.argv[1:] == ['--verify-native-roundtrips']:
        verify_native_roundtrips()
    else:
        assert not sys.argv[1:]
        main()
