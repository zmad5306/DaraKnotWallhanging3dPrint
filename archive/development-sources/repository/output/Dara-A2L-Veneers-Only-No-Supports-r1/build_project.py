"""Extract the saved A2L veneers, trim carrier stock, and disable all supports.

Production inputs are read-only. No geometry is regenerated from CAD.
"""
import copy
import hashlib
import json
import math
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / '.work/python-libs'), str(ROOT / 'scripts')]
import numpy as np
import trimesh
import shapely
from shapely.geometry import shape
from scipy.spatial import cKDTree
import development_3mf as d
from development_3mf import solid, mesh, sha, tag, transform, props, mesh_xml, xml, P

OUT = Path(__file__).resolve().parent
SOURCE = ROOT / 'Dara.3mf'
FINAL = OUT / 'Dara-A2L-Veneers-Only-No-Supports-r1.3mf'
GEOMETRY = ROOT / 'working/bambu/Dara-Photo-Frame-A2L/M-geometry-validation.json'


def protected():
    paths = [SOURCE, ROOT / 'working/bambu/Dara-Photo-Frame-A2L/Dara-A2L-Complete.3mf',
             ROOT / 'working/bambu/Dara-Photo-Frame-A2L/Dara-A2L-Editable.3mf']
    paths += sorted((ROOT / 'working/bambu/Dara-A1-Companion').glob('*'))
    return {str(p.relative_to(ROOT)): sha(p) for p in paths if p.is_file()}


def setmeta(element, key, value):
    found = next((m for m in element.findall('metadata') if m.get('key') == key), None)
    if found is None:
        found = ET.SubElement(element, 'metadata', key=key)
    found.set('value', str(value))


def main():
    before = protected()
    evidence = json.loads(GEOMETRY.read_text())
    plan_path = GEOMETRY.with_name('production-plan.json')
    plan = json.loads(plan_path.read_text())
    assert evidence['veneer_flat_back_mm'] == 8.6
    rear_z = evidence['veneer_flat_back_mm']
    records = []
    with zipfile.ZipFile(SOURCE) as z:
        model = ET.fromstring(z.read('3D/3dmodel.model'))
        cfg = ET.fromstring(z.read('Metadata/model_settings.config'))
        settings = json.loads(z.read('Metadata/project_settings.config'))
        source_settings = copy.deepcopy(settings)
        resources = model.find(tag('resources'))
        build = model.find(tag('build'))
        source_plates = cfg.findall('plate')
        source_columns = math.ceil(math.sqrt(len(source_plates)))
        area = np.array([[float(x) for x in s.split('x')] for s in settings['printable_area']])
        pitch = np.ptp(area, axis=0) * 1.2
        new_cfg = ET.Element('config')
        retained_ids = []
        files = {n: z.read(n) for n in ['[Content_Types].xml', '_rels/.rels']}
        relationships = ET.fromstring(z.read('3D/_rels/3dmodel.model.rels'))
        retained_paths = []
        for number in (1, 2, 3):
            config = next(o for o in cfg.findall('object')
                          if props(o).get('name', '').startswith(f'V{number} A2L'))
            oid = config.get('id')
            retained_ids.append(oid)
            obj = next(o for o in resources if o.get('id') == oid)
            components = list(obj.find(tag('components')))
            assert len(components) == 1
            co = components[0]
            path = co.get('{' + P + '}path').lstrip('/')
            retained_paths.append(path)
            child = ET.fromstring(z.read(path))
            child_resources = child.find(tag('resources'))
            child_obj = next(o for o in child_resources if o.get('id') == co.get('objectid'))
            source_mesh = child_obj.find(tag('mesh'))
            vertices = np.array([[float(v.get(k)) for k in ('x', 'y', 'z')]
                                 for v in source_mesh.find(tag('vertices'))])
            triangles = source_mesh.find(tag('triangles'))
            # The saved support blockers are irrelevant with supports off;
            # reject any unhandled per-face material painting.
            assert all(set(t.attrib) <= {'v1', 'v2', 'v3', 'paint_supports'} for t in triangles)
            faces = np.array([[int(f.get(k)) for k in ('v1', 'v2', 'v3')] for f in triangles])
            original = trimesh.Trimesh(vertices, faces, process=False)
            item = next(i for i in build if i.get('objectid') == oid)
            pi = next(i for i, p in enumerate(source_plates)
                      if any(props(inst).get('object_id') == oid for inst in p.findall('model_instance')))
            assert pi + 1 == number + 14
            build_t = transform(item.get('transform'))
            build_t[:2, 3] -= [pi % source_columns * pitch[0], -(pi // source_columns) * pitch[1]]
            component_t = transform(co.get('transform'))
            original.apply_transform(build_t @ component_t)
            pose = np.array(evidence['skins'][number - 1]['assembly_to_printer'])
            normal = pose[:3, 2]
            assert np.allclose(pose[:3, :3], evidence['common_complete_rotation'])
            assert abs(math.degrees(math.acos(normal[2])) - 55) < 1e-9
            assembly = original.vertices @ pose[:3, :3] - pose[:3, 3] @ pose[:3, :3]
            rear_errors = np.abs(assembly[:, 2] - rear_z)
            assert np.count_nonzero(rear_errors < 0.00002) > 100
            body = solid(original)
            offset = float(normal @ pose[:3, 3] + rear_z)
            veneer = body.trim_by_plane(normal, offset)
            components_after = veneer.decompose()
            # The ground perimeter may cross the infinite rear plane outside
            # the artwork. Select the complete veneer, then independently
            # prove every other component is outside its saved footprint.
            region = shape(plan['skin_regions'][number - 1])
            components_after.sort(key=lambda c: c.volume(), reverse=True)
            discarded = []
            for component in components_after[1:]:
                cm = mesh(component)
                cv = (cm.vertices - pose[:3, 3]) @ pose[:3, :3]
                separation = shapely.distance(shapely.points(cv[:, :2]), region)
                assert separation.min() > 0.001, ('Unexpected detached veneer material', separation.min(), component.volume())
                discarded.append(dict(volume_mm3=component.volume(),minimum_vertex_distance_from_veneer_mm=float(separation.min())))
            veneer = components_after[0]
            components_after = [veneer]
            finished = mesh(veneer)
            assert finished.is_volume and finished.is_watertight
            finished_assembly = (finished.vertices - pose[:3, 3]) @ pose[:3, :3]
            outline_error = float(shapely.distance(shapely.points(finished_assembly[:, :2]), region).max())
            assert outline_error < 0.00002, ('Source veneer differs from recorded region', outline_error)
            # The original decorative and seating surfaces must survive the
            # operation unchanged. Only the rear-plane intersection is new.
            within = shapely.intersects_xy(region.buffer(0.00002), assembly[:, 0], assembly[:, 1])
            keep_points = original.vertices[(assembly[:, 2] > rear_z + 0.00002) & within]
            retained_error = float(cKDTree(finished.vertices).query(keep_points)[0].max())
            assert retained_error < 0.00002, retained_error
            remaining_rear = (finished.vertices - pose[:3, 3]) @ normal
            assert remaining_rear.min() >= rear_z - 0.00002
            z_drop = -float(finished.bounds[0, 2])
            finished.apply_translation([0, 0, z_drop])
            assert abs(finished.bounds[0, 2]) < 1e-8
            assert np.all(finished.bounds[0] >= -1e-7)
            assert np.all(finished.bounds[1] <= [330, 320, 325])
            new_name = f'V{number} A2L hammered veneer - no supports'
            child_resources.remove(child_obj)
            mesh_xml(child_resources, int(co.get('objectid')), finished)
            files[path] = xml(child)
            co.set('transform', '1 0 0 0 1 0 0 0 1 0 0 0')
            new_t = np.eye(4)
            new_pi = number - 1
            new_t[:2, 3] = [new_pi % 2 * pitch[0], -(new_pi // 2) * pitch[1]]
            item.set('transform', ' '.join(format(float(v), '.12g') for v in new_t[:3].T.reshape(-1)))
            obj_settings = {k: v for k, v in props(config).items() if k}
            setmeta(config, 'name', new_name)
            setmeta(config, 'enable_support', '0')
            parts = config.findall('part')
            assert len(parts) == 1 and parts[0].get('subtype') == 'normal_part'
            setmeta(parts[0], 'name', new_name)
            for m in list(parts[0].findall('metadata')):
                if m.get('key') in ('matrix', 'source_file', 'source_object_id', 'source_volume_id',
                                    'source_offset_x', 'source_offset_y', 'source_offset_z'):
                    parts[0].remove(m)
            if 'enable_support' in props(parts[0]):
                setmeta(parts[0], 'enable_support', '0')
            stat = parts[0].find('mesh_stat')
            stat.set('face_count', str(len(finished.faces)))
            new_cfg.append(config)
            plate = copy.deepcopy(source_plates[pi])
            for m in list(plate.findall('metadata')):
                if m.get('key') in ('gcode_file', 'thumbnail_file', 'thumbnail_no_light_file',
                                    'top_file', 'pick_file', 'pattern_bbox_file'):
                    plate.remove(m)
            setmeta(plate, 'plater_id', number)
            setmeta(plate, 'plater_name', f'{number} - V{number} veneer only - supports off')
            new_cfg.append(plate)
            records.append(dict(veneer=f'V{number}',source_plate=pi+1,source_object_id=oid,
                source_mesh_path=path,source_child_sha256=hashlib.sha256(z.read(path)).hexdigest(),
                source_object_settings=obj_settings,
                exported_object_settings={k:v for k,v in props(config).items() if k},
                assembly_to_printer_rotation=pose[:3,:3].tolist(),lean_degrees=55,
                carrier_cut_plane_assembly_z_mm=rear_z,added_geometry=False,
                preserved_surface_vertex_error_mm=retained_error,
                source_volume_mm3=body.volume(),veneer_volume_mm3=veneer.volume(),
                removed_carrier_volume_mm3=body.volume()-veneer.volume(),
                translation_after_fin_removal_mm=[0,0,z_drop],
                bounds_mm=finished.bounds.tolist(),watertight=bool(finished.is_watertight),
                connected_components=len(components_after),triangles=len(finished.faces)))
            records[-1]['detached_carrier_components_discarded'] = discarded
            print(f'V{number}: {len(finished.faces)} faces; watertight, one solid; bounds {finished.extents.round(3).tolist()}',flush=True)
        for o in list(resources):
            if o.get('id') not in retained_ids:
                resources.remove(o)
        for i in list(build):
            if i.get('objectid') not in retained_ids:
                build.remove(i)
        for rel in list(relationships):
            if rel.get('Target', '').lstrip('/') not in retained_paths:
                relationships.remove(rel)
        for m in model.findall(tag('metadata')):
            if m.get('name') == 'Title': m.text = 'Dara A2L - three veneers only, no supports'
            if m.get('name') == 'Description':
                m.text = 'Production veneers with carrier stock removed at rear plane; saved rotation; supports disabled by request.'
        settings['print_settings_id'] = 'Dara A2L veneers only - 8% gyroid; solid veneers; supports off'
        settings['enable_support'] = '0'
        for key in ('wipe_tower_x', 'wipe_tower_y'):
            settings[key] = [source_settings[key][i] for i in (14,15,16)]
        files['3D/3dmodel.model'] = xml(model)
        files['3D/_rels/3dmodel.model.rels'] = xml(relationships)
        files['Metadata/model_settings.config'] = xml(new_cfg)
        files['Metadata/project_settings.config'] = json.dumps(settings, indent=2).encode()
    # Serialize with the established native-compatible multi-plate writer.
    # In particular, relationship XML must use the unprefixed default
    # namespace expected by Bambu Studio's package reader.
    export_plates = []
    for config in new_cfg.findall('object'):
        parts, object_settings = d.read_object(files, config.get('id'))
        export_plates.append([dict(name=object_settings['name'],parts=parts,
            settings={k:v for k,v in object_settings.items() if k and k!='name'},
            transform=np.eye(4))])
    original_source, original_path = d.source, d.source_path
    try:
        d.source = lambda: files
        d.source_path = lambda: SOURCE
        d.write_project(FINAL,export_plates,'Dara A2L veneers only - no supports',settings_update=settings)
    finally:
        d.source, d.source_path = original_source, original_path
    differences = {k: {'before': source_settings.get(k), 'after': settings.get(k)}
                   for k in source_settings.keys() | settings.keys() if source_settings.get(k) != settings.get(k)}
    assert set(differences) <= {'print_settings_id','enable_support','wipe_tower_x','wipe_tower_y'}
    assert settings['sparse_infill_density'] == '8%' and settings['sparse_infill_pattern'] == 'gyroid'
    for record in records:
        old, new = record['source_object_settings'], record['exported_object_settings']
        assert {k for k in old.keys() | new.keys() if old.get(k) != new.get(k)} <= {'name','enable_support'}
        assert new['sparse_infill_density'] == '100%' and new['extruder'] == '3'
        assert new['enable_support'] == '0'
    assert protected() == before, 'Protected production inputs changed'
    report = dict(source_project=str(SOURCE),source_sha256=before['Dara.3mf'],
        project=FINAL.name,sha256=sha(FINAL),source_geometry_report_sha256=sha(GEOMETRY),
        footprint_reference_sha256=sha(plan_path),
        source_projects_unchanged=True,protected_sha256=before,
        requested_change='Remove all modeled carrier stock and disable all slicer supports',
        back_pockets_and_surface_texture_preserved=True,
        source_orientation_preserved=True,global_setting_differences=differences,
        native_slice_validated=False,physical_result_unknown=True,veneers=records)
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    (OUT/'README.txt').write_text(
        'Dara A2L - veneers only, no supports - r1\n\n'
        'Open Dara-A2L-Veneers-Only-No-Supports-r1.3mf as a project.\n'
        'Plate 1: V1 left; plate 2: V2 right; plate 3: V3 center.\n'
        'All three retain the saved 55-degree lean and in-plane rotation.\n'
        'The fins, starter ribs, feet and carrier are removed at the original rear plane (assembly Z8.6).\n'
        'The original texture, outline, mounting pockets and rear trim recesses remain.\n'
        'Only translation lowers each veneer to the bed after carrier removal.\n'
        'All slicer supports are disabled as explicitly requested.\n'
        'A2L / 0.4 mm nozzle / 0.20 mm layers / 4 walls / 5 top and bottom layers.\n'
        'Veneers: 100% solid, filament 3 copper silk. Global process remains 8% gyroid.\n'
        'Production projects are unchanged. This editable project contains no stored slices.\n'
        'Geometry verification does not establish unsupported printability or a successful physical print.\n'
        'Source and output SHA-256 and detailed checks are in validation.json.\n')
    print(str(FINAL), flush=True)
    print('SHA-256 '+report['sha256'],flush=True)


if __name__ == '__main__':
    main()
