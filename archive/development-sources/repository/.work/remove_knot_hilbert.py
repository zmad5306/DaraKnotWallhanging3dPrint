"""Restore the exact validated screw-skin release, preserving unrelated work."""
import copy
import hashlib
import json
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / '.work/knot-white-hilbert-removal-r2'
REPORT = ROOT / 'release/knot-white-hilbert-removal-r2'
SOURCE = ROOT / '.work/knot-white-hilbert-r1/Knot-before.3mf'
CURRENT_SHA = 'e28d0026b64fe154e701240f735d06d6cfc74c83a084eb84ed810af3a073c060'
RESTORED_SHA = '8a76b70a1c1430d74a16ec06c9689827d33f3902afb1d7de90e4436072c251c3'
REV = 'c8f8f7acf1495dd0098871385fab180de20d2cbd'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def historical(path):
    return subprocess.check_output(['git', 'show', REV+':'+path], cwd=ROOT)

def dump(path, data):
    path.write_text(json.dumps(data, indent=2)+'\n', encoding='utf-8')

def protected():
    paths = [p for p in ROOT.glob('*.3mf') if p.name != 'Knot.3mf']
    paths += list(ROOT.glob('Knot STL/*.stl')) + [ROOT/'Knot.scad']
    paths += list((ROOT/'release/samples').glob('*.3mf'))
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in paths}

assert sha(ROOT/'Knot.3mf') == CURRENT_SHA
assert sha(SOURCE) == RESTORED_SHA
pointer = historical('Knot.3mf').decode()
assert 'oid sha256:'+RESTORED_SHA in pointer
WORK.mkdir(parents=True, exist_ok=True)
REPORT.mkdir(parents=True, exist_ok=True)
before = protected()
shared = ['AGENTS.md', 'release/root-projects/README.md',
          'release/root-projects/catalog.json', 'release/root-projects/gcode-sha256.json']
for path in shared:
    target = WORK/'initial'/path
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT/path, target)
shutil.copyfile(ROOT/'Knot.3mf', WORK/'Knot-before.3mf')

with zipfile.ZipFile(ROOT/'Knot.3mf') as z:
    current = {n:z.read(n) for n in z.namelist()}
with zipfile.ZipFile(SOURCE) as z:
    restored = {n:z.read(n) for n in z.namelist()}
assert all(current[n] == v for n,v in restored.items() if n.endswith('.model'))
assert current['Metadata/project_settings.config'] == restored['Metadata/project_settings.config']
assert 'Metadata/layer_config_ranges.xml' not in restored
assert 'hilbertcurve' in current['Metadata/layer_config_ranges.xml'].decode()
old_cfg = ET.fromstring(current['Metadata/model_settings.config'])
new_cfg = ET.fromstring(restored['Metadata/model_settings.config'])
blue_overrides = 0
for old, new in zip(old_cfg.findall('object'), new_cfg.findall('object')):
    normalized = copy.deepcopy(old)
    for part in normalized.findall('part'):
        props = {m.get('key'):m.get('value') for m in part.findall('metadata')}
        if props.get('extruder') == '4':
            option = part.find("metadata[@key='top_surface_pattern']")
            assert option is not None and option.get('value') == 'monotonicline'
            part.remove(option)
            blue_overrides += 1
    assert ET.tostring(normalized) == ET.tostring(new)
assert blue_overrides == 10
settings = json.loads(restored['Metadata/project_settings.config'])
assert settings['top_surface_pattern'] == 'monotonicline'
assert b'hilbertcurve' not in restored['Metadata/model_settings.config']
proof = json.loads((ROOT/'release/knot-reinforcement-skin-r1/validation.json').read_text())
assert proof['project_sha256'] == RESTORED_SHA
assert proof['modifier_count'] == 50
assert proof['all_five_top_shell_layers_cross_former_modifier_boundary']
plate_hashes = {}
for row in proof['plates']:
    n=row['plate'];data=restored[f'Metadata/plate_{n}.gcode']
    assert hashlib.sha256(data).hexdigest()==row['gcode_sha256']
    assert hashlib.md5(data).hexdigest().upper()==restored[f'Metadata/plate_{n}.gcode.md5'].decode().strip().upper()
    assert re.search(r'^; top_surface_pattern = monotonicline\s*$',data.decode(),re.M)
    for zone in row['shell_continuity']:
        assert len(zone['new_cross_boundary_extrusion_segments'])==5
        assert all(v>0 for v in zone['new_cross_boundary_extrusion_segments'].values())
    plate_hashes[str(n)] = row['gcode_sha256']
assert len(plate_hashes)==10

shutil.copyfile(SOURCE, ROOT/'Knot.3mf')
for path in shared[2:]:
    work = json.loads((ROOT/path).read_text())
    work['Knot'] = json.loads(historical(path))['Knot']
    dump(ROOT/path, work)
(ROOT/'release/root-projects/Knot-native.json').write_bytes(historical('release/root-projects/Knot-native.json'))

agents = (ROOT/'AGENTS.md').read_text(encoding='utf-8')
start=agents.index('- **Approved white knot Hilbert finish,')
end=agents.index('- **Approved knot screw-skin correction,', start)
replacement='''- **Approved removal of white knot Hilbert finish, 2026-10-23:** the user
  requested removing Hilbert while preserving the hidden screw reinforcement.
  Restore the exact screw-skin release from `c8f8f7a`: original monotonic-line
  white surface pattern and finish directions, with all 50 solid screw
  modifiers still capped at **Z12.4 mm** beneath five continuous top layers.
  Remove the Hilbert height ranges and redundant blue pattern overrides;
  retain the original brown/blue geometry, settings and toolpaths. The project
  and ten stored native slices exactly match the validated screw-skin release
  (SHA-256 `8a76b70a1c1430d74a16ec06c9689827d33f3902afb1d7de90e4436072c251c3`).
  CAD/STL, poses and every other print setting remain unchanged. The Hilbert
  revision in `release/knot-white-hilbert-r1/` is withdrawn; restoration evidence
  is in `release/knot-white-hilbert-removal-r2/`. Physical finish remains pending.

'''
(ROOT/'AGENTS.md').write_text(agents[:start]+replacement+agents[end:],encoding='utf-8')
readme_path=ROOT/'release/root-projects/README.md'
readme=readme_path.read_text(encoding='utf-8')
readme,count=re.subn(r'^\| Knot \|.*$', '| Knot | 10 | 80h 32m | 2271.52 g |',readme,flags=re.M)
assert count==1
old_para=re.search(r'^Knot now uses.*$',readme,re.M)[0]
suffix=old_para[old_para.index('Sanding Block is'):]
new_para='Knot has returned to the original monotonic-line white surface finish. The project and all ten stored slices exactly match the validated screw-skin release: all 50 solid reinforcement modifiers stop at Z12.4 beneath five continuous top layers. Brown texture, blue trim, geometry, CAD/STL, poses and all other settings remain unchanged. See `../knot-white-hilbert-removal-r2/` for restoration evidence and `../knot-reinforcement-skin-r1/` for the matching native toolpath checks. The Hilbert revision is withdrawn. '+suffix
readme_path.write_text(readme.replace(old_para,new_para),encoding='utf-8')
hilbert_readme=ROOT/'release/knot-white-hilbert-r1/README.md'
text=hilbert_readme.read_text(encoding='utf-8')
text=text.replace('# White knot Hilbert finish\n','# White knot Hilbert finish — withdrawn\n\n**Withdrawn at the user\'s request on 2026-10-23.** Root `Knot.3mf` now restores\nthe original monotonic-line white finish while retaining the screw-skin correction.\nThis directory records the superseded Hilbert revision, not the current release.\nSee `../knot-white-hilbert-removal-r2/` for the restoration. Do not reapply the\nhistorical Hilbert builder without a new request.\n',1)
text=text.replace('It describes the source revision; this directory identifies the current slices.',
                  'It describes the restored current release; this directory identifies the superseded Hilbert slices.')
hilbert_readme.write_text(text,encoding='utf-8')

assert sha(ROOT/'Knot.3mf')==RESTORED_SHA
assert protected()==before
for path in shared[2:]:
    a=json.loads((WORK/'initial'/path).read_text())
    b=json.loads((ROOT/path).read_text())
    assert {k:v for k,v in a.items() if k!='Knot'}=={k:v for k,v in b.items() if k!='Knot'}
dump(REPORT/'validation.json',dict(
    project='Knot.3mf',project_sha256=RESTORED_SHA,source_hilbert_sha256=CURRENT_SHA,
    restored_from_commit=REV,exact_pre_hilbert_project_restored=True,
    all_ten_stored_native_slices_restored_exactly=True,plates=plate_hashes,
    no_reslice_required='Exact project, geometry, settings and slices restored together; original checks remain tied to the identical SHA-256.',
    white_top_surface_pattern='monotonicline',hilbert_height_ranges_removed=True,
    redundant_blue_monotonic_overrides_removed=blue_overrides,
    all_mesh_xml_and_global_process_settings_unchanged=True,
    all_object_and_volume_settings_unchanged_except_blue_override_removal=True,
    modifier_count=50,modifier_max_z_mm=12.4,
    five_skin_layer_continuity_checks_restored_exactly=True,
    native_slice_validation='release/knot-reinforcement-skin-r1/validation.json',
    protected_before=before,protected_after=protected(),
    unrelated_catalog_and_toolpath_entries_preserved=True,
    total_seconds=proof['total_seconds'],total_grams=proof['total_grams'],
    physical_finish_confirmation_pending=True,printer_job_sent=False))
print('Restored exact screw-skin project and ten native slices; protected files unchanged.')
