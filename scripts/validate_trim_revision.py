"""Regression checks against failed coupons, plus unchanged release bindings.

The old starter shoe must fail the same cutter-access check the revision passes.
Only sample_project changes in the shared M module; production functions and
all production project bytes must remain unchanged when refreshing provenance.
"""
import argparse
import ast
import json
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
import numpy as np
from shapely.geometry import box
from development_3mf import ROOT,OUT,read_object,solid,mesh,save_json,sha,props,tag,transform
from develop_m_veneer import prism
from preserve_unchanged_plates import read

BASELINE='1aba43ad66e21ffbb15b598fed86296aeba7ee39'


def validate(baseline):
    cases=[]
    for kind in ['Glue','Seam']:
        name=f'M-Veneer-{kind}-Coupon-A1';old=read(baseline/(name+'.3mf'));new=read(OUT/(name+'.3mf'))
        seating=json.loads((OUT/(name+'-seating.json')).read_text())
        guide=json.loads((OUT/(name+'.json')).read_text())
        for panel in seating['panels']:
            c=panel['carrier'];pose=np.array(c['assembly_to_printer'])
            oid=str(next(r for r in guide['records'] if r['plate']==panel['panel']+1)['object_id'])
            before=read_object(old,oid)[0][0]['mesh'];after=read_object(new,oid)[0][0]['mesh']
            for m in [before,after]:m.apply_transform(np.linalg.inv(pose))
            a,b=solid(before),solid(after)
            front=prism(box(-1000,-1000,1000,1000),9.21,40)
            change=((a-b)^front).volume()+((b-a)^front).volume()
            assert change<1e-5,('Changed show face',kind,panel['panel'],change)
            blocked_old=[];blocked_new=[]
            for probe in c['bond_probes_print_xyz_mm'][-c['starter_rib_count']:]:
                x,y,_=(np.array(probe)-pose[:3,3])@pose[:3,:3]
                opening=box(x-1,y-1,x+1,y+1).difference(box(x-.6,y-.6,x+.6,y+.6))
                tool=prism(opening,8.5,8.7)
                blocked_old.append(float((tool^a).volume()))
                blocked_new.append(float((tool^b).volume()))
            assert max(blocked_new)<1e-5
            assert max(blocked_old)>.05,'Negative control failed to detect the old welded shoe'
            cases.append(dict(project=name,panel=panel['panel'],show_face_difference_mm3=float(change),
                old_shoe_cutter_obstruction_mm3=max(blocked_old),new_rib_cutter_obstruction_mm3=max(blocked_new)))
    old,new=read(baseline/'baseline.3mf'),read(OUT/'All-Development-Tests-A1-Sliced.3mf')
    # All three structural coupons retain exact geometry and process settings.
    cores=[]
    def core_ids(files):
        cfg=ET.fromstring(files['Metadata/model_settings.config'])
        return {props(o)['name']:o.get('id') for o in cfg.findall('object') if props(o).get('name','').startswith(('M glue core','M seam core'))}
    before_ids,after_ids=core_ids(old),core_ids(new);assert before_ids.keys()==after_ids.keys() and len(before_ids)==3
    for name,oid in before_ids.items():
        nid=after_ids[name]
        a,sa=read_object(old,oid);b,sb=read_object(new,nid);assert sa==sb
        poses=[]
        for files,identity in [(old,oid),(new,nid)]:
            root=ET.fromstring(files['3D/3dmodel.model'])
            poses.append(transform(root.find(tag('build')).find(f"{tag('item')}[@objectid='{identity}']").get('transform')))
        assert np.array_equal(*poses)
        for x,y in zip(a,b):
            assert x['settings']==y['settings'] and x['subtype']==y['subtype']
            assert np.array_equal(x['mesh'].vertices,y['mesh'].vertices)
            assert np.array_equal(x['mesh'].faces,y['mesh'].faces)
        cores.append(dict(name=sa['name'],geometry_settings_and_pose_exact=True))
    preserved=json.loads((OUT/'Zero-gap-plate-preservation.json').read_text())
    assert preserved['project_sha256']==sha(OUT/'All-Development-Tests-A1-Sliced.3mf')
    report=dict(baseline_commit=BASELINE,negative_control_and_front_preservation=cases,
        unchanged_structural_coupons=cores,preserved_complete_plates=[1,3],
        project_sha256=preserved['project_sha256'],physical_cutting_and_finish_confirmation_pending=True)
    save_json(OUT/'M-clean-trim-regression-validation.json',report)
    return report


def rebind():
    path=ROOT/'working/bambu/Dara-Photo-Frame-A2L/release-validation.json'
    release=json.loads(path.read_text());script='scripts/develop_m_veneer.py'
    old_source=subprocess.check_output(['git','show',f'{BASELINE}:{script}'],cwd=ROOT).decode()
    def nodes(source):
        return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(source).body if isinstance(n,ast.FunctionDef)}
    old,new=nodes(old_source),nodes((ROOT/script).read_text())
    assert old.keys()==new.keys()
    assert [k for k in old if old[k]!=new[k]]==['sample_project']
    # The only module-level edit must also be within the coupon function.
    def without_coupon(source):
        tree=ast.parse(source);tree.body=[n for n in tree.body if not (isinstance(n,ast.FunctionDef) and n.name=='sample_project')]
        return ast.dump(tree,include_attributes=False)
    assert without_coupon(old_source)==without_coupon((ROOT/script).read_text())
    for rel,h in release['evidence_sha256'].items():
        if rel!=script:assert sha(ROOT/rel)==h,rel
    for project in ['Dara.3mf','working/bambu/Dara-Photo-Frame-A2L/Dara-A2L-Complete.3mf']:
        assert sha(ROOT/project)==release['project_sha256']
    old_hash=release['evidence_sha256'][script]
    release['evidence_sha256'][script]=sha(ROOT/script)
    release['sample_project_sha256']=sha(OUT/'All-Development-Tests-A1-Sliced.3mf')
    release['coupon_carrier_update']=dict(revision='clean-trim-coupon-v1',baseline_commit=BASELINE,
        previous_shared_M_module_sha256=old_hash,current_shared_M_module_sha256=sha(ROOT/script),
        only_sample_project_function_changed=True,production_functions_and_project_bytes_unchanged=True,
        geometry_proof='output/development/m-veneer-cosmetic-fit/M-clean-trim-carrier-validation.json',
        physical_removal_confirmation_pending=True,A2L_veneer_plates_15_to_17_on_hold=True)
    save_json(path,release)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('baseline',type=Path);parser.add_argument('--rebind',action='store_true')
    args=parser.parse_args();r=validate(args.baseline)
    if args.rebind:rebind()
    print('PASS: original shoe fails access check; new ribs pass; show faces, three cores, plates 1 and 3 preserved.')
