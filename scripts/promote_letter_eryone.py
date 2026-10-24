"""Promote the successful ERYONE sample's identity, preserving print commands.

Revision-specific migration. The sample and Letter already have identical
printing parameters. Only slot 3's name/vendor and their G-code comments change;
no reslice or printer job is required. Validate and reopen before publication.
"""
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
WORK = ROOT / '.work/letter-eryone-r1'
REPORT = ROOT / 'release/letter-eryone-r1'
SAMPLE = Path(r'C:\Users\Zach\Desktop\Dara-A2L-Hammered-Finish-ERYONE-r3.3mf')
TRACKED_SAMPLE = ROOT / 'release/samples/Dara-A2L-Hammered-Finish-ERYONE-r4.3mf'
BEFORE_SHA = 'd12cfb8b76a3aac2bdc667a0385896fc4ce2e770557d226551de5bd45b09a8f5'
SAMPLE_SHA = 'b82b2356c92c14640b4107405c0fde04488d61ced29d34821572c8b84003f0f6'
IDENTITY = {'filament_settings_id', 'filament_vendor'}
DRYER = {'filament_dev_ams_drying_ams_limitations',
         'filament_dev_ams_drying_temperature', 'filament_dev_ams_drying_time'}
LOCKS = dict(sparse_infill_density='8%', sparse_infill_pattern='gyroid',
             nozzle_diameter=['0.4'], layer_height='0.2',
             initial_layer_print_height='0.2', wall_loops='4',
             top_shell_layers='5', bottom_shell_layers='5',
             curr_bed_type='Textured PEI Plate', is_infill_first='0')


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


def main():
    assert file_sha(ROOT / 'Letter.3mf') == BEFORE_SHA
    assert file_sha(SAMPLE) == file_sha(TRACKED_SAMPLE) == SAMPLE_SHA
    WORK.mkdir(parents=True, exist_ok=True)
    baseline = WORK / 'Letter-before.3mf'
    if not baseline.exists():
        shutil.copyfile(ROOT / 'Letter.3mf', baseline)
    assert file_sha(baseline) == BEFORE_SHA
    protected_paths = [p for p in ROOT.glob('*.3mf') if p.name != 'Letter.3mf']
    protected_paths += list(ROOT.glob('*.scad')) + list(ROOT.glob('* STL/*.stl'))
    protected_paths += [TRACKED_SAMPLE]
    protected = {p.relative_to(ROOT).as_posix(): file_sha(p) for p in protected_paths}
    old, sample = read(baseline), read(SAMPLE)
    a = json.loads(old['Metadata/project_settings.config'])
    b = json.loads(sample['Metadata/project_settings.config'])
    differences = {k: dict(letter=a.get(k), sample=b.get(k))
                   for k in sorted(a.keys() | b.keys()) if a.get(k) != b.get(k)}
    assert set(differences) == IDENTITY | DRYER | {'print_settings_id', 'wipe_tower_x', 'wipe_tower_y'}
    updated = copy.deepcopy(a)
    for key in IDENTITY:
        assert len(a[key]) == len(b[key]) == 4
        assert all(a[key][i] == b[key][i] for i in (0, 1, 3))
        updated[key][2] = b[key][2]
    for key, value in LOCKS.items():
        assert a[key] == b[key] == updated[key] == value
    assert a['printer_model'] == b['printer_model'] == 'Bambu Lab A2L'
    model = ET.fromstring(old['Metadata/model_settings.config'])
    sample_obj = ET.fromstring(sample['Metadata/model_settings.config']).find('object')
    sample_overrides = {k: v for k, v in props(sample_obj).items() if k != 'name'}
    objects = []
    for obj in model.findall('object'):
        settings = props(obj)
        assert settings['extruder'] == '3'
        if settings['name'].startswith('V'):
            assert {k: v for k, v in settings.items() if k != 'name'} == sample_overrides
            assert settings['sparse_infill_density'] == '100%'
            assert settings['enable_support'] == '1' and a['support_type'] == 'tree(auto)'
        objects.append(settings['name'])
    assert len(objects) == 8
    files = dict(old)
    files['Metadata/project_settings.config'] = (json.dumps(updated, indent=2) + '\n').encode()
    sample_config = config(sample['Metadata/plate_1.gcode'])
    plates = []
    for i in range(1, 7):
        name = f'Metadata/plate_{i}.gcode'
        raw = old[name]
        before_config = config(raw)
        for key, value in LOCKS.items():
            expected = value[0] if isinstance(value, list) else value
            assert before_config[key.encode()] == expected.encode()
        for key in sorted(IDENTITY):
            pattern = rb'(?m)^; ' + key.encode() + rb' = [^\r\n]*'
            replacement = b'; ' + key.encode() + b' = ' + sample_config[key.encode()]
            raw, count = re.subn(pattern, lambda _: replacement, raw)
            assert count == 1
        after_config = config(raw)
        assert {k for k in before_config if before_config[k] != after_config[k]} == {k.encode() for k in IDENTITY}
        for key in IDENTITY:
            assert after_config[key.encode()] == sample_config[key.encode()]
        # Stronger than comparing moves: every byte outside the two identity
        # comment lines is identical, including all native slicer toolpaths.
        stripped = lambda data: re.sub(rb'(?m)^; filament_(?:settings_id|vendor) = [^\r\n]*', b'', data)
        assert stripped(raw) == stripped(old[name])
        files[name] = raw
        md5 = hashlib.md5(raw).hexdigest().upper().encode()
        prior_md5 = old[name + '.md5']
        assert hashlib.md5(old[name]).hexdigest().upper() == prior_md5.decode().strip().upper()
        files[name + '.md5'] = prior_md5.replace(prior_md5.strip(), md5)
        plates.append(dict(plate=i, before_gcode_sha256=sha(old[name]),
                           gcode_sha256=sha(raw), md5_verified=True,
                           identity_comments_only=True, printer_commands_byte_preserved=True,
                           content_excluding_identity_comments_sha256=sha(stripped(raw))))
    changed = sorted(n for n in files if files[n] != old[n])
    assert len(changed) == 13
    assert files['Metadata/model_settings.config'] == old['Metadata/model_settings.config']
    assert all(files[n] == old[n] for n in old if n.startswith('3D/'))
    final = WORK / 'Letter-final.3mf'
    with zipfile.ZipFile(baseline) as source, zipfile.ZipFile(final, 'w') as z:
        for info in source.infolist():
            z.writestr(info, files[info.filename])
    assert read(final) == files
    reopen = WORK / 'reopen'
    reopen.mkdir(exist_ok=True)
    exe = Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe')
    with (reopen / 'run.log').open('w') as log:
        result = subprocess.run([str(exe), '--info', '--outputdir', str(reopen), str(final)],
                                cwd=exe.parent, stdout=log, stderr=subprocess.STDOUT,
                                creationflags=subprocess.CREATE_NO_WINDOW)
    result.check_returncode()
    native = json.loads((reopen / 'result.json').read_text())
    assert native['return_code'] == 0
    info = ET.fromstring(files['Metadata/slice_info.config'])
    estimates = [dict(plate=int(props(p)['index']), seconds=int(props(p)['prediction']),
                      material_g=float(props(p)['weight'])) for p in info.findall('plate')]
    veneer_g = sum(p['material_g'] for p in estimates if p['plate'] >= 4)
    assert veneer_g < 1000
    assert file_sha(ROOT / 'Letter.3mf') == BEFORE_SHA
    shutil.copyfile(final, ROOT / 'Letter.3mf')
    assert protected == {n: file_sha(ROOT / n) for n in protected}
    assert file_sha(SAMPLE) == SAMPLE_SHA
    report_path = 'release/letter-eryone-r1/validation.json'
    evidence = dict(date='2026-10-23', project='Letter.3mf',
        source_project_sha256=BEFORE_SHA, project_sha256=file_sha(final),
        sample_path=str(SAMPLE), sample_sha256=SAMPLE_SHA,
        matching_tracked_sample=TRACKED_SAMPLE.relative_to(ROOT).as_posix(),
        sample_revision='r4 with r8 obsolete wall-base cleanup; Desktop filename retains r3',
        physical_evidence=dict(user_report='This test was a raging success.',
            scope='User-reported success for the supplied sample; no individual measured outcomes supplied.',
            saved_printer='Bambu Lab A2L 0.4 nozzle', actual_printer_independently_verified=False,
            locally_printed_file_hash_independently_verified=False,
            full_size_letter_physically_qualified=False),
        filament_slot=3, setting_changes={k: dict(before=a[k], after=updated[k]) for k in sorted(IDENTITY)},
        all_source_setting_differences=differences,
        retained_differences_explanation='Retain Letter process name, six-plate tower arrays and existing AMS dryer array serialization; these are not extrusion parameters. All printing parameters already match the sample.',
        locked_settings=LOCKS, objects=objects, veneer_object_overrides_match_sample=True,
        geometry_support_paint_poses_object_and_volume_settings_byte_preserved=True,
        changed_archive_entries=changed,
        preserved_archive_entries_sha256={n: sha(v) for n, v in files.items() if n not in changed},
        protected_files_sha256=protected, protected_files_unchanged=True,
        native_reopen=native, resliced=False,
        slice_status='Existing native commands retained exactly; two identity comments and MD5 updated on all six plates.',
        plates=plates, estimates=estimates, veneer_and_support_material_g=veneer_g,
        total_material_g=sum(p['material_g'] for p in estimates),
        total_seconds=sum(p['seconds'] for p in estimates), printer_job_sent=False)
    dump(REPORT / 'validation.json', evidence)
    catalog_path = ROOT / 'release/root-projects/catalog.json'
    catalog = json.loads(catalog_path.read_text())
    catalog['Letter'].update(sha256=file_sha(final), validation=report_path,
                             filament_slot_3=updated['filament_settings_id'][2])
    dump(catalog_path, catalog)
    hashes_path = ROOT / 'release/root-projects/gcode-sha256.json'
    hashes = json.loads(hashes_path.read_text())
    hashes['Letter'] = {f'plate_{p["plate"]}': p['gcode_sha256'] for p in plates}
    dump(hashes_path, hashes)
    samples_path = ROOT / 'release/samples/catalog.json'
    samples = json.loads(samples_path.read_text())
    samples['Dara-A2L-Hammered-Finish-ERYONE-r4']['physical_result'] = dict(
        date='2026-10-23', user_report='This test was a raging success.',
        supplied_file_sha256=SAMPLE_SHA, evidence=report_path,
        full_size_letter_physically_qualified=False)
    dump(samples_path, samples)
    print(json.dumps(dict(project_sha256=file_sha(final), changed_entries=len(changed),
                          native_reopen_passed=True, native_commands_preserved_on_plates=6,
                          veneer_and_support_material_g=veneer_g), indent=2))


if __name__ == '__main__':
    main()
