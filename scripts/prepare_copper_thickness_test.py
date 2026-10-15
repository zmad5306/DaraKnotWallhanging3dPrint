"""Build and audit four small copper thickness coupons without changing production.

Run stage, slice, publish. All heights and extrusion roles are checked against
the actual exported G-code before publishing the separate Bambu project.
"""
import argparse
import collections
import csv
import json
import math
from pathlib import Path
import statistics
import subprocess
import xml.etree.ElementTree as ET

from build_jointed_bambu_project import P, R, IDENTITY, meta, mesh_object, model, tag, uid, trimesh
from tune_silk_project import OBJECT_SETTINGS, read_zip, write_zip, props, setmeta, sha, xml
from prepare_copper_diagnostic_test import inspect_moves
from validate_print_project import scan_gcode

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / '.work/copper-thickness'
TARGET = ROOT / 'Dara-Copper-Thickness-Test.3mf'
NOTES = ROOT / 'Dara-Copper-Thickness-Test.txt'
MEASUREMENTS = ROOT / 'Dara-Copper-Thickness-Measurements.csv'
REPORT = ROOT / 'working/bambu/Dara-Photo-Frame-A1-Jointed/copper-thickness-test.json'
PRODUCTION = [ROOT / 'Dara.3mf', ROOT / 'working/bambu/Dara-Photo-Frame-A1-Jointed/Dara-Photo-Frame-A1-Complete.3mf']
TITLE = 'Copper thickness - 1 / 2 / 4 mm and gyroid'
SAMPLES = [
    dict(label='S1', position='front left', xy=[100, 100], height=1.0, layers=5, solid=True),
    dict(label='S2', position='front right', xy=[155, 100], height=2.0, layers=10, solid=True),
    dict(label='S4', position='rear left', xy=[100, 155], height=4.0, layers=20, solid=True),
    dict(label='G4', position='rear right', xy=[155, 155], height=4.0, layers=20, solid=False),
]


def overrides(sample):
    settings = dict(OBJECT_SETTINGS, name=f"{sample['label']} - {sample['position']} - {sample['height']:.1f}mm - "
                    + ('solid' if sample['solid'] else '15% gyroid'),
                    extruder='3', enable_support='0', brim_type='no_brim')
    if sample['solid']:
        # Make every layer beneath the top a solid shell, at the same internal
        # solid speed/width. Merely setting density=100% leaves a different
        # sparse-infill role (and possibly speed/width) in the taller sample.
        settings.update(top_shell_layers='20', top_shell_thickness='4',
                        sparse_infill_density='100%', sparse_infill_pattern='zig-zag')
    else:
        settings.update(sparse_infill_density='15%', sparse_infill_pattern='gyroid')
    return settings


def stage():
    WORK.mkdir(parents=True, exist_ok=True)
    assert not (WORK / 'manifest.json').exists(), 'Keep the existing test evidence; use a fresh work directory.'
    hashes = {str(p.relative_to(ROOT)): sha(p) for p in PRODUCTION}
    assert len(set(hashes.values())) == 1
    preserved = dict(hashes)
    preserved['Dara-Copper-Diagnostic-Test.3mf'] = sha(ROOT / 'Dara-Copper-Diagnostic-Test.3mf')
    source = read_zip(PRODUCTION[0])
    settings = json.loads(source['Metadata/project_settings.config'])
    for key in ['layer_height', 'initial_layer_print_height']:
        assert float(settings[key]) == .2, (key, settings[key])
    assert settings['printer_model'] == 'Bambu Lab A1'
    assert settings['nozzle_diameter'] == ['0.4']
    assert settings['curr_bed_type'] == 'Textured PEI Plate'
    assert settings['filament_flow_ratio'][2] == '0.96'
    assert settings['wall_loops'] == '4' and settings['top_one_wall_type'] == 'all top'
    settings.update(print_settings_id=TITLE, print_sequence='by layer', enable_prime_tower='0', enable_support='0')
    files = {
        '[Content_Types].xml': source['[Content_Types].xml'],
        '_rels/.rels': b'<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>',
        'Metadata/project_settings.config': json.dumps(settings, indent=2).encode(),
    }
    root = model()
    del root.attrib['xmlns:p']
    for key, value in [('Application', 'BambuStudio-02.08.02.61'), ('BambuStudio:3mfVersion', '1'),
                       ('Title', TITLE), ('Description', 'Four 25 x 25 mm coupons. Solid heights 1, 2, 4 mm; 4 mm gyroid control. No pause.')]:
        ET.SubElement(root, tag('metadata'), name=key).text = value
    resources = ET.SubElement(root, tag('resources'))
    build = ET.SubElement(root, tag('build'), attrib={'{' + P + '}UUID': uid()})
    config = ET.Element('config')
    relationships = ET.Element('Relationships', xmlns=R)
    for index, sample in enumerate(SAMPLES, 1):
        obj_id, part_id = index * 1000, index * 1000 + 1
        path = f"3D/Objects/Coupon-{sample['label']}.model"
        mesh = trimesh.creation.box(extents=[25, 25, sample['height']])
        mesh.apply_translation([0, 0, sample['height'] / 2])
        assert mesh.is_watertight and abs(mesh.volume - 625 * sample['height']) < 1e-8
        child = model()
        mesh_object(ET.SubElement(child, tag('resources')), part_id, mesh)
        top = ET.SubElement(resources, tag('object'), id=str(obj_id), type='model', attrib={'{' + P + '}UUID': uid()})
        ET.SubElement(ET.SubElement(top, tag('components')), tag('component'), objectid=str(part_id), transform=IDENTITY,
                      attrib={'{' + P + '}path': '/' + path, '{' + P + '}UUID': uid()})
        obj = ET.SubElement(config, 'object', id=str(obj_id))
        for key, value in overrides(sample).items():
            meta(obj, key, value)
        part = ET.SubElement(obj, 'part', id=str(part_id), subtype='normal_part')
        meta(part, 'name', f"Coupon {sample['label']}")
        ET.SubElement(part, 'mesh_stat', face_count='12', edges_fixed='0', degenerate_facets='0',
                      facets_removed='0', facets_reversed='0', backwards_edges='0')
        files[path] = xml(child)
        ET.SubElement(relationships, 'Relationship', Target='/' + path, Id=f'rel-{index}',
                      Type='http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel')
        x, y = sample['xy']
        ET.SubElement(build, tag('item'), objectid=str(obj_id), printable='1',
                      transform=f'1 0 0 0 1 0 0 0 1 {x} {y} 0', attrib={'{' + P + '}UUID': uid()})
    plate = ET.SubElement(config, 'plate')
    for key, value in [('plater_id', 1), ('plater_name', TITLE), ('locked', 'false'),
                       ('filament_map_mode', 'Auto For Flush'), ('filament_maps', '1 1 1 1'), ('filament_volume_maps', '0 0 0 0')]:
        meta(plate, key, value)
    for index in range(1, len(SAMPLES) + 1):
        instance = ET.SubElement(plate, 'model_instance')
        for key, value in [('object_id', index * 1000), ('instance_id', 0), ('identify_id', 100 + index)]:
            meta(instance, key, value)
    files.update({'3D/3dmodel.model': xml(root), '3D/_rels/3dmodel.model.rels': xml(relationships),
                  'Metadata/model_settings.config': xml(config)})
    write_zip(WORK / 'staged.3mf', files)
    (WORK / 'manifest.json').write_text(json.dumps(dict(preserved_hashes=preserved, samples=SAMPLES), indent=2))
    print(json.dumps(dict(staged=str(WORK / 'staged.3mf'), samples=SAMPLES), indent=2))


def slice_project():
    exe = Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe')
    output = WORK / 'slice'
    output.mkdir(exist_ok=True)
    with (WORK / 'slice.log').open('w', encoding='utf-8') as log:
        result = subprocess.run([str(exe), '--slice', '1', '--export-3mf', 'sliced.3mf', '--outputdir', str(output),
                                 str(WORK / 'staged.3mf')], cwd=exe.parent, stdout=log, stderr=subprocess.STDOUT,
                                creationflags=subprocess.CREATE_NO_WINDOW)
    print(json.dumps(dict(return_code=result.returncode, log=str(WORK / 'slice.log'))))
    result.check_returncode()


def publish():
    manifest = json.loads((WORK / 'manifest.json').read_text())
    for path, digest in manifest['preserved_hashes'].items():
        assert sha(ROOT / path) == digest, f'Existing project changed: {path}'
    files = read_zip(WORK / 'slice/sliced.3mf')
    config = ET.fromstring(files['Metadata/model_settings.config'])
    assert len(config.findall('plate')) == 1 and len(config.findall('object')) == 4
    numeric = {'top_solid_infill_flow_ratio', 'top_shell_thickness'}
    for sample in SAMPLES:
        obj = next(o for o in config.findall('object') if props(o).get('name', '').startswith(sample['label'] + ' - '))
        for key, value in overrides(sample).items():
            actual = props(obj)[key]
            assert (float(actual) == float(value) if key in numeric else actual == value), (sample['label'], key, actual)
    settings = json.loads(files['Metadata/project_settings.config'])
    assert float(settings['filament_flow_ratio'][2]) == .96
    assert float(settings['layer_height']) == float(settings['initial_layer_print_height']) == .2
    assert settings['print_sequence'] == 'by layer'
    assert settings['enable_prime_tower'] == settings['enable_support'] == '0'
    # No labels/cutouts/modifiers are added to the flat measurement surfaces.
    meshes = []
    for path, data in files.items():
        if path.startswith('3D/') and path.endswith('.model'):
            tree = ET.fromstring(data)
            for mesh in tree.iter(tag('mesh')):
                vertices = [[float(v.get(k)) for k in ('x', 'y', 'z')] for v in mesh.find(tag('vertices'))]
                bounds = [[min(v[i] for v in vertices), max(v[i] for v in vertices)] for i in range(3)]
                extents = [b - a for a, b in bounds]
                assert abs(extents[0] - 25) < 1e-5 and abs(extents[1] - 25) < 1e-5
                assert len(mesh.find(tag('triangles'))) == 12
                meshes.append(round(extents[2], 4))
    assert sorted(meshes) == [1.0, 2.0, 4.0, 4.0], meshes
    setmeta(config.find('plate'), 'plater_name', TITLE)
    files['Metadata/model_settings.config'] = xml(config)
    info = ET.fromstring(files['Metadata/slice_info.config'])
    assert len(info.findall('plate')) == 1
    setmeta(info.find('plate'), 'printer_model_id', 'N2S')
    metadata_repairs = []
    # This CLI version can export an uninitialized first-layer time. Omit the
    # optional invalid display value; never invent a replacement or edit G-code.
    slice_plate = info.find('plate')
    for entry in list(slice_plate.findall('metadata')):
        if entry.get('key') == 'first_layer_time':
            first_time = float(entry.get('value'))
            if not math.isfinite(first_time) or not 0 <= first_time <= float(props(slice_plate)['prediction']):
                metadata_repairs.append(dict(key='first_layer_time', invalid_value=entry.get('value'), action='omit'))
                slice_plate.remove(entry)
    files['Metadata/slice_info.config'] = xml(info)
    if 'Metadata/custom_gcode_per_layer.xml' in files:
        assert not ET.fromstring(files['Metadata/custom_gcode_per_layer.xml']).findall('.//layer')
    gcode = files['Metadata/plate_1.gcode'].decode()
    audit = scan_gcode(gcode)
    assert audit['conservative_bed_edge_clearance_mm'] > 50
    assert set(audit['model_extrusion_z_by_filament_mm']) == {'3'}
    assert not any('Support' in k or 'Ironing' in k for k in audit['features'])
    records, pauses = inspect_moves(gcode, SAMPLES, (12.5, 12.5))
    assert not pauses
    samples_report = []
    for sample in SAMPLES:
        moves = records[sample['label']]
        heights = sorted({m['z'] for m in moves})
        assert heights == [round(i * .2, 1) for i in range(1, sample['layers'] + 1)]
        features = collections.Counter(m['feature'] for m in moves)
        if sample['solid']:
            assert features['Sparse infill'] == features['Bridge'] == 0, (sample['label'], features)
        else:
            assert features['Sparse infill'] > 0 and features['Bridge'] > 0, features
        top = [m for m in moves if m['feature'] == 'Top surface' and m['length'] > 10 and m['command'] == 'G1']
        assert top and {m['z'] for m in top} == {sample['height']}
        assert {m['speed'] for m in top} == {30}
        internal = [m for m in moves if m['feature'] == 'Internal solid infill' and m['length'] > 10 and m['command'] == 'G1']
        assert internal and {m['speed'] for m in internal} == {50}, (sample['label'], {m['speed'] for m in internal})
        samples_report.append(dict(sample, dimensions_mm=[25, 25, sample['height']],
            model_layer_z_mm=heights, features=dict(features), verified_top_speed_mm_s=30,
            verified_internal_solid_speed_mm_s=50,
            top_long_line_median_e_per_mm=statistics.median(m['e_per_mm'] for m in top),
            internal_long_line_median_e_per_mm=statistics.median(m['e_per_mm'] for m in internal)))
    for key in ['top_long_line_median_e_per_mm', 'internal_long_line_median_e_per_mm']:
        values = [s[key] for s in samples_report]
        assert max(values) / min(values) < 1.001, (key, values)
    result = json.loads((WORK / 'slice/result.json').read_text())
    assert result['return_code'] == 0 and result['plate_index'] == 1
    report = dict(project=TARGET.name, preserved_hashes=manifest['preserved_hashes'],
        filament_slot=3, base_filament_flow_ratio=.96, top_flow_multiplier=1,
        layer_height_mm=.2, initial_layer_height_mm=.2, ironing=False, pauses=0,
        samples=samples_report, toolpath_audit=audit, slicer_result=result, slice_metadata_repairs=metadata_repairs,
        limitations=['Calipers measure surface peaks, including the textured underside; they do not measure nozzle clearance.',
                    'A height trend does not distinguish Z motion, material buildup, shrinkage or surface texture by itself.',
                    'No physical replicate at each height, to conserve filament; take repeated readings at multiple locations.',
                    'G4 compares production-style sparse interior/bridge/roof construction with fully solid shells, not infill density alone.',
                    'Different heights finish on different layers and at different times; layer cooling and surface direction can differ.',
                    'A small coupon may not reproduce the full part.'])
    write_zip(TARGET, files)
    read_zip(TARGET)
    report['project_sha256'] = sha(TARGET)
    REPORT.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    write_instructions(info)
    print(json.dumps(dict(project=str(TARGET), report=str(REPORT), slice_metadata=props(info.find('plate'))), indent=2))


def write_instructions(info):
    plate = info.find('plate')
    metadata = props(plate)
    seconds = int(metadata['prediction'])
    estimate = f'{seconds // 60} min {seconds % 60} sec'
    grams = sum(float(f.get('used_g', '0')) for f in plate.findall('filament'))
    NOTES.write_text(f'''COPPER THICKNESS TEST

Open Dara-Copper-Thickness-Test.3mf as a project in Bambu Studio.
One already sliced plate: Bambu A1, 0.4 mm nozzle, textured PEI.
Map project filament 3 to the copper SUNLU Silk 2.0 spool.
Use normal 100% printer speed. No inspection pause and no ironing.
Slicer estimate: {grams:.2f} g, {estimate} (printer preparation/purge may add material).

Four coupons, each 25 x 25 mm: half the previous 50 mm width.
Viewed from above with the FRONT of the printer nearest you:

                       REAR
        [ S4: 4 mm solid ]   [ G4: 4 mm gyroid ]
        [ S1: 1 mm solid ]   [ S2: 2 mm solid  ]
                       FRONT

Expected finished thickness / layer count:
S1 = 1.00 mm / 5 layers
S2 = 2.00 mm / 10 layers
S4 = 4.00 mm / 20 layers
G4 = 4.00 mm / 20 layers

Every layer, including the first, is 0.20 mm. All use the selected C
finish: 30 mm/s top, 100% top multiplier, 0.96 base filament flow,
50 mm/s internal solid infill, 220 C nozzle, 55 C textured PEI bed.
S1/S2/S4 use enough solid shell layers to fill their entire thickness;
G4 retains production 15% gyroid and eight top shell layers / 1.6 mm.
All retain four walls and one perimeter on the final top face.
Labels are object names only: the measurement surfaces have no lettering.

MEASUREMENT
Let the plate and all pieces cool completely. Before mixing them up,
mark each label on a SIDE, leaving the top and bottom faces untouched.
Zero clean calipers. Use light, consistent jaw pressure; do not flex S1.
Measure near the center and at four other interior locations. Keep both
jaws inside the perimeter so a raised border does not dominate the reading.
Re-seat and repeat each reading to see how repeatable it is. Keep min/max,
not just the average. The CSV has five locations, two readings per location.
Also note whether the top is rough and whether the roughness varies by area.

INTERPRETATION
Compare measured thickness minus expected thickness for S1, S2 and S4.
A similar absolute offset is not evidence of error accumulating per layer.
A repeatable error that grows with height supports investigating a height
trend, but cannot by itself identify Z motion versus extrusion or shrinkage.
Correct overall thickness does not rule out local ridges or valleys.
Compare S4 with G4 to see whether the interior construction changes the
thickness or roughness at the same nominal height. This is not an isolated
infill-density test: bridge and solid-shell construction also differ.

Calipers touch the highest points, including the textured underside.
Only treat differences larger than the reading variation as meaningful.
There are no duplicate pieces at each height, to conserve material.
Different heights finish at different times; cooling and top-line direction
can differ. This small test cannot prove a unique cause of the full part's
finish. Existing production and prior diagnostic projects are unchanged.
''', encoding='utf-8')
    if MEASUREMENTS.exists():
        return  # Preserve any user-entered measurements when re-publishing.
    with MEASUREMENTS.open('w', newline='', encoding='utf-8') as out:
        writer = csv.writer(out)
        writer.writerow(['sample', 'plate_position', 'construction', 'expected_mm', 'layers', 'measurement_location',
                         'reading_1_mm', 'reading_2_mm', 'surface_notes'])
        for sample in SAMPLES:
            for location in ['center', 'front left interior', 'front right interior', 'rear left interior', 'rear right interior']:
                writer.writerow([sample['label'], sample['position'], 'solid' if sample['solid'] else '15% gyroid',
                                 f"{sample['height']:.2f}", sample['layers'], location, '', '', ''])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['stage', 'slice', 'publish'])
    command = parser.parse_args().command
    {'stage': stage, 'slice': slice_project, 'publish': publish}[command]()
