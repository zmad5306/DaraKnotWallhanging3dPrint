"""Apply meaningful veneer names without changing meshes, settings or G-code."""
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / '.work/python-libs'), str(ROOT / 'scripts')]
import organize_root_projects as org

NAMES = {f'V{i} A2L hammered veneer and wall cradle r6 end ties': f'{side} letter veneer'
         for i, side in [(1, 'Left'), (2, 'Right'), (3, 'Center')]}
SOURCE = ROOT / 'output/Dara-A2L-Veneers-ERYONE-r10/Dara-A2L-Veneers-ERYONE-r10.3mf'
OUT = ROOT / 'output/Letter Veneers'
DEST = OUT / 'Letter Veneers.3mf'
EVIDENCE = ROOT / 'release/letter-veneer-names'


def rename_project(source, dest):
    before = org.read(source)
    files = dict(before)
    cfg = ET.fromstring(files['Metadata/model_settings.config'])
    mapping = {}
    for obj in cfg.findall('object'):
        old = org.props(obj)['name']
        if old not in NAMES:
            continue
        mapping[obj.get('id')] = NAMES[old]
        for node in obj.iter('metadata'):
            if node.get('key') == 'name' and node.get('value') in NAMES:
                node.set('value', NAMES[node.get('value')])
    labels = []
    for p in cfg.findall('plate'):
        ids = [org.props(ins)['object_id'] for ins in p.findall('model_instance')]
        if len(ids) == 1 and ids[0] in mapping:
            old = org.props(p)['plater_name']
            org.setmeta(p, 'plater_name', mapping[ids[0]])
            labels.append(dict(plate=int(org.props(p)['plater_id']), old=old, name=mapping[ids[0]]))
    assert len(labels) == 3
    files['Metadata/model_settings.config'] = org.xml(cfg)
    for n in files:
        if n == 'Metadata/slice_info.config' or re.fullmatch(r'Metadata/plate_\d+\.json', n):
            for old, new in NAMES.items():
                files[n] = files[n].replace(old.encode(), new.encode())
    changed = [n for n in files if files[n] != before[n]]
    assert all(n in ['Metadata/model_settings.config', 'Metadata/slice_info.config'] or
               re.fullmatch(r'Metadata/plate_\d+\.json', n) for n in changed)
    # Remove only the allowed name fields, then compare effective configuration.
    def without_names(data):
        tree = ET.fromstring(data)
        for node in tree.iter('metadata'):
            if node.get('key') in ['name', 'plater_name']:
                node.set('value', '')
        return ET.tostring(tree)
    assert without_names(before['Metadata/model_settings.config']) == without_names(files['Metadata/model_settings.config'])
    gcode = {n:hashlib.sha256(b).hexdigest() for n,b in before.items() if n.endswith('.gcode')}
    assert all(before[n] == files[n] for n in before if n.startswith('3D/') or '.gcode' in n or n == 'Metadata/project_settings.config')
    source_hash = org.sha(source)
    org.write(dest, files)
    reread = org.read(dest)
    assert reread == files
    return dict(source=str(source), source_sha256=source_hash, file=str(dest), sha256=org.sha(dest),
                names=labels, changed_archive_entries=changed, unchanged_gcode_sha256=gcode,
                archive_entries_sha256={n:hashlib.sha256(b).hexdigest() for n,b in files.items()},
                all_geometry_paint_poses_process_material_settings_and_gcode_byte_identical=True)


def replace_strings(obj, replacements):
    if isinstance(obj, dict):
        return {k:replace_strings(v, replacements) for k,v in obj.items()}
    if isinstance(obj, list):
        return [replace_strings(v, replacements) for v in obj]
    if isinstance(obj, str):
        for old, new in replacements.items():
            obj = obj.replace(old, new)
    return obj


def main():
    OUT.mkdir(exist_ok=True);EVIDENCE.mkdir(exist_ok=True)
    assert org.sha(SOURCE) == 'b2d2a7b0299ddc1b604d557f5c90d2f4052297461487a1afc6fa47136d164ee9'
    candidate = rename_project(SOURCE, DEST)
    (OUT/'name-preservation.json').write_text(json.dumps(candidate, indent=2)+'\n')
    # Export only the current correction project; production geometry is separate.
    old_root, old_report, old_titles = org.ROOT, org.REPORT, org.TITLES
    org.ROOT = OUT;org.REPORT = OUT;org.TITLES = ['Letter Veneers']
    org.export_cad()
    org.ROOT, org.REPORT, org.TITLES = old_root, old_report, old_titles
    report = json.loads((SOURCE.parent/'validation.json').read_text())
    report['physical_observation'] = {
        'reported_plate':'Plate 5 of Letter; previous saved plate labels conflict with selector numbers',
        'identity_not_assumed':'Earlier V1 answer and later Plate 5 report retained; selector 4 was labelled 5 - V1, selector 5 was labelled 6 - V2.',
        'user_has_printed_or_inspected_other_veneers':False,
        'finding':'Whole part and carrier reportedly shift at both front and rear ends. Right-side photographs. Cause remains unresolved.'}
    report['delivered_file'] = str(DEST);report['delivered_sha256'] = org.sha(DEST)
    report['name_only_preservation'] = candidate
    (OUT/'validation.json').write_text(json.dumps(report, indent=2)+'\n')

    # Rename the production project's labels only. Its original slices stay intact.
    production = ROOT/'Letter.3mf'
    assert org.sha(production) == '8e391762ecb8415b77680a7bd4825e94afe37951d831bcfe41f6a43f31b16d4a'
    backup = ROOT/'.work/veneer-full-height/Letter-before-names.3mf'
    backup.parent.mkdir(exist_ok=True);shutil.copyfile(production, backup)
    root_report = rename_project(production, production)
    replacements = dict(NAMES)
    # Keep adjacent CAD paths and catalog synchronized; STL bytes are untouched.
    for old, new in NAMES.items():
        old_slug = re.sub(r'[^A-Za-z0-9_-]+', '-', old).strip('-')[:65]
        new_slug = new.replace(' ', '-')
        old_path = ROOT/f'Letter STL/{old_slug}-volume-1.stl'
        new_path = ROOT/f'Letter STL/{new_slug}-volume-1.stl'
        assert old_path.resolve().is_relative_to(ROOT) and new_path.resolve().is_relative_to(ROOT)
        assert old_path.exists() and not new_path.exists()
        digest = org.sha(old_path)
        old_path.rename(new_path)
        assert org.sha(new_path) == digest
        replacements[old_path.name] = new_path.name
    cad = ROOT/'Letter.scad'
    cad.write_text(replace_strings(cad.read_text(), replacements), encoding='utf-8', newline='\n')
    catalog_path = ROOT/'release/root-projects/catalog.json'
    catalog = json.loads(catalog_path.read_text())
    catalog['Letter'] = replace_strings(catalog['Letter'], replacements)
    catalog['Letter']['sha256'] = org.sha(production)
    catalog['Letter']['cad_sha256'] = org.sha(cad)
    catalog['Letter']['name_validation'] = 'release/letter-veneer-names/validation.json'
    catalog_path.write_text(json.dumps(catalog, indent=2)+'\n', encoding='utf-8', newline='\n')
    root_report['stl_geometry_bytes_unchanged'] = True
    root_report['cad_sha256'] = org.sha(cad)
    (EVIDENCE/'validation.json').write_text(json.dumps(root_report, indent=2)+'\n')
    print(json.dumps(dict(current_project=str(DEST), current_sha256=org.sha(DEST),
                         root_name_only_sha256=org.sha(production), names=list(NAMES.values())), indent=2), flush=True)


if __name__ == '__main__':
    main()
