"""Record the user's r2 joint-fit report and verify the matching production file.

This does not edit or reslice a print artifact: the accepted test was already
cropped from the current production geometry and settings.
"""
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'.work/python-libs'),str(ROOT/'scripts')]
import numpy as np
from shapely.geometry import shape
from development_3mf import solid
from build_a2l_project import prism
from organize_root_projects import rows,BOOKKEEPING
from remove_unused_project_filaments import read,digest,dump
from revert_knot_infill_first import protected

SOURCE=ROOT/'Knot.3mf'
SAMPLE_DIR=ROOT/'output/Dara-A2L-Joint-Photo-Retainer-Bolster-r2'
SAMPLE=SAMPLE_DIR/'Dara-A2L-Joint-Photo-Retainer-Bolster-r2.3mf'
SOURCE_SHA='aefab9b242945a149fdc18900c694c556eb7ad5d8d5d5f7fbc4451280730ae46'
SAMPLE_SHA='c0e48a0b2f7c8bf8adcc696b9785d4ff49359dd9104536ca486a1ec50055154d'
OUT=ROOT/'release/knot-joint-approval-r1'

def effective(s):return {k:v for k,v in s.items() if k not in BOOKKEEPING}

def main():
    assert digest(SOURCE)==SOURCE_SHA and digest(SAMPLE)==SAMPLE_SHA
    before=protected()
    geometry=json.loads((SAMPLE_DIR/'geometry-validation.json').read_text())
    sample_report=json.loads((SAMPLE_DIR/'validation.json').read_text())
    target=json.loads((SAMPLE_DIR/'photo-retainer-audit.json').read_text())
    release=json.loads((ROOT/'release/knot-normal-supports-r1/validation.json').read_text())
    assert geometry['source_sha256']==sample_report['source_sha256']==release['project_sha256']==SOURCE_SHA
    assert sample_report['sample_sha256']==target['native_project_sha256']==SAMPLE_SHA
    assert target['feature']=='PHOTO_RETAINER_BLIND_SCREW_HOLE'
    s,objects=rows(SOURCE);ss,sample=rows(SAMPLE)
    difference={k:[s.get(k),ss.get(k)] for k in set(s)|set(ss) if s.get(k)!=ss.get(k)}
    assert difference==geometry['global_setting_changes']
    assert set(difference)=={'print_settings_id','wipe_tower_x','wipe_tower_y'}
    crop=prism(shape(geometry['crop_assembly_polygon']),*geometry['crop_z_mm'])
    comparisons=[]
    for original,got,record in zip([objects[1],objects[2]],sample,geometry['source_volume_checks']):
        assert effective(original['settings'])==effective(got['settings'])
        assert np.max(abs(original['transform'][:3,:3]-got['transform'][:3,:3]))<1e-6
        assert len(got['parts'])==len(record['volume_crops'])
        for p,link in zip(got['parts'],record['volume_crops']):
            source=original['parts'][link['source_volume_index']]
            assert source['subtype']==p['subtype'] and effective(source['settings'])==effective(p['settings'])
            assert source['paint']==p['paint']==[]
            expected=solid(source['mesh'])^crop;actual=solid(p['mesh'])
            extra=abs((actual-expected).volume());missing=abs((expected-actual).volume())
            tolerance=p['mesh'].area*.000005
            assert extra+missing<tolerance
            comparisons.append(dict(source_object=original['name'],source_volume=link['source_volume_index'],
                extra_volume_mm3=extra,missing_volume_mm3=missing,native_rounding_tolerance_mm3=tolerance))
    files=read(SOURCE);plates=[]
    assert s['is_infill_first']=='0' and s['support_type']=='normal(auto)'
    for i in range(1,11):
        text=files[f'Metadata/plate_{i}.gcode'].decode()
        config=dict(re.findall(r'^; ([A-Za-z_0-9]+) = (.*)$',text,re.M))
        assert config['is_infill_first']=='0' and config['support_type']=='normal(auto)'
        plates.append(dict(plate=i,infill_first=False,support_type='normal(auto)'))
    joint_geometry=json.loads((ROOT/release['joint_geometry_report']).read_text())
    joint_paths=json.loads((ROOT/release['joint_toolpath_report']).read_text())
    assert joint_geometry['joint_count']==14 and joint_geometry['key_count']==28
    assert len(joint_paths['probes'])==140
    assert digest(SOURCE)==SOURCE_SHA and digest(SAMPLE)==SAMPLE_SHA and protected()==before
    evidence=[SAMPLE_DIR/n for n in ('geometry-validation.json','validation.json','photo-retainer-audit.json')]
    evidence+=[ROOT/'release/knot-normal-supports-r1/validation.json',ROOT/release['joint_geometry_report'],ROOT/release['joint_toolpath_report']]
    report=dict(date='2026-10-25',project='Knot.3mf',project_sha256=SOURCE_SHA,
        accepted_sample=SAMPLE.relative_to(ROOT).as_posix(),accepted_sample_sha256=SAMPLE_SHA,
        user_statement='Joints are ok, propagate them into the project as well as the infill first change. Commit and push when done.',
        sample_identification_basis='Follow-up to the supplied current r2 J3 photo-retainer sample; actual printed hash/printer not independently observed.',
        user_reported_sample_joint_fit_pass=True,bolster_surface_finish_confirmed=False,
        full_size_print_performance_confirmed=False,production_geometry_already_matches_accepted_sample=True,
        new_geometry_changes=[],new_slices_required=False,
        slice_reason='The unchanged current production hash is the source of accepted r2; all ten native slices already contain the authorized rollback and normal supports.',
        production_joint_count=14,key_count=28,native_key_layer_checks=140,plates=plates,
        sample_crop_comparisons=comparisons,sample_packaging_setting_changes=difference,
        evidence_sha256={p.relative_to(ROOT).as_posix():digest(p) for p in evidence},
        protected_artifacts_sha256=before,printer_job_sent=False)
    dump(OUT/'validation.json',report)
    print('Verified accepted r2 matches production: 14 joints, 28 keys, ten infill-first-off normal-support slices. No artifact regeneration required.',flush=True)

if __name__=='__main__':main()
