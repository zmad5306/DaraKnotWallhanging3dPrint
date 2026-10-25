"""One-variable experiment: solid J3 laps in the accepted photo-retainer r2 crop.

Clone the accepted native project. Add local solid-fill modifiers over the actual
18 mm lap, without rebuilding any existing mesh, moving objects, or touching
production. Validate saved settings, native extrusion and native reopen.
"""
import copy
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'scripts'), str(ROOT/'.work/python-libs')]
import numpy as np
import manifold3d as mf
import shapely
from shapely.geometry import box, Point, LineString, MultiPoint
import build_joint_photo_retainer_sample as r2
from build_joint_photo_retainer_sample import base
from development_3mf import solid, mesh, mesh_xml, model, tag, xml, meta, uid, P, R, IDENTITY
from build_a2l_project import prism
from develop_m_veneer import locate
from develop_cosmetic_joints import cross_section
from organize_root_projects import rows, BOOKKEEPING
from remove_unused_project_filaments import read, write, dump, digest, props, ASSET
from audit_knot_rollback_joints import paths_with_width, key_paths, vertical_hits
from build_photo_support_test import paths as all_extrusions
from validate_print_project import scan_gcode
from check_a2l_towers import check_startup_tower, check_tower
from revert_knot_infill_first import LOCKS

ACCEPTED = base.FINAL
ACCEPTED_SHA = 'c0e48a0b2f7c8bf8adcc696b9785d4ff49359dd9104536ca486a1ec50055154d'
ACCEPTED_RECORD = base.OUT/'geometry-validation.json'
NAME = 'Dara-A2L-Joint-Solid-Laps-r3'
TITLE = 'A2L J3 - solid laps - 8% gyroid bodies - r3'
OUT = ROOT/'output'/NAME
WORK = ROOT/'.work/joint-solid-laps-r3'
EDIT = WORK/'editable.3mf'
FINAL = OUT/(NAME+'.3mf')
MOD_NAMES = ['100% solid LOWER lap - J3 - X0 to 18 mm',
             '100% solid UPPER lap - J3 - X0 to 18 mm']
base.OUT, base.WORK, base.EDIT, base.FINAL = OUT, WORK, EDIT, FINAL
base.NAME, base.TITLE = NAME, TITLE


def protected():
    paths = [base.SOURCE, ROOT/'Knot.scad', ACCEPTED, ACCEPTED_RECORD]
    paths += list((ROOT/'Knot STL').glob('*.stl'))
    return {p.relative_to(ROOT).as_posix(): digest(p) for p in paths}


def diff(a, b):
    return {k: [a.get(k), b.get(k)] for k in a.keys() | b.keys() if a.get(k) != b.get(k)}


def compare_to_accepted(path):
    s0, aa = rows(ACCEPTED); s1, bb = rows(path)
    assert diff(s0, s1) == {'print_settings_id': [s0['print_settings_id'], TITLE]}
    assert len(aa) == len(bb) == 2
    errors = []
    for k, (a, b) in enumerate(zip(aa, bb)):
        assert a['name'] == b['name'] and a['settings'] == b['settings']
        assert np.max(abs(a['transform']-b['transform'])) < .0001
        assert len(b['parts']) == len(a['parts'])+1
        for p, q in zip(a['parts'], b['parts'][:-1]):
            assert p['subtype'] == q['subtype'] and p['paint'] == q['paint']
            assert set(diff(p['settings'], q['settings'])) <= BOOKKEEPING
            assert np.array_equal(p['mesh'].faces, q['mesh'].faces)
            e = float(np.max(abs(p['mesh'].vertices-q['mesh'].vertices)))
            assert e < .0001
            errors.append(e)
        added = b['parts'][-1]
        assert added['settings']['name'] == MOD_NAMES[k] and added['subtype'] == 'modifier_part'
        assert base.effective(added['settings']) == {'sparse_infill_density': '100%', 'sparse_infill_pattern':'zig-zag'}
        assert added['paint'] == []
    return dict(original_volumes_preserved=8, max_original_vertex_error_mm=max(errors),
                original_object_settings_and_poses_preserved=True, added_local_solid_fill_modifiers=2)


def build():
    assert digest(ACCEPTED) == ACCEPTED_SHA and digest(base.SOURCE) == base.SOURCE_SHA
    OUT.mkdir(parents=True, exist_ok=True); WORK.mkdir(parents=True, exist_ok=True)
    before = protected(); original = read(ACCEPTED); files = dict(original)
    record = json.loads(ACCEPTED_RECORD.read_text()); j = record['source_joint_record']
    # A modifier is a settings mask, never added printable material. Both parts
    # receive the same XY envelope so the entire upper AND lower lap are solid.
    region = locate(box(0, -38, 18, 38), j)
    mask = mesh(prism(region, 0, 13.5))
    root = ET.fromstring(files['3D/3dmodel.model'])
    cfg = ET.fromstring(files['Metadata/model_settings.config'])
    rels = ET.fromstring(files['3D/_rels/3dmodel.model.rels'])
    for k, obj in enumerate(cfg.findall('object')):
        pid = 2001+k; path = f'3D/Objects/solid_lap_{k+1}.model'
        child = model(); resources = ET.SubElement(child, tag('resources'))
        mesh_xml(resources, pid, mask); files[path] = xml(child)
        top = root.find(tag('resources')).find(f"{tag('object')}[@id='{obj.get('id')}']")
        ET.SubElement(top.find(tag('components')), tag('component'), objectid=str(pid),
                      transform=IDENTITY, attrib={'{'+P+'}path': '/'+path, '{'+P+'}UUID': uid()})
        part = ET.SubElement(obj, 'part', id=str(pid), subtype='modifier_part')
        meta(part, 'name', MOD_NAMES[k]); meta(part, 'sparse_infill_density', '100%')
        # Native inspection of 100% gyroid showed curved infill channels, not
        # closed solid fill. Rectilinear is local to these two requested solid
        # laps; structural body and screw-bolster patterns remain untouched.
        # Bambu PrintConfig.cpp maps the Rectilinear UI label to "zig-zag".
        meta(part, 'sparse_infill_pattern', 'zig-zag')
        ET.SubElement(part, 'mesh_stat', face_count=str(len(mask.faces)), edges_fixed='0',
                      degenerate_facets='0', facets_removed='0', facets_reversed='0', backwards_edges='0')
        ET.SubElement(rels, '{'+R+'}Relationship', Target='/'+path, Id=f'rel-solid-lap-{k+1}',
                      Type='http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel')
    for node in root.findall(tag('metadata')):
        if node.get('name') == 'Title': node.text = TITLE
    settings = json.loads(files['Metadata/project_settings.config'])
    settings['print_settings_id'] = TITLE
    files['Metadata/project_settings.config'] = json.dumps(settings, indent=2).encode()
    # Delete all cached slices and thumbnails before native slicing.
    for n in list(files):
        if ASSET.fullmatch(n) or n in ('Metadata/slice_info.config', 'Metadata/filament_sequence.json'):
            del files[n]
    for plate in cfg.findall('plate'):
        for md in list(plate.findall('metadata')):
            if md.get('key') in ('gcode_file', 'thumbnail_file', 'thumbnail_no_light_file', 'top_file', 'pick_file'):
                plate.remove(md)
    for rel in list(rels):
        if rel.get('TargetMode') != 'External' and rel.get('Target').lstrip('/') not in files:
            rels.remove(rel)
    files['3D/3dmodel.model'] = xml(root)
    # Studio's relationship reader requires the default namespace spelling.
    # Also remove package thumbnail links whose old caches were discarded.
    files['3D/_rels/3dmodel.model.rels'] = xml(rels)
    for name in [n for n in files if n.endswith('.rels')]:
        clean = ET.Element('Relationships', xmlns=R)
        for rel in ET.fromstring(files[name]):
            if rel.get('TargetMode') == 'External' or rel.get('Target').lstrip('/') in files:
                ET.SubElement(clean, 'Relationship', rel.attrib)
        files[name] = xml(clean)
    files['Metadata/model_settings.config'] = xml(cfg)
    write(EDIT, files, ACCEPTED)
    unchanged = [n for n in original if n.startswith('3D/Objects/')]
    assert all(files[n] == original[n] for n in unchanged)
    comparison = compare_to_accepted(EDIT)
    record.update(accepted_sample=str(ACCEPTED.relative_to(ROOT)), accepted_sample_sha256=ACCEPTED_SHA,
        geometry_changes='No changes to any existing mesh. Two new local solid-fill lap modifiers.',
        experiment='100% rectilinear instead of 8% gyroid in both 18 mm overlapping lap sections only',
        lap_modifier_joint_local_bounds_mm=[[0,-38,0],[18,38,13.5]],
        original_mesh_archive_entries_byte_identical=unchanged, accepted_comparison=comparison,
        editable_sha256=digest(EDIT), protected_before=before)
    dump(OUT/'geometry-validation.json', record)
    assert protected() == before
    print('Cloned accepted r2; all original embedded mesh files byte-identical. Added two 100% rectilinear lap masks.', flush=True)


def path_groups(path):
    settings, objects = rows(path); files = read(path); text = files['Metadata/plate_1.gcode'].decode()
    cfg = ET.fromstring(files['Metadata/model_settings.config'])
    ids = {props(i)['object_id']: int(props(i)['identify_id']) for i in cfg.find('plate').findall('model_instance')}
    paths = [paths_with_width(text, o['transform'], ids[str(o['id'])]) for o in objects]
    return settings, objects, files, text, paths


def validate():
    record = json.loads((OUT/'geometry-validation.json').read_text()); j = record['source_joint_record']
    assert protected() == record['protected_before'] and digest(EDIT) == record['editable_sha256']
    candidate = WORK/'native/sliced.3mf'
    preservation = compare_to_accepted(candidate)
    roundtrip = base.compare_sample(EDIT, candidate)
    settings, objects, files, text, paths = path_groups(candidate)
    s0, old_objects, old_files, old_text, old_paths = path_groups(ACCEPTED)
    locks = {**LOCKS, 'support_type':'normal(auto)', 'nozzle_diameter':['0.4']}
    assert settings['printer_model'] == 'Bambu Lab A2L'
    for k,v in locks.items(): assert settings[k] == v, (k,settings[k])
    bodies = []; hulls = []; density_checks = []
    footprint = locate(box(0,-38,18,38), j)
    for k,o in enumerate(objects):
        assert o['settings']['enable_support'] == '1' and o['settings']['support_interface_spacing'] == '0.2'
        body = mf.Manifold.batch_boolean([solid(p['mesh']) for p in o['parts'] if p['subtype']=='normal_part'], mf.OpType.Add)
        bodies.append(body)
        # Native r2 has two adjacent normal volumes in F3. Preserve their saved
        # boundary/rounding exactly instead of welding or rebuilding the body.
        old_body = mf.Manifold.batch_boolean([solid(p['mesh']) for p in old_objects[k]['parts'] if p['subtype']=='normal_part'], mf.OpType.Add)
        assert np.allclose(sorted(m.volume() for m in body.decompose()),
                           sorted(m.volume() for m in old_body.decompose()),atol=.001,rtol=0)
        for part in o['parts']:
            e = {**settings, **base.effective(o['settings']), **base.effective(part['settings'])}
            expected = dict(locks)
            if part['settings'].get('name') in MOD_NAMES+['Local solid screw reinforcement']:
                expected['sparse_infill_density'] = '100%'
            if part['settings'].get('name') in MOD_NAMES:
                expected['sparse_infill_pattern'] = 'zig-zag'
            for key,value in expected.items(): assert e[key] == value, (k,key,e[key])
        mask = solid(o['parts'][-1]['mesh'])
        exact = prism(footprint,0,13.5)
        error = abs((mask-exact).volume())+abs((exact-mask).volume())
        assert error < .03, error
        assert np.allclose(o['parts'][-1]['mesh'].bounds[:,2],[0,13.5],atol=.0001)
        v = mesh(body).vertices@o['transform'][:3,:3].T+o['transform'][:3,3]
        hulls.append(MultiPoint(v[:,:2]).convex_hull)
        assert abs(v[:,2].min()) < .001
        # Every interior layer is checked, not just a percentage or feature
        # label. Studio calls even 100% rectilinear "Sparse infill" in G-code;
        # the actual swept line widths must form closed dense coverage.
        zs = sorted({round(float(p[2][1,2]),3) for p in paths[k]})
        for z in zs:
            section = cross_section(body,z-.1).intersection(footprint).buffer(-.6)
            if section.area < 1: continue
            ps = [p for p in paths[k] if abs(p[2][1,2]-z)<.001]
            lines = shapely.linestrings(np.array([p[2][:,:2] for p in ps]))
            near = shapely.intersects(lines,section)
            chosen = [(p,ln) for p,ln,hit in zip(ps,lines,near) if hit]
            assert chosen, (k,z,'Missing lap extrusion')
            bands = shapely.union_all([ln.buffer(p[3]/2,quad_segs=6) for p,ln in chosen])
            fraction = bands.intersection(section).area/section.area
            assert fraction > .98, (k,z,fraction)
            density_checks.append(dict(piece=k+1,z_mm=z,lap_interior_area_mm2=section.area,
                commanded_coverage_fraction=fraction,features=sorted({p[1] for p,ln in chosen})))
        # Surrounding body still actually emits gyroid sparse infill.
        assert any(p[1]=='Sparse infill' and LineString(p[2][:,:2]).distance(footprint)>1 for p in paths[k])
    assert hulls[0].distance(hulls[1]) > 8
    assert abs((bodies[0]^bodies[1]).volume()) < .001
    center = np.array(record['bolsters'][0]['center_assembly_mm'])
    assert Point(center).buffer(7).distance(footprint) > 20
    # This independently rechecks the actual photo-retainer blind bore, cap and
    # five-layer skin against the production project, including native paths.
    r2.target_audit()
    keychecks = []
    for ki,y in enumerate(j[5],1):
        for z in [5.2,5.4,5.6,5.8,6.0]:
            a,order = key_paths(paths[0],j,y,z); b,_ = key_paths(paths[1],j,y,z)
            gap = a.distance(b); overlap = a.intersection(b).area
            assert gap > .05 and overlap < 1e-6, (ki,z,gap,overlap)
            if order['wall_before_fill'] is not None: assert order['wall_before_fill']
            keychecks.append(dict(key=ki,z_mm=z,commanded_clearance_mm=gap,overlap_mm2=overlap,order=order))
    # Check material boundaries using the original color meshes and native
    # extrusion centerlines on both sides of the new modifier intersection.
    color_checks = []
    for k,o in enumerate(objects):
        modifiers = {int(p['settings']['extruder']):solid(p['mesh']) for p in o['parts'] if 'extruder' in p['settings']}
        count = 0
        for slot,body in modifiers.items():
            for z in sorted({round(float(p[2][1,2]),3) for p in paths[k] if p[0]==slot}):
                expected = cross_section(body,z-.1).buffer(-.5)
                if expected.is_empty: continue
                for p in paths[k]:
                    if abs(p[2][1,2]-z)>.001: continue
                    mid = Point(p[2][:,:2].mean(axis=0))
                    if expected.contains(mid):
                        assert p[0] == slot,(k,z,'Wrong color inside original color region',p[0],slot)
                        count += 1
        assert count > 0; color_checks.append(dict(piece=k+1,checked_native_segments=count))
    # Real support backing under each groove, and the original 0.20 mm air gap.
    emitted = all_extrusions(text); supportchecks = []
    angle = math.radians(j[3]); normal = np.array([math.cos(angle),math.sin(angle)])
    tangent = np.array([-normal[1],normal[0]]); tr = objects[1]['transform']
    for ki,y in enumerate(j[5],1):
        xy = np.array(j[2])+9*normal+y*tangent
        bed = (np.array([*xy,0])@tr[:3,:3].T+tr[:3,3])[:2]
        support = [p for p in emitted if p['feature']=='Support interface' and LineString(p['segment']).distance(Point(bed))<.6]
        assert support; top = max(p['z'] for p in support)
        first = min(p[2][1,2] for p in paths[1] if LineString(p[2][:,:2]).distance(Point(xy))<.6)
        assert abs(first-.2-top-.2)<.001
        supportchecks.append(dict(key=ki,interface_top_z_mm=top,first_model_layer_z_mm=float(first),air_gap_mm=float(first-.2-top)))
    scan = scan_gcode(text); lo,hi = np.array(scan['bead_xy_bounds_mm'])
    clearance = float(min(*lo,*(np.array([330,320])-hi))); assert clearance>.5
    assert scan['model_extrusion_z_by_filament_mm']['3']==[12.8,13.,13.2,13.4,13.6]
    startup = check_startup_tower(settings,hulls,3,13.6,1)
    tower = check_tower(text,hulls,[0,0,330,320]); tower.pop('actual_tower_convex_envelope')
    config = dict(re.findall(r'^; ([A-Za-z_0-9]+) = (.*)$',text,re.M))
    oldconfig = dict(re.findall(r'^; ([A-Za-z_0-9]+) = (.*)$',old_text,re.M))
    assert diff(oldconfig,config)=={'print_settings_id':[s0['print_settings_id'],TITLE]},diff(oldconfig,config)
    for key,value in locks.items(): assert config[key]==('0.4' if key=='nozzle_diameter' else value)
    raw = files['Metadata/plate_1.gcode']
    assert hashlib.md5(raw).hexdigest()==files['Metadata/plate_1.gcode.md5'].decode().strip().lower()
    warnings = [w.attrib for w in ET.fromstring(files['Metadata/slice_info.config']).iter('warning')]
    assert all(w.get('msg')=='not_support_traditional_timelapse' for w in warnings),warnings
    result = json.loads((WORK/'native/result.json').read_text()); estimate = result['sliced_plates'][0]
    assert protected()==record['protected_before']
    shutil.copyfile(candidate,FINAL); base.native(True)
    reopen = base.compare_sample(FINAL,WORK/'reopen/reopened.3mf')
    compare_to_accepted(WORK/'reopen/reopened.3mf')
    report = dict(status='DIGITAL_CHECKS_PASS_PHYSICAL_SOLID_LAP_TEST_PENDING',current_sample=FINAL.name,
        sample_sha256=digest(FINAL),accepted_sample_sha256=ACCEPTED_SHA,production_sha256=base.SOURCE_SHA,
        geometry_validation_sha256=digest(OUT/'geometry-validation.json'),accepted_preservation=preservation,
        native_roundtrip=roundtrip,native_reopen=reopen,
        changed_variable='Both overlapping 18 mm lap regions: 8% gyroid to 100% rectilinear. All existing geometry unchanged.',
        lap_density_toolpath_checks=density_checks,body_sparse_infill_retained_both_pieces=True,
        key_toolpath_checks=keychecks,color_boundary_checks=color_checks,groove_support_checks=supportchecks,
        photo_retainer_audit_sha256=digest(OUT/'photo-retainer-audit.json'),
        model_z_by_filament_mm=scan['model_extrusion_z_by_filament_mm'],bed_clearance_mm=clearance,
        startup_tower=startup,tower=tower,warnings=warnings,gcode_md5_verified=True,
        gcode_sha256=hashlib.sha256(raw).hexdigest(),gcode_global_config_changes=diff(oldconfig,config),
        estimated_seconds=estimate['total_predication'],estimated_grams=sum(f['total_used_g'] for f in estimate['filaments']),
        production_and_accepted_sample_unchanged=protected()==record['protected_before'],protected_after=protected(),
        printer_job_sent=False,physical_fit_clamping_resistance_and_surface_finish_unverified=True)
    assert report['production_and_accepted_sample_unchanged']
    dump(OUT/'validation.json',report); shutil.copyfile(WORK/'native/result.json',OUT/'native-result.json')
    for name in ['plate_1.png','top_1.png']:
        (OUT/name).write_bytes(files['Metadata/'+name])
    document(report); guide()
    print(f"Validated r3: {report['estimated_seconds']/60:.1f} minutes / {report['estimated_grams']:.2f} g.",flush=True)


def document(report):
    minutes = round(report['estimated_seconds']/60)
    (OUT/'README.md').write_text(f'''# Solid overlapping laps — r3 experiment

Use **{FINAL.name}**. Open as a **project** in Bambu Studio. One A2L plate with the same two J3 F2/F3 pieces and photo-retainer blind-hole bolster as the accepted r2 sample.

Estimate: **{minutes//60}h {minutes%60:02d}m / {report['estimated_grams']:.2f} g**, including supports and tower.

The only printing change is **100% rectilinear fill in BOTH overlapping lap sections**, joint-local X0–18 mm across the full crop width. These local settings modifiers cover Z0–13.5 and affect only existing model stock: the lower tongue, its keys, and the matching upper socket section. They add no material to the glue gap, key grooves, screw hole or photo openings. Full-thickness bodies outside the overlap remain **8% gyroid**. Rectilinear is used only in the laps because native inspection of 100% gyroid still showed open channels. This is a requested clamping experiment; resistance to deformation has not yet been physically established.

Unchanged: all eight original model/color/bolster volumes, joint clearances, crop X−14–66 / Y−38–38 mm, rotations and bed positions, materials, finish directions, normal supports, infill-first OFF, 0.4 mm nozzle, 0.20 mm layers, four walls, five top/bottom layers and Textured PEI. No new crop or translation was made. The accepted sample's recorded production source is `Knot.3mf` SHA-256 `{base.SOURCE_SHA}`.

The actual **photo-retainer bolster** is still 14 mm diameter / 100% infill, ending at **Z12.4** below the exposed Z13.5 face and its five top layers. Its 3.175 mm blind bore ends at Z10.7. This feature lies outside the solid-lap region. The native slice was checked for the capped bolster and covered face.

Remove normal supports from both grooves before dry fitting. Support also remains inside the photo-retainer blind bore; remove it from the back if checking the screw. Check joint fit and face alignment, then clamping behavior. The r2 joint-fit report does not physically qualify this new infill revision.

Validation checks all original geometry/settings against r2, dense native extrusion on every lap layer, retained sparse body infill, key clearances, material boundaries, groove backing, photo-retainer skin, bed/tower clearance, G-code checksum and native reopen. First layers over supports can use the preserved bridge spacing; a 100% modifier does not change bridge settings or promise a void-free physical print.

Production and accepted r2 remain unchanged. No print job was sent. r2 remains the accepted reference; r1 remains withdrawn for the wrong screw feature. This r3 is the current **solid-lap experiment**, not a production promotion.

- Accepted r2 SHA-256: `{ACCEPTED_SHA}`
- This r3 SHA-256: `{report['sample_sha256']}`
- Evidence: `geometry-validation.json`, `photo-retainer-audit.json`, `validation.json` and `native-result.json`.
''',encoding='utf-8',newline='\n')


def guide():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    _,objects=rows(FINAL); record=json.loads((OUT/'geometry-validation.json').read_text()); j=record['source_joint_record']
    fig,axes=plt.subplots(1,2,figsize=(12,5))
    for k,(o,ax,z) in enumerate(zip(objects,axes,[2.5,7.5])):
        body=mf.Manifold.batch_boolean([solid(p['mesh']) for p in o['parts'] if p['subtype']=='normal_part'],mf.OpType.Add)
        shape=base.local(cross_section(body,z),j)
        for geom,color in [(shape,'#cfdce4'),(shape.intersection(box(0,-38,18,38)),'#efa94c')]:
            for p in getattr(geom,'geoms',[geom]):
                if p.is_empty:continue
                ax.fill(*p.exterior.xy,color=color,ec='#52636c',lw=.6)
                for hole in p.interiors:ax.fill(*hole.xy,color='white')
        ax.axvline(0,color='#b97316',ls='--',lw=1);ax.axvline(18,color='#b97316',ls='--',lw=1)
        ax.text(9,-44,'18 mm solid lap',ha='center',fontsize=11)
        ax.set_title(['A — lower tongue: section at Z2.5','B — upper socket: section at Z7.5'][k])
        if k:
            q=base.local(Point(record['bolsters'][0]['center_assembly_mm']),j)
            ax.add_patch(plt.Circle((q.x,q.y),7,fill=False,color='#b83b3b',lw=2))
            ax.annotate('Photo-retainer bolster\ncap stays at Z12.4',xy=(q.x,q.y),xytext=(42,44),ha='center',fontsize=10,
                        arrowprops={'arrowstyle':'->','color':'#b83b3b'},color='#a12a2a')
        ax.set_xlim(-18,70);ax.set_ylim(-48,52);ax.set_aspect('equal');ax.axis('off')
    fig.suptitle('r3 — solid overlapping laps (orange); bodies retain 8% gyroid',fontsize=15)
    fig.text(.5,.02,'Actual mesh sections in assembly coordinates. Shading identifies density regions, not filament colors.',ha='center',fontsize=10)
    fig.tight_layout(rect=[0,.05,1,.93]);fig.savefig(OUT/'solid-lap-guide.png',dpi=160);plt.close(fig)


if __name__=='__main__':
    action=sys.argv[1]
    if action=='build': build()
    elif action=='slice': base.native()
    elif action=='validate': validate()
    elif action=='guide': guide()
    else: raise ValueError(action)
