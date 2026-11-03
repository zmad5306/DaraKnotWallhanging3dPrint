"""Audit the separate r1 wall cradle; does not modify production."""
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'.work/python-libs'),str(ROOT/'scripts')]
import numpy as np
import trimesh
from scipy.spatial import cKDTree
from build_veneer_wall_cradle import OUT,WORK,SOURCE,protected,source_veneer
from development_3mf import sha,save_json
from validate_production_split import Project
from validate_print_project import scan_gcode
from check_fin_toolpaths import check_fin_bonds


def differences(a,b):
    return {k:[a.get(k),b.get(k)] for k in a.keys()|b.keys() if a.get(k)!=b.get(k)}


def main():
    if (OUT/'WITHDRAWN.txt').exists():
        raise SystemExit('r1 is withdrawn. This validator must not relabel it as a current print candidate.')
    fingerprints=json.loads((WORK/'source-fingerprints.json').read_text())
    assert protected()==fingerprints
    with zipfile.ZipFile(SOURCE) as z: production=json.loads(z.read('Metadata/project_settings.config'))
    rows=[];all_estimates=[];files=[];all_changed=[]
    for i in [1,2,3]:
        editable=OUT/f'Dara-A2L-Veneer-Wall-Cradle-r1-V{i}-Editable.3mf'
        native=WORK/f'V{i}/sliced.3mf'
        a=Project(editable);b=Project(native)
        assert a.settings==b.settings
        assert a.rows.keys()==b.rows.keys()
        assert len(a.rows)==1
        name,row=next(iter(a.rows.items()))
        changed=differences(production,a.settings)
        assert set(changed)<={'print_settings_id','wipe_tower_x','wipe_tower_y'}
        all_changed.append(changed)
        for key,value in {'sparse_infill_density':'8%','sparse_infill_pattern':'gyroid','wall_loops':'4',
                          'top_shell_layers':'5','bottom_shell_layers':'5','layer_height':'0.2',
                          'initial_layer_print_height':'0.2','curr_bed_type':'Textured PEI Plate',
                          'printer_model':'Bambu Lab A2L'}.items():
            assert a.settings[key]==value,(key,a.settings.get(key),value)
        assert a.settings['nozzle_diameter']==['0.4']
        estimates=json.loads((WORK/f'V{i}/result.json').read_text())
        assert estimates['return_code']==0
        all_estimates.append(estimates)
        expected=json.loads((WORK/f'V{i}-geometry.json').read_text())
        assert expected['source_sha256']==sha(SOURCE)
        saved=b.rows[name]
        _,_,st,*_=source_veneer(i)
        source_process={k:v for k,v in st.items() if k and k!='name' and v is not None}
        for key,value in source_process.items():
            assert row['settings'][key]==saved['settings'][key]==value,(name,key)
        object_diff=differences(row['settings'],saved['settings'])
        assert set(object_diff)<={'extruder','name'},object_diff
        assert saved['settings']['sparse_infill_density']=='100%'
        assert saved['settings']['enable_support']=='1'
        assert saved['settings']['extruder']=='3'
        assert len(row['parts'])==len(saved['parts'])==1
        u=row['parts'][0]['mesh'].copy();u.apply_transform(row['T'])
        v=saved['parts'][0]['mesh'].copy();v.apply_transform(saved['T'])
        error=max(float(cKDTree(u.vertices).query(v.vertices)[0].max()),
                  float(cKDTree(v.vertices).query(u.vertices)[0].max()))
        assert error<.001,(name,error)
        assert v.is_volume
        assert np.all(v.bounds[0]>=[.49,.49,-.001]) and np.all(v.bounds[1]<=[329.51,319.51,325.001])
        raw=b.z.read('Metadata/plate_1.gcode');text=raw.decode()
        assert hashlib.md5(raw).hexdigest()==b.z.read('Metadata/plate_1.gcode.md5').decode().strip().lower()
        scan=scan_gcode(text)
        lo,hi=np.array(scan['bead_xy_bounds_mm'])
        clearance=float(min(*lo,*(np.array([330,320])-hi)))
        assert clearance>.5
        assert set(scan['model_extrusion_z_by_filament_mm'])=={'3'}
        levels=scan['model_extrusion_z_by_filament_mm']['3']
        assert min(levels)==.2 and max(levels)<=325
        assert scan['features'].get('Support',0)>0
        for key,value in [('sparse_infill_density','8%'),('sparse_infill_pattern','gyroid'),('wall_loops','4'),
                          ('top_shell_layers','5'),('bottom_shell_layers','5'),('layer_height','0.2')]:
            found=re.search(r'^; '+key+r' = (.*)$',text,re.M)
            assert found and found[1].strip()==value,(key,found[1] if found else None)
        bonds=check_fin_bonds(text,expected)
        info=ET.fromstring(b.z.read('Metadata/slice_info.config')).findall('plate')[0]
        warnings=[w.attrib for w in info.findall('warning')]
        assert all(w['msg']=='not_support_traditional_timelapse' for w in warnings),warnings
        estimate=estimates['sliced_plates'][0]
        weight=sum(f['total_used_g'] for f in estimate['filaments'])
        header=re.search(r'^; total filament weight \[g\] : (.*)$',text,re.M)
        assert abs(sum(float(x) for x in header[1].split(','))-weight)<.03
        final=OUT/f'Dara-A2L-Veneer-Wall-Cradle-r1-V{i}.3mf'
        files.append(dict(final_file=str(final),native_source=str(native),final_sha256=sha(native),
                          editable_file=str(editable),editable_sha256=sha(editable)))
        rows.append(dict(veneer=f'V{i}',plate=1,source_plate=i+14,estimated_filament_g=weight,
            estimated_seconds=estimate['total_predication'],native_mesh_error_mm=error,
            gcode_sha256=hashlib.sha256(raw).hexdigest(),gcode_md5_verified=True,
            bed_clearance_including_beads_mm=clearance,print_height_mm=max(levels),
            support_extrusion_moves=scan['features'].get('Support',0),bond_toolpath_check=bonds,
            native_warnings=warnings,geometry=expected))
        print(f'Validated V{i}: {weight:.2f} g; {estimate["total_predication"]/3600:.2f} hours; {bonds["bond_probes_checked"]} necks',flush=True)
    total=sum(r['estimated_filament_g'] for r in rows)
    assert total<1000,total
    assert protected()==fingerprints
    for f in files:shutil.copyfile(f['native_source'],f['final_file'])
    report=dict(status='DIGITAL_CHECKS_COMPLETE_PHYSICAL_STABILITY_AND_REMOVAL_UNTESTED',
        source=str(SOURCE),source_sha256=sha(SOURCE),user_current_slicer_total_g=1203.88,
        native_total_filament_g=total,headroom_to_1000g=1000-total,
        reduction_from_user_current_total_g=1203.88-total,
        native_total_seconds=sum(r['estimated_seconds'] for r in rows),
        files=files,
        global_settings_differences=all_changed,object_process_settings_preserved=True,
        production_and_A1_fingerprints=fingerprints,production_and_A1_unchanged=True,
        plates=rows,physical_limitations=['Full-height rigidity, adhesion and warping are untested.',
            'Continuous backing has no cutter-access openings, as explicitly requested.',
            'Removal of the new wall cradle without veneer damage is untested.',
            'Slicer estimate is not a measured spool consumption guarantee.'])
    save_json(OUT/'validation.json',report)
    save_json(OUT/'native-slice-result.json',all_estimates)
    print(json.dumps({k:report[k] for k in ['native_total_filament_g','headroom_to_1000g','native_total_seconds']}),flush=True)


if __name__=='__main__':main()
