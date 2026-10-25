"""Current production J2 crop with both keys and one complete screw bolster.

Source is the saved root Knot, never a historical approximation. Only cropping,
translation-only plate placement, sample naming and tower-array packaging vary.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'.work/python-libs'),str(ROOT/'scripts')]
import numpy as np
import manifold3d as mf
import shapely
from shapely import affinity
from shapely.geometry import box,LineString,Point,MultiPoint,mapping
import development_3mf as dev
from development_3mf import solid,mesh,centered
from organize_root_projects import rows,compare,BOOKKEEPING
from remove_unused_project_filaments import read,write,digest,dump,props,EXE
from develop_m_veneer import locate
from develop_cosmetic_joints import cross_section
from build_a2l_project import prism
from check_a2l_towers import check_startup_tower,check_tower
from revert_knot_infill_first import protected as other_files,LOCKS

NAME='Dara-A2L-Joint-Screw-Bolster-r1'
TITLE='A2L J2 joint and screw bolster - 8% gyroid - r1'
SOURCE=ROOT/'Knot.3mf'
SOURCE_SHA='aefab9b242945a149fdc18900c694c556eb7ad5d8d5d5f7fbc4451280730ae46'
OUT=ROOT/'output'/NAME
WORK=ROOT/'.work/joint-screw-bolster-r1'
EDIT=WORK/'editable.3mf'
FINAL=OUT/(NAME+'.3mf')
PLAN=ROOT/'working/bambu/Dara-Photo-Frame-A2L/production-plan.json'
CROP=(-18.,-32.,44.,48.)
CENTERS=[[90.,110.],[210.,110.]]
NAMES=['A - J2 F3 tongue','B - J2 F1 socket and screw bolster']
JOINT_INDEX=1
ALLOW_SOURCE_OPENINGS=False
REQUIRE_PHOTO_RETAINER=False
WITHDRAWN=True  # r1 selected an M through-hole; use the photo-retainer r2 wrapper.


def protected():
    return {**other_files(),'Knot.3mf':digest(SOURCE)}


def effective(s):
    return {k:v for k,v in s.items() if k not in BOOKKEEPING}


def local(g,j):
    return affinity.rotate(affinity.translate(g,-j[2][0],-j[2][1]),-j[3],origin=(0,0))


def build():
    assert not WITHDRAWN,'r1 is withdrawn: wrong screw feature. Use build_joint_photo_retainer_sample.py.'
    assert digest(SOURCE)==SOURCE_SHA
    WORK.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
    before=protected();settings,objects=rows(SOURCE)
    plan=json.loads(PLAN.read_text());j=plan['frame_joints'][JOINT_INDEX]
    region=locate(box(*CROP),j);crop=prism(region,-.01,20)
    entries=[];checks=[];bodies=[];hulls=[];bolsters=[]
    for k,oi in enumerate(j[:2]):
        obj=objects[oi];parts=[];records=[];model=[]
        for vi,p in enumerate(obj['parts']):
            assert not p['paint'],'Preserve source paint explicitly before cropping a painted revision.'
            original=solid(p['mesh']);clipped=original^crop
            if clipped.volume()<1e-7:continue
            m=mesh(clipped);roundtrip=solid(m)
            error=abs((roundtrip-clipped).volume())+abs((clipped-roundtrip).volume())
            assert error<1e-5
            outside=abs((roundtrip-original).volume());assert outside<1e-5
            parts.append(dict(mesh=m,subtype=p['subtype'],settings=p['settings']))
            records.append(dict(source_volume_index=vi,source_settings=p['settings'],subtype=p['subtype'],
                crop_volume_mm3=clipped.volume(),crop_roundtrip_error_mm3=error,added_outside_source_mm3=outside))
            if p['subtype']=='normal_part':model.append(clipped)
            if p['settings'].get('name')=='Local solid screw reinforcement':
                assert abs(original.volume()-clipped.volume())<1e-5,'Do not retain a partial bolster.'
                assert p['settings']['sparse_infill_density']=='100%'
                assert np.allclose(m.bounds[:,2],[0,12.4],atol=1e-6)
                b=m.bounds;center=b[:,:2].mean(axis=0);radius=float(np.ptp(b[:,0])/2)
                assert region.boundary.distance(Point(center))>radius+4
                bolsters.append(dict(object=NAMES[k],source_object=obj['name'],center_assembly_mm=center.tolist(),
                    radius_mm=radius,z_mm=[0,12.4],source_volume_index=vi,complete_modifier_retained=True,
                    crop_clearance_beyond_modifier_mm=region.boundary.distance(Point(center))-radius))
        body=mf.Manifold.batch_boolean(model,mf.OpType.Add);bodies.append(body)
        assert len([b for b in body.decompose() if b.volume()>1e-7])==1
        t=centered(mesh(body),rotation=obj['transform'][:3,:3],xy=CENTERS[k])
        assert np.array_equal(t[:3,:3],obj['transform'][:3,:3]) and abs(t[2,3]-obj['transform'][2,3])<1e-6
        st={a:b for a,b in obj['settings'].items() if a not in (None,'name')}
        entries.append(dict(name=NAMES[k],parts=parts,settings=st,transform=t))
        vertices=mesh(body).vertices@t[:3,:3].T+t[:3,3]
        hulls.append(MultiPoint(vertices[:,:2]).convex_hull)
        checks.append(dict(source_name=obj['name'],source_plate=obj['plate'],source_object_settings=obj['settings'],
            source_rotation=obj['transform'][:3,:3].tolist(),translation_delta_mm=(t[:3,3]-obj['transform'][:3,3]).tolist(),
            volume_crops=records,model_volume_mm3=body.volume(),bed_contact_area_mm2=cross_section(body,.1).area))
    assert len(bolsters)==1 and bolsters[0]['object']==NAMES[1]
    photo_identity=None
    if REQUIRE_PHOTO_RETAINER:
        from audit_knot_rollback_joints import vertical_hits
        anchors=(np.array(plan['photo_anchors_mm'])+np.array(plan['photo_normals'])*9.5).reshape(-1,2)
        bolster=bolsters[0];center=np.array(bolster['center_assembly_mm']);distances=np.linalg.norm(anchors-center,axis=1)
        index=int(distances.argmin());assert distances[index]<.0001
        assert abs(bolster['radius_mm']-7)<.0001
        assert min(np.linalg.norm(np.array(r[2])-center) for r in plan['screw_mounts'])>15
        heights=vertical_hits(mesh(bodies[1]),center)
        assert np.allclose(heights,[10.7,13.5],atol=.0001),heights
        for z in [.1,5.5,10.6]:
            section=cross_section(bodies[1],z)
            void=LineString([center+[-3,0],center+[3,0]]).difference(section)
            assert abs(void.length-3.175)<.001,(z,void.length)
        face=cross_section(bodies[1],13.4)
        assert Point(center).buffer(7).difference(face).area<.0001
        photo_identity=dict(role='PHOTO_RETAINER_BLIND_SCREW_HOLE',production_photo_anchor_flat_index=index,
            production_photo_anchor_mm=anchors[index].tolist(),modifier_center_error_mm=float(distances[index]),
            blind_hole_diameter_mm=3.175,blind_hole_end_z_mm=heights[0],show_face_z_mm=heights[1],
            material_over_blind_hole_mm=heights[1]-heights[0],modifier_radius_mm=7,
            modifier_cap_z_mm=12.4,full_modifier_footprint_has_unbroken_show_face=True,
            matches_M_mount=False)
    assert hulls[0].distance(hulls[1])>8
    # A boundary may meet the real outer edge, but must not split a photo hole
    # into an artificial side notch. Each crop edge has one material interval.
    side_checks=[]
    x0,y0,x1,y1=CROP
    edges=[[(x0,y0),(x1,y0)],[(x0,y1),(x1,y1)],[(x0,y0),(x0,y1)],[(x1,y0),(x1,y1)]]
    if ALLOW_SOURCE_OPENINGS:
        source_bodies=[mf.Manifold.batch_boolean([solid(p['mesh']) for p in objects[oi]['parts'] if p['subtype']=='normal_part'],mf.OpType.Add) for oi in j[:2]]
    for z in [.1,2.5,8.5]:
        g=local(shapely.union_all([cross_section(b,z) for b in bodies]),j).buffer(.001)
        if ALLOW_SOURCE_OPENINGS:source_g=local(shapely.union_all([cross_section(b,z) for b in source_bodies]),j).buffer(.001)
        for ei,ends in enumerate(edges):
            hit=LineString(ends).intersection(g)
            if not ALLOW_SOURCE_OPENINGS:
                assert hit.geom_type=='LineString' and hit.length>10,(z,ei,hit.wkt)
            else:
                # Retain the real photo-opening edge next to its retainer.
                # Prove each apparent side notch already exists in production.
                expected=LineString(ends).intersection(source_g)
                assert hit.symmetric_difference(expected).length<.001
            side_checks.append(dict(z_mm=z,edge=ei,material_interval_mm=hit.length,geometry=hit.wkt,
                source_photo_opening_retained=ALLOW_SOURCE_OPENINGS))
    # Keep both complete key/pocket footprints, with clearance to crop edges.
    key_checks=[]
    for ki,y in enumerate(j[5],1):
        for z in [5.1,5.3,5.5,5.7,5.9]:
            a,b=[local(cross_section(q,z),j) for q in bodies]
            key=a.intersection(box(1,y-3.5,17,y+3.5));gap=key.distance(b)
            assert key.area>30 and gap>.14
            for x in [3.5,9,14.5]:
                line=LineString([(x,y-3.5),(x,y+3.5)])
                male=a.intersection(line);female=line.difference(b)
                if female.geom_type=='MultiLineString':female=next(g for g in female.geoms if g.distance(Point(x,y))<.0001)
                assert abs((male.bounds[3]-male.bounds[1])-3)<.001
                assert female.length>3.29
            key_checks.append(dict(key=ki,z_mm=z,minimum_section_clearance_mm=gap))
    updates=copy.deepcopy(settings)
    updates.update(print_settings_id=TITLE,wipe_tower_x=['285'],wipe_tower_y=['160'])
    source_files=read(SOURCE)
    dev.source=lambda:{n:source_files[n] for n in ('Metadata/project_settings.config','[Content_Types].xml')}
    dev.source_path=lambda:SOURCE
    records=dev.write_project(EDIT,[entries],TITLE,settings_update=updates)
    files=read(EDIT);cfg=ET.fromstring(files['Metadata/model_settings.config'])
    for md in cfg.find('plate').findall('metadata'):
        if md.get('key')=='filament_maps':md.set('value','1 1 1')
        if md.get('key')=='filament_volume_maps':md.set('value','0 0 0')
    files['Metadata/model_settings.config']=ET.tostring(cfg,encoding='utf-8',xml_declaration=True)
    # Write to a separate archive, then replace; never read and truncate one ZIP.
    staged=WORK/'edited.3mf';write(staged,files,EDIT);staged.replace(EDIT)
    assert json.loads(read(EDIT)['Metadata/project_settings.config'])==updates
    differences={k:[settings.get(k),updates.get(k)] for k in set(settings)|set(updates) if settings.get(k)!=updates.get(k)}
    assert set(differences)=={'print_settings_id','wipe_tower_x','wipe_tower_y'}
    maximum_model_z=max(r['body_bounds_mm'][1][2] for r in records)
    startup=check_startup_tower(updates,hulls,3,math.ceil(maximum_model_z/.2)*.2,1)
    assert protected()==before
    dump(OUT/'geometry-validation.json',dict(source_project='Knot.3mf',source_sha256=SOURCE_SHA,
        joint=f'J{JOINT_INDEX+1}',source_joint_record=j,source_plan_sha256=digest(PLAN),source_parts=[objects[i]['name'] for i in j[:2]],
        crop_joint_local_xy_mm=[[x0,y0],[x1,y1]],crop_assembly_polygon=mapping(region),crop_z_mm=[-.01,20],
        geometry_changes='Cropping only; production joint, clearances and complete screw bolster unchanged',
        sample_dimensions_local_mm=[x1-x0,y1-y0,maximum_model_z],nominal_show_face_mm=13.5,photo_retainer_identity=photo_identity,
        existing_alignment_pin_retained=maximum_model_z>13.6,side_cut_checks=side_checks,key_geometry_checks=key_checks,
        bolsters=bolsters,source_volume_checks=checks,records=records,global_setting_changes=differences,
        sample_slot_mapping={'1':'white','2':'wood tan','3':'Azurite blue'},startup_tower=startup,
        editable_sha256=digest(EDIT),protected_before=before,physical_fit_and_finish_unverified=True))
    print(f'Built J{JOINT_INDEX+1}: both original keys and the required screw feature; source-derived crop only.',flush=True)


def native(reopen=False):
    assert not WITHDRAWN,'r1 is withdrawn: wrong screw feature.'
    folder=WORK/('reopen' if reopen else 'native');folder.mkdir(exist_ok=True)
    args=['--info','--export-3mf','reopened.3mf'] if reopen else ['--slice','0','--export-3mf','sliced.3mf']
    for attempt in range(3):
        with (folder/f'run-{attempt+1}.log').open('w') as log:
            result=subprocess.run([str(EXE),*args,'--outputdir',str(folder),str(FINAL if reopen else EDIT)],
                cwd=EXE.parent,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        if result.returncode!=3221225477:break
    result.check_returncode();data=json.loads((folder/'result.json').read_text());assert data['return_code']==0
    if not reopen:assert [p['id'] for p in data['sliced_plates']]==[1]
    print('Native reopen passed.' if reopen else 'Sample sliced natively.',flush=True)


def compare_sample(a,b):
    sa,aa=rows(a);sb,bb=rows(b);assert sa==sb and len(aa)==len(bb)==2
    errors=[];bookkeeping=[]
    for x,y in zip(aa,bb):
        assert x['name']==y['name'] and effective(x['settings'])==effective(y['settings'])
        assert np.max(abs(x['transform']-y['transform']))<.0001
        assert len(x['parts'])==len(y['parts'])
        for p,q in zip(x['parts'],y['parts']):
            assert p['subtype']==q['subtype'] and effective(p['settings'])==effective(q['settings'])
            assert p['paint']==q['paint']==[]
            assert np.array_equal(p['mesh'].faces,q['mesh'].faces)
            error=float(np.max(abs(p['mesh'].vertices-q['mesh'].vertices)));assert error<.0001
            errors.append(error)
            d={k:[p['settings'].get(k),q['settings'].get(k)] for k in set(p['settings'])|set(q['settings']) if p['settings'].get(k)!=q['settings'].get(k)}
            assert set(d)<=BOOKKEEPING
            if d:bookkeeping.append(dict(object=x['name'],changes=d))
    return dict(max_vertex_error_mm=max(errors),settings_unchanged=True,poses_preserved=True,source_bookkeeping=bookkeeping)


def validate():
    assert not WITHDRAWN,'r1 is withdrawn: wrong screw feature.'
    from validate_print_project import scan_gcode
    from audit_knot_rollback_joints import paths_with_width,key_paths
    from correct_knot_reinforcement_skin import crossings
    from build_photo_support_test import paths as all_extrusions
    record=json.loads((OUT/'geometry-validation.json').read_text())
    if REQUIRE_PHOTO_RETAINER:assert record['photo_retainer_identity']['role']=='PHOTO_RETAINER_BLIND_SCREW_HOLE'
    assert digest(SOURCE)==record['source_sha256']==SOURCE_SHA and digest(EDIT)==record['editable_sha256']
    assert protected()==record['protected_before']
    candidate=WORK/'native/sliced.3mf';roundtrip=compare_sample(EDIT,candidate)
    original_settings,source_objects=rows(SOURCE);settings,objects=rows(candidate)
    difference={k:[original_settings.get(k),settings.get(k)] for k in set(original_settings)|set(settings) if original_settings.get(k)!=settings.get(k)}
    assert difference==record['global_setting_changes']
    locks={**LOCKS,'support_type':'normal(auto)','nozzle_diameter':['0.4']}
    for k,v in locks.items():assert settings[k]==v,(k,settings[k])
    assert settings['printer_model']=='Bambu Lab A2L'
    bolster_count=0;hulls=[]
    for k,obj in enumerate(objects):
        saved=record['source_volume_checks'][k]
        assert effective(obj['settings'])==effective(saved['source_object_settings'])
        assert obj['settings']['enable_support']=='1' and obj['settings']['support_interface_spacing']=='0.2'
        for part,source_part in zip(obj['parts'],saved['volume_crops']):
            assert effective(part['settings'])==effective(source_part['source_settings'])
            e={**settings,**effective(obj['settings']),**effective(part['settings'])}
            reinforcement=part['settings'].get('name')=='Local solid screw reinforcement'
            for key,value in locks.items():
                if key=='sparse_infill_density' and reinforcement:value='100%'
                assert e[key]==value,(obj['name'],key,e[key])
            if reinforcement:
                assert np.allclose(part['mesh'].bounds[:,2],[0,12.4],atol=1e-5);bolster_count+=1
            if part['settings'].get('extruder')=='3':assert np.allclose(part['mesh'].bounds[:,2],[12.5,13.5],atol=1e-5)
        t=obj['transform'];v=np.concatenate([p['mesh'].vertices for p in obj['parts'] if p['subtype']=='normal_part'])@t[:3,:3].T+t[:3,3]
        assert abs(v[:,2].min())<.001
        hulls.append(MultiPoint(v[:,:2]).convex_hull)
    assert bolster_count==1 and hulls[0].distance(hulls[1])>8
    files=read(candidate);raw=files['Metadata/plate_1.gcode'];text=raw.decode()
    assert hashlib.md5(raw).hexdigest()==files['Metadata/plate_1.gcode.md5'].decode().strip().lower()
    assert '; EXECUTABLE_BLOCK_END' in text
    config=dict(re.findall(r'^; ([A-Za-z_0-9]+) = (.*)$',text,re.M))
    for key,value in locks.items():assert config[key]==('0.4' if key=='nozzle_diameter' else value),(key,config[key])
    with zipfile.ZipFile(SOURCE) as z:source_gcode=z.read('Metadata/plate_3.gcode').decode()
    oldconfig=dict(re.findall(r'^; ([A-Za-z_0-9]+) = (.*)$',source_gcode,re.M))
    configdiff={k:[oldconfig.get(k),config.get(k)] for k in set(oldconfig)|set(config) if oldconfig.get(k)!=config.get(k)}
    # The native configuration footer keeps the stored value on this two-object
    # plate, while production records its normalized value. Prove it is inert
    # here by comparing every printer command with an isolated diagnostic slice.
    assert configdiff.get('independent_support_layer_height')==['0','1']
    assert settings['independent_support_layer_height']==original_settings['independent_support_layer_height']=='1'
    assert set(configdiff)<=set(record['global_setting_changes'])|{'independent_support_layer_height'},configdiff
    diagnostic=read(WORK/'support-normalization-check/sliced.3mf')
    diagnostic_input=json.loads(read(WORK/'support-normalization-check/diagnostic.3mf')['Metadata/project_settings.config'])
    expected_diagnostic=dict(settings,independent_support_layer_height='0')
    assert diagnostic_input==expected_diagnostic
    def commands(t):return '\n'.join(l.split(';')[0].rstrip() for l in t.splitlines() if l.split(';')[0].strip())
    assert commands(text)==commands(diagnostic['Metadata/plate_1.gcode'].decode())
    support_normalization=dict(saved_setting_preserved='1',production_footer='0',sample_footer='1',
        diagnostic_value='0',all_printer_commands_identical=True,
        command_stream_sha256=hashlib.sha256(commands(text).encode()).hexdigest())
    scan=scan_gcode(text);lo,hi=np.array(scan['bead_xy_bounds_mm'])
    clearance=float(min(*lo,*(np.array([330,320])-hi)));assert clearance>.5
    assert scan['model_extrusion_z_by_filament_mm']['3']==[12.8,13.0,13.2,13.4,13.6]
    assert scan['features'].get('Support',0)>0 and scan['features'].get('Support interface',0)>0
    startup=check_startup_tower(settings,hulls,3,max(max(z) for z in scan['model_extrusion_z_by_filament_mm'].values()),1)
    tower=check_tower(text,hulls,[0,0,330,320]);tower.pop('actual_tower_convex_envelope')
    cfg=ET.fromstring(files['Metadata/model_settings.config']);configs={o.get('id'):props(o)['name'] for o in cfg.findall('object')}
    ids={configs[props(i)['object_id']]:int(props(i)['identify_id']) for i in cfg.find('plate').findall('model_instance')}
    model_paths={o['name']:paths_with_width(text,o['transform'],object_id=ids[o['name']]) for o in objects}
    for name,ps in model_paths.items():assert ps and any(abs(p[2][1,2]-.2)<.001 for p in ps),(name,'No model bed contact')
    joint=record['source_joint_record'];keychecks=[]
    for ki,y in enumerate(joint[5],1):
        for z in [5.2,5.4,5.6,5.8,6.0]:
            a,order=key_paths(model_paths[NAMES[0]],joint,y,z);b,_=key_paths(model_paths[NAMES[1]],joint,y,z)
            gap=a.distance(b);overlap=a.intersection(b).area
            assert gap>.05 and overlap<1e-6,(ki,z,gap,overlap)
            if order['wall_before_fill'] is not None:assert order['wall_before_fill']
            keychecks.append(dict(key=ki,z_mm=z,commanded_bead_clearance_mm=gap,commanded_overlap_mm2=overlap,key_path_order=order))
    skin=[]
    for bolster in record['bolsters']:
        ps=[p for p in model_paths[bolster['object']] if 12.79<=p[2][1,2]<=13.61]
        counts=crossings(ps,np.array(bolster['center_assembly_mm']),bolster['radius_mm'])
        assert min(counts.values())>=5
        skin.append(dict(**bolster,continuous_layer_crossings=counts))
    frame=json.loads((ROOT/'working/bambu/Dara-Photo-Frame-A2L/frame-geometry-validation.json').read_text())['joints'][JOINT_INDEX]
    crop=shapely.geometry.shape(record['crop_assembly_polygon']);pad_checks=[]
    for oi,name in enumerate(NAMES):
        a=np.array([p[2] for p in model_paths[name]]);start=a[:,0,:2];delta=a[:,1,:2]-start;lengths=(delta*delta).sum(axis=1)
        for xy in frame['seating_pads_xy']:
            if not crop.buffer(-1).covers(Point(xy)):continue
            frac=np.clip(((np.array(xy)-start)*delta).sum(axis=1)/lengths,0,1)
            near=np.linalg.norm(start+frac[:,None]*delta-np.array(xy),axis=1)<.65
            z=float(a[near,:,2].max() if oi==0 else a[near,:,2].min())
            assert abs(z-(4.8 if oi==0 else 5.2))<.001
            pad_checks.append(dict(object=name,xy_assembly_mm=xy,model_z_mm=z))
    expected_pad_sites=sum(crop.buffer(-1).covers(Point(xy)) for xy in frame['seating_pads_xy'])
    assert len(pad_checks)==2*expected_pad_sites and expected_pad_sites>0
    # Inspect local backing under the two actual groove roofs, excluding
    # supports from model fit but including them in this backing check.
    emitted=all_extrusions(text);socket=objects[1];t=socket['transform'];supportchecks=[]
    a=math.radians(joint[3]);normal=np.array([math.cos(a),math.sin(a)]);tangent=np.array([-normal[1],normal[0]])
    for ki,y in enumerate(joint[5],1):
        xy=np.array(joint[2])+9*normal+y*tangent;bed=(np.array([*xy,0])@t[:3,:3].T+t[:3,3])[:2]
        region=Point(bed).buffer(.6)
        support=[p for p in emitted if p['feature'] in ('Support','Support interface','Support transition') and LineString(p['segment']).intersects(region)]
        assert support,(ki,'No local groove backing')
        interface=[p for p in support if p['feature']=='Support interface'];assert interface
        roof=max(p['z'] for p in interface)
        model=[p for p in model_paths[NAMES[1]] if LineString(p[2][:,:2]).intersects(Point(xy).buffer(.6))]
        first=min(float(p[2][1,2]) for p in model);gap=first-.2-roof
        assert abs(gap-.2)<.001,(ki,roof,first,gap)
        supportchecks.append(dict(key=ki,interface_top_z_mm=roof,first_model_layer_top_z_mm=first,air_gap_mm=gap))
    info=ET.fromstring(files['Metadata/slice_info.config']);warnings=[w.attrib for w in info.iter('warning')]
    assert all(w.get('msg')=='not_support_traditional_timelapse' for w in warnings),warnings
    result=json.loads((WORK/'native/result.json').read_text());estimate=result['sliced_plates'][0]
    assert protected()==record['protected_before']
    # Only one current printable sample is exposed in output; editable scratch
    # remains in .work. The native 3MF retains both editable meshes and slices.
    shutil.copyfile(candidate,FINAL);native(True);reopen=compare_sample(FINAL,WORK/'reopen/reopened.3mf')
    assert protected()==record['protected_before']
    report=dict(status='PASS_DIGITAL_CHECKS_PHYSICAL_FIT_PENDING',current_sample=FINAL.name,sample_sha256=digest(FINAL),
        source_project='Knot.3mf',source_sha256=SOURCE_SHA,editable_sha256=digest(EDIT),
        geometry_validation_sha256=digest(OUT/'geometry-validation.json'),native_roundtrip=roundtrip,native_reopen=reopen,
        photo_retainer_identity=record.get('photo_retainer_identity'),
        global_setting_changes=difference,gcode_configuration_changes=configdiff,support_normalization=support_normalization,
        all_other_process_and_material_settings_preserved=True,
        object_and_volume_overrides_preserved=True,rotations_preserved=True,normal_supports=True,infill_first=False,
        key_toolpath_checks=keychecks,screw_skin_checks=skin,pad_toolpath_checks=pad_checks,groove_support_backing=supportchecks,
        model_z_by_filament_mm=scan['model_extrusion_z_by_filament_mm'],gcode_sha256=hashlib.sha256(raw).hexdigest(),md5_verified=True,
        model_bed_contact_both_pieces=True,bed_clearance_mm=clearance,startup_tower=startup,tower=tower,warnings=warnings,
        estimated_seconds=estimate['total_predication'],estimated_grams=sum(f['total_used_g'] for f in estimate['filaments']),
        protected_after=protected(),printer_job_sent=False,physical_fit_support_cleanup_surface_finish_unverified=True)
    dump(OUT/'validation.json',report);shutil.copyfile(WORK/'native/result.json',OUT/'native-result.json')
    for n in ['plate_1.png','top_1.png']:
        if 'Metadata/'+n in files:(OUT/n).write_bytes(files['Metadata/'+n])
    document(report,record)
    print(f"Validated one-plate J{JOINT_INDEX+1} sample: {report['estimated_seconds']/60:.1f} minutes, {report['estimated_grams']:.2f} g.",flush=True)


def document(report,record):
    mins=round(report['estimated_seconds']/60)
    text=f'''# Current joint + screw-bolster sample, r1

Print **{FINAL.name}** as a **Bambu Studio project** on the **A2L / 0.4 mm nozzle / Textured PEI**. One plate contains both mating pieces. Estimate: **{mins//60}h {mins%60:02d}m / {report['estimated_grams']:.2f} g** including the saved supports and purge tower.

- **A / left:** production J2 F3 tongue, retaining both original locating keys.
- **B / right:** production J2 F1 socket, both matching grooves and one complete original screw bolster. An existing production alignment pin within the crop is also retained.
- The complete solid modifier ends at **Z12.4**, below the nominal **Z13.5** show face. All five native top layers at Z12.8–13.6 cross its boundary.

This is a direct crop of current root Knot.3mf, with **normal(auto) supports and infill-first OFF**. Structural **8% gyroid**, 0.20 mm initial/regular layers, four walls, five top/bottom layers, original 100% screw reinforcement, 0.20 mm support top gap and object interface spacing are preserved. Slots remain **1 white, 2 wood tan, 3 Azurite blue**, with their exact saved production profiles and values.

## Printing and checking

1. Open this exact 3MF as a project to retain the saved settings and A2L slices.
2. Remove normal supports, including the support/interface material from both grooves. Dry-fit A into B before gluing or sanding. Check both keys seat and the front surfaces meet flush.
3. Inspect the show face over the screw-bolster region for a visible circular boundary. Record fit, support cleanup and surface appearance against this r1 file.

Digital validation passes; **physical fit, cleanup and surface finish are not yet established**. No print job was sent.

## Source and exact crop

- Source: root `Knot.3mf`, SHA-256 `{SOURCE_SHA}`.
- Sample SHA-256: `{report['sample_sha256']}`.
- Source joint: J2, F3 tongue / F1 socket. Full-scale, unchanged joint geometry, two complete keys and one complete screw modifier.
- Joint-local crop: **X −18 to +44 mm, Y −32 to +48 mm**, Z −0.01 to 20 mm. Local X follows the source joint normal; origin/angle and the assembly polygon are recorded in `geometry-validation.json`.
- Nominal crop envelope: 62 × 80 mm. Both source rotations, all thicknesses and in-crop features remain. The existing alignment pin reaches Z16.5.
- Cropping and translation-only bed repositioning are the only geometry/pose operations. Sample name and single-plate tower arrays are the only global-setting differences. Tower X285 / Y160. No fit clearance, material boundary, support spacing, reinforcement height or surface finish was redesigned.

`geometry-validation.json` records exact per-volume intersections, source hashes, complete bolster retention, connected bodies and clean crop edges without split photo-opening scallops. `validation.json` records native roundtrip/reopen, full setting comparisons, both key clearances, groove backing with a 0.20 mm air gap, pad removal, five-layer screw skin, bed/tower clearance, warnings, checksums and estimates. All production projects and CAD/STLs remain byte-identical.

Bambu's sample G-code configuration footer reports independent support layer height as 1, while production's footer reports 0; both editable projects retain the same saved value of 1. A separate diagnostic slice using 0 produced **identical printer commands**, including all support moves. This footer difference does not change this sample's toolpaths. The diagnostic is retained only in scratch; the delivered project preserves production's saved setting.

This is the sole current joint/bolster test supplied for this request. Earlier production-joint, flush-joint and infill-first samples are historical and must not be substituted for this file.
'''
    (OUT/'README.md').write_text(text,encoding='utf-8',newline='\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['build','slice','validate']);action=parser.parse_args().action
    if action=='slice':native()
    else:globals()[action]()
