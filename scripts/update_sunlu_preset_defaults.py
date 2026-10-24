"""Revision-specific SUNLU default promotion, approved October 23, 2026.

Prepare reviewable JSON snapshots, validate with Bambu, then install the three
changed existing presets. Backups and account-specific sidecars stay ignored.
Production projects are hash-protected and are never rewritten by this script.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import zipfile

from apply_sunlu_pla_profiles import compare

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / '.work/sunlu-profile-defaults-r2'
RELEASE = ROOT / 'release/sunlu-profile-defaults-r2'
USER = Path(os.environ['APPDATA']) / 'BambuStudio/user/2065895616/filament/base'
CHANGES = {
    'SUNLU PLA Basic @Bambu Lab A1 0.4 nozzle': {},
    'SUNLU PLA Basic @Bambu Lab A2L 0.4 nozzle': {
        'textured_plate_temp': ('55', '65'), 'textured_plate_temp_initial_layer': ('55', '65')},
    'SUNLU PLA Metallic @Bambu Lab A1 0.4 nozzle': {'filament_max_volumetric_speed': ('12', '7.5')},
    'SUNLU PLA Metallic @Bambu Lab A2L 0.4 nozzle': {
        'textured_plate_temp': ('55', '65'), 'textured_plate_temp_initial_layer': ('55', '65'),
        'filament_max_volumetric_speed': ('12', '7.5')},
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def prepare():
    prior = json.loads((ROOT/'release/sunlu-pla-r1/validation.json').read_text())
    report = dict(date='2026-10-23', profiles={},
                  protected_projects={p.name: digest(p) for p in ROOT.glob('*.3mf')},
                  project_files_unchanged=True, resliced=False, printer_job_sent=False,
                  bambu_cloud_sync='Pending normal Bambu Studio sync; not remotely verified.',
                  native_reference='https://github.com/bambulab/BambuStudio/wiki/Command-Line-Usage',
                  sync_reference='https://github.com/bambulab/BambuStudio/blob/master/src/libslic3r/Preset.cpp')
    (WORK/'before').mkdir(parents=True, exist_ok=True)
    (RELEASE/'presets').mkdir(parents=True, exist_ok=True)
    for name, changes in CHANGES.items():
        source = USER/(name+'.json')
        assert digest(source) == prior['presets'][name]['sha256'], ('Preset changed since comparison', name)
        for suffix in ('.json', '.info'):
            path = USER/(name+suffix)
            backup = WORK/'before'/path.name
            if not backup.exists():
                backup.write_bytes(path.read_bytes())
            assert backup.read_bytes() == path.read_bytes()
        raw = source.read_bytes()
        old = json.loads(raw)
        for key, (before, after) in changes.items():
            assert old[key] == [before]
            pattern = rb'("' + key.encode() + rb'"\s*:\s*\[\s*")' + before.encode() + rb'("\s*\])'
            raw, count = re.subn(pattern, lambda m: m[1]+after.encode()+m[2], raw)
            assert count == 1
        new = json.loads(raw)
        assert {k for k in old if old[k] != new[k]} == set(changes)
        candidate = RELEASE/'presets'/source.name
        candidate.write_bytes(raw)
        report['profiles'][name] = dict(source_path=str(source), before_sha256=digest(source),
            after_sha256=digest(candidate), changed=bool(changes),
            differences={k: {'before': [a], 'after': [b]} for k,(a,b) in changes.items()},
            all_other_fields_preserved=True)
    dump(RELEASE/'validation.json', report)
    print('Prepared three changed presets and one unchanged A1 Basic reference.')


def install():
    report_path = RELEASE/'validation.json'
    report = json.loads(report_path.read_text())
    assert report.get('native_validation_passed'), 'Validate candidates before installation.'
    running = subprocess.check_output(['tasklist', '/FI', 'IMAGENAME eq bambu-studio.exe', '/FO', 'CSV']).decode(errors='replace')
    assert 'bambu-studio.exe' not in running.lower(), 'Bambu Studio must be closed to avoid overwriting in-memory presets.'
    for name, row in report['profiles'].items():
        assert digest(USER/(name+'.json')) == row['before_sha256']
        assert (USER/(name+'.info')).read_bytes() == (WORK/'before'/(name+'.info')).read_bytes()
    for name, row in report['profiles'].items():
        source = USER/(name+'.json')
        if row['changed']:
            candidate = RELEASE/'presets'/source.name
            assert digest(candidate) == row['after_sha256']
            source.write_bytes(candidate.read_bytes())
            info = source.with_suffix('.info')
            raw = info.read_bytes()
            old_time = int(re.search(rb'(?m)^updated_time = (\d+)', raw)[1])
            timestamp = max(int(time.time()), old_time + 1)
            raw, n = re.subn(rb'(?m)^sync_info = [^\r\n]*', b'sync_info = update', raw)
            assert n == 1
            raw, n = re.subn(rb'(?m)^updated_time = \d+', b'updated_time = '+str(timestamp).encode(), raw)
            assert n == 1
            # Preserve user/setting/base IDs exactly; only sync state and time change.
            strip = lambda b: re.sub(rb'(?m)^(?:sync_info|updated_time) = [^\r\n]*', b'', b)
            assert strip(raw) == strip(info.read_bytes())
            info.write_bytes(raw)
            row['sync_marked_for_update'] = True
        assert digest(source) == row['after_sha256']
        row['installed_and_read_back_verified'] = True
    assert report['protected_projects'] == {n: digest(ROOT/n) for n in report['protected_projects']}
    report['local_preset_installation_complete'] = True
    dump(report_path, report)
    print('Installed and verified the three changed existing Bambu presets; A1 Basic and all 3MF files unchanged.')


def validate():
    report_path = RELEASE/'validation.json'
    report = json.loads(report_path.read_text())
    exe = Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe')
    for name in CHANGES:
        printer = 'A2L' if ' A2L ' in name else 'A1'
        project = 'Knot.3mf' if printer == 'A2L' else 'Small Parts.3mf'
        folder = WORK/'native'/name
        folder.mkdir(parents=True, exist_ok=True)
        # Validate each preset independently in slot 1. Multi-preset CLI imports
        # interleave AMS dryer limitation tuples incorrectly; do not publish
        # those temporary exports or change the original user tuples.
        preset = json.loads((RELEASE/'presets'/(name+'.json')).read_text())
        wrapper = folder/(name+'.json')
        assert 'type' not in preset
        dump(wrapper, dict(preset, type='filament'))
        with (folder/'run.log').open('w') as log:
            result = subprocess.run([str(exe), '--load-filaments', str(wrapper),
                '--export-3mf', 'validation-only.3mf', '--outputdir', str(folder), str(ROOT/project)],
                cwd=exe.parent, stdout=log, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
        result.check_returncode()
        native = json.loads((folder/'result.json').read_text())
        assert native['return_code'] == 0
        with zipfile.ZipFile(folder/'validation-only.3mf') as z:
            settings = json.loads(z.read('Metadata/project_settings.config'))
        differences, checked = compare(settings, preset, 0)
        assert not differences, (name, differences)
        row = report['profiles'][name]
        row['native_load_verified'] = True
        row['native_compared_option_count'] = len(checked)
        report.setdefault('native_validation', {})[name] = native
        print(f'{name}: Bambu loaded and retained all 134 compared options.', flush=True)
    assert report['protected_projects'] == {n: digest(ROOT/n) for n in report['protected_projects']}
    report['native_validation_passed'] = True
    report['native_import_wrapper'] = 'Temporary copies add only type=filament, required by CLI; installed user files preserve the original format.'
    dump(report_path, report)


if __name__ == '__main__':
    {'prepare': prepare, 'validate': validate, 'install': install}[sys.argv[1]]()
