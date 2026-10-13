"""Verify native exports and stage repaired geometry in the existing 31 plates."""
import copy
import json
import re
import shutil
import xml.etree.ElementTree as ET

from repair_curve_artifacts import WORK, REVIEW
from validate_print_project import ROOT, CAD, STLS, digest, props, transform, nearest_error
from build_jointed_bambu_project import tag, P, xml, mesh_object, read_array
from add_weave_test_coupon import read_zip, write_zip, NAME
from add_blue_ribbon_edge import artwork, section, as_mesh, in_print_coordinates, coupon_shape, plot, GAP, WIDTH, BOTTOM, TOP
from export_jointed_stls import verify
from restore_weave_project import refresh_preview_cache
from colorize_print_project import weave_modifier
import numpy as np
import trimesh
import manifold3d
from shapely import union_all, affinity
from shapely.geometry import Point

AFFECTED = {'F1', 'F2', 'F6', 'F8', 'F13', 'F15', 'F19'}


def solid(mesh):
    result = manifold3d.Manifold(manifold3d.Mesh64(mesh.vertices, mesh.faces.astype(np.uint64)))
    assert result.status() == manifold3d.Error.NoError
    return result


def verify_exports():
    original = WORK/'original-stls'
    cad = CAD.read_text()
    placements = read_array(cad, 'frame_placements')
    findings = json.loads((REVIEW/'source-repair.json').read_text())['findings_repaired']
    zones = union_all([Point(r['assembly_xy_mm']).buffer(14.03, quad_segs=32) for r in findings])
    delta = artwork(cad, 'knot_outline').symmetric_difference(artwork((WORK/'original.scad').read_text(), 'knot_outline'))
    photo_zones = union_all([artwork(cad, f'photo_loop_{i}').buffer(4.01) for i in range(1, 9)])
    lap_zones = union_all([affinity.scale(artwork(cad, f'frame_joint_domain_{i}'), 1/.75, 1/.75, origin=(0, 0)) for i in range(31)])
    screw_zones = union_all([Point(r[2]).buffer(7) for r in read_array(cad, 'screw_mounts')])
    dowel_zones = union_all([Point(r[2]).buffer(3) for r in read_array(cad, 'dowel_mounts')])
    anchors = np.asarray(read_array(cad, 'photo_anchors')).reshape(-1, 2)*.75
    normals = np.asarray(read_array(cad, 'photo_normals')).reshape(-1, 2)
    pilot_zones = union_all([Point(p).buffer(7) for p in anchors+normals*9.5])
    clearances = {}
    for label, protected in [('photo_recesses', photo_zones), ('lap_joint_domains', lap_zones),
                             ('M_screws', screw_zones), ('M_locators', dowel_zones), ('photo_screws', pilot_zones)]:
        assert delta.intersection(protected).area < 1e-7, label
        clearances[label] = delta.distance(protected)
    manifest = json.loads((STLS/'manifest.json').read_text())
    checks, kept = [], []
    for record in manifest['parts']:
        name = record['part']; path = STLS/record['file']
        old, new = [trimesh.load_mesh(p) for p in (original/record['file'], path)]
        a, b = solid(old), solid(new)
        difference = (a-b)+(b-a)
        volume = difference.volume()
        check = dict(part=name, symmetric_difference_mm3=volume)
        if name not in AFFECTED:
            assert volume < .001, (name, volume)
            assert nearest_error(old.vertices, new.vertices) < .0001
            assert nearest_error(new.vertices, old.vertices) < .0001
            shutil.copy2(original/record['file'], path)
            record.update(verify(path)); kept.append(name)
            check['byte_identical_to_prior'] = True
        else:
            assert volume > .01 and volume < 100
            local = in_print_coordinates(zones, placements[int(name[1:])-1])
            outside = (difference-section(local).extrude(30).translate([0, 0, -1])).volume()
            assert outside < .02, (name, outside)
            bounds_change = new.bounds-old.bounds
            assert np.abs(bounds_change).max() < .31, (name, bounds_change)
            assert np.allclose(old.bounds[:, 2], new.bounds[:, 2], atol=.0001)
            check.update(changed_volume_outside_repair_regions_mm3=outside, bounds_change_mm=bounds_change.tolist(),
                         thickness_unchanged=True, saved_print_transform_unchanged=True)
        checks.append(check)
        print(name, 'geometric delta', round(volume, 6), flush=True)
    assert len(kept) == 32
    (STLS/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    refresh_preview_cache()
    strip = lambda t: re.sub(r'module (?:knot_outline|fabric_outline|preview_frame_\d+)\(\) \{.*?\n\}', '', t, flags=re.S)
    assert strip((WORK/'original.scad').read_text()) == strip(CAD.read_text())
    report = dict(source_cad_sha256=digest(CAD), native_feature_code_unchanged=True,
                  minimum_outline_change_distance_from_protected_features_mm=clearances,
                  unchanged_stl_files=kept, changed_stl_files=sorted(AFFECTED, key=lambda n:int(n[1:])), parts=checks)
    (REVIEW/'geometry-verification.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


def main():
    geometry = verify_exports()
    source = WORK/'baseline.3mf'
    base = json.loads((WORK/'baseline.json').read_text())
    assert digest(source) == base['project_sha256']
    files = read_zip(source)
    root = ET.fromstring(files['3D/3dmodel.model'])
    config = ET.fromstring(files['Metadata/model_settings.config'])
    objects = {o.get('id'): o for o in root.find(tag('resources'))}
    children = {n:ET.fromstring(d) for n,d in files.items() if n.startswith('3D/Objects/') and n.endswith('.model')}
    cad = CAD.read_text(); placements = read_array(cad, 'frame_placements')
    knot = artwork(cad, 'knot_outline')
    fabric = artwork(cad, 'fabric_outline').buffer(.1125, quad_segs=16)
    blue = (fabric.buffer(GAP+WIDTH, quad_segs=16)-fabric.buffer(GAP, quad_segs=16)).intersection(knot).simplify(.001, preserve_topology=True)
    evidence, wood_evidence = [], []
    for obj in config.findall('object'):
        name = props(obj)['name']
        if not (re.fullmatch(r'F\d+', name) or name == NAME):
            continue
        path = (ROOT/'working/stl/Dara-Print-Checks' if name == NAME else STLS)/(name+'.stl')
        mesh = trimesh.load_mesh(path); body = solid(mesh)
        local = coupon_shape(blue, cad) if name == NAME else in_print_coordinates(blue, placements[int(name[1:])-1])
        expected = section(local) ^ body.slice((BOTTOM+TOP)/2)
        for z in (BOTTOM+.001, TOP-.001):
            assert (expected-body.slice(z).offset(.0001)).area() < .02
        blue_mesh = as_mesh(expected.extrude(TOP-BOTTOM).translate([0, 0, BOTTOM]))
        evidence.append(dict(part=name, area_mm2=expected.area(), volume_mm3=blue_mesh.volume,
                             source_stl_sha256=digest(path), z_mm=[BOTTOM, TOP], triangles=len(blue_mesh.faces),
                             connected_regions=len(blue_mesh.split()), printable_geometry_unchanged=name not in AFFECTED))
        replacements = {4:blue_mesh}
        if name in AFFECTED:
            wood_mesh, proof = weave_modifier(mesh)
            replacements.update({0:mesh, 2:wood_mesh})
            wood_evidence.append(dict(part=name, **proof))
        comps = {c.get('objectid'):c for c in objects[obj.get('id')].find(tag('components'))}
        for part in obj.findall('part'):
            slot = 0 if part.get('subtype') == 'normal_part' else int(props(part).get('extruder', 0))
            if part.get('subtype') != 'normal_part' and slot == 0:
                continue
            if slot not in replacements:
                continue
            comp = comps[part.get('id')]
            res = children[comp.get('{'+P+'}path').lstrip('/')].find(tag('resources'))
            new = replacements[slot].copy()
            new.apply_transform(np.linalg.inv(transform(comp.get('transform'))))
            res.remove(next(o for o in res if o.get('id') == part.get('id')))
            mesh_object(res, part.get('id'), new)
            part.find('mesh_stat').set('face_count', str(len(new.faces)))
        print(name, 'color regions refreshed', flush=True)
    assert len(evidence) == 21 and len(wood_evidence) == 7
    for plate in config.findall('plate'):
        for md in list(plate.findall('metadata')):
            if md.get('key', '').endswith('_file'):
                plate.remove(md)
    files = {n:d for n,d in files.items() if not n.startswith('Metadata/') or n in ('Metadata/model_settings.config', 'Metadata/project_settings.config')}
    files['Metadata/model_settings.config'] = xml(config)
    for n, child in children.items():
        files[n] = xml(child)
    output = WORK/'repaired-curves.3mf'
    write_zip(output, files)
    manifest = json.loads((STLS/'manifest.json').read_text())
    for part in base['parts']:
        entry = next(p for p in manifest['parts'] if p['part'] == part.get('part', part.get('name')))
        for key in ('triangles', 'bounds_mm', 'size_mm', 'volume_mm3'):
            if key in part:
                part[key] = entry[key]
        part['file_sha256'] = entry['sha256']
    base['project_sha256'] = digest(output)
    base['test_plate'].update(source_cad_sha256=digest(CAD), sliced=False)
    for record in base['weave_restoration']['surface_masks']:
        replacement = next((r for r in wood_evidence if r['part'] == record['part']), None)
        if replacement:
            record.update(replacement)
    base['blue_ribbon_edge'].update(source_cad_sha256=digest(CAD), masks=evidence,
                                    physical_geometry_unchanged=False, digital_checks_passed=False,
                                    curve_repair='working/review/curve-repair/source-repair.json')
    base['curve_repair'] = dict(prior_project_sha256=digest(source), source_cad_sha256=digest(CAD),
                                repaired_locations=12, repaired_plates=[1, 2, 6, 8, 13, 15, 19],
                                geometry_verification='working/review/curve-repair/geometry-verification.json',
                                unchanged_stl_files=geometry['unchanged_stl_files'], wood_modifiers=wood_evidence)
    for key in ('bambu_studio_slice', 'bambu_studio_round_trip', 'bambu_studio_slice_warnings'):
        base.pop(key, None)
    (WORK/'staged.json').write_text(json.dumps(base, indent=2)+'\n')
    plot(cad, blue, REVIEW/'assembly-color-map.png')
    print(output, flush=True)


if __name__ == '__main__':
    main()
