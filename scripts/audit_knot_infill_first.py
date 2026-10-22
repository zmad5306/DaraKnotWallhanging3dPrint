"""Portable audit of the separate knot release and preserved main/M/A1 files."""
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'working/bambu/Dara-A2L-Knot-Infill-First'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def props(node):
    return {m.get('key'): m.get('value') for m in node.findall('metadata')}


def audit():
    report = json.loads((OUT / 'validation.json').read_text())
    provenance = json.loads((OUT / 'source-provenance.json').read_text())
    assert report['source_sha256'] == provenance['source_sha256'] == sha(ROOT / 'Dara.3mf')
    assert report['protected_before'] == report['protected_after'] == provenance['protected_before']
    for name, h in report['protected_after'].items():
        assert sha(ROOT / name) == h, name
    reference = report['physical_reference']
    assert sha(ROOT / reference['file']) == reference['sha256']
    assert report['native_reopen_result']['return_code'] == report['native_slice_result']['return_code'] == 0
    assert len(report['plates']) == 10 and len(report['removed_pad_toolpath_checks']) == 42
    assert all(p['maximum_model_z_mm'] == 4.8 for p in report['removed_pad_toolpath_checks'])
    for suffix, key in [('.3mf', 'project_sha256'), ('-Editable.3mf', 'editable_sha256')]:
        path = OUT / ('Dara-A2L-Knot-Infill-First' + suffix)
        assert sha(path) == report[key]
        with zipfile.ZipFile(path) as z:
            assert z.testzip() is None
            for name in (n for n in z.namelist() if n.endswith('.rels')):
                for rel in ET.fromstring(z.read(name)):
                    if rel.get('TargetMode') != 'External':
                        assert rel.get('Target').lstrip('/') in z.namelist(), (name, rel.attrib)
            settings = json.loads(z.read('Metadata/project_settings.config'))
            assert settings['printer_model'] == 'Bambu Lab A2L' and settings['nozzle_diameter'] == ['0.4']
            assert settings['is_infill_first'] == '1'
            assert settings['sparse_infill_density'] == '8%' and settings['sparse_infill_pattern'] == 'gyroid'
            assert settings['layer_height'] == settings['initial_layer_print_height'] == '0.2'
            assert settings['wall_loops'] == '4' and settings['top_shell_layers'] == settings['bottom_shell_layers'] == '5'
            assert settings['curr_bed_type'] == 'Textured PEI Plate'
            cfg = ET.fromstring(z.read('Metadata/model_settings.config'))
            assert len(cfg.findall('plate')) == len(cfg.findall('object')) == 10
            assert {props(o)['name'] for o in cfg.findall('object')} == {f'F{i} A2L knot' for i in range(1, 11)}
            assert all(props(o)['support_interface_spacing'] == '0.2' for o in cfg.findall('object'))
            if suffix != '.3mf':
                for name, h in provenance['child_mesh_assets_sha256'].items():
                    assert hashlib.sha256(z.read(name)).hexdigest() == h
                continue
            assert len([n for n in z.namelist() if re.fullmatch(r'Metadata/plate_\d+\.gcode', n)]) == 10
            for plate in report['plates']:
                name = f'Metadata/plate_{plate["plate"]}.gcode'
                raw = z.read(name)
                assert hashlib.sha256(raw).hexdigest() == plate['gcode_sha256']
                assert hashlib.md5(raw).hexdigest() == z.read(name + '.md5').decode().strip().lower()
                assert b'; is_infill_first = 1' in raw
                assert b'; sparse_infill_density = 8%' in raw and b'; sparse_infill_pattern = gyroid' in raw
                assert plate['max_native_mesh_and_pose_error_mm'] < .001
                assert plate['bed_clearance_mm'] > .5
                assert not plate['startup_tower']['intersects_model']
                assert plate['tower_clearance']['studio_model_convex_hull_clearance_mm'] > 8
                assert plate['tower_clearance']['actual_tower_to_other_extrusion_clearance_mm'] > 3
                if plate['first_supported_layer_order']:
                    assert plate['first_supported_layer_order']['bridge_before_first_overhang_wall']
    assert report['plates'][1]['first_supported_layer_order']['bridge_before_first_overhang_wall']
    assert sum(p['grams'] for p in report['plates']) == report['total_grams']
    print('PASS: ten native knot slices, exact release hashes, 8% gyroid, infill-first, corrected lap paths, main/M/A1 preserved.')


if __name__ == '__main__':
    audit()
