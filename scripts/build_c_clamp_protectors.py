"""Build the user-requested 12-piece A1 clamp-shoe plate without changing production."""
import hashlib
import json
import math
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.work/python-libs'))
import numpy as np
import trimesh
from build_jointed_bambu_project import P, R, IDENTITY, model, tag, meta, uid, xml, mesh_object
from remove_unused_project_filaments import compact_settings
from apply_sunlu_pla_profiles import compare, locks
from colorize_print_project import read_mesh
from validate_print_project import transform, props, nearest_error, scan_gcode

OUT = ROOT / 'output/C-Clamp Protectors A1'
WORK = ROOT / '.work/c-clamp-protectors-a1'
PROJECT = OUT / 'C-Clamp Protectors - 12 - A1.3mf'
SOURCE = ROOT / 'Small Parts.3mf'
PRESET = Path(os.environ['APPDATA']) / 'BambuStudio/user/2065895616/filament/base/SUNLU PLA Basic @Bambu Lab A1 0.4 nozzle.json'
EXE = Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe')
DIAMETER, HOLE, HEIGHT, DEPTH = np.array([.500, .420, .300, .150]) * 25.4
FLOOR = HEIGHT - DEPTH
TITLE = 'C-Clamp Protectors - A1 - 8% gyroid'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def read(path):
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        return {n: z.read(n) for n in z.namelist()}


def write(path, files):
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in files.items():
            z.writestr(name, data)


def native(source, folder, slice_it):
    folder.mkdir(exist_ok=True)
    args = ['--slice', '0'] if slice_it else ['--info']
    with (folder / 'run.log').open('w') as log:
        result = subprocess.run([str(EXE), *args, '--export-3mf', 'project.3mf',
            '--outputdir', str(folder), str(source)], cwd=EXE.parent,
            stdout=log, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
    result.check_returncode()
    outcome = json.loads((folder / 'result.json').read_text())
    assert outcome['return_code'] == 0, outcome
    return folder / 'project.3mf', outcome


def audit():
    report = json.loads((OUT / 'validation.json').read_text())
    reference = trimesh.load_mesh(OUT / 'C-Clamp Protector.stl')
    checks = []
    for path in [PROJECT, WORK/'reopen/project.3mf']:
        package = read(path)
        root = ET.fromstring(package['3D/3dmodel.model'])
        cfg = ET.fromstring(package['Metadata/model_settings.config'])
        max_error = 0.
        for item in root.find(tag('build')):
            oid = item.get('objectid')
            co = cfg.find(f"object[@id='{oid}']")
            number = int(props(co)['name'].split()[-1])
            assert props(co)['extruder'] == '1'
            obj = root.find(tag('resources')).find(f"{tag('object')}[@id='{oid}']")
            component = obj.find(tag('components'))[0]
            child = ET.fromstring(package[component.get('{' + P + '}path').lstrip('/')])
            m = read_mesh(child.find(tag('resources')).find(f"{tag('object')}[@id='{component.get('objectid')}']"))
            m.apply_transform(transform(component.get('transform')))
            m.apply_transform(transform(item.get('transform')))
            m.apply_translation(-np.array(report['centers_mm'][number-1]))
            assert m.is_volume and len(m.split()) == 1
            assert len(m.faces) == len(reference.faces)
            error = max(nearest_error(reference.vertices, m.vertices), nearest_error(m.vertices, reference.vertices))
            assert error < .00002, (path, number, error)
            max_error = max(max_error, error)
        checks.append(dict(path=str(path), all_12_meshes_and_poses_match=True, max_vertex_error_mm=max_error))
    package = read(PROJECT)
    graw = package['Metadata/plate_1.gcode']
    assert hashlib.md5(graw).hexdigest().upper() == package['Metadata/plate_1.gcode.md5'].decode().strip()
    gcode = graw.decode()
    config = dict(re.findall(r'^; ([^\r\n=]+) = ([^\r\n]*)', gcode, re.M))
    for key, value in locks('C-Clamp Protectors').items():
        assert config[key] == (','.join(value) if isinstance(value, list) else value), (key, config[key])
    assert config['printer_model'] == 'Bambu Lab A1'
    assert config['filament_colour'] == '#FFFFFF'
    assert config['filament_settings_id'].strip('"') == 'SUNLU PLA Basic @Bambu Lab A1 0.4 nozzle'
    scan = scan_gcode(gcode)
    assert scan['conservative_bed_edge_clearance_mm'] > 60
    assert not any('Support' in f for f in scan['features'])
    assert set(scan['model_extrusion_z_by_filament_mm']) == {'1'}
    assert np.allclose(scan['model_extrusion_z_by_filament_mm']['1'], np.arange(1,39)*.2)

    # Inspect actual upper-wall line segments for an open bore on every piece.
    x = y = z = 0.
    width, feature, obj = .42, 'Custom', None
    ring_ids, floor_ids = set(), set()
    minimum_bore_radius = math.inf
    for raw in gcode.splitlines():
        if raw.startswith('; start printing object, unique label id: '):
            obj = int(raw.split(': ')[1])
        elif raw.startswith('; stop printing object'):
            obj = None
        elif raw.startswith('; FEATURE: '):
            feature = raw.split(': ')[1]
        elif raw.startswith('; LINE_WIDTH: '):
            width = float(raw.split(': ')[1])
        code = raw.split(';')[0].strip()
        if not code:
            continue
        command = code.split()[0]
        if command not in ('G0', 'G1', 'G2', 'G3'):
            continue
        values = {k: float(v) for k,v in re.findall(r'([XYZEIJ])([+-]?(?:\d+(?:\.\d*)?|\.\d+))', code)}
        nx, ny, nz = values.get('X', x), values.get('Y', y), values.get('Z', z)
        if obj and values.get('E', 0) > 0 and ('X' in values or 'Y' in values) and feature != 'Custom':
            center = np.array(report['centers_mm'][obj-1][:2])
            a, b = np.array([x,y])-center, np.array([nx,ny])-center
            d = b-a
            t = np.clip(-np.dot(a,d)/max(np.dot(d,d),1e-20), 0, 1)
            radius = float(np.linalg.norm(a+t*d))
            if nz > FLOOR + .01:
                assert command == 'G1', 'Upper-wall arc requires a separate arc-distance check'
                bead_radius = radius-width/2
                assert bead_radius > HOLE/2-.04, (obj,nz,bead_radius)
                minimum_bore_radius = min(minimum_bore_radius, bead_radius)
                ring_ids.add(obj)
            elif abs(nz-3.8) < .001 and radius < 1 and feature == 'Top surface':
                floor_ids.add(obj)
        x,y,z = nx,ny,nz
    assert ring_ids == set(range(1,13)) and floor_ids == set(range(1,13)), (ring_ids,floor_ids)
    info = ET.fromstring(package['Metadata/slice_info.config'])
    slice_meta = props(info.find('plate'))
    report.update(geometry_roundtrip=checks, gcode_checksum_passed=True, gcode_audit=scan,
        blind_bores_verified_in_all_12_toolpaths=True, minimum_toolpath_bore_radius_mm=minimum_bore_radius,
        sliced_top_mm=7.6, sliced_floor_top_mm=3.8, sliced_hole_depth_mm=3.8,
        estimated_total_time_seconds=int(slice_meta['prediction']), estimated_filament_g=float(slice_meta['weight']),
        native_notices=[w.attrib for w in info.iter('warning')],
        native_notices_explanation='Only traditional timelapse compatibility notices; no geometry or slicing warnings.')
    (OUT/'Plate preview.png').write_bytes(package['Metadata/plate_1.png'])
    save(OUT/'validation.json',report)
    (OUT/'README.txt').write_text(f'''C-Clamp Protectors - 12 - A1.3mf
Open as a project in Bambu Studio. One freshly sliced plate; 12 separate pieces.
White SUNLU PLA Basic @Bambu Lab A1 0.4 nozzle. Textured PEI plate.
Nominal: 0.500 inch OD, 0.420 inch blind bore, 0.150 inch bore depth, 0.300 inch height.
Metric: 12.700 mm OD, 10.668 mm bore, 3.810 mm bore depth, 7.620 mm height.
Side wall: 1.016 mm; floor: 3.810 mm. No additional fit clearance.
0.20 mm layers, 4 walls, 5 top/bottom layers, 8% gyroid; infill first off.
220 C nozzle / 65 C bed. Source 5 mm outer brims with 0.10 mm gap retained.
No generated supports or prime tower. 38 layers: sliced top 7.60 mm, floor 3.80 mm.
Estimated total time: 28 min 35 sec. Filament including brims: 8.23 g.
Native slice, native reopen, all 12 mesh/pose comparisons and bore toolpath checks pass.
Only traditional-timelapse compatibility notices are stored in the native slice.
Physical clamp fit and compression performance are not yet verified. No print was sent.
Project SHA-256: {sha(PROJECT)}
''', encoding='utf-8')
    print('Audit passed: 12 open blind bores, all meshes/poses preserved, 38 white-only layers, 8.23 g, 28m35s.')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    protected = {p.name: sha(p) for p in ROOT.glob('*.3mf')}
    original = read(SOURCE)
    before = json.loads(original['Metadata/project_settings.config'])
    # Newer machine profiles have a compatibility list unrelated to slot count.
    slot_source = dict(before)
    compatible = slot_source.pop('upward_compatible_machine', None)
    settings = compact_settings(slot_source, [0])
    if compatible is not None:
        settings['upward_compatible_machine'] = compatible
    preset = json.loads(PRESET.read_text())
    differences, compared = compare(settings, preset, 0)
    assert not differences, differences
    settings.update(print_settings_id=TITLE, enable_prime_tower='0', print_sequence='by layer')
    settings['wipe_tower_x'] = settings['wipe_tower_x'][:1]
    settings['wipe_tower_y'] = settings['wipe_tower_y'][:1]
    assert settings['filament_colour'] == ['#FFFFFF']
    assert settings['enable_support'] == '0'
    assert settings['printer_model'] == 'Bambu Lab A1'
    for key, value in locks('C-Clamp Protectors').items():
        assert settings[key] == value, (key, settings[key])

    # A smooth cylindrical cup: blind bore, flat bottom, no unrequested clearance.
    profile = np.array([[0, 0], [DIAMETER/2, 0], [DIAMETER/2, HEIGHT],
        [HOLE/2, HEIGHT], [HOLE/2, FLOOR], [0, FLOOR]])
    mesh = trimesh.creation.revolve(profile, sections=256)
    assert mesh.is_volume and mesh.is_watertight and mesh.is_winding_consistent
    assert len(mesh.split()) == 1
    assert np.allclose(mesh.bounds, [[-DIAMETER/2, -DIAMETER/2, 0], [DIAMETER/2, DIAMETER/2, HEIGHT]])
    expected_volume = math.pi/4 * (DIAMETER**2 * HEIGHT - HOLE**2 * DEPTH)
    assert abs(mesh.volume / expected_volume - 1) < .00011
    mesh.export(OUT / 'C-Clamp Protector.stl')
    (OUT / 'C-Clamp Protector.scad').write_text('''// Dimensions in inches, converted exactly to millimeters.
inch = 25.4;
outer_diameter = 0.500 * inch;
hole_diameter = 0.420 * inch;
height = 0.300 * inch;
hole_depth = 0.150 * inch;
$fn = 256;
difference() {
    cylinder(d = outer_diameter, h = height);
    translate([0, 0, height - hole_depth])
        cylinder(d = hole_diameter, h = hole_depth + 0.01);
}
''', encoding='utf-8')

    root = model()
    del root.attrib['xmlns:p']
    for k, v in [('Application', 'BambuStudio-02.08.02.61'), ('BambuStudio:3mfVersion', '1'),
                 ('Title', TITLE), ('Description', '12 clamp protectors; 0.500 OD, 0.420 blind bore, 0.150 bore depth, 0.300 thickness (inches).')]:
        ET.SubElement(root, tag('metadata'), name=k).text = v
    resources = ET.SubElement(root, tag('resources'))
    build = ET.SubElement(root, tag('build'), attrib={'{' + P + '}UUID': uid()})
    config = ET.Element('config')
    rels = ET.Element('Relationships', xmlns=R)
    files = {k: original[k] for k in ['[Content_Types].xml', '_rels/.rels']}
    # Remove stale thumbnails and any other source-package relationships.
    package_rels = ET.Element('Relationships', xmlns=R)
    ET.SubElement(package_rels, 'Relationship', Target='/3D/3dmodel.model', Id='rel-1',
        Type='http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel')
    files['_rels/.rels'] = xml(package_rels)
    plate = ET.SubElement(config, 'plate')
    for k, v in [('plater_id', 1), ('plater_name', '12 white C-clamp protectors'), ('locked', 'false'),
                 ('filament_map_mode', 'Auto For Flush'), ('filament_maps', '1'), ('filament_volume_maps', '0')]:
        meta(plate, k, v)
    centers = []
    for i in range(12):
        oid = 1000 + i*10
        name = f'C-clamp protector {i+1:02d}'
        center = [89 + (i % 4)*26, 102 + (i // 4)*26, 0]
        centers.append(center)
        child = model()
        mesh_object(ET.SubElement(child, tag('resources')), oid+1, mesh)
        path = f'3D/Objects/protector_{i+1:02d}.model'
        files[path] = xml(child)
        obj = ET.SubElement(resources, tag('object'), id=str(oid), type='model', attrib={'{' + P + '}UUID': uid()})
        ET.SubElement(ET.SubElement(obj, tag('components')), tag('component'), objectid=str(oid+1),
            transform=IDENTITY, attrib={'{' + P + '}path': '/' + path, '{' + P + '}UUID': uid()})
        ET.SubElement(rels, 'Relationship', Target='/' + path, Id=f'rel-{i+1}',
            Type='http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel')
        ET.SubElement(build, tag('item'), objectid=str(oid), printable='1',
            transform=IDENTITY.rsplit(' ', 3)[0] + ' ' + ' '.join(map(str, center)),
            attrib={'{' + P + '}UUID': uid()})
        co = ET.SubElement(config, 'object', id=str(oid))
        meta(co, 'name', name)
        meta(co, 'extruder', 1)
        part = ET.SubElement(co, 'part', id=str(oid+1), subtype='normal_part')
        meta(part, 'name', name)
        ET.SubElement(part, 'mesh_stat', face_count=str(len(mesh.faces)), edges_fixed='0', degenerate_facets='0',
            facets_removed='0', facets_reversed='0', backwards_edges='0')
        inst = ET.SubElement(plate, 'model_instance')
        for k, v in [('object_id', oid), ('instance_id', 0), ('identify_id', i+1)]:
            meta(inst, k, v)
    files.update({'3D/3dmodel.model': xml(root), '3D/_rels/3dmodel.model.rels': xml(rels),
        'Metadata/model_settings.config': xml(config), 'Metadata/project_settings.config': json.dumps(settings, indent=2).encode()})
    editable = WORK / 'editable.3mf'
    write(editable, files)
    report = dict(date='2026-10-30', source_project=str(SOURCE), source_sha256=sha(SOURCE),
        local_filament_preset=str(PRESET), preset_sha256=sha(PRESET), compared_preset_options=len(compared),
        dimensions_mm=dict(outside_diameter=DIAMETER, hole_diameter=HOLE, total_height=HEIGHT,
                           hole_depth=DEPTH, floor_thickness=FLOOR, radial_wall=(DIAMETER-HOLE)/2),
        hole_clearance_added_mm=0, quantity=12, plates=1, orientation='Flat floor on bed; blind bore faces up.',
        geometry=dict(watertight=True, connected_components_per_piece=1, triangles_per_piece=len(mesh.faces),
            volume_per_piece_mm3=mesh.volume, maximum_circle_chord_error_mm=DIAMETER/2*(1-math.cos(math.pi/256))),
        centers_mm=centers, minimum_part_gap_mm=26-DIAMETER,
        project_setting_changes={k: dict(before=before.get(k), after=v) for k,v in settings.items() if before.get(k) != v},
        protected_projects=protected, printer_job_sent=False, physical_fit_verified=False)
    save(OUT / 'validation.json', report)
    print('Built 12 watertight cups; slicing with native Bambu Studio.', flush=True)
    sliced, outcome = native(editable, WORK/'native', True)
    report['native_slice'] = outcome
    shutil.copyfile(sliced, PROJECT)
    reopened, outcome = native(PROJECT, WORK/'reopen', False)
    report['native_reopen'] = outcome
    for path in [editable, PROJECT, reopened]:
        package = read(path)
        saved = json.loads(package['Metadata/project_settings.config'])
        for key, value in locks('C-Clamp Protectors').items():
            assert saved[key] == value, (str(path), key, saved[key])
        diff, _ = compare(saved, preset, 0)
        assert not diff, (str(path), diff)
        assert saved['filament_colour'] == ['#FFFFFF']
        assert saved['printer_model'] == 'Bambu Lab A1'
        cfg = ET.fromstring(package['Metadata/model_settings.config'])
        assert len(cfg.findall('plate')) == 1
        assert len(cfg.findall('object')) == 12
        assert len(cfg.find('plate').findall('model_instance')) == 12
    assert protected == {n: sha(ROOT/n) for n in protected}
    assert report['preset_sha256'] == sha(PRESET)
    report.update(project_sha256=sha(PROJECT), protected_projects_unchanged=True,
        native_reopen_passed=True, native_slice_passed=True)
    save(OUT / 'validation.json', report)
    print(PROJECT)
    print(json.dumps(outcome, indent=2))
    audit()


if __name__ == '__main__':
    audit() if '--validate' in sys.argv else main()
