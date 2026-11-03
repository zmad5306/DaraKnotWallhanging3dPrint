"""Build a small, unqualified A2L joint-clearance test; never edit production.

The user has printed only the original joint, which has a 0.005-0.007 inch
front-face lip. This candidate retains the common rear plane and introduces
0.4 mm vertical clearance over the tongue, including its pads and keys.
It requires a flat assembly surface to establish face alignment; it is not
the earlier recessed-back coupon and is not a self-registering Z joint.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'.work/python-libs'))
import numpy as np
import manifold3d as mf
from shapely.geometry import box, MultiPoint, Point
from development_3mf import solid, mesh, centered, z_rotation, write_project, sha, save_json, props
from develop_m_veneer import locate
from develop_cosmetic_joints import cross_section
from build_a2l_project import prism
from validate_production_split import Project, distance
from check_a2l_towers import check_startup_tower, check_tower
from validate_print_project import scan_gcode
from validate_ribbon_bed_datum import segments

OUT = ROOT/'working/bambu/Dara-A2L-Flush-Joint-Test'
WORK = ROOT/'.work/a2l-flush-joint-test'
EDIT = OUT/'Dara-A2L-Flush-Joint-Test-Editable.3mf'
FINAL = OUT/'Dara-A2L-Flush-Joint-Test.3mf'
A2L = ROOT/'working/bambu/Dara-Photo-Frame-A2L'
GAP = .4


def protected():
    paths = [ROOT/'Dara.3mf', A2L/'Dara-A2L-Complete.3mf', A2L/'Dara-A2L-Editable.3mf']
    paths += list((ROOT/'working/bambu/Dara-A1-Companion').glob('*'))
    return {str(p.relative_to(ROOT)): sha(p) for p in paths if p.is_file()}


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    fingerprints = protected()
    project = Project(A2L/'Dara-A2L-Editable.3mf')
    plan = json.loads((A2L/'production-plan.json').read_text())
    j = plan['frame_joints'][3]  # J4, F4 tongue -> F3 socket; straight 67 mm crossing.
    records = json.loads((A2L/'frame-geometry-validation.json').read_text())['joints'][3]
    crop_xy = locate(box(-24, -j[4]/2-1, 42, j[4]/2+1), j)
    crop = prism(crop_xy, -.01, 20)
    bodies, rows = [], []
    for index in j[:2]:
        row = project.rows[f'F{index+1} A2L knot']
        body = mf.Manifold.batch_boolean([solid(p['mesh']) for p in row['parts'] if p['subtype']=='normal_part'], mf.OpType.Add)
        bodies.append(body ^ crop)
        rows.append(row)
    male, old_female = bodies
    # Raise the solid tongue envelope, including all curved shoulders and keys.
    # The cut ends below Z8, preserving the zero-gap cosmetic seam and every
    # show face. It changes no lateral key dimensions, rear faces or hardware.
    envelope = (male ^ prism(crop_xy, -.01, 7.5)).translate([0, 0, GAP])
    female = old_female - envelope
    removed = old_female - female
    assert removed.volume() > 1
    assert (female-old_female).volume() < 1e-7
    lo, hi = np.array(removed.bounding_box()).reshape(2,3)
    assert lo[2] >= 4.19 and hi[2] < 8, (lo.tolist(),hi.tolist())
    for label, body in [('tongue',male), ('socket',female)]:
        assert len([q for q in body.decompose() if q.volume()>1e-7]) == 1, label
        assert abs(body.bounding_box()[2]) < 1e-6, (label, body.bounding_box())
    assert abs((male ^ female).volume()) < 1e-6
    assert abs((female ^ envelope).volume()) < 1e-6
    roof_checks = []
    for xy in records['seating_pads_xy']:
        assert cross_section(male, 4.99).covers(Point(xy))
        assert not cross_section(female, 5.39).covers(Point(xy))
        assert cross_section(female, 5.41).covers(Point(xy))
        roof_checks.append(dict(xy_mm=xy,tongue_top_mm=5.,socket_bottom_mm=5.4,nominal_clearance_mm=GAP))
    # Re-express the cropped parts in their joint's local XY basis.
    local = np.eye(4)
    local[:3,:3] = z_rotation(-j[3])
    local[:3,3] = -local[:3,:3] @ np.array([*j[2],0.])
    entries = []
    hulls = []
    for k,(body,row) in enumerate(zip([male,female],rows)):
        model = mesh(body).copy()
        model.apply_transform(local)
        parts = [dict(mesh=model)]
        for p in row['parts']:
            if p['subtype']=='normal_part': continue
            clipped = solid(p['mesh']) ^ crop ^ body
            if clipped.volume()<1e-7: continue
            m = mesh(clipped)
            m.apply_transform(local)
            parts.append(dict(mesh=m,subtype=p['subtype'],settings=p['settings']))
        T = centered(model, xy=[100+110*k,100])
        st = {key:value for key,value in row['settings'].items() if key and key!='name'}
        st.update(infill_direction=str((45-j[3])%180))
        entry = dict(name=['Tongue - keep flat back','Socket - relieved underside'][k],parts=parts,transform=T,settings=st)
        entries.append(entry)
        v = model.vertices @ T[:3,:3].T + T[:3,3]
        hulls.append(MultiPoint(v[:,:2]).convex_hull)
    # The native release contains Studio-normalized keys; the editable source
    # also contains obsolete profile keys that Studio drops on import.
    with zipfile.ZipFile(ROOT/'Dara.3mf') as z:
        saved_settings=json.loads(z.read('Metadata/project_settings.config'))
    settings = dict(saved_settings, wipe_tower_x=['285'],wipe_tower_y=['160'])
    title = 'A2L flush joint test - physical confirmation required'
    settings['print_settings_id'] = title
    placement = write_project(EDIT,[entries],title,settings_update=settings)
    sidecar=json.loads(EDIT.with_suffix('.json').read_text())
    sidecar.update(source_project=str((A2L/'Dara-A2L-Editable.3mf').relative_to(ROOT)),
                   source_sha256=sha(A2L/'Dara-A2L-Editable.3mf'))
    save_json(EDIT.with_suffix('.json'),sidecar)
    startup = check_startup_tower(settings,hulls,3,13.6,1)
    assert protected() == fingerprints
    save_json(OUT/'geometry-validation.json',dict(
        status='DIGITAL_GEOMETRY_PASS_PHYSICAL_TEST_REQUIRED',source_joint=4,
        source_parts=['F4','F3'],source_editable_sha256=sha(A2L/'Dara-A2L-Editable.3mf'),
        editable_sha256=sha(EDIT),reported_lip_inches=[.005,.007],reported_lip_mm=[.127,.1778],
        nominal_clearance_mm=GAP,former_pad_contacts=roof_checks,
        receiver_removed_volume_mm3=removed.volume(),removed_bounds_assembly_mm=[lo.tolist(),hi.tolist()],
        geometry_above_z8_and_below_z4_19_preserved=True,lateral_key_fit_preserved=True,
        common_flat_rear_assembly_z_mm=0,automatic_vertical_registration=False,
        alignment_method='Hold both existing flat backs against the same flat surface during fitting and adhesive cure.',
        exposed_underside_joint_gap_may_increase=True,extra_spacers=0,production_projects_modified=False,
        plates_1_to_10_not_resliced=True,protected_project_sha256=fingerprints,
        startup_tower=startup,records=placement))
    print('Created one A2L test plate with two cropped production joint parts; production unchanged.',flush=True)


def slice_plate():
    WORK.mkdir(parents=True,exist_ok=True)
    exe = Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe')
    with (WORK/'cli.log').open('w') as log:
        result = subprocess.run([str(exe),'--slice','1','--export-3mf','sliced.3mf',
                                 '--outputdir',str(WORK),str(EDIT)],cwd=exe.parent,
                                stdout=log,stderr=subprocess.STDOUT,
                                creationflags=subprocess.CREATE_NO_WINDOW)
    result.check_returncode()
    print('Native test plate slice completed.',flush=True)


def validate():
    source, native = Project(EDIT), Project(WORK/'sliced.3mf')
    assert source.rows.keys()==native.rows.keys()
    errors, hulls = [], []
    for name,row in native.rows.items():
        old = source.rows[name]
        assert len(row['parts'])==len(old['parts'])
        for p,q in zip(row['parts'],old['parts']):
            assert p['subtype']==q['subtype'] and p['mesh'].is_volume
            a=p['mesh'].vertices @ row['T'][:3,:3].T + row['T'][:3,3]
            b=q['mesh'].vertices @ old['T'][:3,:3].T + old['T'][:3,3]
            errors.append(distance(a,b))
            assert errors[-1]<.001
            if p['subtype']=='normal_part': hulls.append(MultiPoint(a[:,:2]).convex_hull)
    assert native.settings == source.settings
    raw=native.z.read('Metadata/plate_1.gcode')
    assert hashlib.md5(raw).hexdigest()==native.z.read('Metadata/plate_1.gcode.md5').decode().strip().lower()
    gcode=raw.decode()
    path=WORK/'validated-test.gcode'
    path.write_bytes(raw)
    r=scan_gcode(gcode)
    lo,hi=np.array(r['bead_xy_bounds_mm'])
    margin=float(min(*lo,*(np.array([330,320])-hi)))
    assert margin>.5
    maximum=max(max(z) for z in r['model_extrusion_z_by_filament_mm'].values())
    assert maximum<325
    assert set(r['model_extrusion_z_by_filament_mm'])=={'1','2','4'}
    r['conservative_bed_edge_clearance_mm']=margin
    tower=check_tower(gcode.replace('; LINE_WIDTH: ','; WIDTH: '),hulls,[282,157,318,197])
    record=json.loads((OUT/'geometry-validation.json').read_text())
    import xml.etree.ElementTree as ET
    info=ET.fromstring(native.z.read('Metadata/slice_info.config'))
    warnings=[w.attrib for p in info.findall('plate') for w in p.findall('warning')]
    assert all(w.get('msg')=='not_support_traditional_timelapse' for w in warnings),warnings
    ids={int(props(i)['identify_id']):props(native.configs[props(i)['object_id']])['name']
         for plate in native.cfg.findall('plate') for i in plate.findall('model_instance')}
    paths=segments(gcode,ids)
    joint=json.loads((A2L/'production-plan.json').read_text())['frame_joints'][3]
    pad_checks=[]
    surface_checks=[]
    for index,entry in enumerate(record['records']):
        name=entry['name']; T=np.array(entry['assembly_to_printer'])
        raw_paths=paths[name]
        a=np.array([p[2] for p in raw_paths]); tools=np.array([p[0] for p in raw_paths])
        start=a[:,0,:2]; delta=a[:,1,:2]-start
        length2=(delta*delta).sum(axis=1)
        assert abs(float(a[:,:,2].min())-.2)<1e-6, 'Missing bed layer'
        for point in record['former_pad_contacts']:
            local=(np.array([*point['xy_mm'],0])-np.array([*joint[2],0])) @ z_rotation(-joint[3]).T
            target=(local @ T[:3,:3].T+T[:3,3])[:2]
            along=np.clip(((target-start)*delta).sum(axis=1)/length2,0,1)
            near=np.linalg.norm(start+along[:,None]*delta-target,axis=1)<.7
            nearby=a[near]
            assert len(nearby)
            z=float(nearby[:,1,2].max() if index==0 else nearby[:,1,2].min())
            assert abs(z-(5.0 if index==0 else 5.6))<.001, (name,point,z)
            pad_checks.append(dict(part=name,xy_assembly_mm=point['xy_mm'],model_extrusion_z_mm=z,
                role='tongue pad top' if index==0 else 'first socket roof layer',support_extrusion_excluded=True))
        heights={str(slot):float(a[tools==slot,:,2].max()) for slot in [1,2,4]}
        assert heights=={'1':13.6,'2':10.0,'4':13.6}, (name,heights)
        surface_checks.append(dict(part=name,maximum_extrusion_z_by_filament_mm=heights))
    assert protected()==record['protected_project_sha256']
    # Publish only the separate test file after successful native checks.
    FINAL.write_bytes((WORK/'sliced.3mf').read_bytes())
    sidecar=json.loads(EDIT.with_suffix('.json').read_text())
    sidecar.update(source_project=str((A2L/'Dara-A2L-Editable.3mf').relative_to(ROOT)),
        source_sha256=sha(A2L/'Dara-A2L-Editable.3mf'),native_slice_validated=True,
        native_project=FINAL.name,native_sha256=sha(FINAL),physical_confirmation_pending=True)
    save_json(EDIT.with_suffix('.json'),sidecar)
    save_json(OUT/'native-validation.json',dict(status='DIGITAL_PASS_PHYSICAL_TEST_REQUIRED',
        project_sha256=sha(FINAL),editable_sha256=sha(EDIT),
        builder_sha256=sha(Path(__file__)),geometry_validation_sha256=sha(OUT/'geometry-validation.json'),
        maximum_native_mesh_pose_error_mm=max(errors),gcode_sha256=hashlib.sha256(raw).hexdigest(),
        scan=r,tower=tower,production_and_A1_preserved=True,
        joint_pad_toolpath_checks=pad_checks,actual_show_surface_heights=surface_checks,
        slicer_warnings=warnings,
        physical_underside_roughness_and_flushness_not_verified=True))
    print('Native checks passed. Separate test file saved; production and companion unchanged.',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('action',choices=['build','slice','validate'])
    a=p.parse_args()
    p.error('Withdrawn after the reported physical failure on 2026-10-19. '
            'Do not regenerate or publish this failed coupon. '
            'The separate build_simple_joint_correction.py draft is unqualified.')
