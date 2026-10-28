"""Extend native painted brims along the 14 current lower-lap edges.

No printable mesh is added or changed. Native brim points are object-space
positions, attached to the existing object rather than a modifier volume.
"""
import argparse
import collections
import json
import re
import shutil
import xml.etree.ElementTree as ET
import set_knot_white_support_base as shared
from set_knot_white_support_base import (
    ROOT, read, write, digest, props, ASSET, dump, sha, protected, LOCKS,
    rows, compare, extrusion_paths, signatures, support_summary, SUPPORT, OTHER,
    scan_gcode, np, MultiPoint, check_startup_tower, check_tower,
)
from shapely import union_all, affinity
from shapely.geometry import Point, LineString, box, shape, mapping
from shapely.ops import nearest_points
from mesh_sections import mesh_slice
from audit_knot_rollback_joints import local
from develop_m_veneer import locate
from development_3mf import solid
from develop_cosmetic_joints import cross_section

WORK = ROOT / '.work/knot-lower-lap-brims-r2'
REPORT = ROOT / 'release/knot-lower-lap-brims-r2'
BASE, EDIT, FINAL = [WORK / n for n in ('before.3mf', 'editable.3mf', 'final.3mf')]
SOURCE_SHA = '95e678abe97fe5f30dad2063d154214555ccd0646e9b3d6bfbbffdb1b94276d8'
CHANGE = {}
POINTS = 'Metadata/brim_ear_points.txt'
RADIUS = 6.0


def bind():
    shared.WORK, shared.EDIT, shared.FINAL, shared.BASE, shared.CHANGE = WORK, EDIT, FINAL, BASE, CHANGE


def bed_polygon(g, obj):
    t = obj['transform']
    return affinity.affine_transform(g, [t[0, 0], t[0, 1], t[1, 0], t[1, 1], t[0, 3], t[1, 3]])


def check_plate_order(path):
    cfg = ET.fromstring(read(path)['Metadata/model_settings.config'])
    assert len(cfg.findall('plate')) == 10
    for p in cfg.findall('plate'):
        assert props(p)['first_layer_print_sequence'] == '1 3 2'


def build():
    assert digest(ROOT / 'Knot.3mf') == SOURCE_SHA
    WORK.mkdir(parents=True, exist_ok=True)
    if not BASE.exists():
        shutil.copyfile(ROOT / 'Knot.3mf', BASE)
    assert digest(BASE) == SOURCE_SHA
    settings, objects = rows(BASE)
    files = read(BASE)
    assert POINTS in files and settings['brim_type'] == 'brim_ears'
    plan = json.loads((ROOT / 'working/bambu/Dara-Photo-Frame-A2L/production-plan.json').read_text())['frame_joints']
    records, plate_records, laps, lines = [], [], [], ['brim_points_format_version=1']
    for oi, obj in enumerate(objects):
        contact = union_all([mesh_slice(p['mesh'], .1) for p in obj['parts'] if p['subtype'] == 'normal_part'])
        points = []
        lowers = [p for p in obj['parts'] if p['settings'].get('name', '').endswith(' - LOWER')]
        for part in lowers:
            ji = int(re.search(r'J(\d+)', part['settings']['name'])[1])
            joint = plan[ji - 1]
            assert joint[0] == oi and part['settings']['sparse_infill_density'] == '100%'
            assert part['settings']['sparse_infill_pattern'] == 'zig-zag'
            mask = cross_section(solid(part['mesh']), .1)
            lap = contact.intersection(mask)
            # Actual outside bed-contact edges only: the mask's artificial X0
            # cut must never create a brim across or behind the lap shoulder.
            edge = local(contact.boundary.intersection(mask.buffer(.00001)), joint)
            edge = edge.intersection(box(2, -200, 18.01, 200))
            # Separate stock meshes can leave micron-wide section cracks.
            # Exclude their internal boundaries; they are not exposed edges
            # in the native slice. This only filters placement coordinates.
            sealed = contact.buffer(.001).buffer(-.001)
            assert contact.symmetric_difference(sealed).area < .01
            edge = edge.difference(local(sealed.buffer(-.01), joint))
            pieces = [edge] if edge.geom_type == 'LineString' else list(edge.geoms)
            assert edge.length > 60
            positions = []
            for part_edge in pieces:
                if part_edge.length < .001: continue
                for d in np.linspace(0, part_edge.length, int(np.ceil(part_edge.length / 2.5)) + 1):
                    pt = part_edge.interpolate(d)
                    if all(pt.distance(q) > .1 for q in positions): positions.append(pt)
            for idx, pt in enumerate(positions):
                pos = locate(pt, joint)
                center = [pos.x, pos.y, -.0001]
                bed = (obj['transform'] @ np.array([*center, 1]))[:2]
                clearance = min(*bed, *(np.array([330, 320]) - bed))
                radius = min(RADIUS, pt.x, clearance - .6)
                assert radius >= 1.99 and contact.boundary.distance(pos) < .001
                points.append([*center, radius, -1])
                records.append(dict(plate=oi + 1, joint=ji, corner=f'edge-{idx+1}',
                    object_xyz_mm=center, bed_xy_mm=bed.tolist(), radius_mm=radius,
                    head_diameter_mm=2 * radius, volume_index=-1,
                    contact_boundary_distance_mm=contact.boundary.distance(pos)))
            laps.append(dict(plate=oi+1, joint=ji, edge_length_mm=edge.length,
                exposed_edge_bed=mapping(bed_polygon(locate(edge, joint), obj)),
                lower_lap_bed_footprint=mapping(bed_polygon(lap,obj))))
        if points:
            lines.append(f'object_id={oi + 1}|' + ' '.join(' '.join(f'{v:.6f}' for v in p[:4]) + f' {p[4]}' for p in points))
        plate_records.append(dict(plate=oi+1, lower_lap_count=len(lowers), ears=len(points),
            body_contact_bed_outline=mapping(bed_polygon(contact,obj))))
    assert len(laps) == 14 and sorted(p['joint'] for p in laps) == list(range(1,15))
    assert [p['plate'] for p in plate_records if not p['ears']] == [1,6]
    files[POINTS] = ('\n'.join(lines) + '\n').encode()
    # Bambu's GUI stores custom filament order in each plate's model settings.
    # Retain the existing matching global order and explicitly persist the same
    # white-first order on every plate, including plates without lower laps.
    cfg = ET.fromstring(files['Metadata/model_settings.config'])
    for plate in cfg.findall('plate'):
        assert 'first_layer_print_sequence' not in props(plate)
        ET.SubElement(plate,'metadata',key='first_layer_print_sequence',value='1 3 2')
    files['Metadata/model_settings.config'] = shared.xml(cfg)
    for name in list(files):
        if ASSET.fullmatch(name) or name in ('Metadata/slice_info.config','Metadata/filament_sequence.json'):
            del files[name]
    files['Metadata/model_settings.config'] = re.sub(rb'\s*<metadata key="(?:gcode|thumbnail|thumbnail_no_light|top|pick)_file" value="[^"]*"\s*/>', b'', files['Metadata/model_settings.config'])
    for name in list(files):
        if name.endswith('.rels'):
            def keep(match):
                rel = ET.fromstring(match[0])
                return match[0] if rel.get('TargetMode') == 'External' or rel.get('Target').lstrip('/') in files else b''
            files[name] = re.sub(rb'<Relationship\s[^>]+/>', keep, files[name])
    write(EDIT, files, BASE)
    compare(BASE, EDIT); check_plate_order(EDIT)
    dump(REPORT / 'provenance.json', dict(source_project='Knot.3mf',source_project_sha256=SOURCE_SHA,
        editable_sha256=digest(EDIT),changed_setting=CHANGE,protected_before=protected(),
        source_catalog_entry=json.loads((ROOT/'release/root-projects/catalog.json').read_text())['Knot'],
        authorization='User: Brims only hit the corners and they are in blue, need to be white. Earlier scope: solid bottom laps on all plates.',
        ears=records,lower_laps=laps,plates=plate_records,brim_point_file_sha256=sha(files[POINTS]),
        plate_setting_change={'first_layer_print_sequence': [None,'1 3 2']},
        source_brim_points_sha256=sha(read(BASE)[POINTS]),
        intent='Overlapping native painted brim discs along all 14 lower-lap exposed edges. Maximum radius 6 mm, tapered at shoulder and trimmed in radius for bed clearance. No mesh or pose changes.',
        preview_color_diagnosis='Prior native slices used white but GUI plate order was absent. Explicit per-plate white-first order now saved; original screenshot cause not independently reproduced because UI helper failed.'))
    print(f'Built {len(records)} overlapping points over 14 lower laps; white-first order on 10 plates.',flush=True)


def native(reopen=False):
    bind()
    shared.native(reopen)


def check_order():
    """Isolate the plate order from the existing global white-first value."""
    import subprocess
    folder = WORK / 'plate-order-isolation'
    folder.mkdir(parents=True, exist_ok=True)
    files = read(EDIT)
    settings = json.loads(files['Metadata/project_settings.config'])
    assert settings['first_layer_print_sequence'] == ['1', '3', '2']
    settings['first_layer_print_sequence'] = ['0']
    files['Metadata/project_settings.config'] = json.dumps(settings, indent=2).encode()
    probe = folder / 'global-auto-plate-white.3mf'
    write(probe, files, EDIT)
    check_plate_order(probe)
    with (folder / 'run.log').open('w') as log:
        result = subprocess.run([str(shared.native_driver.EXE), '--slice', '4', '--export-3mf',
            'checked.3mf', '--outputdir', str(folder), str(probe)],
            stdout=log, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
    result.check_returncode()
    code = (folder / 'plate_4.gcode').read_text()
    paths = extrusion_paths(code)
    brim = [p for p in paths if p[1] == 'Brim']
    assert brim and {p[0] for p in brim} == {1}
    order = list(dict.fromkeys(p[0] for p in paths if p[4][2] == .2 and p[1] != 'Prime tower'))
    assert order == [1, 3]
    dump(REPORT / 'plate-order-isolation.json', dict(
        diagnostic_only=True, printer_job_sent=False, plate=4,
        source_editable_sha256=digest(EDIT), diagnostic_sha256=digest(probe),
        temporary_global_sequence=['0'], saved_plate_sequence=[1,3,2],
        actual_first_layer_order=order, brim_filament_slots=[1], brim_segments=len(brim),
        native_gcode_sha256=sha(code.encode()),
        conclusion='Native slice uses the explicit plate order even when global order is Auto.'))
    print('Per-plate white-first order works independently of the global setting.',flush=True)


def check_points(path):
    actual = read(path)[POINTS].decode().strip().splitlines()
    expected = read(EDIT)[POINTS].decode().strip().splitlines()
    assert actual[0] == expected[0] and len(actual) == len(expected)
    for a, b in zip(actual[1:], expected[1:]):
        ka, va = a.split('|'); kb, vb = b.split('|')
        assert ka == kb
        assert np.allclose(list(map(float, va.split())), list(map(float, vb.split())), atol=.00005, rtol=0)


def compare_model_paths(before, after):
    old = collections.Counter(signatures(before)); new = collections.Counter(signatures(after))
    removed, added = list((old-new).elements()), list((new-old).elements())
    changes = []
    # Native slicing can regenerate short upper shell-fill endpoints. Require
    # identical walls, joints, colors and all other model paths; explicitly
    # bound and report these fill-only differences rather than call them equal.
    assert len(removed) == len(added) <= 8, (len(removed), len(added))
    for a in removed:
        assert a[0] == 1 and a[1] == 'Floating vertical shell' and a[3][2] >= 12.6, a
        candidates = [b for b in added if a[:3] == b[:3] and (a[3] == b[3] or a[4] == b[4])]
        assert candidates, a
        b = min(candidates, key=lambda b: max(np.linalg.norm(np.array(a[k])-b[k]) for k in (3,4)))
        delta = float(max(np.linalg.norm(np.array(a[k])-b[k]) for k in (3,4)))
        assert delta <= .1 and a[3][2] == b[3][2] == a[4][2] == b[4][2], (a,b,delta)
        changes.append(dict(before=a, after=b, maximum_endpoint_change_mm=delta))
        added.remove(b)
    assert not added
    return dict(exact_segment_equality=not removed, unchanged_model_segments=sum((old & new).values()),
        exterior_walls_joint_paths_materials_and_widths_identical=True,
        upper_shell_fill_endpoint_changes=changes,
        maximum_endpoint_change_mm=max((v['maximum_endpoint_change_mm'] for v in changes), default=0))


def validate():
    bind(); shared.parser_check()
    proof = json.loads((REPORT / 'provenance.json').read_text())
    assert digest(BASE) == SOURCE_SHA and digest(EDIT) == proof['editable_sha256'] and protected() == proof['protected_before']
    check_points(WORK / 'native/sliced.3mf'); check_plate_order(WORK / 'native/sliced.3mf')
    native_check = shared.assemble()
    files = read(FINAL); files[POINTS] = read(EDIT)[POINTS]; write(FINAL, files, BASE)
    old = read(BASE); settings, objects = rows(FINAL)
    before_plates = ET.fromstring(old['Metadata/model_settings.config']).findall('plate')
    after_plates = ET.fromstring(files['Metadata/model_settings.config']).findall('plate')
    for before_plate, after_plate in zip(before_plates, after_plates):
        assert props(after_plate) == {**props(before_plate), 'first_layer_print_sequence': '1 3 2'}
    assert all(files[n] == data for n, data in old.items() if n.startswith('3D/'))
    for k, v in {**LOCKS, 'support_type': 'normal(auto)', 'support_filament': '1', 'support_interface_filament': '0',
                 'nozzle_diameter': ['0.4'], 'brim_width': '1', 'brim_object_gap': '0.1', 'brim_type': 'brim_ears',
                 'first_layer_print_sequence': ['1', '3', '2'], 'other_layers_print_sequence': ['0'], 'prime_tower_brim_width': '2'}.items():
        assert settings[k] == v, (k, settings[k])
    labels = json.loads((ROOT / 'release/knot-first-layer-labels-r1/validation.json').read_text())['labels']
    result = json.loads((WORK / 'native/result.json').read_text())
    info = ET.fromstring(files['Metadata/slice_info.config']); records = []
    for obj in objects:
        n = obj['plate']; name = f'Metadata/plate_{n}.gcode'; raw = files[name]; text = raw.decode(); oldtext = old[name].decode()
        assert shared.hashlib.md5(raw).hexdigest() == files[name + '.md5'].decode().strip().lower()
        cfg = lambda txt: dict(re.findall(r'^; ([A-Za-z_0-9]+) = (.*)$', txt, re.M))
        a, b = cfg(oldtext), cfg(text)
        delta = {k: [a.get(k), b.get(k)] for k in set(a) | set(b) if a.get(k) != b.get(k)}
        assert delta == CHANGE, (n, delta)
        paths, before = extrusion_paths(text), extrusion_paths(oldtext)
        support = support_summary(paths)
        assert set(support['Support']) == {'1'} and all('3' not in tools for tools in support.values())
        brim = [p for p in paths if p[1] == 'Brim']; ears = [e for e in proof['ears'] if e['plate'] == n]
        assert bool(brim) == bool(ears) and all(p[0] == 1 and p[4][2] == .2 for p in brim)
        assert not any(p[1] == 'Skirt' for p in paths)
        permitted = union_all([Point(e['bed_xy_mm']).buffer(e['radius_mm'] + .001) for e in ears])
        beads = union_all([LineString([p[3][:2], p[4][:2]]).buffer(p[2] / 2, cap_style=2) for p in brim])
        assert beads.difference(permitted).area < .001, (n, 'Brim outside selected lower-lap edges')
        contact = shape(proof['plates'][n - 1]['body_contact_bed_outline'])
        ear_checks = []
        for e in ears:
            ear = beads.intersection(Point(e['bed_xy_mm']).buffer(e['radius_mm'] + .001))
            assert ear.area > 1, (n, e['joint'], ear.area)
            gap = ear.distance(shape(next(l['lower_lap_bed_footprint'] for l in proof['lower_laps'] if l['joint']==e['joint'])))
            assert gap < .5, (n, e['joint'], 'Ear does not reach lower lap', gap)
            ear_checks.append(dict(joint=e['joint'], corner=e['corner'], bead_area_mm2=ear.area, distance_to_lap_contact_mm=gap))
        edge_checks = []
        for lap in [l for l in proof['lower_laps'] if l['plate'] == n]:
            edge = shape(lap['exposed_edge_bed'])
            distance = max(edge.interpolate(d).distance(beads) for d in np.linspace(0,edge.length,int(edge.length*4)+1))
            uncovered = edge.difference(beads.buffer(.7)).length
            assert distance < .7 and uncovered < .001, (n,lap['joint'],distance,uncovered)
            edge_checks.append(dict(joint=lap['joint'],edge_length_mm=edge.length,
                maximum_sampled_edge_to_brim_distance_mm=distance,uncovered_edge_mm=uncovered))
        assert beads.intersection(contact.buffer(-.1)).area < .001, (n, 'Brim inside model')
        model = [p for p in paths if p[1] not in SUPPORT | OTHER]
        oldmodel = [p for p in before if p[1] not in SUPPORT | OTHER]
        model_check = compare_model_paths(oldmodel, model)
        support_equal = signatures([p for p in paths if p[1] in SUPPORT]) == signatures([p for p in before if p[1] in SUPPORT])
        contacts = {'Support interface', 'Support transition'}
        contact_equal = signatures([p for p in paths if p[1] in contacts]) == signatures([p for p in before if p[1] in contacts])
        bed_equal = signatures([p for p in paths if p[1] == 'Support' and p[4][2] == .2]) == signatures([p for p in before if p[1] == 'Support' and p[4][2] == .2])
        assert contact_equal and bed_equal, (n, 'Support contacts changed')
        blue = [p for p in model if p[0] == 3 and p[4][2] == .2]
        mask = shape(next(l for l in labels if l['plate'] == n)['bed_outline'])
        centers = union_all([LineString([p[3][:2], p[4][:2]]) for p in blue])
        assert blue and centers.difference(mask).length < .000001
        blue_beads = union_all([LineString([p[3][:2], p[4][:2]]).buffer(p[2] / 2, cap_style=2) for p in blue])
        assert blue_beads.difference(mask.buffer(.05)).area < .001
        outer = [p for p in model if p[1] == 'Outer wall' and p[4][2] == .2 and not mask.buffer(1).intersects(LineString([p[3][:2], p[4][:2]]))]
        assert outer and {p[0] for p in outer} == {1}
        first_tools = list(dict.fromkeys(p[0] for p in paths if p[4][2] == .2 and p[1] != 'Prime tower'))
        assert first_tools == [1, 3]
        scan = scan_gcode(text)
        assert scan['model_extrusion_z_by_filament_mm']['3'] == [.2, 12.8, 13, 13.2, 13.4, 13.6]
        lo, hi = np.array(scan['bead_xy_bounds_mm']); clearance = float(min(*lo, *(np.array([330, 320]) - hi)))
        assert clearance > .5
        tr = obj['transform']
        hulls = [MultiPoint((p['mesh'].vertices @ tr[:3, :3].T + tr[:3, 3])[:, :2]).convex_hull for p in obj['parts'] if p['subtype'] == 'normal_part']
        top = max(max(z) for z in scan['model_extrusion_z_by_filament_mm'].values())
        startup = check_startup_tower(settings, hulls, 3, top, n)
        tower = check_tower(text, hulls, [0, 0, 330, 320]); tower.pop('actual_tower_convex_envelope')
        tower_beads = union_all([LineString([p[3][:2], p[4][:2]]).buffer(p[2] / 2) for p in paths if p[1] == 'Prime tower' and p[4][2] == .2])
        if ears:
            assert beads.distance(tower_beads) > 1
        pi = next(p for p in info.findall('plate') if props(p)['index'] == str(n))
        warnings = [w.attrib for w in pi.findall('warning')]
        assert all(w.get('msg') == 'not_support_traditional_timelapse' for w in warnings)
        estimate = next(p for p in result['sliced_plates'] if p['id'] == n)
        records.append(dict(plate=n, ears=len(ears), brim_white_segments=len(brim), ear_checks=ear_checks,
            lower_lap_edge_checks=edge_checks, brim_bead_area_mm2=beads.area, brim_confined_to_lower_lap_edges=True,
            source_gcode_sha256=sha(old[name]), gcode_sha256=sha(raw), md5_verified=True, gcode_setting_changes=delta,
            all_brim_white=True, all_brim_on_first_layer=True, no_skirt=True, support_after=support,
            no_blue_support_extrusion=True, blue_first_layer_confined_to_ID=True, first_layer_blue_label_segments=len(blue),
            first_layer_nonlabel_outer_walls_white=True, first_layer_filament_order=first_tools,
            model_path_geometry_materials_widths_identical=model_check['exact_segment_equality'],
            model_path_comparison=model_check, support_paths_identical=support_equal,
            interface_transition_paths_identical=contact_equal, first_layer_support_paths_identical=bed_equal,
            bed_clearance_mm=clearance, startup_tower=startup, tower=tower, warnings=warnings,
            seconds=estimate['total_predication'], grams=sum(f['total_used_g'] for f in estimate['filaments'])))
        dump(WORK / 'validation-progress.json', records)
        print(f'P{n}: {len(ears)} ears, {len(brim)} white brim paths; {len(model_check["upper_shell_fill_endpoint_changes"])} small shell-fill endpoint changes; walls/joints/support contacts preserved.', flush=True)
    native(True); check_points(WORK / 'reopen/reopened.3mf'); check_plate_order(WORK / 'reopen/reopened.3mf'); check_plate_order(FINAL)
    reopened = compare(FINAL, WORK / 'reopen/reopened.3mf')
    assert not reopened['settings_changes'] and protected() == proof['protected_before']
    order_proof = json.loads((REPORT / 'plate-order-isolation.json').read_text())
    assert order_proof['source_editable_sha256'] == digest(EDIT)
    assert order_proof['actual_first_layer_order'] == [1,3] and order_proof['brim_filament_slots'] == [1]
    dump(REPORT / 'validation.json', dict(project='Knot.3mf', project_sha256=digest(FINAL), source_project_sha256=SOURCE_SHA,
        changed_setting=CHANGE, plate_setting_change=proof['plate_setting_change'], native_plate_order_roundtrip_verified=True, native_roundtrip=native_check, native_reopen=reopened,
        fresh_native_slices=True, native_reopen_verified=True, native_brim_points_roundtrip_verified=True,
        all_other_project_settings_preserved=True, geometry_poses_paint_object_volume_overrides_preserved=True,
        all_original_3d_archive_entries_byte_identical=True, all_cad_stl_unchanged=True,
        preserved_archive_entries_sha256={n: sha(v) for n, v in old.items() if files.get(n) == v},
        brim_point_file_sha256=sha(files[POINTS]), per_plate_white_order_isolation_verified=True,
        evidence_sha256={n:digest(REPORT/n) for n in ('provenance.json','plate-order-isolation.json')},
        changed_archive_entries=sorted(n for n in set(old) | set(files) if old.get(n) != files.get(n)),
        plates=records, total_seconds=sum(p['seconds'] for p in records), total_grams=sum(p['grams'] for p in records),
        protected_after=protected(), printer_job_sent=False, physical_adhesion_and_removal_unqualified=True))
    shutil.copyfile(WORK / 'native/result.json', REPORT / 'native-result.json')
    shutil.copyfile(WORK / 'reopen/result.json', REPORT / 'native-reopen.json')


def publish():
    r = json.loads((REPORT / 'validation.json').read_text()); p = json.loads((REPORT / 'provenance.json').read_text())
    assert digest(FINAL) == r['project_sha256'] and digest(ROOT / 'Knot.3mf') == SOURCE_SHA and protected() == p['protected_before']
    catpath = ROOT / 'release/root-projects/catalog.json'; cat = json.loads(catpath.read_text())
    assert cat['Knot'] == p['source_catalog_entry']
    cat['Knot'].update(sha256=r['project_sha256'], lower_lap_edge_brim_validation='release/knot-lower-lap-brims-r2/validation.json')
    hp = ROOT / 'release/root-projects/gcode-sha256.json'; hashes = json.loads(hp.read_text())
    hashes['Knot'] = {f"plate_{v['plate']}": v['gcode_sha256'] for v in r['plates']}
    staged = WORK / 'publish.3mf'; shutil.copyfile(FINAL, staged); staged.replace(ROOT / 'Knot.3mf')
    dump(catpath, cat); dump(hp, hashes)
    shutil.copyfile(REPORT / 'native-result.json', ROOT / 'release/root-projects/Knot-native.json')
    assert protected() == p['protected_before']


def preview():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    proof = json.loads((REPORT / 'provenance.json').read_text())
    fig, axes = plt.subplots(2, 5, figsize=(17, 9), facecolor='#222831')
    for n, ax in enumerate(axes.ravel(), 1):
        paths = extrusion_paths((WORK / f'native/plate_{n}.gcode').read_text())
        first = [p for p in paths if p[4][2] == .2]
        groups = [('#8a929c', .4, [p for p in first if p[1] not in SUPPORT | OTHER and p[0] != 3]),
                  ('#606c7a', .5, [p for p in first if p[1] in SUPPORT]),
                  ('#ffffff', 1.0, [p for p in first if p[1] == 'Brim']),
                  ('#68acff', 1.0, [p for p in first if p[1] not in SUPPORT | OTHER and p[0] == 3])]
        for color, width, pool in groups:
            ax.add_collection(LineCollection([[p[3][:2], p[4][:2]] for p in pool], colors=color, linewidths=width))
        count = proof['plates'][n - 1]['ears']
        ax.set(xlim=(-8, 338), ylim=(-8, 328), aspect='equal', facecolor='#222831')
        ax.set_title(f'P{n} / F{n}: {proof["plates"][n-1]["lower_lap_count"]} lower laps' if count else f'P{n} / F{n}: no lower laps', color='white', fontsize=11)
        ax.axis('off')
    fig.suptitle('Actual first-layer extrusion: continuous white brims on 14 lower laps', color='white', fontsize=17)
    fig.text(.5, .065, 'White: lower-lap edge brims  |  Gray: body/support  |  Blue: ID', ha='center', color='white', fontsize=11)
    fig.text(.5, .035, 'All ten native slices checked. View from above; purge towers omitted. No model geometry changed.', ha='center', color='#bbc3cc', fontsize=10)
    fig.subplots_adjust(left=.015, right=.985, bottom=.13, top=.88, hspace=.30, wspace=.10)
    fig.savefig(REPORT / 'first-layer-lower-lap-brims.png', dpi=160, facecolor=fig.get_facecolor()); plt.close(fig)
    preview_detail()


def preview_detail():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    proof = json.loads((REPORT / 'provenance.json').read_text())

    # Enlarged P4 J4 view, taken from the same actual native G-code.
    paths = extrusion_paths((WORK / 'native/plate_4.gcode').read_text())
    lap = next(l for l in proof['lower_laps'] if l['plate'] == 4 and l['joint'] == 4)
    edge = shape(lap['exposed_edge_bed'])
    lines = [edge] if edge.geom_type == 'LineString' else list(edge.geoms)
    a,b = max(((np.array(a),np.array(b)) for line in lines for a,b in zip(line.coords,list(line.coords)[1:])),
        key=lambda pair: np.linalg.norm(pair[1]-pair[0]))
    origin = (a+b)/2; tangent = (b-a)/np.linalg.norm(b-a)
    inward = np.array([-tangent[1],tangent[0]])
    center = np.array(shape(lap['lower_lap_bed_footprint']).centroid.coords[0])
    if (center-origin) @ inward < 0: inward = -inward
    def planar(xy): return [float((np.array(xy)-origin) @ v) for v in (tangent,inward)]
    lap_points = np.array([planar(p) for p in shape(lap['lower_lap_bed_footprint']).exterior.coords])
    x0,y0 = lap_points.min(axis=0); x1,y1 = lap_points.max(axis=0)
    fig, ax = plt.subplots(figsize=(11, 4), facecolor='#222831')
    for color, width, pool in [
        ('#9299a2', .5, [p for p in paths if p[4][2] == .2 and p[1] not in OTHER]),
        ('white', 1.2, [p for p in paths if p[4][2] == .2 and p[1] == 'Brim'])]:
        ax.add_collection(LineCollection([[planar(p[3][:2]),planar(p[4][:2])] for p in pool], colors=color, linewidths=width))
    ax.set(xlim=(x0-8,x1+8),ylim=(y0-10,y1+10),aspect='equal',facecolor='#222831')
    ax.axis('off')
    ax.set_title('P4 / J4: continuous white brim along the lower lap',color='white',fontsize=15)
    fig.text(.5,.045,'Actual first-layer toolpaths. White: brim, filament 1. Gray: existing part/support.',
        ha='center',color='#c1c7cf',fontsize=11)
    fig.subplots_adjust(left=.03,right=.97,bottom=.18,top=.83)
    fig.savefig(REPORT / 'P4-lower-lap-detail.png',dpi=160,facecolor=fig.get_facecolor())
    plt.close(fig)


def document():
    r = json.loads((REPORT/'validation.json').read_text())
    p = json.loads((REPORT/'provenance.json').read_text())
    previous = json.loads((ROOT/'release/knot-lower-lap-brims-r1/validation.json').read_text())
    def duration(seconds):
        minutes=round(seconds/60)
        return f'{minutes//60}h {minutes%60:02d}m'
    table='\n'.join(f"| {v['plate']} | {len(v['lower_lap_edge_checks'])} | {v['brim_white_segments']} | {duration(v['seconds'])} | {v['grams']:.2f} |" for v in r['plates'])
    maxgap=max(c['maximum_sampled_edge_to_brim_distance_mm'] for v in r['plates'] for c in v['lower_lap_edge_checks'])
    maxshell=max(v['model_path_comparison']['maximum_endpoint_change_mm'] for v in r['plates'])
    text=f"""# Continuous white lower-lap brims — October 27, 2026

Current project: root **Knot.3mf**, Bambu Lab A2L, all ten plates freshly sliced.
This replaces the corner-only placement in r1 after the user reported that
brims only reached the corners and appeared blue.

## Changes

- Replace 28 isolated ears with **{len(p['ears'])} overlapping native painted
  points**, making continuous brims along the full free-end edges of all
  **14 solid lower laps**, wrapping around their corners and tapering along
  their side edges toward the shoulders. P1/P6 have only upper laps and receive
  no model brim; the rest of the part perimeter remains brimless.
- Painted radius is up to **6 mm** (roughly 5 mm of resulting outer brim),
  reducing to **2 mm** at the shoulders and as needed near the bed edge.
  No object moves. Local X0–2 is the tapered shoulder transition; the entire
  free-end edge and side edges from X2 to the tip are checked for coverage.
- Save explicit **first_layer_print_sequence = 1 3 2** on every plate.
  The matching global setting already existed. This per-plate setting is
  retained by native export and reopening, and keeps white slot1 first.
- Retain **brim_ears** mode, **0.10 mm object gap**, **0.20 mm first layer**,
  dormant ordinary brim width1 mm and the existing **2 mm purge-tower brim**.
  All global process/material settings remain byte-identical.

The prior stored G-code commanded white brims, but lacked the explicit plate
order in model metadata. The original screenshot's blue preview was not
independently reproduced: the computer-use helper returned an active-request
error through recovery attempts. This revision fixes the missing persisted
plate order and verifies actual native filament commands. It does not claim
that the screenshot was simply a display artifact.

The saved plate-order field follows Bambu's
[native project format](https://github.com/bambulab/BambuStudio/blob/master/src/libslic3r/Format/bbs_3mf.cpp)
and [plate configuration](https://github.com/bambulab/BambuStudio/blob/master/src/slic3r/GUI/PartPlate.cpp).

## Verification

- All ten fresh slices and the final project reopen natively. All painted
  coordinates and all ten custom plate orders survive the roundtrip.
- A separate native P4 diagnostic temporarily sets global order to Auto,
  keeping only the explicit plate order. It still commands white brims and
  white-then-blue on layer one. The diagnostic stays outside the production
  project; its proof is in `plate-order-isolation.json`.
- Every Brim extrusion is **white slot1** at **Z0.20** and remains inside the
  selected lower-lap edge regions. Full sampled edge coverage passes on all
  14 laps: maximum distance from checked edge to commanded brim bead is
  **{maxgap:.3f} mm**, with zero uncovered edge at a 0.70 mm search distance.
  This is spatial validation, not a physical adhesion measurement.
- All first-layer blue model extrusion remains confined to the existing ID
  glyphs. Other first-layer outer walls are white; five upper blue layers remain.
  Support base/body is white and no support feature uses blue.
- All original 3D archive entries are byte-identical: stock, joints, keys,
  grooves, all modifiers, IDs, material geometry, paint and poses remain.
  CAD/STL and all other production/sample projects retain their hashes.
- All model exterior walls, joint paths, colors and widths are preserved.
  Native upper shell-fill endpoint changes are recorded individually, with
  maximum displacement **{maxshell:.6f} mm**. Complete support hatch equality
  is recorded per plate; support interface/transition and first-layer support
  paths remain identical.
- Checksums, printable bounds, startup/purge-tower clearances and locked
  process constants pass. Native warnings contain only the existing
  traditional-timelapse notice. No printer job was sent.

![P4 actual first-layer brim detail](P4-lower-lap-detail.png)

![All ten actual first layers](first-layer-lower-lap-brims.png)

White highlights actual Brim paths; existing model/support paths are shown in
gray for contrast. Blue paths in the overview are the underside identifiers.

| Plate | Lower laps | White brim segments | Time | Material, g |
| --- | ---: | ---: | ---: | ---: |
{table}
| **Total** | **14** | | **{duration(r['total_seconds'])}** | **{r['total_grams']:.2f}** |

Compared with the isolated-ear slice: **{r['total_seconds']-previous['total_seconds']:.0f} seconds**
and **{r['total_grams']-previous['total_grams']:.2f} g** added across ten plates.
Estimates include supports and purge.

Physical adhesion, removal and full-size performance remain unqualified.
Photo-rabbet support/speed settings are unchanged by this brim correction.

Project SHA-256: `{r['project_sha256']}`.
Source SHA-256: `{SOURCE_SHA}`.
"""
    (REPORT/'README.md').write_text(text,encoding='utf-8',newline='\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('action', choices=['build', 'native', 'check_order', 'validate', 'preview', 'preview_detail', 'publish', 'document'])
    globals()[parser.parse_args().action]()
