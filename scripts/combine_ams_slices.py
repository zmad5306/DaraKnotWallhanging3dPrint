"""Combine GUI-saved editable models and their all-plate sliced export.

Bambu's GUI saves models and G-code separately. Use Save Project As and Export
all sliced file on the same unchanged, fully sliced project, then run this tool.
It stages a candidate and validation input; publishing requires the full audit.
"""
import argparse
import copy
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

from colorize_print_project import setmeta
from build_jointed_bambu_project import xml, tag
from validate_print_project import PACKAGE, props, digest


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--models', required=True, type=Path)
    ap.add_argument('--slices', required=True, type=Path)
    ap.add_argument('--output', required=True, type=Path)
    args = ap.parse_args()
    with zipfile.ZipFile(args.models) as z:
        files = {n: z.read(n) for n in z.namelist()}
    with zipfile.ZipFile(args.slices) as z:
        sliced = {n: z.read(n) for n in z.namelist()}
    model = ET.fromstring(files['Metadata/model_settings.config'])
    toolpaths = ET.fromstring(sliced['Metadata/model_settings.config'])
    info = ET.fromstring(sliced['Metadata/slice_info.config'])
    root = ET.fromstring(files['3D/3dmodel.model'])
    names = {o.get('id'): props(o)['name'] for o in model.findall('object')}
    assert len(model.findall('plate')) == len(toolpaths.findall('plate')) == len(info.findall('plate')) == 30
    for plate, sliced_plate, stat in zip(model.findall('plate'), toolpaths.findall('plate'), info.findall('plate')):
        number = props(plate)['plater_id']
        assert number == props(sliced_plate)['plater_id'] == props(stat)['index']
        assert props(plate)['plater_name'] == props(sliced_plate)['plater_name']
        # Slice info lists distinct objects (Retainer has 32 instances).
        instances = plate.findall('model_instance')
        exported = list(stat.findall('object'))
        assert set(names[props(i)['object_id']] for i in instances) == {o.get('name') for o in exported}
        # Bambu's Save Project As retains all 32 Retainer build items but
        # serializes only the first plate link. Restore explicit links from
        # those existing build items and the corresponding G-code label IDs.
        gcode = sliced[props(sliced_plate)['gcode_file']].decode()
        labels = re.search(r'^; model label id: (.*)$', gcode, re.M)
        label_ids = list(map(int, labels[1].split(','))) if labels else []
        for instance in instances:
            ip = props(instance)
            if names[ip['object_id']] != 'Retainer':
                continue
            builds = [b for b in root.find(tag('build')) if b.get('objectid') == ip['object_id']]
            links = [i for i in instances if props(i)['object_id'] == ip['object_id']]
            assert len(builds) == 32 and number == '29'
            if len(links) == 1:
                first = int(ip['identify_id'])
                assert all(first + i in label_ids for i in range(32))
                for i in range(1, 32):
                    new = copy.deepcopy(instance)
                    setmeta(new, 'instance_id', i)
                    setmeta(new, 'identify_id', first + i)
                    plate.append(new)
            else:
                assert len(links) == 32
                break
        if label_ids:
            assert set(label_ids) == {int(props(i)['identify_id']) for i in plate.findall('model_instance')}
        for metadata in sliced_plate.findall('metadata'):
            if metadata.get('key').endswith('_file'):
                setmeta(plate, metadata.get('key'), metadata.get('value'))
    files.update({n: d for n, d in sliced.items() if n.startswith('Metadata/') and n != 'Metadata/model_settings.config'})
    files['Metadata/model_settings.config'] = xml(model)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.output, 'w', zipfile.ZIP_DEFLATED) as z:
        for n, data in files.items():
            z.writestr(n, data)
    baseline = json.loads((PACKAGE / 'project-validation.json').read_text())
    # Refresh Bambu's re-numbered IDs without changing the verified geometry
    # and XY placement records used by the independent audit.
    for layout, plate in zip(baseline['plate_layout'], model.findall('plate')):
        remaining = list(plate.findall('model_instance'))
        for item in layout['items']:
            instance = next(i for i in remaining if names[props(i)['object_id']] == item['name'])
            remaining.remove(instance)
            item.update({k: int(props(instance)[k]) for k in ('object_id', 'instance_id', 'identify_id')})
        assert not remaining
    baseline['test_plate']['plate_layout'] = copy.deepcopy(baseline['plate_layout'][-1])
    baseline['project_sha256'] = digest(args.output)
    baseline['settings'] = {k: v for k, v in json.loads(files['Metadata/project_settings.config']).items()
                            if k in baseline['settings'] or k == 'filament_colour'}
    # Prior toolpaths and round-trip topology reports do not describe this file.
    for key in ('bambu_studio_slice', 'bambu_studio_round_trip', 'bambu_studio_slice_warnings'):
        baseline.pop(key, None)
    baseline['test_plate'].pop('production_gcodes_byte_identical', None)
    baseline['ams_color_workflow'] = {
        'models_sha256': digest(args.models), 'slices_sha256': digest(args.slices),
        'color_assignment': 'Original printable meshes; wood filament modifiers at Z=8.4..9.6 mm; copper M.',
        'slice_export': 'Bambu Studio GUI: Slice all, Export all sliced file',
        'audit': 'Run validate_print_project.py against this candidate before publishing.'}
    args.output.with_suffix('.json').write_text(json.dumps(baseline, indent=2) + '\n')
    print(args.output)


if __name__ == '__main__':
    main()
