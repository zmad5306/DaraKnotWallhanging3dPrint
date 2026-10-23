"""Replace only the solid M and cover plates in the main self-contained 3MF.

Retain all other geometry/settings and native slices. Rebase plate origins from
the original six-column grid in the 36-plate project without changing
plate-local poses. Copy the twelve independently verified native M slices.
"""
import argparse
import collections
import copy
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import xml.etree.ElementTree as ET
import zipfile
import numpy as np
from development_3mf import ROOT,OUT,WORK,source_path,sha,save_json,props,tag,P,R,transform,read_object,common_m_rotation,solid
from build_jointed_bambu_project import xml
from validate_print_project import scan_gcode

PACKAGE=ROOT/'working/bambu/Dara-Photo-Frame-A1-Jointed'
BUILD=WORK/'main-project'
REPORT=PACKAGE/'m-veneer-release-validation.json'
M_PLATES=[21,22,23,24,25,26,31,32,33,34,35,36]
REMOVED=set(range(21,27))|{31,32}
BASE_SHA='d5e57cb2cf359a46a681c052a002d991044ae35f5d5810f134c701953f97d04b'


def read(path):
    with zipfile.ZipFile(path) as z:return {n:z.read(n) for n in z.namelist()}


def put(element,key,value):
    m=element.find(f"metadata[@key='{key}']")
    if m is None:m=ET.SubElement(element,'metadata',key=key)
    m.set('value',str(value))


def origin(plate,columns):
    return np.array([(plate-1)%columns*307.2,-((plate-1)//columns)*307.2,0])


def set_transform(item,t):
    item.set('transform',' '.join(format(float(v),'.12g') for v in t[:3].T.reshape(-1)))


def prepare():
    BUILD.mkdir(exist_ok=True)
    assert sha(source_path())==BASE_SHA
    base=read(source_path());m=read(OUT/'M-Core-and-Veneer-A1.3mf')
    native=read(OUT/'M-Core-and-Veneer-A1-Sliced.3mf')
    validation=json.loads((OUT/'M-Core-and-Veneer-A1-native-validation.json').read_text())
    assert validation['staged_sha256']==sha(OUT/'M-Core-and-Veneer-A1.3mf')
    assert validation['native_project_sha256']==sha(OUT/'M-Core-and-Veneer-A1-Sliced.3mf')
    plan=json.loads((OUT/'M-geometry-validation.json').read_text())
    assert plan['cosmetic_gap_mm']==0 and plan['core_crown_mm']==0
    assert len(plan['skins'])==6
    for skin in plan['skins']:
        carrier=skin['carrier']
        assert carrier['continuous_starter_shoe'] is False
        assert carrier['cutter_access_necks_checked']==carrier['bonded_tooth_count']
        assert carrier['maximum_cutter_access_obstruction_mm3']<1e-5
        assert carrier['flush_trim_excess_outside_finished_veneer_mm3']<1e-5
    root=ET.fromstring(base['3D/3dmodel.model']);cfg=ET.fromstring(base['Metadata/model_settings.config'])
    mr=ET.fromstring(m['3D/3dmodel.model']);mc=ET.fromstring(m['Metadata/model_settings.config'])
    resources=root.find(tag('resources'));build=root.find(tag('build'))
    old_plates=cfg.findall('plate');remove_ids={props(i)['object_id'] for p in old_plates if int(props(p)['plater_id']) in REMOVED for i in p.findall('model_instance')}
    old_builds=collections.defaultdict(list)
    for b in build:old_builds[b.get('objectid')].append(copy.deepcopy(b))
    for parent in [resources,cfg]:
        for obj in list(parent):
            if obj.tag in [tag('object'),'object'] and obj.get('id') in remove_ids:parent.remove(obj)
    for b in list(build):build.remove(b)
    for p in old_plates:cfg.remove(p)
    for assembly in cfg.findall('assemble'):
        for item in list(assembly):
            if item.get('object_id') in remove_ids:assembly.remove(item)
    plate_table={}
    for number,p in enumerate(old_plates,1):
        if number in REMOVED:continue
        cfg.append(p)
        for instance in p.findall('model_instance'):
            st=props(instance);b=copy.deepcopy(old_builds[st['object_id']][int(st['instance_id'])])
            t=transform(b.get('transform'));local=t.copy();local[:3,3]-=origin(number,6)
            t[:3,3]=local[:3,3]+origin(number,6);set_transform(b,t);build.append(b)
        plate_table[number]=dict(plate=number,kind='preserved',name=props(p)['plater_name'])
    files=dict(base)
    # Remove only obsolete plate assets and no-longer-referenced child resources.
    for path in list(files):
        for number in REMOVED:
            if re.fullmatch(rf'Metadata/(?:plate_{number}(?:_small)?|plate_no_light_{number}|top_{number}|pick_{number})\.(?:png|json|gcode(?:\.md5)?)',path):del files[path];break
    info=ET.fromstring(base['Metadata/slice_info.config']);mi=ET.fromstring(native['Metadata/slice_info.config'])
    for p in list(info.findall('plate')):
        if int(props(p)['index']) in REMOVED:info.remove(p)
    sequence=json.loads(base['Metadata/filament_sequence.json']);ms=json.loads(native['Metadata/filament_sequence.json'])
    for number in REMOVED:sequence.pop(f'plate_{number}',None)
    for i,number in enumerate(M_PLATES,1):
        p=copy.deepcopy(mc.findall('plate')[i-1]);oid=props(p.find('model_instance'))['object_id']
        obj=copy.deepcopy(mc.find(f"object[@id='{oid}']"));label=props(obj)['name']
        assert cfg.find(f"object[@id='{oid}']") is None
        cfg.append(obj);top=copy.deepcopy(mr.find(tag('resources')).find(f"{tag('object')}[@id='{oid}']"));resources.append(top)
        for co in top.find(tag('components')):
            path=co.get('{'+P+'}path').lstrip('/')
            if path in files:assert files[path]==m[path]
            files[path]=m[path]
        b=copy.deepcopy(mr.find(tag('build')).find(f"{tag('item')}[@objectid='{oid}']"))
        t=transform(b.get('transform'));t[:3,3]+=origin(number,6)-origin(i,4);set_transform(b,t);build.append(b)
        put(p,'plater_id',number);put(p,'plater_name',f'{number:02d} - {label}')
        native_cfg=ET.fromstring(native['Metadata/model_settings.config']).findall('plate')[i-1]
        for md in native_cfg.findall('metadata'):
            if md.get('key','').endswith('_file'):
                put(p,md.get('key'),md.get('value').replace(f'_{i}.',f'_{number}.').replace(f'_{i}_small.',f'_{number}_small.'))
        cfg.append(p)
        for path,data in native.items():
            if re.fullmatch(rf'Metadata/(?:plate_{i}(?:_small)?|plate_no_light_{i}|top_{i}|pick_{i})\.(?:png|json|gcode(?:\.md5)?)',path):
                new=re.sub(rf'_{i}(?=\.|_small\.)',f'_{number}',path);files[new]=data
        stat=copy.deepcopy(mi.findall('plate')[i-1]);put(stat,'index',number);put(stat,'printer_model_id','N2S');info.append(stat)
        sequence[f'plate_{number}']=ms[f'plate_{i}']
        plate_table[number]=dict(plate=number,kind='core' if i<=6 else 'veneer',source_plate=i,name=f'{number:02d} - {label}',
            gcode_sha256=hashlib.sha256(files[f'Metadata/plate_{number}.gcode']).hexdigest(),
            native_validation=validation['plates'][i-1])
    # Keep plate order and every global print/material setting except array lengths.
    plates=sorted(cfg.findall('plate'),key=lambda p:int(props(p)['plater_id']))
    for p in plates:cfg.remove(p)
    for p in plates:cfg.append(p)
    stats=sorted(info.findall('plate'),key=lambda p:int(props(p)['index']))
    for p in stats:info.remove(p)
    for p in stats:info.append(p)
    for name in root.findall(tag('metadata')):
        if name.get('name')=='Title':name.text='Dara A1 - flat M cores and consistent Y-oriented veneers'
        if name.get('name')=='Description':name.text='Six flat structural M cores and six band-free veneers with zero nominal cosmetic gaps. All veneers share the full 55-degree M5 rotation with face planes parallel to bed Y travel.'
    needed={c.get('{'+P+'}path').lstrip('/') for c in root.iter(tag('component'))}
    for path in list(files):
        if path.startswith('3D/Objects/') and path not in needed:del files[path]
    rels=ET.Element('Relationships',xmlns=R)
    for i,path in enumerate(sorted(needed),1):ET.SubElement(rels,'Relationship',Target='/'+path,Id=f'rel-{i}',Type='http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel')
    grels=ET.Element('Relationships',xmlns=R)
    for number in range(1,37):ET.SubElement(grels,'Relationship',Target=f'/Metadata/plate_{number}.gcode',Id=f'rel-{number}',Type='http://schemas.bambulab.com/package/2021/gcode')
    settings=json.loads(base['Metadata/project_settings.config'])
    for key,default in [('wipe_tower_x','15'),('wipe_tower_y','214')]:
        settings[key]=settings[key]+[default]*(36-len(settings[key]))
    settings['print_settings_id']='Dara A1 - flat M cores and consistent veneers'
    assert settings['bed_exclude_area']==json.loads(m['Metadata/project_settings.config'])['bed_exclude_area']==[]
    files.update({'3D/3dmodel.model':xml(root),'3D/_rels/3dmodel.model.rels':xml(rels),
        'Metadata/model_settings.config':xml(cfg),'Metadata/slice_info.config':xml(info),
        'Metadata/_rels/model_settings.config.rels':xml(grels),
        'Metadata/filament_sequence.json':json.dumps(sequence).encode(),
        'Metadata/project_settings.config':json.dumps(settings,indent=2).encode()})
    files.pop('Metadata/cut_information.xml',None)  # obsolete empty native cut IDs
    target=BUILD/'Dara.3mf'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        for name,data in files.items():z.writestr(name,data)
    report=check_candidate(target,base,plan,plate_table,validation)
    save_json(BUILD/'validation.json',report)
    print(json.dumps(dict(candidate=str(target),plates=report['plates'],unchanged_plates=len(report['preserved_plates']),
        new_m_plates=M_PLATES,weight_g=report['total_weight_g'],hours=round(report['total_seconds']/3600,2)),indent=2))


def check_candidate(path,baseline,plan,plate_table,validation):
    files=read(path);cfg=ET.fromstring(files['Metadata/model_settings.config']);root=ET.fromstring(files['3D/3dmodel.model'])
    bc=ET.fromstring(baseline['Metadata/model_settings.config']);br=ET.fromstring(baseline['3D/3dmodel.model'])
    info=ET.fromstring(files['Metadata/slice_info.config'])
    assert len(cfg.findall('plate'))==len(info.findall('plate'))==36
    assert len(cfg.findall('object'))==46 and len(root.find(tag('build')))==77
    known=[]
    for name,data in files.items():
        if name.endswith('.model'):
            r=ET.fromstring(data);known.extend(o.get('id') for o in r.find(tag('resources')))
            for c in r.iter(tag('component')):assert c.get('{'+P+'}path').lstrip('/') in files
    assert len(known)==len(set(known)),'Duplicate resource IDs'
    changed=[];preserved=[];estimates=[]
    source=read(OUT/'M-Core-and-Veneer-A1.3mf');sc=ET.fromstring(source['Metadata/model_settings.config'])
    sr=ET.fromstring(source['3D/3dmodel.model'])
    old_builds=collections.defaultdict(list);new_builds=collections.defaultdict(list)
    for b in br.find(tag('build')):old_builds[b.get('objectid')].append(b)
    for b in root.find(tag('build')):new_builds[b.get('objectid')].append(b)
    for number,p in enumerate(cfg.findall('plate'),1):
        assert int(props(p)['plater_id'])==number
        for md in p.findall('metadata'):
            if md.get('key','').endswith('_file') and md.get('value'):assert md.get('value') in files,md.attrib
        gc=files[f'Metadata/plate_{number}.gcode']
        assert hashlib.md5(gc).hexdigest()==files[f'Metadata/plate_{number}.gcode.md5'].decode().strip().lower()
        s=next(s for s in info.findall('plate') if int(props(s)['index'])==number);stat=props(s)
        estimates.append(dict(plate=number,name=props(p)['plater_name'],weight_g=float(stat['weight']),seconds=int(stat['prediction'])))
        if number not in M_PLATES:
            assert gc==baseline[f'Metadata/plate_{number}.gcode'],number
            for inst in p.findall('model_instance'):
                values=props(inst);oid=values['object_id'];idx=int(values['instance_id'])
                assert xml(cfg.find(f"object[@id='{oid}']"))==xml(bc.find(f"object[@id='{oid}']"))
                top=root.find(tag('resources')).find(f"{tag('object')}[@id='{oid}']")
                for co in top.find(tag('components')):
                    child=co.get('{'+P+'}path').lstrip('/');assert files[child]==baseline[child]
                old=transform(old_builds[oid][idx].get('transform'));new=transform(new_builds[oid][idx].get('transform'))
                old[:3,3]-=origin(number,6);new[:3,3]-=origin(number,6)
                assert np.allclose(old,new,atol=1e-8,rtol=0),(number,oid,'Pose changed')
            preserved.append(dict(plate=number,gcode_sha256=hashlib.sha256(gc).hexdigest(),geometry_settings_and_local_poses_unchanged=True))
        else:
            row=plate_table[number];i=row['source_plate'];oid=props(p.find('model_instance'))['object_id']
            assert xml(cfg.find(f"object[@id='{oid}']"))==xml(sc.find(f"object[@id='{oid}']"))
            t=transform(new_builds[oid][0].get('transform'));t[:3,3]-=origin(number,6)
            a=transform(sr.find(tag('build')).find(f"{tag('item')}[@objectid='{oid}']").get('transform'));a[:3,3]-=origin(i,4)
            assert np.allclose(t,a,atol=1e-8,rtol=0)
            text=gc.decode();assert '; EXECUTABLE_BLOCK_END' in text
            row=dict(row);row['native_gcode_reused_without_changes']=True
            assert row['gcode_sha256']==validation['plates'][i-1]['gcode_sha256']
            changed.append(row)
    # Check all six actual saved assembly-to-bed rotations, not only normals.
    rotations=[];expected=common_m_rotation()
    for skin in plan['skins']:
        r=np.array(skin['assembly_to_printer'])[:3,:3]
        assert np.allclose(r,expected,atol=1e-12)
        normal=r[:,2];assert abs(normal[1])<1e-12
        rotations.append(dict(veneer=skin['name'],rotation=r.tolist(),show_face_normal_in_bed=normal.tolist(),bed_y_in_show_plane=True))
    seams=check_full_seams(plan)
    fin_coverage=None
    if all('area_coverage' in s['carrier'] for s in plan['skins']):
        proof_path=OUT/'M-fin-coverage-validation.json';proof=json.loads(proof_path.read_text())
        assert proof['baseline_contacts_sha256']==sha(ROOT/'working/review/m-fin-density/baseline-fin-contacts.json')
        assert proof['geometry_plan_sha256']==sha(OUT/'M-geometry-validation.json')
        assert all(r['trial_geometric_checks_pass'] for r in proof['veneers'])
        assert all(not s['carrier']['tall_fins_without_diagonal_restraint'] for s in plan['skins'])
        face_path=OUT/'M-fin-face-preservation.json';face=json.loads(face_path.read_text())
        assert face['all_show_faces_preserved']
        assert face['geometry_plan_sha256']==proof['geometry_plan_sha256']
        fin_coverage=dict(report=str(proof_path.relative_to(ROOT)),sha256=sha(proof_path),
            baseline_fin_count=proof['original_fins'],revised_fin_count=proof['revised_fins'],
            validation_grid_mm=proof['validation_grid_mm'],
            tall_fins_diagonally_restrained=True,physical_rigidity_confirmation_pending=True,
            face_preservation_sha256=sha(face_path))
    return dict(project_sha256=sha(path),baseline_sha256=BASE_SHA,baseline_file=str(source_path().relative_to(ROOT)),
        source_cad_sha256=sha(ROOT/'working/Dara-Photo-Frame-A1-Jointed.scad'),
        plates=36,objects=46,instances=77,frame_sections=20,frame_joints=32,core_count=6,veneer_count=6,cover_bands=0,legacy_glue_sample_removed=True,
        core_body_mm=8.4,veneer_flat_back_z_mm=8.6,glue_gap_mm=.2,cosmetic_gap_mm=0,
        full_core_infill='15% gyroid with 4 walls and 5 top/bottom layers; local solid screw reinforcement',veneer_infill='100%',
        orientation=dict(common_lean_deg=55,all_full_rotations_equal=True,broad_show_planes_parallel_to_bed_y=True,veneers=rotations),
        zero_gap_seams=seams,changed_m_plates=changed,preserved_plates=preserved,plate_estimates=estimates,
        total_weight_g=round(sum(e['weight_g'] for e in estimates),2),total_seconds=sum(e['seconds'] for e in estimates),
        m_weight_g=round(sum(e['weight_g'] for e in estimates if e['plate'] in M_PLATES),2),
        m_seconds=sum(e['seconds'] for e in estimates if e['plate'] in M_PLATES),
        full_m_native_validation_sha256=sha(OUT/'M-Core-and-Veneer-A1-native-validation.json'),
        source_child_mesh_sha256={p:hashlib.sha256(files[p]).hexdigest() for p in sorted(files) if p.startswith('3D/Objects/')},
        fin_coverage=fin_coverage,physical_confirmation_pending=True)


def check_full_seams(plan):
    import trimesh
    from scipy.spatial import cKDTree
    from develop_m_veneer import axes
    meshes=[]
    for i in range(6):
        a=np.load(WORK/f'V{i+1}.npz');meshes.append(trimesh.Trimesh(a['vertices'],a['faces'],process=False))
    rows=[]
    for index,j in enumerate(plan['skin_joints'],1):
        n,t=axes(j);center=np.array(j[2]);edges=[]
        for part in j[:2]:
            v=meshes[part-1].vertices;d=v[:,:2]-center
            edge=v[(abs(d@n)<2e-7)&(abs(d@t)<j[4]/2+30)&(v[:,2]>10.4)]
            assert len(edge)>10,(index,part,len(edge));edges.append(np.unique(np.round(edge,7),axis=0))
        error=max(float(cKDTree(edges[0]).query(edges[1])[0].max()),float(cKDTree(edges[1]).query(edges[0])[0].max()))
        assert error<.0002,(index,'Front seam mismatch',error)
        rows.append(dict(seam=index,veneers=j[:2],maximum_front_edge_mismatch_mm=error,nominal_gap_mm=0))
    return rows


def publish():
    report=json.loads((BUILD/'validation.json').read_text());target=BUILD/'Dara.3mf'
    assert sha(target)==report['project_sha256']
    opened=json.loads((BUILD/'result.json').read_text());assert opened['return_code']==0
    assert (BUILD/'result.json').stat().st_mtime>=target.stat().st_mtime,'Reopen the prepared candidate before publishing'
    report['native_project_reopen_return_code']=0
    report['native_reopen_input_sha256']=report['project_sha256']
    # The repository root is now the A2L production project. Refresh the A1
    # production copy without replacing that separate printer's root project.
    for output in [PACKAGE/'Dara-Photo-Frame-A1-Complete.3mf']:
        shutil.copyfile(target,output);assert sha(output)==report['project_sha256']
    save_json(REPORT,report)
    print('Published the A1 production copy, with 24 original native plates preserved.')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','publish']);a=p.parse_args()
    {'prepare':prepare,'publish':publish}[a.action]()
