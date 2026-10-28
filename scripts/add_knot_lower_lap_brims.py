"""Add native painted ears only to the 14 current bed-contact lower laps.

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

WORK = ROOT / '.work/knot-lower-lap-brims-r1'
REPORT = ROOT / 'release/knot-lower-lap-brims-r1'
BASE, EDIT, FINAL = [WORK / n for n in ('before.3mf', 'editable.3mf', 'final.3mf')]
SOURCE_SHA = '8726fdcd42b2916d01b9656c698c738bc4ca536520af7e7abe5533f7d1d80bb6'
CHANGE = {'brim_type': ['no_brim', 'brim_ears']}
POINTS = 'Metadata/brim_ear_points.txt'
RADIUS = 6.0


def bind():
    shared.WORK, shared.EDIT, shared.FINAL, shared.BASE, shared.CHANGE = WORK, EDIT, FINAL, BASE, CHANGE


def bed_polygon(g, obj):
    t = obj['transform']
    return affinity.affine_transform(g, [t[0, 0], t[0, 1], t[1, 0], t[1, 1], t[0, 3], t[1, 3]])


def build():
    assert digest(ROOT / 'Knot.3mf') == SOURCE_SHA
    WORK.mkdir(parents=True, exist_ok=True)
    if not BASE.exists():
        shutil.copyfile(ROOT / 'Knot.3mf', BASE)
    assert digest(BASE) == SOURCE_SHA
    settings, objects = rows(BASE)
    files = read(BASE)
    assert POINTS not in files and settings['brim_type'] == 'no_brim'
    plan = json.loads((ROOT / 'working/bambu/Dara-Photo-Frame-A2L/production-plan.json').read_text())['frame_joints']
    records, plate_records, lines = [], [], ['brim_points_format_version=1']
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
            g = local(lap, joint)
            # The saved lower lap has a first-layer tip chamfer. Use its actual
            # contact, not the mask's nominal X18 silhouette, to find corners.
            x = g.bounds[2] - .01
            tip = g.intersection(LineString([(x, -200), (x, 200)]))
            assert not tip.is_empty and tip.bounds[3] - tip.bounds[1] > 50
            for side, y in [('left', tip.bounds[1]), ('right', tip.bounds[3])]:
                pos = locate(Point(x, y), joint)
                assert contact.boundary.distance(pos) < .001 and mask.buffer(.001).covers(pos)
                center = [pos.x, pos.y, -.0001]
                bed = (obj['transform'] @ np.array([*center, 1]))[:2]
                shift = 0.0
                if min(*bed, *(np.array([330, 320]) - bed)) <= RADIUS + .5:
                    # Preserve the pose and ear diameter at the one corner
                    # near the bed edge by sliding along the contact edge.
                    safe = box(RADIUS+.6, RADIUS+.6, 330-RADIUS-.6, 320-RADIUS-.6)
                    edge = bed_polygon(contact, obj).boundary.intersection(safe)
                    old_bed = Point(bed)
                    relocated = nearest_points(old_bed, edge)[1]
                    shift = old_bed.distance(relocated)
                    assert shift < 2.5
                    bed = np.array(relocated.coords[0])
                    center = (np.linalg.inv(obj['transform']) @ np.array([*bed, -.0001, 1]))[:3].tolist()
                    pos = Point(center[:2])
                    assert mask.buffer(.001).covers(pos) and contact.boundary.distance(pos) < .001
                assert min(*bed, *(np.array([330, 320]) - bed)) > RADIUS + .5, (oi+1, ji, side, bed.tolist())
                points.append([*center, RADIUS, -1])
                records.append(dict(plate=oi + 1, joint=ji, corner=side,
                    object_xyz_mm=center, bed_xy_mm=bed.tolist(), head_diameter_mm=2 * RADIUS,
                    volume_index=-1, edge_slide_for_bed_clearance_mm=shift, contact_boundary_distance_mm=contact.boundary.distance(pos),
                    lower_lap_bed_footprint=mapping(bed_polygon(lap, obj))))
        if points:
            lines.append(f'object_id={oi + 1}|' + ' '.join(' '.join(f'{v:.6f}' for v in p[:4]) + f' {p[4]}' for p in points))
        plate_records.append(dict(plate=oi + 1, lower_lap_count=len(lowers), ears=len(points),
            body_contact_bed_outline=mapping(bed_polygon(contact, obj))))
    assert len(records) == 28 and sorted({p['joint'] for p in records}) == list(range(1, 15))
    assert [r['plate'] for r in plate_records if not r['ears']] == [1, 6]
    files[POINTS] = ('\n'.join(lines) + '\n').encode()
    files['Metadata/project_settings.config'], count = re.subn(
        rb'("brim_type"\s*:\s*)"no_brim"', rb'\g<1>"brim_ears"', files['Metadata/project_settings.config'])
    assert count == 1 and json.loads(files['Metadata/project_settings.config']) == {**settings, 'brim_type': 'brim_ears'}
    for name in list(files):
        if ASSET.fullmatch(name) or name in ('Metadata/slice_info.config', 'Metadata/filament_sequence.json'):
            del files[name]
    files['Metadata/model_settings.config'] = re.sub(rb'\s*<metadata key="(?:gcode|thumbnail|thumbnail_no_light|top|pick)_file" value="[^"]*"\s*/>', b'', files['Metadata/model_settings.config'])
    for name in list(files):
        if name.endswith('.rels'):
            def keep(match):
                rel = ET.fromstring(match[0])
                return match[0] if rel.get('TargetMode') == 'External' or rel.get('Target').lstrip('/') in files else b''
            files[name] = re.sub(rb'<Relationship\s[^>]+/>', keep, files[name])
    write(EDIT, files, BASE)
    dump(REPORT / 'provenance.json', dict(source_project='Knot.3mf', source_project_sha256=SOURCE_SHA,
        editable_sha256=digest(EDIT), changed_setting=CHANGE, protected_before=protected(),
        source_catalog_entry=json.loads((ROOT / 'release/root-projects/catalog.json').read_text())['Knot'],
        authorization='User: OK do it on the solid bottom lap parts. Do it on all plates.',
        physical_report='User reports a lower-lap corner lifted on P4 and caused a failed print.',
        printed_hash_and_printer_independently_observed=False,
        ears=records, plates=plate_records, brim_point_file_sha256=sha(files[POINTS]),
        native_point_format='Bambu brim_points_format_version=1; 1-based object order; object-space XYZ, radius, volume index -1',
        native_source='https://github.com/bambulab/BambuStudio/blob/master/src/libslic3r/Format/bbs_3mf.cpp',
        intent='Two 12 mm painted ears at the actual bed-contact free-end corners of each solid lower lap. Existing 0.10 mm gap, 0.20 mm layer, white-first order; no mesh changes.'))
    print('Built 28 ears on 14 lower laps. P1/P6 have no lower laps; all ten plates will be sliced.', flush=True)


def native(reopen=False):
    bind()
    shared.native(reopen)


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
    check_points(WORK / 'native/sliced.3mf')
    native_check = shared.assemble()
    files = read(FINAL); files[POINTS] = read(EDIT)[POINTS]; write(FINAL, files, BASE)
    old = read(BASE); settings, objects = rows(FINAL)
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
        assert raw != old[name] and shared.hashlib.md5(raw).hexdigest() == files[name + '.md5'].decode().strip().lower()
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
        permitted = union_all([Point(e['bed_xy_mm']).buffer(RADIUS + .001) for e in ears])
        beads = union_all([LineString([p[3][:2], p[4][:2]]).buffer(p[2] / 2, cap_style=2) for p in brim])
        assert beads.difference(permitted).area < .001, (n, 'Brim outside selected lower-lap corners')
        contact = shape(proof['plates'][n - 1]['body_contact_bed_outline'])
        ear_checks = []
        for e in ears:
            ear = beads.intersection(Point(e['bed_xy_mm']).buffer(RADIUS + .001))
            assert ear.area > 20, (n, e['joint'], ear.area)
            gap = ear.distance(shape(e['lower_lap_bed_footprint']))
            assert gap < .5, (n, e['joint'], 'Ear does not reach lower lap', gap)
            ear_checks.append(dict(joint=e['joint'], corner=e['corner'], bead_area_mm2=ear.area, distance_to_lap_contact_mm=gap))
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
            brim_bead_area_mm2=beads.area, brim_confined_to_lower_lap_corners=True,
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
    native(True); check_points(WORK / 'reopen/reopened.3mf')
    reopened = compare(FINAL, WORK / 'reopen/reopened.3mf')
    assert not reopened['settings_changes'] and protected() == proof['protected_before']
    dump(REPORT / 'validation.json', dict(project='Knot.3mf', project_sha256=digest(FINAL), source_project_sha256=SOURCE_SHA,
        changed_setting=CHANGE, native_roundtrip=native_check, native_reopen=reopened,
        fresh_native_slices=True, native_reopen_verified=True, native_brim_points_roundtrip_verified=True,
        all_other_project_settings_preserved=True, geometry_poses_paint_object_volume_overrides_preserved=True,
        all_original_3d_archive_entries_byte_identical=True, all_cad_stl_unchanged=True,
        preserved_archive_entries_sha256={n: sha(v) for n, v in old.items() if files.get(n) == v},
        brim_point_file_sha256=sha(files[POINTS]), evidence_sha256={'provenance.json': digest(REPORT / 'provenance.json')},
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
    cat['Knot'].update(sha256=r['project_sha256'], lower_lap_brim_validation='release/knot-lower-lap-brims-r1/validation.json')
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
        for e in [e for e in proof['ears'] if e['plate'] == n]:
            x, y = e['bed_xy_mm']
            ax.add_patch(plt.Circle((x, y), 11, color='#ffd274', fill=False, linewidth=.8))
        count = proof['plates'][n - 1]['ears']
        ax.set(xlim=(-8, 338), ylim=(-8, 328), aspect='equal', facecolor='#222831')
        ax.set_title(f'P{n} / F{n}: {count} ears' if count else f'P{n} / F{n}: no lower laps', color='white', fontsize=11)
        ax.axis('off')
    fig.suptitle('Actual first-layer extrusion: 28 white ears on 14 lower laps', color='white', fontsize=17)
    fig.text(.5, .065, 'White: brim ears  |  Gold circles: location annotations  |  Gray: body/support  |  Blue: ID', ha='center', color='white', fontsize=11)
    fig.text(.5, .035, 'All ten native slices checked. View from above; purge towers omitted. No model geometry changed.', ha='center', color='#bbc3cc', fontsize=10)
    fig.subplots_adjust(left=.015, right=.985, bottom=.13, top=.88, hspace=.30, wspace=.10)
    fig.savefig(REPORT / 'first-layer-lower-lap-brims.png', dpi=160, facecolor=fig.get_facecolor()); plt.close(fig)


def document():
    r = json.loads((REPORT / 'validation.json').read_text())
    p = json.loads((REPORT / 'provenance.json').read_text())
    previous = json.loads((ROOT / 'release/knot-no-brim-r1/validation.json').read_text())
    def duration(seconds):
        minutes = round(seconds / 60)
        return f'{minutes // 60}h {minutes % 60:02d}m'
    table = '\n'.join(f"| {v['plate']} / F{v['plate']} | {v['ears']} | {v['brim_white_segments']} | {duration(v['seconds'])} | {v['grams']:.2f} g |" for v in r['plates'])
    shifted = [e for e in p['ears'] if e['edge_slide_for_bed_clearance_mm']]
    shell_changes = sum(len(v['model_path_comparison']['upper_shell_fill_endpoint_changes']) for v in r['plates'])
    largest_change = max(v['model_path_comparison']['maximum_endpoint_change_mm'] for v in r['plates'])
    adjustments = '\n'.join(f"- P{e['plate']} J{e['joint']} {e['corner']}: {e['edge_slide_for_bed_clearance_mm']:.3f} mm along the existing contact edge." for e in shifted)
    text = f'''# Knot lower-lap brim ears — October 27, 2026

Current production project: root **Knot.3mf**, Bambu Lab A2L, ten plates.

The user reported a lower-lap corner lifting on P4 and causing a failed print,
then authorized brim ears on the solid bottom laps on all plates. This is a
user-reported adhesion failure; the actual printed hash and printer were not
independently observed. The prior no-brim assessment did not establish physical
adhesion at these corners.

## Exact change

**brim_type: no_brim → brim_ears** (Bambu Studio's Painted mode). Add 28 native
brim points: two **12 mm diameter** ears at the actual first-layer free-end
corners of each of the **14 solid lower laps**. The saved bed-contact chamfer is
accounted for when locating the corners. No printable mesh is added or edited.
The ears occupy one **0.20 mm first layer**, use **white slot 1**, and keep the
saved **0.10 mm object gap**. The ordinary brim-width field remains 1 mm; native
painted points separately store their 6 mm radius.

P1 and P6 have only upper laps, so they receive no ears. The rest of every
part's perimeter stays brimless. All ten plates are freshly sliced.

Three P9 points slide slightly along the existing lower-lap contact edges to
keep the full nominal ear discs within the bed with at least 0.60 mm margin:

{adjustments}

All object poses are preserved. Ear placement is stored in
`Metadata/brim_ear_points.txt` inside the project and survives native reopening.
The [native format](https://github.com/bambulab/BambuStudio/blob/master/src/libslic3r/Format/bbs_3mf.cpp)
uses object order, XYZ, radius and volume index; the points here use object
coordinates and volume index -1.

## Preservation and checks

- All original 3D archive entries are byte-identical: stock, keys, grooves,
  removed pads, material boundaries, support paint, labels and poses remain.
- All 28 solid-lap modifiers and 50 screw modifiers retain their geometry and
  settings. Bodies remain 8% gyroid; laps remain 100% rectilinear. The screw
  modifiers retain their Z12.4 caps. CAD/STL files are unchanged.
- Exterior wall paths, joint paths, colors, feature types and widths are
  identical. Native slicing changes **{shell_changes} short upper shell-fill
  endpoints**, by at most **{largest_change:.6f} mm**. These differences are
  recorded individually in `validation.json`; those segments are not claimed identical.
  Support interface/transition paths and first-layer support paths are identical.
  Complete support-path equality is recorded separately for each plate.
- All actual Brim extrusion is white at Z0.20 and lies within the selected
  lower-lap corner discs. Each of the 28 ears has more than 20 mm2 of commanded
  bead area and lies within 0.50 mm of its intended lap's actual mesh contact;
  exact measured distances are in `validation.json`. This is a toolpath check,
  not a physical adhesion measurement.
- All support base/body extrusion remains white; no blue support extrusion is
  present. First-layer blue model extrusion remains confined to the ID glyphs.
  All other first-layer outer walls are white. Five upper blue layers remain.
- White-first order, normal supports, infill-first off, 65 C Textured PEI bed,
  all material values, finish directions and the 2 mm purge-tower brim remain.
- All ten native slices, command-stream checksums, printable bounds, startup
  and purge-tower clearance pass. Native warnings are limited to the existing
  traditional-timelapse notice. The final project and all 28 painted points
  reopen natively with settings and geometry preserved.

![Actual first-layer paths and annotated ear locations](first-layer-lower-lap-brims.png)

Gold rings are annotations around the white brim extrusion, not printed paths.
The view is from above; underside IDs are intentionally mirrored. Purge towers
are omitted from this illustration, but included in the checks and estimates.

| Plate / part | Ears | White brim segments | Time | Material |
| --- | ---: | ---: | ---: | ---: |
{table}
| **Total** | **28** | | **{duration(r['total_seconds'])}** | **{r['total_grams']:.2f} g** |

Compared with the previous no-brim slice: **{r['total_seconds'] - previous['total_seconds']:.0f} seconds**
and **{r['total_grams'] - previous['total_grams']:.2f} g** added across all ten plates.
These are slicer estimates including supports and purge.

Physical ear adhesion, removal and full-size joint performance remain
unqualified. No printer job was sent.

Project SHA-256: `{r['project_sha256']}`.
Source SHA-256: `{SOURCE_SHA}`.
'''
    (REPORT / 'README.md').write_text(text, encoding='utf-8', newline='\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('action', choices=['build', 'native', 'validate', 'preview', 'publish', 'document'])
    globals()[parser.parse_args().action]()
