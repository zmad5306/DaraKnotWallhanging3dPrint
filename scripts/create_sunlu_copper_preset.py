"""Create A1/A2L SUNLU Silk Copper base presets from saved production slot 3.

No geometry, project assignments or process settings are changed. Full local
user presets are installed only after native loading and setting comparison.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
import zipfile

from apply_sunlu_pla_profiles import compare, META, DRYER
import update_sunlu_preset_defaults as defaults

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT/'release/sunlu-silk-copper-r1'
WORK = ROOT/'.work/sunlu-silk-copper-r1'
USER = Path(os.environ['APPDATA'])/'BambuStudio/user/2065895616/filament/base'
FAMILY = 'SUNLU PLA Silk Copper'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def closed():
    output = subprocess.check_output(['tasklist', '/FI', 'IMAGENAME eq bambu-studio.exe', '/FO', 'CSV']).decode(errors='replace')
    assert 'bambu-studio.exe' not in output.lower(), 'Close Bambu Studio before installing presets.'


def main():
    closed()
    user_info = (USER/'SUNLU PLA Basic @Bambu Lab A1 0.4 nozzle.info').read_text()
    user_id = re.search(r'(?m)^user_id = (\d+)', user_info)[1]
    filament_id = 'P' + hashlib.md5((FAMILY+'@'+user_id).encode()).hexdigest()[:7]
    existing = {str(p): sha(p) for p in USER.iterdir() if p.is_file()}
    for p in USER.glob('*.json'):
        assert json.loads(p.read_text()).get('filament_id') != filament_id, 'Filament ID already in use.'
    protected = {p.name: sha(p) for p in ROOT.glob('*.3mf')}
    report = dict(date='2026-10-23', filament_name=FAMILY, filament_id=filament_id,
        profiles={}, protected_projects=protected, project_assignments_changed=False,
        project_files_unchanged=True, printer_job_sent=False, resliced=False,
        physical_status='Copies the saved SUNLU copper settings; no new physical qualification.',
        custom_id_reference='https://github.com/bambulab/BambuStudio/blob/master/src/slic3r/GUI/CreatePresetsDialog.cpp')
    for printer, project in [('A1','Small Parts.3mf'), ('A2L','Knot.3mf')]:
        with zipfile.ZipFile(ROOT/project) as z:
            source = json.loads(z.read('Metadata/project_settings.config'))
        assert source['filament_settings_id'][2] == f'Generic PLA Silk @BBL {printer}'
        template = json.loads((ROOT/'release/sunlu-pla-r1/presets'/f'SUNLU PLA Basic @Bambu Lab {printer} 0.4 nozzle.json').read_text())
        preset = copy.deepcopy(template)
        for key, value in template.items():
            if key in META:
                continue
            saved = source[key]
            if key in DRYER:
                width = DRYER[key]
                assert len(saved) == 4*width
                preset[key] = saved[2*width:3*width]
            elif isinstance(value, list):
                assert len(value) == 1 and len(saved) in (1,4)
                preset[key] = [saved[min(2,len(saved)-1)]]
            else:
                preset[key] = saved
        name = f'{FAMILY} @Bambu Lab {printer} 0.4 nozzle'
        preset.update(name=name, filament_settings_id=[name], filament_id=filament_id,
                      filament_vendor=['SUNLU'], default_filament_colour=[source['filament_colour'][2]],
                      inherits='', **{'from':'User'})
        assert not (USER/(name+'.json')).exists() and not (USER/(name+'.info')).exists()
        difference, checked = compare(source,preset,2)
        assert not difference
        path = RELEASE/'presets'/(name+'.json')
        defaults.dump(path,preset)
        report['profiles'][name] = dict(source_project=project, source_project_sha256=protected[project],
            source_filament_slot=3, source_filament_name=source['filament_settings_id'][2],
            after_sha256=sha(path), compared_options=checked, source_parameter_differences={},
            copper_color=source['filament_colour'][2], all_source_parameters_preserved=True)
    defaults.dump(RELEASE/'validation.json',report)
    # Reuse the same native single-preset import validation as the default update.
    defaults.RELEASE, defaults.WORK, defaults.CHANGES = RELEASE, WORK, report['profiles']
    defaults.validate()
    report = json.loads((RELEASE/'validation.json').read_text())
    closed()
    assert existing == {p:sha(Path(p)) for p in existing}
    for name,row in report['profiles'].items():
        source = RELEASE/'presets'/(name+'.json')
        destination = USER/source.name
        assert not destination.exists() and not destination.with_suffix('.info').exists()
        with destination.open('xb') as f:
            f.write(source.read_bytes())
        info = f'sync_info = create\r\nuser_id = {user_id}\r\nsetting_id = \r\nbase_id = \r\nupdated_time = {int(time.time())}\r\n'
        with destination.with_suffix('.info').open('xb') as f:
            f.write(info.encode())
        assert sha(destination) == row['after_sha256']
        row.update(installed_and_read_back_verified=True, local_path=str(destination),
                   sync_marked_for_create=True)
    assert existing == {p:sha(Path(p)) for p in existing}
    assert protected == {p:sha(ROOT/p) for p in protected}
    report.update(local_preset_installation_complete=True, existing_presets_byte_preserved=True,
                  bambu_cloud_sync='Pending normal Bambu Studio sync; not remotely verified.')
    defaults.dump(RELEASE/'validation.json',report)
    print('Installed SUNLU PLA Silk Copper for A1 and A2L. Existing profiles and all project files are unchanged.')


if __name__ == '__main__':
    main()
