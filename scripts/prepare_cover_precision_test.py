"""Isolate B1 and compare native toolpaths without changing its geometry.

Historical experiment; NOT the recommended remedy for the physical scar.
Subsequent renderer inspection reproduced preview notches from segment joins
without extrusion gaps. See working/review/cover-edge/README.md. This script
remains available to reproduce the unchanged earlier precision experiment.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

import prepare_hammered_bands as b
from integrate_hammered_dara import selected_entries, relationship_xml, TARGETS
from prepare_y_stable_dara import motion_audit
from validate_print_project import TOKEN

WORK = b.ROOT / '.work/cover-precision'
REVIEW = b.ROOT / 'working/review/cover-precision'
TARGET = b.ROOT / 'Dara-Cover-Only-Test.3mf'
VARIANTS = {'control': ('1', '0.012'), 'no-arcs': ('0', '0.012'),
            'precise': ('0', '0.001')}


def stage():
    WORK.mkdir(parents=True, exist_ok=True)
    report = json.loads((b.ROOT/'working/review/y-stable-dara/test-validation.json').read_text())
    assert b.sha(b.TEST) == report['project_sha256'], 'Recheck source orientation after a new release.'
    files = b.read_zip(b.TEST)
    cfg = ET.fromstring(files['Metadata/model_settings.config'])
    root = ET.fromstring(files['3D/3dmodel.model'])
    rels = ET.fromstring(files['3D/_rels/3dmodel.model.rels'])
    resources, build = root.find(b.tag('resources')), root.find(b.tag('build'))
    keep = next(o.get('id') for o in cfg.findall('object') if b.props(o)['name'].startswith('B1 -'))
    original = selected_entries(files, {'B1'})['B1'][0]['mesh']
    shift = b.np.array([128., 128., 0.])
    shift[:2] -= original.bounds.mean(axis=0)[:2]
    for obj in list(resources):
        if obj.get('id') == keep:
            continue
        for comp in obj.find(b.tag('components')):
            path = comp.get('{'+b.P+'}path').lstrip('/')
            files.pop(path)
            for rel in list(rels):
                if rel.get('Target').lstrip('/') == path:
                    rels.remove(rel)
        resources.remove(obj)
    for item in list(build):
        if item.get('objectid') != keep:
            build.remove(item)
        else:
            t = b.transform(item.get('transform'))
            t[:3, 3] += shift
            item.set('transform', ' '.join(f'{v:.12g}' for v in t[:3, :].T.ravel()))
    for obj in list(cfg.findall('object')):
        if obj.get('id') != keep:
            cfg.remove(obj)
    for plate in cfg.findall('plate'):
        for inst in list(plate.findall('model_instance')):
            if b.props(inst)['object_id'] != keep:
                plate.remove(inst)
        for md in list(plate.findall('metadata')):
            if md.get('key', '').endswith('_file'):
                plate.remove(md)
        b.setmeta(plate, 'plater_name', 'B1 cover only - precision test')
    assemble = cfg.find('assemble')
    if assemble is not None:
        cfg.remove(assemble)
    for path in list(files):
        if path.startswith('Metadata/') and path not in ('Metadata/model_settings.config', 'Metadata/project_settings.config'):
            del files[path]
    files.update({'3D/3dmodel.model': b.xml(root), 'Metadata/model_settings.config': b.xml(cfg),
                  '3D/_rels/3dmodel.model.rels': relationship_xml(rels)})
    settings = json.loads(files['Metadata/project_settings.config'])
    for label, (arc, resolution) in VARIANTS.items():
        variant = copy.deepcopy(settings)
        variant.update(enable_arc_fitting=arc, resolution=resolution,
                       print_settings_id='Dara B1 cover - '+label)
        files['Metadata/project_settings.config'] = json.dumps(variant, indent=2).encode()
        b.write_zip(WORK/(label+'-staged.3mf'), files)
    orientation = next(o for o in report['orientation'] if o['name'] == 'B1')
    t = b.np.array(orientation['build_transform'])
    t[:3, 3] += shift
    manifest = dict(source_sha256=b.sha(b.TEST), build_transform=t.tolist(),
                    source_translation_mm=shift.tolist(), variants=VARIANTS,
                    preserved={str(p.relative_to(b.ROOT)): b.sha(p) for p in [*TARGETS, b.TARGET, b.TEST]})
    (WORK/'stage.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print('Staged identical B1 geometry, orientation and supports; only precision differs.')


def slice_all():
    exe = Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe')
    for label in VARIANTS:
        out = WORK/label
        out.mkdir(exist_ok=True)
        with (out/'cli.log').open('w') as log:
            result = subprocess.run([str(exe), '--slice', '1', '--export-3mf', 'sliced.3mf',
                                     '--outputdir', str(out), str(WORK/(label+'-staged.3mf'))],
                                    cwd=exe.parent, stdout=log, stderr=subprocess.STDOUT,
                                    creationflags=subprocess.CREATE_NO_WINDOW)
        assert result.returncode == 0, (label, result.returncode)
        print(label, 'sliced', flush=True)


def face_paths(text, transform):
    """Measure tangent joins in a defined interior region of the show face.

    These are geometric G-code angles, not measured motion or a surface-quality
    score. Preserve arc tangents rather than substituting straight chords.
    """
    _, outline, joints, _ = b.layout()
    joint = joints[0]
    local = b.rotation(-joint[3])
    local[:2, 3] = -local[:2, :2] @ b.np.array(joint[2])
    undo = b.np.linalg.inv(transform)
    x = y = z = e = 0.
    relative = xyzrelative = False
    feature = 'Custom'
    last = None
    paths, jumps = [], []
    outer_arcs = model_arcs = 0
    for line, raw in enumerate(text.splitlines(), 1):
        if raw.startswith('; FEATURE: '):
            feature = raw[11:].strip()
        code = raw.split(';', 1)[0].strip()
        if not code:
            continue
        cmd = code.split()[0]
        v = {k: float(n) for k, n in TOKEN.findall(code)}
        if cmd == 'M83':
            relative = True
        elif cmd == 'M82':
            relative = False
        elif cmd in ['G90', 'G91']:
            xyzrelative = cmd == 'G91'
        elif cmd == 'G92':
            x, y, z, e = [v.get(k, old) for k, old in zip('XYZE', (x, y, z, e))]
        elif cmd in ['G0', 'G1', 'G2', 'G3']:
            nx, ny, nz = [old+v.get(k, 0) if xyzrelative else v.get(k, old) for k, old in zip('XYZ', (x, y, z))]
            de = v.get('E', 0) if relative else v.get('E', e)-e
            p = b.np.array([[x, y, z], [nx, ny, nz]])
            if b.np.linalg.norm(p[1]-p[0]) > .00001:
                if de > 0 and feature not in ['Custom', 'Support', 'Support interface', 'Brim'] and cmd in ['G2', 'G3']:
                    model_arcs += 1
                if de > 0 and feature == 'Outer wall':
                    if cmd in ['G2', 'G3']:
                        center = b.np.array([x+v.get('I', 0), y+v.get('J', 0)])
                        radii = p[:, :2]-center
                        sign = 1 if cmd == 'G3' else -1
                        d0 = sign*b.np.array([-radii[0, 1], radii[0, 0], 0])
                        d1 = sign*b.np.array([-radii[1, 1], radii[1, 0], 0])
                        radius = b.np.linalg.norm(radii[0])
                        a0, a1 = b.np.arctan2(radii[:, 1], radii[:, 0])
                        delta = (a1-a0)%(2*math.pi) if sign > 0 else -((a0-a1)%(2*math.pi))
                        angles = b.np.linspace(a0, a0+delta, max(2, int(abs(delta)*radius/.06)+1))
                        sample = b.np.column_stack([center[0]+radius*b.np.cos(angles), center[1]+radius*b.np.sin(angles), b.np.linspace(z, nz, len(angles))])
                        outer_arcs += 1
                    else:
                        d0 = d1 = p[1]-p[0]
                        sample = p
                    assembled = b.trimesh.transform_points(p, undo)
                    roof = 10.5+b.crown(outline, assembled[:, :2])-.6+.15+1.2
                    q = b.trimesh.transform_points(assembled, local)
                    onfront = min(q[:, 2]-roof) > -.4
                    if onfront:
                        samples = b.trimesh.transform_points(b.trimesh.transform_points(sample, undo), local)
                        paths.extend(b.np.stack([samples[:-1], samples[1:]], axis=1).tolist())
                        if (last is not None and last['onfront'] and b.np.linalg.norm(p[0]-last['end']) < .00001
                                and abs(q[0, 0]) < 4.8 and -16 < q[0, 1] < 12):
                            cosine = b.np.dot(d0, last['dir'])/(b.np.linalg.norm(d0)*b.np.linalg.norm(last['dir']))
                            angle = math.degrees(math.acos(b.np.clip(cosine, -1, 1)))
                            jumps.append(dict(angle_deg=angle, xy_mm=q[0, :2].tolist(), gcode_line=line))
                    last = dict(dir=d1, end=p[1], onfront=onfront)
                else:
                    last = None
            elif de < 0:
                last = None
            x, y, z = nx, ny, nz
            e = e+v.get('E', 0) if relative else v.get('E', e)
    angles = [q['angle_deg'] for q in jumps]
    return paths, dict(outer_wall_arcs=outer_arcs, model_extrusion_arcs=model_arcs,
                       interior_join_count=len(jumps), max_tangent_change_deg=max(angles),
                       p95_tangent_change_deg=float(b.np.percentile(angles, 95)), joins=jumps)


def verify_publish():
    REVIEW.mkdir(parents=True, exist_ok=True)
    stageinfo = json.loads((WORK/'stage.json').read_text())
    t = b.np.array(stageinfo['build_transform'])
    assert abs(t[1, 2]) < 1e-8 and abs(t[2, 2]-math.cos(math.radians(55))) < 1e-8
    results, plotdata = {}, {}
    source = selected_entries(b.read_zip(b.TEST), {'B1'})['B1'][0]
    source['mesh'].apply_translation(stageinfo['source_translation_mm'])
    for label, (arc, resolution) in VARIANTS.items():
        out = WORK/label
        result = json.loads((out/'result.json').read_text())
        assert result['return_code'] == 0 and result['plate_index'] == 1
        staged = b.read_zip(WORK/(label+'-staged.3mf'))
        files = b.read_zip(out/'sliced.3mf')
        actualsettings = json.loads(files['Metadata/project_settings.config'])
        expectedsettings = json.loads(staged['Metadata/project_settings.config'])
        assert all(actualsettings.get(k) == v for k, v in expectedsettings.items())
        assert set(actualsettings)-set(expectedsettings) <= {'different_settings_to_system', 'inherits_group', 'filament_map_2'}
        entries = b.model_entries(files)
        assert set(entries) == {'B1'} and len(entries['B1']) == 1
        entry = entries['B1'][0]
        mesh = entry['mesh']
        assert mesh.is_volume and mesh.is_watertight and mesh.body_count == 1
        error = max(b.cKDTree(mesh.vertices).query(source['mesh'].vertices)[0].max(),
                    b.cKDTree(source['mesh'].vertices).query(mesh.vertices)[0].max())
        assert error < .0002
        assert all(int((entry['paint'] == k).sum()) == int((source['paint'] == k).sum()) for k in [4, 8])
        info = ET.fromstring(files['Metadata/slice_info.config'])
        assert len(info.findall('plate')) == 1
        plate = info.find('plate')
        assert b.props(plate)['outside'] == 'false' and b.props(plate)['pause_count'] == '0'
        assert {f.get('id') for f in plate.findall('filament')} == {'1'}
        assert all(w.get('msg') == 'not_support_traditional_timelapse' for w in plate.findall('warning'))
        b.setmeta(plate, 'printer_model_id', 'N2S')
        first = float(b.props(plate).get('first_layer_time', 0))
        if not math.isfinite(first) or not 0 <= first <= float(b.props(plate)['prediction']):
            plate.remove(plate.find("metadata[@key='first_layer_time']"))
        gcode = files['Metadata/plate_1.gcode']
        assert hashlib.md5(gcode).hexdigest() == files['Metadata/plate_1.gcode.md5'].decode().strip().lower()
        text = gcode.decode()
        assert not re.search(r'^\s*(?:M400\s+U1|M0(?:\s|$)|M1(?:\s|$)|M25(?:\s|$))', text, re.M)
        audit = b.scan_gcode(text)
        zs = audit.pop('model_extrusion_z_by_filament_mm')
        assert set(zs) == {'1'} and .1999 <= min(zs['1']) <= max(zs['1']) < 250
        assert audit['conservative_bed_edge_clearance_mm'] > 6
        assert all(audit['features'].get(k, 0) > 0 for k in ['Outer wall', 'Support', 'Support interface'])
        assert not audit['features'].get('Ironing', 0) and not audit['features'].get('Prime tower', 0)
        paths, _ = b.support_paths(text)
        base = paths['Support'][b.np.max(paths['Support'][:, :, 2], axis=1) <= .201]
        assert len(base) > 0
        local = b.trimesh.transform_points(paths['Support interface'].mean(axis=1), b.np.linalg.inv(t))
        _, outline, joints, _ = b.layout()
        j = joints[0]
        footprint = b.locate(b.rect(-6, -j[4], 6, j[4]), j[2], j[3]).intersection(outline.buffer(-.15))
        inside = b.shapely.contains(footprint.buffer(-.6), b.shapely.points(local[:, :2]))
        assert inside.any()
        floor = 10.5+b.crown(outline, local[inside, :2])-.6+.15
        max_delta = float((local[inside, 2]-floor).max())
        assert max_delta < .12
        motion = motion_audit(text)
        assert 'M201 X1000 Y1000 Z1500 E5000' in motion['axis_limit_commands']
        assert 'M203 X150 Y150 Z30 E30' in motion['axis_limit_commands']
        plotdata[label], tangent = face_paths(text, t)
        if arc == '0':
            assert tangent['model_extrusion_arcs'] == tangent['outer_wall_arcs'] == 0
        stats = b.props(plate)
        results[label] = dict(resolution_mm=resolution, arc_fitting=arc, mesh_roundtrip_error_mm=float(error),
                              mesh_volume_mm3=float(mesh.volume), mesh_triangles=len(mesh.faces),
                              mesh_watertight=True, mesh_components=1, gcode_sha256=hashlib.sha256(gcode).hexdigest(),
                              weight_g=float(stats['weight']), seconds=int(stats['prediction']),
                              model_z_mm=[min(zs['1']), max(zs['1'])], support_base_segments=len(base),
                              max_interface_above_band_underside_mm=max_delta, motion=motion,
                              path_audit=audit, tangent_audit=tangent)
        if label == 'precise':
            files['Metadata/slice_info.config'] = b.xml(info)
            b.write_zip(TARGET, files)
    # Tangent statistics describe the paths; no angle threshold proves finish.
    for path, digest in stageinfo['preserved'].items():
        assert b.sha(b.ROOT/path) == digest
    report = dict(project_sha256=b.sha(TARGET), source=stageinfo, variants=results,
                  conclusion='Historical precision comparison. Preview notches can be renderer segment-join artifacts; '
                             'arc-join angles do not establish the physical scar cause or cure. See cover-edge investigation.',
                  physical_print_pending=True, complete_project_changed=False)
    (REVIEW/'validation.json').write_text(json.dumps(report, indent=2)+'\n')
    render(plotdata, results)
    print('Published', TARGET.name, results['precise']['weight_g'], 'g', results['precise']['seconds'], 'seconds')


def render(paths, results):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    fig, axes = plt.subplots(1, 2, figsize=(7, 9), facecolor='#f4f1eb')
    for ax, label in zip(axes, ['control', 'precise']):
        p = b.np.array(paths[label])
        ax.add_collection(LineCollection(p[:, :, :2], linewidths=.6, colors='#ae6c35'))
        marks = [j for j in results[label]['tangent_audit']['joins'] if j['angle_deg'] >= .75]
        if marks:
            xy = b.np.array([j['xy_mm'] for j in marks])
            ax.scatter(xy[:, 0], xy[:, 1], s=12, color='#713f8c', zorder=3)
        ax.set(xlim=(-6.5, 6.5), ylim=(-21, 23), aspect='equal', xlabel='Width (mm)', ylabel='Length coordinate (mm)')
        ax.set_title('Existing arc fitting / 0.012 mm' if label == 'control' else 'Test: no arcs / 0.001 mm', fontsize=10)
    fig.suptitle('B1 cover — identical mesh, different native paths', fontsize=13)
    fig.text(.5, .015, 'Purple: interior toolpath joins changing direction by at least 0.75 degrees.\nActual G-code, not a rendering or prediction of the finished surface.', ha='center', fontsize=8)
    fig.tight_layout(rect=(0, .065, 1, .95))
    fig.savefig(REVIEW/'toolpath-comparison.png', dpi=170)
    plt.close(fig)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['stage', 'slice', 'verify'])
    args = parser.parse_args()
    {'stage': stage, 'slice': slice_all, 'verify': verify_publish}[args.action]()
