"""Audit the separate r5 wall cradle; does not modify production."""
import argparse
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
from build_veneer_wall_cradle_r5 import OUT,WORK,SOURCE,protected,source_veneer
from development_3mf import sha,save_json,props
from validate_production_split import Project
from validate_print_project import scan_gcode
from check_fin_toolpaths import check_fin_bonds
from check_veneer_wall_openings import check_openings


def differences(a,b):
    return {k:[a.get(k),b.get(k)] for k in a.keys()|b.keys() if a.get(k)!=b.get(k)}


def main(numbers=(1,2,3)):
    if (OUT/'WITHDRAWN.txt').exists():
        raise SystemExit('r5 is withdrawn. This validator must not relabel it as a current print candidate.')
    fingerprints=json.loads((WORK/'source-fingerprints.json').read_text())
    assert protected()==fingerprints
    with zipfile.ZipFile(SOURCE) as z: production=json.loads(z.read('Metadata/project_settings.config'))
    rows=[];all_estimates=[];files=[];all_changed=[]
    cache=json.loads((OUT/'validation.json').read_text()) if set(numbers)!={1,2,3} else None
    cached_estimates=json.loads((OUT/'native-slice-result.json').read_text()) if cache else None
    for i in [1,2,3]:
        if i not in numbers:
            old=next(p for p in cache['plates'] if p['veneer']==f'V{i}')
            oldfile=cache['files'][i-1]
            assert sha(Path(oldfile['final_file']))==oldfile['final_sha256']
            assert sha(Path(oldfile['editable_file']))==oldfile['editable_sha256']
            assert json.loads((WORK/f'V{i}-geometry.json').read_text())==old['geometry']
            rows.append(old);files.append(oldfile);all_estimates.append(cached_estimates[i-1])
            all_changed.append(cache['global_settings_differences'][i-1]);continue
        editable=OUT/f'Dara-A2L-Veneer-Wall-Cradle-r5-V{i}-Editable.3mf'
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
        _,_,st,source_cfg,_,source_oid=source_veneer(i)
        source_process={k:v for k,v in st.items() if k and k!='name' and v is not None}
        for key,value in source_process.items():
            assert row['settings'][key]==saved['settings'][key]==value,(name,key)
        object_diff=differences(row['settings'],saved['settings'])
        assert set(object_diff)<={'extruder','name'},object_diff
        assert saved['settings']['sparse_infill_density']=='100%'
        assert saved['settings']['enable_support']=='1'
        assert saved['settings']['extruder']=='3'
        assert len(row['parts'])==len(saved['parts'])==1
        source_obj=next(o for o in source_cfg.findall('object') if o.get('id')==source_oid)
        source_parts=source_obj.findall('part');assert len(source_parts)==1
        metadata={'name','matrix','source_file','source_object_id','source_volume_id',
                  'source_offset_x','source_offset_y','source_offset_z'}
        volume_overrides=[{k:v for k,v in d.items() if k not in metadata} for d in
            [props(source_parts[0]),row['parts'][0]['settings'],saved['parts'][0]['settings']]]
        assert volume_overrides==[{}, {}, {}],volume_overrides
        assert source_parts[0].get('subtype')==row['parts'][0]['subtype']==saved['parts'][0]['subtype']=='normal_part' 
        u=row['parts'][0]['mesh'].copy();u.apply_transform(row['T'])
        v=saved['parts'][0]['mesh'].copy();v.apply_transform(saved['T'])
        error=max(float(cKDTree(u.vertices).query(v.vertices)[0].max()),
                  float(cKDTree(v.vertices).query(u.vertices)[0].max()))
        assert error<.001,(name,error)
        arrays=np.load(WORK/f'V{i}-candidate.npz')
        generated=arrays['vertices']
        generation_error=max(float(cKDTree(generated).query(v.vertices)[0].max()),
                             float(cKDTree(v.vertices).query(generated)[0].max()))
        assert generation_error<.001,(name,'native versus latest generated geometry',generation_error)
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
        opening_checks=check_openings(text,expected['openings'])
        # Sample native MODEL extrusion on each continuous wall, including the
        # first layer. Wall centrelines come from the actual generated solids.
        wall_checks={}
        for label in ['panel','rear','webs','bands']:
            wall=trimesh.load_mesh(WORK/f'V{i}-{label}.ply',process=False)
            probes=[]
            if label=='bands':
                # Probe printable band interiors, not sharp model corners that
                # become rounded at the extrusion width. Three lanes require
                # material beyond the central 1 mm web on every band layer.
                for band in expected['bed_tie_bands']:
                    xmin,xmax=band['x_span_mm'];half=band['width_mm']/2
                    for height in [.2,.4,.6]:
                        for offset in [-half+.3,0,half-.3]:
                            for x in np.linspace(xmin+.6,xmax-.6,max(3,int((xmax-xmin)/10)+1)):
                                probes.append([float(x),band['center_y_mm']+offset,height])
            heights=[] if label=='bands' else [.2,1.,*np.arange(5,wall.bounds[1,2]-.5,10).tolist()]
            for height in heights:
                path=wall.section(plane_origin=[0,0,height-.1],plane_normal=[0,0,1])
                if path is None:continue
                for loop in path.discrete:
                    # Opposite perimeter strokes lie inside the actual slice;
                    # sampling them also checks both sides of each broad wall.
                    for a0,b0 in zip(loop,loop[1:]):
                        length=np.linalg.norm(b0-a0)
                        if length<3:continue
                        for t in np.linspace(.02,.98,max(2,int(length/12))):
                            point=a0*(1-t)+b0*t;point[2]=height
                            probes.append(point.tolist())
            check=check_fin_bonds(text,{'bond_probes_print_xyz_mm':probes},layer_tolerance_mm=.01 if label=='bands' else .45)
            check['sampling']='Three interior longitudinal lanes on each band at Z0.2, Z0.4 and Z0.6 mm; 0.3 mm inset from side edges, 0.6 mm from ends; exact layer required.' if label=='bands' else 'Actual wall perimeter at first layer, 1 mm, then 5 mm + 10 mm intervals; not a strength test.'
            wall_checks[label]=check
        info=ET.fromstring(b.z.read('Metadata/slice_info.config')).findall('plate')[0]
        warnings=[w.attrib for w in info.findall('warning')]
        assert all(w['msg']=='not_support_traditional_timelapse' for w in warnings),warnings
        estimate=estimates['sliced_plates'][0]
        weight=sum(f['total_used_g'] for f in estimate['filaments'])
        header=re.search(r'^; total filament weight \[g\] : (.*)$',text,re.M)
        assert abs(sum(float(x) for x in header[1].split(','))-weight)<.03
        final=OUT/f'Dara-A2L-Veneer-Wall-Cradle-r5-V{i}.3mf'
        files.append(dict(final_file=str(final),native_source=str(native),final_sha256=sha(native),
                          editable_file=str(editable),editable_sha256=sha(editable)))
        rows.append(dict(veneer=f'V{i}',plate=1,source_plate=i+14,estimated_filament_g=weight,
            estimated_seconds=estimate['total_predication'],native_mesh_error_mm=error,
            gcode_sha256=hashlib.sha256(raw).hexdigest(),gcode_md5_verified=True,
            bed_clearance_including_beads_mm=clearance,print_height_mm=max(levels),
            support_extrusion_moves=scan['features'].get('Support',0),bond_toolpath_check=bonds,
            grounded_wall_toolpath_checks=wall_checks,opening_toolpath_checks=opening_checks,
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
        global_settings_differences=all_changed,object_process_settings_preserved=True,volume_process_overrides_preserved=True,
        production_and_A1_fingerprints=fingerprints,production_and_A1_unchanged=True,
        plates=rows,physical_limitations=['Full-height rigidity, adhesion and warping are untested.',
            'Front backing remains solid; only rear/web walls have lightening openings.',
            'Removal of the new wall cradle without veneer damage is untested.',
            'Slicer estimate is not a measured spool consumption guarantee.'])
    save_json(OUT/'validation.json',report)
    save_json(OUT/'native-slice-result.json',all_estimates)
    print(json.dumps({k:report[k] for k in ['native_total_filament_g','headroom_to_1000g','native_total_seconds']}),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--veneers',type=int,nargs='+',default=[1,2,3]);args=parser.parse_args()
    main(args.veneers)
