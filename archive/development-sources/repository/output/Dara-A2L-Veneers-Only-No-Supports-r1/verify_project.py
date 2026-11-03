"""Verify the exact delivered editable project against its native slice."""
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
sys.path[:0]=[str(ROOT/'.work/python-libs'),str(ROOT/'scripts')]
import numpy as np
from scipy.spatial import cKDTree
import development_3mf as d
from build_project import protected, FINAL

NATIVE=ROOT/'.work/veneer-only-no-supports-r1/canonical/validation-sliced.3mf'


def read(path):
    with zipfile.ZipFile(path) as z:
        files={n:z.read(n) for n in z.namelist() if n.endswith('.model') or n in
               ['Metadata/model_settings.config','Metadata/project_settings.config']}
    root=ET.fromstring(files['3D/3dmodel.model'])
    cfg=ET.fromstring(files['Metadata/model_settings.config'])
    settings=json.loads(files['Metadata/project_settings.config'])
    result={}
    plates=cfg.findall('plate')
    assert len(plates)==3 and len(cfg.findall('object'))==3
    pitch=np.ptp(np.array([[float(v) for v in p.split('x')] for p in settings['printable_area']]),axis=0)*1.2
    for pi,plate in enumerate(plates):
        instances=plate.findall('model_instance');assert len(instances)==1
        oid=d.props(instances[0])['object_id']
        parts,st=d.read_object(files,oid)
        assert len(parts)==1 and parts[0]['subtype']=='normal_part'
        st={k:v for k,v in st.items() if k}
        assert st['enable_support']=='0' and st['sparse_infill_density']=='100%' and st['extruder']=='3'
        assert parts[0]['settings'].get('enable_support','0')=='0'
        item=next(i for i in root.find(d.tag('build')) if i.get('objectid')==oid)
        T=d.transform(item.get('transform'))
        T[:2,3]-=[pi%2*pitch[0],-(pi//2)*pitch[1]]
        m=parts[0]['mesh'];m.apply_transform(T)
        assert m.is_watertight and m.is_volume
        result[pi+1]=dict(mesh=m,settings=st)
    return settings,result


def main():
    report=json.loads((OUT/'validation.json').read_text())
    assert protected()==report['protected_sha256']
    settings,editable=read(FINAL)
    native_settings,native=read(NATIVE)
    assert settings==native_settings
    locked={'sparse_infill_density':'8%','sparse_infill_pattern':'gyroid','layer_height':'0.2',
        'initial_layer_print_height':'0.2','wall_loops':'4','top_shell_layers':'5',
        'bottom_shell_layers':'5','curr_bed_type':'Textured PEI Plate','enable_support':'0'}
    assert all(settings[k]==v for k,v in locked.items())
    assert settings['nozzle_diameter']==['0.4']
    assert settings['printer_model']=='Bambu Lab A2L'
    result=json.loads(NATIVE.with_name('result.json').read_text())
    assert result['return_code']==0 and len(result['sliced_plates'])==3
    checks=[]
    with zipfile.ZipFile(NATIVE) as z:
        for plate in (1,2,3):
            a,b=editable[plate],native[plate]
            assert a['settings']==b['settings']
            error=max(float(cKDTree(a['mesh'].vertices).query(b['mesh'].vertices)[0].max()),
                      float(cKDTree(b['mesh'].vertices).query(a['mesh'].vertices)[0].max()))
            assert error<0.001
            raw=z.read(f'Metadata/plate_{plate}.gcode')
            checksum=z.read(f'Metadata/plate_{plate}.gcode.md5').decode().strip().lower()
            assert hashlib.md5(raw).hexdigest()==checksum
            text=raw.decode()
            features=sorted(set(re.findall(r'^; FEATURE: (.+)$',text,re.M)))
            assert not any('support' in feature.lower() for feature in features)
            for key,value in locked.items():
                assert re.search(r'^; '+key+r' = '+re.escape(value)+r'$',text,re.M),(plate,key)
            assert re.search(r'^; nozzle_diameter = 0\.4$',text,re.M)
            row=next(r for r in result['sliced_plates'] if r['id']==plate)
            checks.append(dict(plate=plate,veneer=f'V{plate}',native_pose_error_mm=error,
                settings_identical=True,gcode_md5=checksum,gcode_features=features,
                support_toolpaths=0,warning=row.get('warning_message',''),
                slicer_estimated_seconds=row['total_predication'],
                slicer_estimated_grams=sum(f['total_used_g'] for f in row['filaments'])))
    report.update(sha256=d.sha(FINAL),native_slice_validated=True,
        native_slice_sha256=d.sha(NATIVE),native_validation=checks,
        delivery_contains_stored_slices=False,
        printability_note='Native slicer flags floating regions on all three veneers with supports disabled. No physical print is established.')
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    with (OUT/'README.txt').open('a') as f:
        f.write('\nNative validation: Bambu Studio successfully sliced all 3 plates; no support toolpaths.\n'
                'Bambu Studio flags FLOATING REGIONS on ALL THREE plates with supports disabled.\n'
                'The requested editable project retains the saved angle and supports-off configuration.\n'
                'Print success has not been established.\n\n')
        for row in checks:
            minutes=round(row['slicer_estimated_seconds']/60)
            f.write(f"V{row['plate']}: {minutes//60}h {minutes%60:02d}m, {row['slicer_estimated_grams']:.1f} g (native estimate).\n")
        f.write('\nDelivered project SHA-256: '+report['sha256']+'\n')
    print(json.dumps({'sha256':report['sha256'],'plates':checks},indent=2))


if __name__=='__main__':main()
