"""Build a separate five-coupon comparison; never modify the production projects.

Run stage, slice, then publish. Publish verifies the exported toolpaths first.
"""
import argparse
import collections
import json
import math
from pathlib import Path
import statistics
import subprocess
import xml.etree.ElementTree as ET

from build_jointed_bambu_project import C, P, R, IDENTITY, meta, mesh_object, model, tag, uid, trimesh
from tune_silk_project import OBJECT_SETTINGS, read_zip, write_zip, props, setmeta, sha, xml
from validate_print_project import scan_gcode, TOKEN

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / '.work/copper-diagnostic'
TARGET = ROOT / 'Dara-Copper-Diagnostic-Test.3mf'
REPORT = ROOT / 'working/bambu/Dara-Photo-Frame-A1-Jointed/copper-diagnostic-test.json'
PRODUCTION = [ROOT / 'Dara.3mf', ROOT / 'working/bambu/Dara-Photo-Frame-A1-Jointed/Dara-Photo-Frame-A1-Complete.3mf']
TITLE = 'Copper diagnostic - pause before final layer'
SAMPLES = [
    dict(label='A', position='front left', xy=[88, 91], speed=30, flow=1.04, density='15%', pattern='gyroid'),
    dict(label='B', position='front right', xy=[168, 91], speed=50, flow=1.04, density='15%', pattern='gyroid'),
    dict(label='C', position='middle left', xy=[88, 128], speed=30, flow=1.00, density='15%', pattern='gyroid'),
    dict(label='D', position='middle right', xy=[168, 128], speed=50, flow=1.00, density='15%', pattern='gyroid'),
    dict(label='S', position='rear center', xy=[128, 165], speed=30, flow=1.04, density='100%', pattern='zig-zag'),
]


def overrides(sample):
    # Bambu's serialized key for the UI's Rectilinear pattern is 'zig-zag'.
    pattern_name = 'rectilinear' if sample['pattern'] == 'zig-zag' else sample['pattern']
    return dict(OBJECT_SETTINGS, name=f"{sample['label']} - {sample['position']} - {sample['speed']}mm-s - {sample['flow'] * 100:.0f}% - {sample['density']} {pattern_name}",
                extruder='3', enable_support='0', brim_type='no_brim',
                top_surface_speed=str(sample['speed']), top_solid_infill_flow_ratio=f"{sample['flow']:.2f}",
                sparse_infill_density=sample['density'], sparse_infill_pattern=sample['pattern'])


def stage():
    WORK.mkdir(parents=True, exist_ok=True)
    hashes = {str(p.relative_to(ROOT)): sha(p) for p in PRODUCTION}
    assert len(set(hashes.values())) == 1
    source = read_zip(PRODUCTION[0])
    settings = json.loads(source['Metadata/project_settings.config'])
    assert settings['filament_flow_ratio'][2] == '0.96'
    assert settings['machine_pause_gcode'] == 'M400 U1'
    assert settings['wall_loops'] == '4' and settings['top_one_wall_type'] == 'all top'
    settings['print_settings_id'] = TITLE
    settings['print_sequence'] = 'by layer'
    settings['enable_prime_tower'] = '0'
    settings['enable_support'] = '0'
    files = {
        '[Content_Types].xml': source['[Content_Types].xml'],
        '_rels/.rels': b'<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>',
        'Metadata/project_settings.config': json.dumps(settings, indent=2).encode(),
    }
    root = model()
    del root.attrib['xmlns:p']
    for key, value in [('Application', 'BambuStudio-02.08.02.61'), ('BambuStudio:3mfVersion', '1'),
                       ('Title', TITLE), ('Description', 'Five 50 x 25 x 4.2 mm coupons; final layer at Z4.2. Inspect briefly at the pause, then resume.')]:
        ET.SubElement(root, tag('metadata'), name=key).text = value
    resources = ET.SubElement(root, tag('resources'))
    build = ET.SubElement(root, tag('build'), attrib={'{' + P + '}UUID': uid()})
    config = ET.Element('config')
    relationships = ET.Element('Relationships', xmlns=R)
    mesh = trimesh.creation.box(extents=[50, 25, 4.2])
    mesh.apply_translation([0, 0, 2.1])
    assert mesh.is_watertight and mesh.volume > 0
    for index, sample in enumerate(SAMPLES, 1):
        obj_id, part_id = index * 1000, index * 1000 + 1
        path = f"3D/Objects/Coupon-{sample['label']}.model"
        child = model()
        mesh_object(ET.SubElement(child, tag('resources')), part_id, mesh)
        top = ET.SubElement(resources, tag('object'), id=str(obj_id), type='model', attrib={'{' + P + '}UUID': uid()})
        component = ET.SubElement(top, tag('components'))
        ET.SubElement(component, tag('component'), objectid=str(part_id), transform=IDENTITY,
                      attrib={'{' + P + '}path': '/' + path, '{' + P + '}UUID': uid()})
        obj = ET.SubElement(config, 'object', id=str(obj_id))
        for k, v in overrides(sample).items():
            meta(obj, k, v)
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
    for k, v in [('plater_id', 1), ('plater_name', TITLE), ('locked', 'false'),
                 ('filament_map_mode', 'Auto For Flush'), ('filament_maps', '1 1 1 1'), ('filament_volume_maps', '0 0 0 0')]:
        meta(plate, k, v)
    for index in range(1, 6):
        inst = ET.SubElement(plate, 'model_instance')
        for k, v in [('object_id', index * 1000), ('instance_id', 0), ('identify_id', 100 + index)]:
            meta(inst, k, v)
    pause = ET.Element('custom_gcodes_per_layer')
    pause_plate = ET.SubElement(pause, 'plate')
    ET.SubElement(pause_plate, 'plate_info', id='1')
    ET.SubElement(pause_plate, 'layer', top_z='4.2', type='1', extruder='3', color='',
                  extra='Inspect the five surfaces briefly, then resume the final layer.', gcode='M400 U1')
    ET.SubElement(pause_plate, 'mode', value='SingleExtruder')
    files.update({'3D/3dmodel.model': xml(root), '3D/_rels/3dmodel.model.rels': xml(relationships),
                  'Metadata/model_settings.config': xml(config), 'Metadata/custom_gcode_per_layer.xml': xml(pause)})
    write_zip(WORK / 'staged.3mf', files)
    (WORK / 'manifest.json').write_text(json.dumps(dict(production_hashes=hashes, samples=SAMPLES), indent=2))
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


def inspect_moves(gcode, samples=None, half_extents=(25, 12.5)):
    samples = SAMPLES if samples is None else samples
    records = {s['label']: [] for s in samples}
    x = y = z = e = speed = 0.
    feature = 'Custom'
    width = .5
    relative_e = relative_xyz = False
    pauses = []
    for index, raw in enumerate(gcode.splitlines()):
        if raw.startswith('; FEATURE: '):
            feature = raw.split(': ', 1)[1]
        elif raw.startswith('; LINE_WIDTH: '):
            width = float(raw.split(': ', 1)[1])
        code = raw.split(';', 1)[0].strip()
        if not code:
            continue
        command = code.split()[0]
        v = {k: float(n) for k, n in TOKEN.findall(code)}
        if code == 'M400 U1':
            pauses.append(index)
        if command == 'M83':
            relative_e = True
        elif command == 'M82':
            relative_e = False
        elif command in ('G90', 'G91'):
            relative_xyz = command == 'G91'
        elif command == 'G92':
            x, y, z, e = v.get('X', x), v.get('Y', y), v.get('Z', z), v.get('E', e)
        elif command in ('G0', 'G1', 'G2', 'G3'):
            nx, ny, nz = [old + v.get(k, 0) if relative_xyz else v.get(k, old)
                          for k, old in zip('XYZ', (x, y, z))]
            de = v.get('E', 0) if relative_e else v.get('E', e) - e
            speed = v.get('F', speed)
            length = math.hypot(nx - x, ny - y)
            if de > 0 and feature != 'Custom' and length > .001:
                mx, my = (x + nx) / 2, (y + ny) / 2
                matched = [s for s in samples if abs(mx - s['xy'][0]) <= half_extents[0] + .01
                           and abs(my - s['xy'][1]) <= half_extents[1] + .01]
                assert len(matched) == 1, (index, raw, matched)
                records[matched[0]['label']].append(dict(line=index, z=round(nz, 4), feature=feature,
                    speed=round(speed / 60, 4), length=length, e_per_mm=de / length, command=command,
                    start=[x, y], end=[nx, ny], width=width))
            x, y, z = nx, ny, nz
            e = e + v.get('E', 0) if relative_e else v.get('E', e)
    return records, pauses


def publish():
    manifest = json.loads((WORK / 'manifest.json').read_text())
    for path, digest in manifest['production_hashes'].items():
        assert sha(ROOT / path) == digest, f'Production project changed: {path}'
    files = read_zip(WORK / 'slice/sliced.3mf')
    config = ET.fromstring(files['Metadata/model_settings.config'])
    assert len(config.findall('plate')) == 1 and len(config.findall('object')) == 5
    for sample in SAMPLES:
        obj = next(o for o in config.findall('object') if props(o).get('name', '').startswith(sample['label'] + ' - '))
        for key, value in overrides(sample).items():
            actual = props(obj)[key]
            assert (float(actual) == float(value) if key == 'top_solid_infill_flow_ratio' else actual == value), (sample['label'], key, actual)
    setmeta(config.find('plate'), 'plater_name', TITLE)
    files['Metadata/model_settings.config'] = xml(config)
    info = ET.fromstring(files['Metadata/slice_info.config'])
    assert len(info.findall('plate')) == 1
    setmeta(info.find('plate'), 'printer_model_id', 'N2S')
    files['Metadata/slice_info.config'] = xml(info)
    pause = ET.fromstring(files['Metadata/custom_gcode_per_layer.xml'])
    assert len(pause.findall('.//layer')) == 1
    assert pause.find('.//layer').get('type') == '1' and float(pause.find('.//layer').get('top_z')) == 4.2
    gcode = files['Metadata/plate_1.gcode'].decode()
    audit = scan_gcode(gcode)
    assert audit['conservative_bed_edge_clearance_mm'] > 20
    assert set(audit['model_extrusion_z_by_filament_mm']) == {'3'}
    assert 'Ironing' not in audit['features'] and 'Support' not in audit['features']
    records, pauses = inspect_moves(gcode)
    assert len(pauses) == 1, pauses
    samples_report = []
    for sample in SAMPLES:
        dense_spacing = None
        moves = records[sample['label']]
        assert sorted(set(m['z'] for m in moves)) == [round(i * .2, 1) for i in range(1, 22)]
        assert max(m['z'] for m in moves if m['line'] < pauses[0]) == 4.0
        assert min(m['z'] for m in moves if m['line'] > pauses[0]) == 4.2
        top = [m for m in moves if m['feature'] == 'Top surface' and m['length'] > 10 and m['command'] == 'G1']
        assert top and all(m['z'] == 4.2 for m in top)
        assert {m['speed'] for m in top} == {sample['speed']}, (sample['label'], {m['speed'] for m in top})
        pretop = [m for m in moves if m['z'] == 4.0 and m['feature'] == 'Internal solid infill' and m['length'] > 10 and m['command'] == 'G1']
        assert pretop and {m['speed'] for m in pretop} == {50}
        features = collections.Counter(m['feature'] for m in moves)
        if sample['label'] == 'S':
            assert features['Bridge'] == 0, features
            # Bambu still calls 100% rectilinear "Sparse infill". Verify density
            # through actual adjacent line spacing, rather than its feature label.
            dense = [m for m in moves if m['z'] == 1.2 and m['feature'] == 'Sparse infill'
                     and m['length'] > 10 and m['command'] == 'G1']
            assert len(dense) > 30
            a = dense[0]
            dx, dy = [(v - u) / a['length'] for u, v in zip(a['start'], a['end'])]
            offsets = sorted((m['start'][0] * -dy + m['start'][1] * dx) for m in dense)
            spacing = statistics.median(v - u for u, v in zip(offsets, offsets[1:]))
            expected_spacing = a['width'] - .2 * (1 - math.pi / 4)
            assert abs(spacing - expected_spacing) < .002, (spacing, expected_spacing)
            dense_spacing = dict(measured_mm=spacing, expected_for_100_percent_mm=expected_spacing)
        else:
            assert features['Sparse infill'] > 0 and features['Bridge'] > 0, features
        samples_report.append(dict(sample, verified_top_speed_mm_s=sample['speed'],
            top_long_line_median_e_per_mm=statistics.median(m['e_per_mm'] for m in top),
            pretop_long_line_median_e_per_mm=statistics.median(m['e_per_mm'] for m in pretop),
            features=dict(features), solid_interior_spacing_check=dense_spacing))
    by_label = {s['label']: s for s in samples_report}
    for high, low in [('A', 'C'), ('B', 'D')]:
        ratio = by_label[high]['top_long_line_median_e_per_mm'] / by_label[low]['top_long_line_median_e_per_mm']
        assert abs(ratio - 1.04) < .0005, ratio
    for first, second in [('A', 'B'), ('C', 'D'), ('A', 'S')]:
        assert abs(by_label[first]['top_long_line_median_e_per_mm'] / by_label[second]['top_long_line_median_e_per_mm'] - 1) < .0005
    assert max(s['pretop_long_line_median_e_per_mm'] for s in samples_report) - min(s['pretop_long_line_median_e_per_mm'] for s in samples_report) < .00001
    result = json.loads((WORK / 'slice/result.json').read_text())
    assert result['return_code'] == 0
    write_zip(TARGET, files)
    read_zip(TARGET)
    report = dict(project=TARGET.name, project_sha256=sha(TARGET), production_hashes_unchanged=manifest['production_hashes'],
        dimensions_mm=[50, 25, 4.2], layer_count=21, pause_before_layer=21, completed_height_at_pause_mm=4.0,
        top_layer_height_mm=4.2, filament_slot=3, base_filament_flow_ratio=.96, top_layers=8, ironing=False,
        samples=samples_report, toolpath_audit=audit, slicer_result=result,
        limitations=['A small flat coupon may not reproduce the full part.',
                    'The inspection pause cools the surface; keep it brief and consistent.',
                    'Solid vs gyroid changes the interior structure, not just a numeric density.',
                    'These comparisons narrow the cause; they do not uniquely diagnose it.'])
    REPORT.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(dict(project=str(TARGET), report=str(REPORT), result=result), indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['stage', 'slice', 'publish'])
    command = parser.parse_args().command
    {'stage': stage, 'slice': slice_project, 'publish': publish}[command]()
