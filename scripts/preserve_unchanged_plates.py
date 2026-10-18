"""Retain exact previously sliced plates after verifying unchanged print inputs.

Select unchanged plates from the prior combined project. Geometry, object
settings, material presets and poses must match first.
Copy original plate assets, model records and toolpaths, then audit hashes.
"""
import argparse
import copy
import hashlib
import json
import re
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile
import numpy as np
from development_3mf import read_object,props,tag,P,transform,sha,save_json,OUT


def read(path):
    with zipfile.ZipFile(path) as z:return {n:z.read(n) for n in z.namelist()}


def replace(parent,old,new):
    index=list(parent).index(old);parent.remove(old);parent.insert(index,copy.deepcopy(new))


def preserve(baseline,target,plates,native_dir=None,baseline_result=None,baseline_commit=None,report_path=None):
    old,new=read(baseline),read(target)
    old_settings=json.loads(old['Metadata/project_settings.config'])
    new_settings=json.loads(new['Metadata/project_settings.config'])
    assert old_settings==new_settings,'Global print/material settings changed'
    cfg_key='Metadata/model_settings.config';model_key='3D/3dmodel.model'
    oc,nc=ET.fromstring(old[cfg_key]),ET.fromstring(new[cfg_key])
    om,nm=ET.fromstring(old[model_key]),ET.fromstring(new[model_key])
    ore,nre=om.find(tag('resources')),nm.find(tag('resources'))
    ob,nb=om.find(tag('build')),nm.find(tag('build'))
    records=[]
    for number in plates:
        op,np_=oc.findall('plate')[number-1],nc.findall('plate')[number-1]
        assert props(op)['plater_name']==props(np_)['plater_name']
        oi,ni=op.findall('model_instance'),np_.findall('model_instance')
        assert [{k:v for k,v in props(i).items() if k!='object_id'} for i in oi]==[{k:v for k,v in props(i).items() if k!='object_id'} for i in ni]
        names=[];id_map={}
        for instance,new_instance in zip(oi,ni):
            oid=props(instance)['object_id'];new_oid=props(new_instance)['object_id'];id_map[oid]=new_oid
            old_parts,old_obj=read_object(old,oid);new_parts,new_obj=read_object(new,new_oid)
            assert old_obj==new_obj,(oid,'Object settings changed')
            assert len(old_parts)==len(new_parts)
            for a,b in zip(old_parts,new_parts):
                # Source object indices are provenance IDs, renumbered when
                # Studio flattens the additional core. They are not settings.
                clean=lambda values:{k:v for k,v in values.items() if k!='source_object_id'}
                assert a['subtype']==b['subtype'] and clean(a['settings'])==clean(b['settings']),(oid,'Part settings changed')
                assert np.array_equal(a['mesh'].faces,b['mesh'].faces),(oid,'Mesh topology changed')
                assert np.allclose(a['mesh'].vertices,b['mesh'].vertices,atol=1e-9,rtol=0),(oid,'Mesh changed')
            old_item=ob.find(f"{tag('item')}[@objectid='{oid}']");new_item=nb.find(f"{tag('item')}[@objectid='{new_oid}']")
            assert np.allclose(transform(old_item.get('transform')),transform(new_item.get('transform')),atol=1e-9,rtol=0),(oid,'Pose changed')
            # Studio renumbers native resource IDs after adding an object.
            # Retain its current, internally consistent mesh graph after the
            # exact mesh/process checks above; remap only saved plate references.
            names.append(old_obj['name'])
        retained_plate=copy.deepcopy(op)
        for instance in retained_plate.findall('model_instance'):
            md=instance.find("metadata[@key='object_id']");md.set('value',id_map[md.get('value')])
        replace(nc,np_,retained_plate)
        asset_pattern=rf'Metadata/(?:(?:plate_{number}(?:_small)?\.(?:png|json|gcode(?:\.md5)?))|(?:plate_no_light|top|pick)_{number}\.png)'
        assets={name:data for name,data in old.items() if re.fullmatch(asset_pattern,name)}
        new.update(assets)
        row=dict(plate=number,objects=names,geometry_settings_and_poses_unchanged=True,native_resource_id_mapping=id_map,
                 preserved_assets_sha256={name:hashlib.sha256(data).hexdigest() for name,data in assets.items()})
        if native_dir is not None:
            gcode=f'Metadata/plate_{number}.gcode';assert gcode in assets
            (native_dir/f'plate_{number}.gcode').write_bytes(old[gcode])
            row['gcode_byte_identical']=True
        records.append(row)
    for key,idx in [('Metadata/slice_info.config','index')]:
        if key not in old:continue
        before,after=ET.fromstring(old[key]),ET.fromstring(new[key])
        for number in plates:
            a=next(p for p in before.findall('plate') if props(p)[idx]==str(number))
            b=next(p for p in after.findall('plate') if props(p)[idx]==str(number))
            replace(after,b,a)
        new[key]=ET.tostring(after,encoding='utf-8',xml_declaration=True)
    seq='Metadata/filament_sequence.json'
    if seq in old:
        a,b=json.loads(old[seq]),json.loads(new[seq])
        for number in plates:b[f'plate_{number}']=a[f'plate_{number}']
        new[seq]=json.dumps(b,separators=(',',':')).encode()
    new[cfg_key]=ET.tostring(nc,encoding='utf-8',xml_declaration=True)
    new[model_key]=ET.tostring(nm,encoding='utf-8',xml_declaration=True)
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        for name,data in new.items():z.writestr(name,data)
    final=read(target)
    for row in records:
        for name,h in row['preserved_assets_sha256'].items():assert hashlib.sha256(final[name]).hexdigest()==h
    if native_dir is not None:
        result=json.loads((native_dir/'result.json').read_text());prior=json.loads(baseline_result.read_text())
        for number in plates:
            index=next(i for i,p in enumerate(result['sliced_plates']) if p['id']==number)
            result['sliced_plates'][index]=next(p for p in prior['sliced_plates'] if p['id']==number)
        save_json(native_dir/'result.json',result)
        report=dict(baseline_project_sha256=sha(baseline),retained_from_commit=baseline_commit,
                    project_sha256=sha(target),plates=records)
        save_json(report_path or OUT/'Zero-gap-plate-preservation.json',report)
    print('Preserved unchanged plates',plates,'in',target,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('baseline',type=Path);p.add_argument('target',type=Path)
    p.add_argument('--plates',type=int,nargs='+',required=True);p.add_argument('--native-dir',type=Path)
    p.add_argument('--baseline-result',type=Path);p.add_argument('--baseline-commit');p.add_argument('--report-path',type=Path);args=p.parse_args()
    preserve(args.baseline,args.target,args.plates,args.native_dir,args.baseline_result,args.baseline_commit,args.report_path)
