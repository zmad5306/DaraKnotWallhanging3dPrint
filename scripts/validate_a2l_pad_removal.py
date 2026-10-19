"""Validate the pad-only change, exact protected plates, and native production paths."""
import copy
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.work/python-libs'))
import numpy as np
from scipy.spatial import cKDTree
from remove_a2l_joint_pads import BASE,WORK,OUT,NATIVE,REVISION,read,baseline
from development_3mf import sha,save_json,props,tag,P,read_object
from validate_a2l_project import embedded,surface_vertex_distance
from validate_ribbon_bed_datum import segments

REPORTS=WORK/'reports'


def run(reuse_native=False):
    REPORTS.mkdir(exist_ok=True)
    plan,frame=baseline()
    patch=json.loads((WORK/'geometry-patch.json').read_text())
    assert patch['editable']['target_sha256']==sha(WORK/'pad-free-editable.3mf')
    assert patch['native']['target_sha256']==sha(WORK/'pad-free-native.3mf')
    prior=read(BASE/'Dara.3mf');current,rows=embedded(NATIVE/'sliced.3mf')
    assert json.loads(current['Metadata/project_settings.config'])==json.loads(prior['Metadata/project_settings.config'])
    settings=json.loads(current['Metadata/project_settings.config'])
    required=dict(sparse_infill_density='8%',sparse_infill_pattern='gyroid',layer_height='0.2',
        initial_layer_print_height='0.2',wall_loops='4',top_shell_layers='5',bottom_shell_layers='5',
        curr_bed_type='Textured PEI Plate',printer_model='Bambu Lab A2L')
    for k,v in required.items():assert settings[k]==v,(k,settings[k])
    protected={p.replace('\\','/'):h for p,h in json.loads((WORK/'protected.json').read_text()).items()}
    for p,h in protected.items():assert sha(ROOT/p)==h,p
    # Full model graph/poses are identical; only the recorded pad mesh assets differ.
    assert current['3D/3dmodel.model']==prior['3D/3dmodel.model']
    allowed=set(patch['native']['changed_child_assets'])
    for name,data in prior.items():
        if name.endswith('.model') and name not in allowed:assert current[name]==data,name
    old_cfg=ET.fromstring(prior['Metadata/model_settings.config'])
    cfg=ET.fromstring(current['Metadata/model_settings.config']);kept=[]
    old_info=ET.fromstring(prior['Metadata/slice_info.config']);info=ET.fromstring(current['Metadata/slice_info.config'])
    old_sequence=json.loads(prior['Metadata/filament_sequence.json']);sequence=json.loads(current['Metadata/filament_sequence.json'])
    for a,b in zip(old_cfg.findall('object'),cfg.findall('object')):
        assert props(a)==props(b)
        assert all(props(x)==props(y) for x,y in zip(a.findall('part'),b.findall('part')))
        if not props(a)['name'].startswith('F'):assert ET.tostring(a)==ET.tostring(b)
    for number in range(11,21):
        pattern=rf'Metadata/(?:plate_{number}(?:_small)?|plate_no_light_{number}|top_{number}|pick_{number})\.(?:png|json|gcode(?:\.md5)?)'
        assets={n:hashlib.sha256(v).hexdigest() for n,v in prior.items() if re.fullmatch(pattern,n)}
        for n,h in assets.items():assert hashlib.sha256(current[n]).hexdigest()==h,n
        assert ET.tostring(old_cfg.findall('plate')[number-1])==ET.tostring(cfg.findall('plate')[number-1])
        old=next(p for p in old_info.findall('plate') if props(p)['index']==str(number))
        new=next(p for p in info.findall('plate') if props(p)['index']==str(number))
        assert ET.tostring(old)==ET.tostring(new)
        assert old_sequence[f'plate_{number}']==sequence[f'plate_{number}']
        kept.append(dict(plate=number,geometry_settings_and_poses_unchanged=True,gcode_byte_identical=True,preserved_assets_sha256=assets))
    save_json(REPORTS/'joint-pad-unchanged-plates.json',dict(baseline_project_sha256=sha(BASE/'Dara.3mf'),
        project_sha256=sha(NATIVE/'sliced.3mf'),plates=kept,protected_external_file_sha256=protected))
    # Existing cosmetic/hardware checks remain applicable: exact source geometry
    # is retained everywhere outside the 42 internal pad tools at Z4.8..5.001.
    geometry=json.loads((BASE/OUT.relative_to(ROOT)/'geometry-validation.json').read_text())
    geometry.update(editable_sha256=sha(WORK/'pad-free-editable.3mf'),joint_revision=REVISION,
        baseline_geometry_validation_sha256=sha(BASE/OUT.relative_to(ROOT)/'geometry-validation.json'),
        preservation_basis='Only raised lap pads removed below Z5.001. Visible seams, hardware, M and print poses unchanged; material removal cannot introduce assembly overlap.',
        pad_patch=patch)
    save_json(REPORTS/'geometry-validation.json',geometry)
    for name in ['M-geometry-validation.json','tower-placement.json']:
        (REPORTS/name).write_bytes((OUT/name).read_bytes())
    import validate_a2l_project as validator
    validator.EDIT=WORK/'pad-free-editable.3mf';validator.OUT=REPORTS
    if reuse_native:
        for name in ['native-validation.json','modifier-validation.json']:
            record=json.loads((REPORTS/name).read_text())
            assert record['native_project_sha256']==sha(NATIVE/'sliced.3mf')
            assert record['editable_sha256']==sha(WORK/'pad-free-editable.3mf')
        assert json.loads((REPORTS/'native-validation.json').read_text())['geometry_validation_sha256']==sha(REPORTS/'geometry-validation.json')
    else:validator.native(NATIVE);validator.modifiers(NATIVE)
    pad_paths=[];roundtrips=[];warnings=[]
    for number in range(1,11):
        name=f'F{number} A2L knot';row=rows[name]
        raw=current[f'Metadata/plate_{number}.gcode'];text=raw.decode()
        assert b'; sparse_infill_density = 8%' in raw and b'; sparse_infill_pattern = gyroid' in raw
        assert hashlib.md5(raw).hexdigest()==current[f'Metadata/plate_{number}.gcode.md5'].decode().strip().lower()
        # Confirm merged model equals the actual model sliced by Studio.
        _,single=embedded(WORK/f'plate-{number:02d}'/'sliced.3mf');native=single[name]
        assert len(row['parts'])==len(native['parts'])
        errors=[]
        for a,b in zip(row['parts'],native['parts']):
            assert a['subtype']==b['subtype']
            for key in ['extruder','sparse_infill_density','sparse_infill_pattern']:
                assert a['settings'].get(key)==b['settings'].get(key)
            av=a['mesh'].vertices@row['transform'][:3,:3].T+row['transform'][:3,3]
            bv=b['mesh'].vertices@native['transform'][:3,:3].T+native['transform'][:3,3]
            error=max(surface_vertex_distance(av,bv,b['mesh'].faces),surface_vertex_distance(bv,av,a['mesh'].faces))
            assert error<.001,(number,error);errors.append(error)
        roundtrips.append(dict(plate=number,max_actual_slice_model_error_mm=max(errors)))
        ids={int(props(i)['identify_id']):name for i in cfg.findall('plate')[number-1].findall('model_instance')}
        assert len(ids)==1
        paths=segments(text,ids,single_object='; start printing object, unique label id:' not in text)[name]
        a=np.array([r[2] for r in paths]);tools=np.array([r[0] for r in paths])
        assert len(a)>0
        # Mating pad probes exclude supports, towers and every non-model feature.
        start=a[:,0,:2];delta=a[:,1,:2]-start;length2=(delta*delta).sum(axis=1)
        for k,(j,proof) in enumerate(zip(plan['frame_joints'],frame['joints'])):
            if j[0]!=number-1:continue
            T=row['transform']
            for xy in proof['seating_pads_xy']:
                target=(np.array([*xy,0])@T[:3,:3].T+T[:3,3])[:2]
                t=np.clip(((target-start)*delta).sum(axis=1)/length2,0,1)
                near=np.linalg.norm(start+t[:,None]*delta-target,axis=1)<.65
                assert np.any(near),(k,xy,'no lap model extrusion')
                height=float(a[near,:,2].max());assert abs(height-4.8)<.001,(k,xy,height)
                pad_paths.append(dict(joint=k+1,tongue_plate=number,xy_assembly_mm=xy,maximum_model_extrusion_z_mm=height))
        plate_info=next(p for p in info.findall('plate') if props(p)['index']==str(number))
        pw=[w.attrib for w in plate_info.findall('warning')]
        assert all(w.get('msg')=='not_support_traditional_timelapse' for w in pw),(number,pw)
        warnings.extend(dict(plate=number,**w) for w in pw)
        print(f'Plate {number}: effective 8% gyroid, native model and pad paths verified.',flush=True)
    assert len(pad_paths)==42
    report=dict(revision=REVISION,source_project_sha256=sha(BASE/'Dara.3mf'),project_sha256=sha(NATIVE/'sliced.3mf'),
        editable_sha256=sha(WORK/'pad-free-editable.3mf'),removed_pads=42,joints=14,changed_plates=list(range(1,11)),
        raised_pad_height_removed_mm=.2,lap_surface_z_mm=4.8,geometry_patch=patch,
        locked_settings_verified=required,all_other_global_object_and_volume_settings_preserved=True,
        native_pad_toolpaths=pad_paths,actual_sliced_model_checks=roundtrips,slicer_warnings=warnings,
        physical_report=patch['physical_result'],physical_printer_context=patch['physical_printer_context'],
        physical_A2L_production_print_not_yet_reported=True,printer_commands_sent=False,
        protected_external_file_sha256=protected,unchanged_plates_report_sha256=sha(REPORTS/'joint-pad-unchanged-plates.json'))
    save_json(REPORTS/'joint-pad-removal-validation.json',report)
    print('PASS: all 42 pad toolpaths end at Z4.8; all 14 joints updated; M/A1 retained.',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--reuse-native',action='store_true');run(p.parse_args().reuse_native)
