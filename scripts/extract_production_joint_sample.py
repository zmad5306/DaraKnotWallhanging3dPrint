"""Crop J4 directly from saved Dara.3mf without changing its joint design."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import xml.etree.ElementTree as ET
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.work/python-libs'))
import numpy as np
import manifold3d as mf
from shapely.geometry import box,MultiPoint,Point
from development_3mf import (solid,mesh,centered,write_project,sha,save_json,
                             read_object,tag,props,transform,P)
from develop_m_veneer import locate
from develop_cosmetic_joints import cross_section
from build_a2l_project import prism
from validate_a2l_project import embedded
from scipy.spatial import cKDTree
from validate_ribbon_bed_datum import segments
from validate_print_project import scan_gcode
from check_a2l_towers import check_startup_tower,check_tower

SOURCE=ROOT/'Dara.3mf'
OUT=ROOT/'working/bambu/Dara-A2L-Production-Joint-Sample'
WORK=ROOT/'.work/a2l-production-joint-sample'
EDIT=OUT/'Dara-A2L-Production-Joint-Sample-Editable.3mf'
FINAL=OUT/'Dara-A2L-Production-Joint-Sample.3mf'
NAMES=['F4 A2L knot','F3 A2L knot']


def protected():
    a2l=ROOT/'working/bambu/Dara-Photo-Frame-A2L'
    paths=[SOURCE,a2l/'Dara-A2L-Complete.3mf',a2l/'Dara-A2L-Editable.3mf']
    paths+=list((ROOT/'working/bambu/Dara-A1-Companion').glob('*'))
    return {str(p.relative_to(ROOT)):sha(p) for p in paths if p.is_file()}


def Project(path):
    files,rows=embedded(path)
    cfg=ET.fromstring(files['Metadata/model_settings.config'])
    return SimpleNamespace(settings=json.loads(files['Metadata/project_settings.config']),cfg=cfg,
        configs={o.get('id'):o for o in cfg.findall('object')},z=zipfile.ZipFile(path),
        rows={name:dict(parts=row['parts'],settings=row['settings'],T=row['transform']) for name,row in rows.items()})


def distance(a,b):
    return float(max(cKDTree(a).query(b)[0].max(),cKDTree(b).query(a)[0].max()))


def source_rows(names=NAMES):
    """Read only the two native production objects, including their volumes."""
    with zipfile.ZipFile(SOURCE) as z:
        files={n:z.read(n) for n in ['3D/3dmodel.model','Metadata/model_settings.config']}
        settings=json.loads(z.read('Metadata/project_settings.config'))
        root=ET.fromstring(files['3D/3dmodel.model']);cfg=ET.fromstring(files['Metadata/model_settings.config'])
        configs={props(o).get('name'):o for o in cfg.findall('object')}
        objects={o.get('id'):o for o in root.find(tag('resources'))}
        items={o.get('objectid'):o for o in root.find(tag('build'))}
        plates={props(i)['object_id']:pi for pi,pl in enumerate(cfg.findall('plate')) for i in pl.findall('model_instance')}
        area=np.array([[float(x) for x in q.split('x')] for q in settings['printable_area']])
        pitch=np.ptp(area,axis=0)*1.2;cols=math.ceil(math.sqrt(len(cfg.findall('plate'))))
        rows=[]
        for name in names:
            oid=configs[name].get('id')
            for co in objects[oid].find(tag('components')):
                path=co.get('{'+P+'}path').lstrip('/')
                if path not in files:files[path]=z.read(path)
                child=ET.fromstring(files[path]).find(tag('resources')).find(f"{tag('object')}[@id='{co.get('objectid')}']")
                # This extraction preserves volume-based color/settings. Fail
                # rather than silently discard future per-triangle painting.
                assert all(set(t.attrib)=={'v1','v2','v3'} for t in child.find(tag('mesh')).find(tag('triangles')))
            parts,st=read_object(files,oid)
            T=transform(items[oid].get('transform'));pi=plates[oid]
            T[:2,3]-=[pi%cols*pitch[0],-(pi//cols)*pitch[1]]
            rows.append(dict(name=name,parts=parts,settings={k:v for k,v in st.items() if k},T=T,plate=pi+1))
    return rows,settings


def build():
    OUT.mkdir(parents=True,exist_ok=True);WORK.mkdir(parents=True,exist_ok=True)
    fingerprints=protected();rows,settings=source_rows()
    plan=json.loads((ROOT/'working/bambu/Dara-Photo-Frame-A2L/production-plan.json').read_text())
    j=plan['frame_joints'][3]
    # Cut at the straight ribbon span. The previous extra 1 mm on each side
    # caught adjacent rounded openings in the knot, creating scalloped
    # sample edges. Crop only: do not fill, reshape or relieve production.
    crop=prism(locate(box(-24,-j[4]/2,42,j[4]/2),j),-.01,20)
    entries=[];checks=[];hulls=[];bodies=[]
    for k,row in enumerate(rows):
        parts=[];part_checks=[];models=[]
        for index,p in enumerate(row['parts']):
            clipped=solid(p['mesh']) ^ crop
            if clipped.volume()<1e-7:continue
            m=mesh(clipped)
            regenerated=solid(m)
            added=(regenerated-clipped).volume();removed=(clipped-regenerated).volume()
            assert max(abs(added),abs(removed))<1e-5
            parts.append(dict(mesh=m,subtype=p['subtype'],settings=p['settings']))
            part_checks.append(dict(source_volume_index=index,subtype=p['subtype'],
                                   settings={key:v for key,v in p['settings'].items() if key},
                                   crop_volume_mm3=clipped.volume(),added_mm3=added,removed_mm3=removed))
            if p['subtype']=='normal_part':models.append(clipped)
        body=mf.Manifold.batch_boolean(models,mf.OpType.Add);bodies.append(body)
        assert len([q for q in body.decompose() if q.volume()>1e-7])==1
        # Translation-only bed repositioning; each saved production rotation
        # and infill direction is retained independently.
        T=centered(mesh(body),rotation=row['T'][:3,:3],xy=[98+107*k,110])
        assert np.array_equal(T[:3,:3],row['T'][:3,:3])
        settings_obj={key:v for key,v in row['settings'].items() if key!='name'}
        entries.append(dict(name=['J4 F4 production tongue','J4 F3 production socket'][k],
                            parts=parts,transform=T,settings=settings_obj))
        v=mesh(body).vertices@T[:3,:3].T+T[:3,3]
        hulls.append(MultiPoint(v[:,:2]).convex_hull)
        checks.append(dict(source_name=row['name'],source_plate=row['plate'],
                           source_rotation=row['T'][:3,:3].tolist(),settings=settings_obj,volumes=part_checks))
    assert (bodies[0]^bodies[1]).volume()<1e-5
    from add_blue_ribbon_edge import artwork
    white_outline=artwork((ROOT/'working/Dara-Photo-Frame-A1-Jointed.scad').read_text(),'knot_outline')
    side_checks=[]
    for z in [8.5,13.4]:
        actual=cross_section(bodies[0],z).union(cross_section(bodies[1],z))
        for sign in [-1,1]:
            y0,y1=(j[4]/2-.2,j[4]/2) if sign>0 else (-j[4]/2,-j[4]/2+.2)
            strip=locate(box(-23.9,y0,41.9,y1),j)
            # Brown fabric ends at Z9.9; it is intentionally absent from the
            # higher white-ribbon section. Check only white artwork there.
            if z>10:strip=strip.intersection(white_outline)
            missing=strip.buffer(-.001).difference(actual.buffer(.001)).area
            assert missing<1e-7,(z,sign,missing)
            side_checks.append(dict(z_mm=z,side=sign,missing_side_strip_mm2=missing,tolerance_mm=.002))
    pads=json.loads((ROOT/'working/bambu/Dara-Photo-Frame-A2L/frame-geometry-validation.json').read_text())['joints'][3]['seating_pads_xy']
    for xy in pads:
        assert cross_section(bodies[0],4.99).covers(Point(xy))
        assert cross_section(bodies[1],5.01).covers(Point(xy))
        assert not cross_section(bodies[1],4.99).covers(Point(xy))
    title='A2L production J4 joint sample - direct crop'
    settings=dict(settings,print_settings_id=title,wipe_tower_x=['285'],wipe_tower_y=['160'])
    records=write_project(EDIT,[entries],title,settings_update=settings)
    with zipfile.ZipFile(EDIT) as z:assert json.loads(z.read('Metadata/project_settings.config'))==settings
    startup=check_startup_tower(settings,hulls,3,13.6,1)
    assert protected()==fingerprints
    save_json(OUT/'geometry-validation.json',dict(status='PASS_UNALTERED_PRODUCTION_EXTRACTION',
        source_project='Dara.3mf',source_sha256=sha(SOURCE),joint='J4',source_parts=NAMES,
        source_joint_record=j,crop_joint_local_xy_mm=[[-24,-j[4]/2],[42,j[4]/2]],
        sample_crop_revision='straight-ribbon-span-v2',straight_sample_side_checks=side_checks,
        joint_geometry_modified=False,material_modifiers_preserved=True,
        production_print_rotations_preserved=True,production_infill_directions_preserved=True,
        global_setting_changes=['print_settings_id','wipe_tower_x','wipe_tower_y'],
        source_volume_checks=checks,seating_pad_xy_mm=pads,original_pad_contact_z_mm=5.,
        records=records,startup_tower=startup,editable_sha256=sha(EDIT),protected_project_sha256=fingerprints))
    side=json.loads(EDIT.with_suffix('.json').read_text());side.update(source_project='Dara.3mf',source_sha256=sha(SOURCE),joint_geometry_modified=False)
    save_json(EDIT.with_suffix('.json'),side)
    print('Extracted unmodified J4 from Dara.3mf; preserved native volumes, settings and print rotations.',flush=True)


def slice_plate():
    exe=Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe')
    with (WORK/'cli.log').open('w') as log:
        r=subprocess.run([str(exe),'--slice','1','--export-3mf','sliced.3mf','--outputdir',str(WORK),str(EDIT)],
                         cwd=exe.parent,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    r.check_returncode();print('Production sample sliced locally.',flush=True)


def validate():
    src=Project(EDIT);native=Project(WORK/'sliced.3mf')
    record=json.loads((OUT/'geometry-validation.json').read_text())
    assert sha(SOURCE)==record['source_sha256']
    assert src.settings==native.settings
    errors=[];hulls=[]
    for name,row in native.rows.items():
        old=src.rows[name]
        for key,value in old['settings'].items():
            if key=='infill_direction':assert float(value)==float(row['settings'][key])
            elif key:assert row['settings'][key]==value,(name,key)
        assert len(row['parts'])==len(old['parts'])
        for a,b in zip(row['parts'],old['parts']):
            assert a['subtype']==b['subtype'] and a['mesh'].is_volume
            for key in ['extruder','sparse_infill_density']:
                assert a['settings'].get(key)==b['settings'].get(key)
            va=a['mesh'].vertices@row['T'][:3,:3].T+row['T'][:3,3]
            vb=b['mesh'].vertices@old['T'][:3,:3].T+old['T'][:3,3]
            errors.append(distance(va,vb));assert errors[-1]<.001
            if a['subtype']=='normal_part':hulls.append(MultiPoint(va[:,:2]).convex_hull)
    raw=native.z.read('Metadata/plate_1.gcode');gcode=raw.decode()
    assert hashlib.md5(raw).hexdigest()==native.z.read('Metadata/plate_1.gcode.md5').decode().strip().lower()
    scan=scan_gcode(gcode);lo,hi=np.array(scan['bead_xy_bounds_mm'])
    scan['conservative_bed_edge_clearance_mm']=float(min(*lo,*(np.array([330,320])-hi)))
    assert scan['conservative_bed_edge_clearance_mm']>.5
    assert set(scan['model_extrusion_z_by_filament_mm'])=={'1','2','4'}
    assert max(max(v) for v in scan['model_extrusion_z_by_filament_mm'].values())<325
    assert scan['features'].get('Support',0)>0 and scan['features'].get('Support interface',0)>0
    tower=check_tower(gcode.replace('; LINE_WIDTH: ','; WIDTH: '),hulls,[282,157,318,197])
    ids={int(props(i)['identify_id']):props(native.configs[props(i)['object_id']])['name'] for pl in native.cfg.findall('plate') for i in pl.findall('model_instance')}
    paths=segments(gcode,ids);surface=[];pad_checks=[]
    for k,entry in enumerate(record['records']):
        name=entry['name'];T=np.array(entry['assembly_to_printer'])
        a=np.array([r[2] for r in paths[name]]);slots=np.array([r[0] for r in paths[name]])
        heights={str(slot):float(a[slots==slot,:,2].max()) for slot in [1,2,4]}
        assert heights=={'1':13.6,'2':10.,'4':13.6},(name,heights)
        surface.append(dict(name=name,maximum_model_z_by_filament_mm=heights))
        start=a[:,0,:2];delta=a[:,1,:2]-start;length2=(delta*delta).sum(axis=1)
        for xy in record['seating_pad_xy_mm']:
            target=(np.array([*xy,0])@T[:3,:3].T+T[:3,3])[:2]
            t=np.clip(((target-start)*delta).sum(axis=1)/length2,0,1)
            near=np.linalg.norm(start+t[:,None]*delta-target,axis=1)<.7
            z=float(a[near,:,2].max() if k==0 else a[near,:,2].min())
            assert abs(z-(5. if k==0 else 5.2))<.001,(name,xy,z)
            pad_checks.append(dict(name=name,xy_assembly_mm=xy,model_extrusion_z_mm=z))
    info=ET.fromstring(native.z.read('Metadata/slice_info.config'))
    warnings=[w.attrib for pl in info.findall('plate') for w in pl.findall('warning')]
    assert all(w.get('msg')=='not_support_traditional_timelapse' for w in warnings),warnings
    assert protected()==record['protected_project_sha256']
    FINAL.write_bytes((WORK/'sliced.3mf').read_bytes())
    result=json.loads((WORK/'result.json').read_text())['sliced_plates'][0]
    seconds=result['total_predication'];grams=sum(f['total_used_g'] for f in result['filaments'])
    save_json(OUT/'native-validation.json',dict(status='PASS_PRODUCTION_SAMPLE_EXTRACTION_AND_SLICE',
        source_project='Dara.3mf',source_sha256=sha(SOURCE),sample_sha256=sha(FINAL),
        editable_sha256=sha(EDIT),geometry_validation_sha256=sha(OUT/'geometry-validation.json'),builder_sha256=sha(Path(__file__)),
        maximum_native_mesh_pose_error_mm=max(errors),scan=scan,tower=tower,surface_heights=surface,pad_toolpaths=pad_checks,
        slicer_metadata_warnings=warnings,estimated_seconds=seconds,estimated_grams=grams,
        production_and_A1_preserved=True,joint_geometry_modified=False,physical_fit_unverified=True,
        printer_commands_sent=False,new_GUI_warning_check_performed=False))
    side=json.loads(EDIT.with_suffix('.json').read_text());side.update(native_slice_validated=True,native_project=FINAL.name,native_sha256=sha(FINAL))
    save_json(EDIT.with_suffix('.json'),side)
    for name in ['plate_1.png','top_1.png']:(OUT/('saved-'+name)).write_bytes(native.z.read('Metadata/'+name))
    print(f'Validated production sample: {seconds/60:.1f} minutes, {grams:.1f} g. Production and A1 unchanged.',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['build','slice','validate'])
    {'build':build,'slice':slice_plate,'validate':validate}[p.parse_args().action]()
