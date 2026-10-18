"""Merge one native sliced plate into a full native project after input checks.

Studio exports only the selected plate's model for --slice N. Keep the full
project's resource IDs and mesh assets; verify the selected mesh/pose, then
replace that plate's native assets and per-object process settings.
"""
import argparse,copy,json,re,shutil,zipfile
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial import cKDTree
from development_3mf import props,read_object,sha,save_json
from validate_development_candidates import project_geometry


def merge(full,selected,target,number,report):
    def read(p):
        with zipfile.ZipFile(p) as z:return {n:z.read(n) for n in z.namelist()}
    before=read(full/'sliced.3mf');one=read(selected/'sliced.3mf');out=dict(before)
    assert json.loads(before['Metadata/project_settings.config'])==json.loads(one['Metadata/project_settings.config'])
    key='Metadata/model_settings.config';fc,sc=[ET.fromstring(f[key]) for f in [before,one]]
    fp,sp=fc.findall('plate')[number-1],sc.findall('plate')[number-1]
    assert len(fp.findall('model_instance'))==len(sp.findall('model_instance'))==1
    foid=props(fp.find('model_instance'))['object_id'];soid=props(sp.find('model_instance'))['object_id']
    a,ast=read_object(before,foid);b,bst=read_object(one,soid)
    assert ast['name']==bst['name'] and len(a)==len(b)
    for x,y in zip(a,b):
        assert x['subtype']==y['subtype'] and x['settings']==y['settings']
        assert np.array_equal(x['mesh'].faces,y['mesh'].faces)
    va=project_geometry(full/'sliced.3mf')[ast['name']];vb=project_geometry(selected/'sliced.3mf')[bst['name']]
    error=max(float(cKDTree(va).query(vb)[0].max()),float(cKDTree(vb).query(va)[0].max()));assert error<.001
    process_changes={k:[ast.get(k),bst.get(k)] for k in ast.keys()|bst.keys() if ast.get(k)!=bst.get(k)}
    obj=fc.find(f"object[@id='{foid}']");newobj=sc.find(f"object[@id='{soid}']")
    for node in obj.findall('metadata'):obj.remove(node)
    for node in newobj.findall('metadata'):obj.insert(0,copy.deepcopy(node))
    for node in fp.findall('metadata'):fp.remove(node)
    for node in sp.findall('metadata'):fp.insert(0,copy.deepcopy(node))
    out[key]=ET.tostring(fc,encoding='utf-8',xml_declaration=True)
    key='Metadata/slice_info.config';fc,sc=[ET.fromstring(f[key]) for f in [before,one]]
    old=next(p for p in fc.findall('plate') if props(p)['index']==str(number));new=next(p for p in sc.findall('plate') if props(p)['index']==str(number))
    index=list(fc).index(old);fc.remove(old);fc.insert(index,copy.deepcopy(new));out[key]=ET.tostring(fc,encoding='utf-8',xml_declaration=True)
    key='Metadata/filament_sequence.json';a,b=[json.loads(f[key]) for f in [before,one]];a[f'plate_{number}']=b[f'plate_{number}'];out[key]=json.dumps(a).encode()
    assets={n:v for n,v in one.items() if re.fullmatch(rf'Metadata/(?:plate_{number}(?:_small)?|plate_no_light_{number}|top_{number}|pick_{number})\.(?:png|json|gcode(?:\.md5)?)',n)}
    assert f'Metadata/plate_{number}.gcode' in assets;out.update(assets)
    target.mkdir(exist_ok=True)
    with zipfile.ZipFile(target/'sliced.3mf','w',zipfile.ZIP_DEFLATED) as z:
        for n,v in out.items():z.writestr(n,v)
    result=json.loads((full/'result.json').read_text());single=json.loads((selected/'result.json').read_text())
    assert result['return_code']==single['return_code']==0
    assert len(single['sliced_plates'])==1 and single['sliced_plates'][0]['id']==number
    index=next(i for i,p in enumerate(result['sliced_plates']) if p['id']==number);result['sliced_plates'][index]=single['sliced_plates'][0]
    save_json(target/'result.json',result)
    kept=[]
    for p in full.glob('plate_*.gcode'):
        pi=int(p.stem.split('_')[-1]);source=selected/p.name if pi==number else p
        shutil.copyfile(source,target/p.name)
        if pi!=number:
            assert out[f'Metadata/{p.name}']==before[f'Metadata/{p.name}'];kept.append(pi)
    assert all(out[n]==v for n,v in before.items() if n.endswith('.model'))
    save_json(report,dict(project_sha256=sha(target/'sliced.3mf'),baseline_sha256=sha(full/'sliced.3mf'),single_native_sha256=sha(selected/'sliced.3mf'),
        replaced_native_plate=number,object=ast['name'],process_changes=process_changes,maximum_mesh_and_pose_error_mm=error,
        all_mesh_assets_byte_identical=True,other_native_toolpaths_byte_identical=sorted(kept)))
    print('Merged native plate',number,'with process changes',process_changes,'; all other slices preserved',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('full',type=Path);p.add_argument('selected',type=Path);p.add_argument('target',type=Path);p.add_argument('plate',type=int);p.add_argument('--report',type=Path,required=True);a=p.parse_args();merge(a.full,a.selected,a.target,a.plate,a.report)
