"""Create and natively slice a three-piece photo-edge fit test from current CAD."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET
import zipfile

from build_jointed_bambu_project import (
    ROOT, P, R, IDENTITY, cylinder, mesh_object, meta, model, tag, uid, xml,
    np, trimesh,
)
from validate_print_project import scan_gcode, props

WORK = ROOT / '.work/photo-fit-test'
OUTPUT = ROOT / 'output/photo-fit-test'
CAD = ROOT / 'working/Dara-Photo-Frame-A1-Jointed.scad'
PRODUCTION = ROOT / 'Dara.3mf'
OPENSCAD = Path(r'C:\Program Files (x86)\OpenSCAD\openscad.exe')
BAMBU = Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe')
TITLE = 'Photo rabbet, backer and retainer fit test'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_logged(args, log, cwd=None):
    with log.open('w', encoding='utf-8') as stream:
        result = subprocess.run([str(a) for a in args], stdout=stream,
                                stderr=subprocess.STDOUT, cwd=cwd,
                                creationflags=subprocess.CREATE_NO_WINDOW)
    result.check_returncode()


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    production_hash = digest(PRODUCTION)
    cad_hash = digest(CAD)
    native = WORK / 'Photo-Fit-Sample.stl'
    run_logged([OPENSCAD, '--hardwarnings', '--export-format=binstl', '--camera=0,0,0,0,0,0,170',
                '-D', 'fast_preview=false', '-D', 'view_mode="fit_sample"',
                '-o', native, CAD], WORK / 'openscad.log')
    assert 'WARNING:' not in (WORK / 'openscad.log').read_text()
    solids = trimesh.load_mesh(native).split(only_watertight=False)
    assert len(solids) == 3 and all(m.is_volume for m in solids)
    frame = next(m for m in solids if m.extents[2] > 10)
    backer = next(m for m in solids if m.extents[2] < 2)
    retainer = next(m for m in solids if 2 < m.extents[2] < 4)
    assert np.allclose(frame.extents, [18, 20, 13.5], atol=1e-5)
    assert np.allclose(backer.extents, [13.7, 18, 1.6], atol=1e-5)
    assert np.allclose(retainer.extents, [20, 10, 3], atol=1e-5)
    assert np.allclose(sorted(set(frame.vertices[:, 2])), [0, 2.4, 10.7, 13.5], atol=1e-5)
    with zipfile.ZipFile(PRODUCTION) as z:
        preset = json.loads(z.read('Metadata/project_settings.config'))
        files = {k: z.read(k) for k in ('[Content_Types].xml', '_rels/.rels')}
        source_config = ET.fromstring(z.read('Metadata/model_settings.config'))
        source_slice = ET.fromstring(z.read('Metadata/slice_info.config'))
        printer_id = props(source_slice.find('plate'))['printer_model_id']
        assert printer_id and preset['printer_model'] == 'Bambu Lab A1'
    frame_settings = props(next(o for o in source_config.findall('object')
                                if props(o).get('name', '').startswith('F1 -')))
    frame_settings.pop('name')
    frame_settings.pop(None, None)
    preset.update(print_settings_id=TITLE, enable_prime_tower='0', print_sequence='by layer')
    files['Metadata/project_settings.config'] = json.dumps(preset, indent=2).encode()
    root = model()
    del root.attrib['xmlns:p']
    for k, v in [('Application', 'BambuStudio-02.08.02.61'), ('BambuStudio:3mfVersion', '1'),
                 ('Title', TITLE), ('Description', 'Current 2.4 mm rabbet; 1.6 mm backer; 3 mm rotating tab. All at 100% scale.')]:
        ET.SubElement(root, tag('metadata'), name=k).text = v
    resources = ET.SubElement(root, tag('resources'))
    build = ET.SubElement(root, tag('build'), attrib={'{' + P + '}UUID': uid()})
    config = ET.Element('config')
    rels = ET.Element('Relationships', xmlns=R)
    entries = [
        ('Photo-Rabbet-2.4mm', frame, [100, 128],
         [('100% photo pilot - D14', cylinder([9.5, 0], 14, 13.5))]),
        ('Photo-Backer-1.6mm', backer, [128, 128], []),
        ('Photo-Retainer-3mm', retainer, [156, 128],
         [('100% retainer screw seat - D12', cylinder([9.5, 24], 12, 3))]),
    ]
    records = []
    for i, (name, mesh, xy, modifiers) in enumerate(entries, 1):
        origin = np.r_[(mesh.bounds[0, :2] + mesh.bounds[1, :2]) / 2, mesh.bounds[0, 2]]
        mesh.apply_translation(-origin)
        for _, modifier in modifiers:
            modifier.apply_translation(-origin)
            assert trimesh.boolean.intersection([mesh, modifier], engine='manifold').volume > 1
        assert abs(mesh.bounds[0, 2]) < 1e-5
        mesh.export(OUTPUT / (name + '.stl'))
        oid = i * 1000
        path = f'3D/Objects/{name}.model'
        child = model()
        child_res = ET.SubElement(child, tag('resources'))
        obj = ET.SubElement(resources, tag('object'), id=str(oid), type='model', attrib={'{' + P + '}UUID': uid()})
        comps = ET.SubElement(obj, tag('components'))
        obj_config = ET.SubElement(config, 'object', id=str(oid))
        settings = frame_settings if i == 1 else dict(enable_support='0', brim_type='no_brim', extruder='1')
        for k, v in dict(settings, name=name).items():
            meta(obj_config, k, v)
        for j, (part_name, part_mesh) in enumerate([(name, mesh)] + modifiers, 1):
            pid = oid + j
            mesh_object(child_res, pid, part_mesh)
            ET.SubElement(comps, tag('component'), objectid=str(pid), transform=IDENTITY,
                          attrib={'{' + P + '}path': '/' + path, '{' + P + '}UUID': uid()})
            part = ET.SubElement(obj_config, 'part', id=str(pid), subtype='normal_part' if j == 1 else 'modifier_part')
            meta(part, 'name', part_name)
            if j > 1:
                meta(part, 'sparse_infill_density', '100%')
                meta(part, 'sparse_infill_pattern', 'cubic')
            ET.SubElement(part, 'mesh_stat', face_count=str(len(part_mesh.faces)), edges_fixed='0',
                          degenerate_facets='0', facets_removed='0', facets_reversed='0', backwards_edges='0')
        files[path] = xml(child)
        ET.SubElement(rels, 'Relationship', Target='/' + path, Id=f'rel-{i}',
                      Type='http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel')
        ET.SubElement(build, tag('item'), objectid=str(oid), printable='1',
                      transform=f'1 0 0 0 1 0 0 0 1 {xy[0]} {xy[1]} 0', attrib={'{' + P + '}UUID': uid()})
        records.append(dict(name=name, size_mm=mesh.extents.tolist(), triangles=len(mesh.faces),
                            watertight=bool(mesh.is_volume), xy=xy, bounds=(mesh.bounds + [*xy, 0]).tolist()))
    plate = ET.SubElement(config, 'plate')
    for k, v in [('plater_id', 1), ('plater_name', TITLE), ('locked', 'false'),
                 ('filament_map_mode', 'Auto For Flush'), ('filament_maps', '1 1 1 1'), ('filament_volume_maps', '0 0 0 0')]:
        meta(plate, k, v)
    for i in range(1, 4):
        instance = ET.SubElement(plate, 'model_instance')
        for k, v in [('object_id', i * 1000), ('instance_id', 0), ('identify_id', 100 + i)]:
            meta(instance, k, v)
    files.update({'3D/3dmodel.model': xml(root), '3D/_rels/3dmodel.model.rels': xml(rels),
                  'Metadata/model_settings.config': xml(config)})
    staged = WORK / 'staged.3mf'
    with zipfile.ZipFile(staged, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in files.items():
            z.writestr(name, data)
    print('Generated current CAD and staged three objects; slicing in Bambu Studio.', flush=True)
    sliced = WORK / 'slice'
    sliced.mkdir(exist_ok=True)
    run_logged([BAMBU, '--slice', '1', '--export-3mf', 'Dara-Photo-Fit-Test.3mf',
                '--outputdir', sliced, staged], WORK / 'slice.log', BAMBU.parent)
    result = sliced / 'Dara-Photo-Fit-Test.3mf'
    with zipfile.ZipFile(result) as z:
        assert z.testzip() is None
        final_files = {n: z.read(n) for n in z.namelist()}
        final_config = ET.fromstring(z.read('Metadata/model_settings.config'))
        assert len(final_config.findall('plate')) == 1 and len(final_config.findall('object')) == 3
        assert all(props(o)['extruder'] == '1' for o in final_config.findall('object'))
        final_root = ET.fromstring(z.read('3D/3dmodel.model'))
        final_objects = {o.get('id'): o for o in final_root.find(tag('resources')).findall(tag('object'))}
        for obj in final_config.findall('object'):
            part_id = obj.find('part').get('id')
            component = next(c for c in final_objects[obj.get('id')].find(tag('components'))
                             if c.get('objectid') == part_id)
            child = ET.fromstring(z.read(component.get('{' + P + '}path').lstrip('/')))
            part = next(o for o in child.find(tag('resources')) if o.get('id') == part_id)
            vertices = np.array([[float(v.get(k)) for k in ('x', 'y', 'z')]
                                 for v in part.find(tag('mesh')).find(tag('vertices'))])
            record = next(r for r in records if r['name'] == props(obj)['name'])
            assert np.allclose(np.ptp(vertices, axis=0), record['size_mm'], atol=1e-4)
        gcode = z.read('Metadata/plate_1.gcode').decode()
        audit = scan_gcode(gcode)
        assert audit['conservative_bed_edge_clearance_mm'] > 3
        assert set(audit['model_extrusion_z_by_filament_mm']) == {'1'}
        assert audit['features'].get('Support interface', 0) > 0
        info = ET.fromstring(z.read('Metadata/slice_info.config'))
        info.find("plate/metadata[@key='printer_model_id']").set('value', printer_id)
        final_files['Metadata/slice_info.config'] = xml(info)
        slice_metadata = props(info.find('plate'))
        for entry in z.namelist():
            if entry.endswith('.png') and 'plate_1' in entry:
                (OUTPUT / Path(entry).name).write_bytes(z.read(entry))
    assert digest(PRODUCTION) == production_hash and digest(CAD) == cad_hash
    target = OUTPUT / result.name
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in final_files.items():
            z.writestr(name, data)
    report = dict(all_passed=True, source_project_sha256=production_hash, cad_sha256=cad_hash,
                  project_sha256=digest(target), parts=records, rabbet_depth_mm=2.4,
                  backer_thickness_mm=1.6, photo_and_surface_allowance_mm=0.8,
                  edge_clearance_mm=0.3, screw_pilot_diameter_mm=3.175,
                  screw_pilot_depth_mm=10.7, tab_clearance_hole_diameter_mm=4,
                  screw='#6-19 x 1/2 inch pan-head', native_slice=slice_metadata,
                  toolpath_check=audit, physical_fit_tested=False)
    (OUTPUT / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    headers = [line for line in gcode.splitlines() if re.match(r'; (estimated printing time|total filament weight|total layer number)', line)]
    print(json.dumps(dict(project=str(target), slice=slice_metadata, estimates=headers, verified=True), indent=2))


if __name__ == '__main__':
    main()
