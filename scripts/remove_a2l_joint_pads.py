"""Remove only the 42 raised A2L lap pads; retain all other production inputs.

Works from an immutable local snapshot. Never sends a printer command.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.work/python-libs'))
import numpy as np
import manifold3d as mf
from shapely.geometry import Point
from shapely import union_all
from development_3mf import solid,mesh,mesh_xml,read_object,tag,P,props,transform,sha,save_json
from build_a2l_project import prism
from build_jointed_bambu_project import xml

OUT=ROOT/'working/bambu/Dara-Photo-Frame-A2L'
WORK=ROOT/'.work/a2l-pad-removal'
BASE=WORK/'baseline'
EDIT=OUT/'Dara-A2L-Editable.3mf'
REL=EDIT.relative_to(ROOT)
NATIVE=WORK/'native'
EXE=Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe')
REVISION='lower-lap-pads-removed-v1'


def read(path):
    with zipfile.ZipFile(path) as z:return {n:z.read(n) for n in z.namelist()}


def write(path,files):
    path.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        for n,v in files.items():z.writestr(n,v)


def baseline():
    assert (BASE/'Dara.3mf').exists(),'Create an immutable baseline snapshot first'
    plan=json.loads((BASE/OUT.relative_to(ROOT)/'production-plan.json').read_text())
    proof=json.loads((BASE/OUT.relative_to(ROOT)/'frame-geometry-validation.json').read_text())
    assert len(proof['joints'])==14
    return plan,proof


def snapshot():
    """Run against the pre-correction checkout; never replace an older snapshot."""
    paths=[ROOT/'Dara.3mf',*OUT.glob('*'),ROOT/'AGENTS.md',ROOT/'README.md']
    for p in paths:
        if not p.is_file():continue
        target=BASE/p.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():assert sha(target)==sha(p),(p,'baseline is immutable')
        else:shutil.copyfile(p,target)
    protected=[*(ROOT/'working/bambu/Dara-A1-Companion').glob('*'),
        ROOT/'working/bambu/Dara-Photo-Frame-A1-Jointed/Dara-Photo-Frame-A1-Complete.3mf',
        ROOT/'output/development/m-veneer-cosmetic-fit/All-Development-Tests-A1-Sliced.3mf']
    save_json(WORK/'protected.json',{p.relative_to(ROOT).as_posix():sha(p) for p in protected if p.is_file()})


def patch(source,target):
    plan,proof=baseline();before=read(source);files=dict(before)
    root=ET.fromstring(files['3D/3dmodel.model']);cfg=ET.fromstring(files['Metadata/model_settings.config'])
    objects={props(o)['name']:o for o in cfg.findall('object')}
    resources=root.find(tag('resources'));reports=[];changed=set();total=0
    for fi in range(10):
        name=f'F{fi+1} A2L knot';co=objects[name];oid=co.get('id')
        joints=[(i,j,r) for i,(j,r) in enumerate(zip(plan['frame_joints'],proof['joints'])) if j[0]==fi]
        points=[xy for _,_,r in joints for xy in r['seating_pads_xy']]
        if not points:continue
        # Tiny radial allowance captures native float serialization only.
        footprint=union_all([Point(xy).buffer(1.5,quad_segs=12).buffer(.001) for xy in points])
        tool=prism(footprint,4.8,5.001)
        parts,settings=read_object(before,oid)
        components={c.get('objectid'):c for c in resources.find(f"{tag('object')}[@id='{oid}']").find(tag('components'))}
        models_before=[];models_after=[];volume_checks=[]
        for part,p in zip(co.findall('part'),parts):
            if p['subtype']!='normal_part':continue
            a=solid(p['mesh']);models_before.append(a)
            removed=(a^tool).volume()
            if removed<1e-6:models_after.append(a);continue
            b=a-tool;m=mesh(b);models_after.append(b)
            assert len([q for q in b.decompose() if q.volume()>1e-7])==1
            added=abs((b-a).volume());outside=abs(((a-b)-tool).volume())
            assert added<1e-5 and outside<1e-5
            component=components[part.get('id')];path=component.get('{'+P+'}path').lstrip('/')
            child=ET.fromstring(files[path]);res=child.find(tag('resources'))
            old=res.find(f"{tag('object')}[@id='{part.get('id')}']")
            assert all(set(t.attrib)=={'v1','v2','v3'} for t in old.find(tag('mesh')).find(tag('triangles')))
            local=m.copy();local.apply_transform(np.linalg.inv(transform(component.get('transform'))))
            temp=ET.Element(tag('resources'));mesh_xml(temp,int(part.get('id')),local)
            old.remove(old.find(tag('mesh')));old.append(temp[0].find(tag('mesh')))
            files[path]=xml(child);changed.add(path)
            part.find('mesh_stat').set('face_count',str(len(m.faces)))
            volume_checks.append(dict(part_id=part.get('id'),removed_mm3=removed,added_mm3=added,removed_outside_pad_tools_mm3=outside))
        old_body=mf.Manifold.batch_boolean(models_before,mf.OpType.Add)
        new_body=mf.Manifold.batch_boolean(models_after,mf.OpType.Add)
        # Native multi-volume boundaries carry float rounding. Require no new
        # components relative to the saved source instead of welding its seams.
        old_count=len([q for q in old_body.decompose() if q.volume()>1e-7])
        new_count=len([q for q in new_body.decompose() if q.volume()>1e-7])
        assert new_count==old_count,(name,old_count,new_count)
        for i,j,r in joints:
            for xy in r['seating_pads_xy']:
                probe=prism(Point(xy).buffer(.8),4.801,4.999)
                assert (old_body^probe).volume()>.35,(i,xy,'baseline pad missing')
                assert abs((new_body^probe).volume())<1e-6,(i,xy,'pad retained')
                floor=prism(Point(xy).buffer(.8),4.78,4.799)
                assert abs((floor-new_body).volume())<1e-5,(i,xy,'lap floor damaged')
                total+=1
        md=next((m for m in co.findall('metadata') if 'face_count' in m.attrib),None)
        if md is not None:md.set('face_count',str(sum(int(p.find('mesh_stat').get('face_count')) for p in co.findall('part'))))
        reports.append(dict(name=name,joints=[i+1 for i,_,_ in joints],removed_pads=len(points),volumes=volume_checks,
                            source_components=old_count,result_components=new_count))
    assert total==42,total
    files['Metadata/model_settings.config']=xml(cfg)
    assert all(files[n]==v for n,v in before.items() if n not in changed|{'Metadata/model_settings.config'})
    # All object/volume process settings and all protected object XML unchanged.
    old_cfg=ET.fromstring(before['Metadata/model_settings.config'])
    for old,new in zip(old_cfg.findall('object'),cfg.findall('object')):
        assert props(old)==props(new)
        assert all(props(a)==props(b) for a,b in zip(old.findall('part'),new.findall('part')))
        if not props(old)['name'].startswith('F'):assert ET.tostring(old)==ET.tostring(new)
    write(target,files)
    return dict(source_sha256=sha(source),target_sha256=sha(target),removed_pads=total,objects=reports,
                changed_child_assets=sorted(changed),settings_and_transforms_byte_preserved=True,
                all_other_zip_entries_byte_preserved=True)


def build():
    WORK.mkdir(parents=True,exist_ok=True)
    editable=patch(BASE/REL,WORK/'pad-free-editable.3mf')
    native=patch(BASE/'Dara.3mf',WORK/'pad-free-native.3mf')
    save_json(WORK/'geometry-patch.json',dict(revision=REVISION,editable=editable,native=native,
        removed_pad_height_mm=.2,remaining_lap_surface_z_mm=4.8,all_14_mortises_unchanged=True,
        physical_result='User trimmed three lower-lap pads; confirmed fit and flush white/brown front surfaces on 2026-10-19.',
        physical_printer_context='User switched the sample to A1 and observed grid; exact locally resliced file was not inspected.'))
    print('Removed 42 raised pads from editable/native candidates; settings, mortises and other parts retained.',flush=True)


def slice_plate(number):
    folder=WORK/f'plate-{number:02d}';folder.mkdir(exist_ok=True)
    with (folder/'cli.log').open('w') as log:
        result=subprocess.run([str(EXE),'--slice',str(number),'--export-3mf','sliced.3mf','--outputdir',str(folder),str(WORK/'pad-free-editable.3mf')],
            cwd=EXE.parent,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    result.check_returncode()
    result=json.loads((folder/'result.json').read_text());assert result['return_code']==0
    assert len(result['sliced_plates'])==1 and result['sliced_plates'][0]['id']==number
    print(f'Plate {number} sliced.',flush=True)


def merge():
    files=read(WORK/'pad-free-native.3mf');before=read(BASE/'Dara.3mf')
    cfg=ET.fromstring(files['Metadata/model_settings.config']);info=ET.fromstring(files['Metadata/slice_info.config'])
    seq=json.loads(files['Metadata/filament_sequence.json'])
    native=json.loads((BASE/OUT.relative_to(ROOT)/'native-validation.json').read_text())
    result=copy.deepcopy(native['slicer_result']);result['sliced_plates']=[]
    for number in range(1,21):
        if number>10:
            result['sliced_plates'].append(next(r for r in native['slicer_result']['sliced_plates'] if r['id']==number));continue
        folder=WORK/f'plate-{number:02d}';one=read(folder/'sliced.3mf')
        assert json.loads(one['Metadata/project_settings.config'])==json.loads(files['Metadata/project_settings.config'])
        sc=ET.fromstring(one['Metadata/model_settings.config']);fp=cfg.findall('plate')[number-1];sp=sc.findall('plate')[number-1]
        foid=props(fp.find('model_instance'))['object_id'];soid=props(sp.find('model_instance'))['object_id']
        fo=cfg.find(f"object[@id='{foid}']");so=sc.find(f"object[@id='{soid}']")
        assert props(fo)==props(so),(number,props(fo),props(so))
        replacement=copy.deepcopy(sp)
        replacement.find("model_instance/metadata[@key='object_id']").set('value',foid)
        idx=list(cfg).index(fp);cfg.remove(fp);cfg.insert(idx,replacement)
        si=ET.fromstring(one['Metadata/slice_info.config'])
        old=next(p for p in info.findall('plate') if props(p)['index']==str(number))
        new=next(p for p in si.findall('plate') if props(p)['index']==str(number))
        idx=list(info).index(old);info.remove(old);info.insert(idx,copy.deepcopy(new))
        seq[f'plate_{number}']=json.loads(one['Metadata/filament_sequence.json'])[f'plate_{number}']
        pattern=rf'Metadata/(?:plate_{number}(?:_small)?|plate_no_light_{number}|top_{number}|pick_{number})\.(?:png|json|gcode(?:\.md5)?)'
        assets={n:v for n,v in one.items() if re.fullmatch(pattern,n)}
        assert f'Metadata/plate_{number}.gcode' in assets
        files.update(assets)
        result['sliced_plates'].append(json.loads((folder/'result.json').read_text())['sliced_plates'][0])
    files['Metadata/model_settings.config']=xml(cfg);files['Metadata/slice_info.config']=xml(info)
    files['Metadata/filament_sequence.json']=json.dumps(seq).encode()
    NATIVE.mkdir(exist_ok=True);write(NATIVE/'sliced.3mf',files)
    for number in range(1,21):
        name=f'Metadata/plate_{number}.gcode'
        assert hashlib.md5(files[name]).hexdigest()==files[name+'.md5'].decode().strip().lower()
        (NATIVE/f'plate_{number}.gcode').write_bytes(files[name])
        if number>10:assert files[name]==before[name]
    save_json(NATIVE/'result.json',result)
    print('Merged newly sliced plates 1-10; plates 11-20 retained byte-for-byte.',flush=True)


def install():
    """Install only after geometry, native toolpaths, reopen and GUI gates pass."""
    reports=WORK/'reports';proof=json.loads((reports/'joint-pad-removal-validation.json').read_text())
    assert proof['project_sha256']==sha(NATIVE/'sliced.3mf')
    assert proof['editable_sha256']==sha(WORK/'pad-free-editable.3mf')
    assert len(proof['native_pad_toolpaths'])==42
    gui=json.loads((reports/'tower-gui-verification.json').read_text())
    assert gui['GUI_tested_file_sha256']==proof['project_sha256']
    assert gui['prime_tower_collision_warning_absent_after_fresh_GUI_open']
    assert json.loads((WORK/'reopen/result.json').read_text())['return_code']==0
    for p,h in proof['protected_external_file_sha256'].items():assert sha(ROOT/p)==h
    for source,target in [(WORK/'pad-free-editable.3mf',EDIT),(NATIVE/'sliced.3mf',ROOT/'Dara.3mf'),(NATIVE/'sliced.3mf',OUT/'Dara-A2L-Complete.3mf')]:
        shutil.copyfile(source,target)
    for name in ['geometry-validation.json','native-validation.json','modifier-validation.json',
                 'joint-pad-removal-validation.json','joint-pad-unchanged-plates.json','tower-gui-verification.json']:
        shutil.copyfile(reports/name,OUT/name)
    plan,frame=baseline()
    for row in frame['joints']:
        row.update(seating_pads_removed=True,seating_pad_top_mm=None,lap_surface_after_pad_removal_mm=4.8,
                   removed_seating_pad_height_mm=.2)
    frame.update(joint_revision=REVISION,pad_removal_validation_sha256=sha(OUT/'joint-pad-removal-validation.json'),
        physical_reference_result=proof['physical_report'],physical_reference_printer_context=proof['physical_printer_context'])
    save_json(OUT/'frame-geometry-validation.json',frame)
    for name in ['plate-plan.json','Dara-A2L-Editable.json']:
        data=json.loads((OUT/name).read_text());data.update(editable_sha256=sha(EDIT),joint_revision=REVISION)
        if name=='Dara-A2L-Editable.json':data.update(native_slice_validated=True,native_project_sha256=proof['project_sha256'])
        save_json(OUT/name,data)
    # The veneer meshes and slices are byte-identical. Refresh container hashes
    # in their inventory without presenting this knot-only edit as a new M build.
    inventory=ROOT/'output/development/m-veneer-cosmetic-fit/All-veneer-production-audit.json'
    catalog=json.loads(inventory.read_text())
    targets={'Dara.3mf',str((OUT/'Dara-A2L-Complete.3mf').relative_to(ROOT)).replace('\\','/'),REL.as_posix()}
    for row in catalog['projects']:
        if row['project'] in targets:
            assert row['sha256']==sha(BASE/row['project'])
            row['sha256']=sha(ROOT/row['project'])
    catalog['pad_removal_hash_refresh_basis']=dict(report='working/bambu/Dara-Photo-Frame-A2L/joint-pad-unchanged-plates.json',
        sha256=sha(OUT/'joint-pad-unchanged-plates.json'),all_M_meshes_settings_poses_and_stored_slices_byte_preserved=True)
    save_json(inventory,catalog)
    print('Installed validated pad-free production inputs and exact preserved M/A1 evidence.',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['snapshot','build','slice','merge','install']);parser.add_argument('--plate',type=int,choices=range(1,11))
    args=parser.parse_args()
    if args.action=='slice':
        for number in ([args.plate] if args.plate else range(1,11)):slice_plate(number)
    else:{'snapshot':snapshot,'build':build,'merge':merge,'install':install}[args.action]()
