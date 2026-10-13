"""Refresh the saved 31-plate project after the 2.0 -> 2.4 mm rabbet revision.

Run export_jointed_stls.py first. Retains all placements, settings and modifiers;
stages editable models without stale G-code. Slice, combine and audit the staged
file before replacing the published project.
"""
import argparse
import json
import shutil
import subprocess
from pathlib import Path
import xml.etree.ElementTree as ET

from add_weave_test_coupon import read_zip, write_zip, NAME
from build_jointed_bambu_project import ROOT, tag, P, mesh_object, xml
from export_jointed_stls import verify
from restore_weave_project import refresh_preview_cache, crop_weave, STLS, CHECKS, CAD
from validate_print_project import props, transform, digest, nearest_error
import numpy as np
import trimesh

WORK = ROOT / '.work/rabbet-clearance'


def refresh_photo_fit_sample():
    """Update the optional photo-fit STL; keep the two material plates alone."""
    executable = shutil.which('openscad') or r'C:\Program Files (x86)\OpenSCAD\openscad.exe'
    manifest_path = CHECKS/'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    prior_hash = manifest['source_sha256']
    path = CHECKS/'Photo-Fit-Sample.stl'
    temporary = WORK/path.name
    result = subprocess.run([executable, '--hardwarnings', '--export-format=binstl',
        '--camera=0,0,0,0,0,0,700', '-o', str(temporary), '-D', 'fast_preview=false',
        '-D', 'view_mode="fit_sample"', str(CAD)], capture_output=True, text=True, timeout=1200)
    log = result.stdout + result.stderr
    (WORK/'photo-fit-export.log').write_text(log)
    assert result.returncode == 0 and 'WARNING:' not in log and 'ERROR:' not in log, log
    mesh = trimesh.load_mesh(temporary)
    solids = mesh.split(only_watertight=False)
    assert len(solids) == 3
    assert all(m.is_watertight and m.volume > 0 and abs(m.bounds[0, 2]) < 1e-5 for m in solids)
    frame = next(m for m in solids if m.extents[2] > 10)
    origin = frame.bounds.mean(axis=0)
    origin[2] = frame.bounds[0, 2]
    frame.apply_translation(-origin)
    # Printed backer and tab samples retain their original dimensions.
    for m, name in ((next(m for m in solids if m.extents[2] < 2), 'Test-Photo-Backer'),
                    (next(m for m in solids if 2 < m.extents[2] < 4), 'Test-Photo-Tab')):
        origin = m.bounds.mean(axis=0)
        origin[2] = m.bounds[0, 2]
        m.apply_translation(-origin)
        old = trimesh.load_mesh(CHECKS/(name+'.stl'))
        assert len(old.faces) == len(m.faces)
        for a, b in ((old, m), (m, old)):
            assert nearest_error(a.vertices, b.vertices) < 1e-4
            assert nearest_error(a.triangles_center, b.triangles_center) < 1e-4
    frame_path = CHECKS/'Test-Photo-Frame.stl'
    frame.export(frame_path)
    shutil.copy2(temporary, path)
    for record in manifest['files']:
        record.setdefault('source_sha256', prior_hash)
        if record['file'] == path.name:
            record.update(sha256=digest(path), source_sha256=digest(CAD), size_mm=mesh.extents.tolist())
    manifest.update(source_sha256=digest(CAD),
        source_hash_note='Photo sample uses current CAD; other archived samples retain their per-file source hashes.',
        standalone_photo_frame=dict(file=frame_path.name, sha256=digest(frame_path),
            source_sha256=digest(CAD), rabbet_depth_mm=2.4, size_mm=frame.extents.tolist(),
            connected_solids=1, watertight=True),
        prior_photo_fit_feedback='2.0 mm rabbet left insufficient photo room; user suspects support roughness.',
        revised_photo_fit_tested=False)
    manifest_path.write_text(json.dumps(manifest, indent=2)+'\n')


def preserve_unchanged_parts(original):
    """Keep byte-identical files for native re-exports with identical geometry."""
    manifest = json.loads((STLS/'manifest.json').read_text())
    kept = []
    for record in manifest['parts']:
        if record['family'] == 'frame':
            continue
        path = STLS / record['file']
        old_path = original / record['file']
        old, new = trimesh.load_mesh(old_path), trimesh.load_mesh(path)
        assert len(old.faces) == len(new.faces), record['part']
        for a, b in ((old, new), (new, old)):
            assert nearest_error(a.vertices, b.vertices) < 1e-4
            assert nearest_error(a.triangles_center, b.triangles_center) < 1e-4
        shutil.copy2(old_path, path)
        record.update(verify(path))
        kept.append(record['part'])
    (STLS/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return kept


def stage(source, baseline, original):
    base = json.loads(baseline.read_text())
    assert digest(source) == base['project_sha256']
    assert base['plates'] == 31 and base['test_plate']['plates'] == [30, 31]
    manifest = json.loads((STLS/'manifest.json').read_text())
    assert manifest['source_sha256'] == digest(CAD), 'Export native CAD before staging.'
    kept = preserve_unchanged_parts(original)
    refresh_preview_cache()
    coupon = crop_weave(CAD.read_text())
    refresh_photo_fit_sample()
    files = read_zip(source)
    root = ET.fromstring(files['3D/3dmodel.model'])
    config = ET.fromstring(files['Metadata/model_settings.config'])
    objects = {o.get('id'): o for o in root.find(tag('resources'))}
    children = {n: ET.fromstring(d) for n, d in files.items() if n.startswith('3D/Objects/') and n.endswith('.model')}
    for obj in config.findall('object'):
        name = props(obj)['name']
        if name != NAME and not (name.startswith('F') and name[1:].isdigit()):
            continue
        mesh = coupon.copy() if name == NAME else trimesh.load_mesh(STLS/(name+'.stl'))
        part = obj.find("part[@subtype='normal_part']")
        comp = next(c for c in objects[obj.get('id')].find(tag('components')) if c.get('objectid') == part.get('id'))
        resources = children[comp.get('{'+P+'}path').lstrip('/')].find(tag('resources'))
        old = next(o for o in resources if o.get('id') == part.get('id'))
        mesh.apply_transform(np.linalg.inv(transform(comp.get('transform'))))
        resources.remove(old)
        mesh_object(resources, part.get('id'), mesh)
        part.find('mesh_stat').set('face_count', str(len(mesh.faces)))
    for plate in config.findall('plate'):
        for md in list(plate.findall('metadata')):
            if md.get('key', '').endswith('_file'):
                plate.remove(md)
    files = {n: d for n, d in files.items() if not n.startswith('Metadata/') or n in
             ('Metadata/model_settings.config', 'Metadata/project_settings.config')}
    files['Metadata/model_settings.config'] = xml(config)
    for name, child in children.items():
        files[name] = xml(child)
    output = WORK/'deeper-rabbet.3mf'
    write_zip(output, files)
    manifest = json.loads((STLS/'manifest.json').read_text())
    for part in base['parts']:
        entry = next(p for p in manifest['parts'] if p['part'] == part.get('part', part.get('name')))
        for key in ('triangles', 'bounds_mm', 'size_mm', 'volume_mm3'):
            if key in part:
                part[key] = entry[key]
        part['file_sha256'] = entry['sha256']
    for part in base['test_plate']['parts']:
        if part['name'] == NAME:
            part.update(sha256=digest(CHECKS/(NAME+'.stl')), triangles=len(coupon.faces),
                        source_stl_sha256=digest(STLS/'F7.stl'), dimensions_mm=coupon.extents.tolist())
    base['test_plate'].update(source_cad_sha256=digest(CAD), sliced=False)
    base['project_sha256'] = digest(output)
    for key in ('bambu_studio_slice', 'bambu_studio_round_trip', 'bambu_studio_slice_warnings', 'ams_color_workflow'):
        base.pop(key, None)
    base['rabbet_revision'] = dict(prior_project_sha256=digest(source), old_depth_mm=2.0,
        depth_mm=2.4, backer_thickness_mm=1.6, photo_and_surface_allowance_mm=.8,
        added_depth_mm=.4, unchanged_stl_files=kept,
        reason='User reports backer flush with rabbet, leaving insufficient photo space; suspected support roughness.',
        geometry_verification='working/review/rabbet-clearance/geometry-verification.json')
    (WORK/'staged.json').write_text(json.dumps(base, indent=2)+'\n')
    print(output, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=WORK/'baseline.3mf')
    parser.add_argument('--baseline', type=Path, default=WORK/'baseline.json')
    parser.add_argument('--original-stls', type=Path, default=WORK/'original-stls')
    args = parser.parse_args()
    stage(args.source, args.baseline, args.original_stls)
