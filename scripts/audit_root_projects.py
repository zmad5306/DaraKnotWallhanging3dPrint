"""Read-only release audit, requiring only Python's standard library.

Hashes tie the deeper mesh/pose checks to the distributed projects, CAD and STL.
This does not slice or send anything to a printer.
"""
import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
C = '{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}'
P = '{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}'


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()


def props(node):
    return {m.get('key'):m.get('value') for m in node.findall('metadata')}


def audit():
    catalog=json.loads((ROOT/'release/root-projects/catalog.json').read_text())
    expected={v['project'] for v in catalog.values()}
    sample_catalog=ROOT/'release/samples/catalog.json'
    samples=json.loads(sample_catalog.read_text()) if sample_catalog.exists() else {}
    expected_tracked=expected|{v['file'] for v in samples.values()}
    tracked=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
    assert {p for p in tracked if p.lower().endswith('.3mf')}==expected_tracked, 'Tracked 3MF inventory differs from the declared releases/samples.'
    for sample in samples.values():
        assert sha(ROOT/sample['file'])==sample['sha256']
        assert (ROOT/sample['validation']).is_file()
    assert {p.name for p in ROOT.glob('*.3mf')}==expected, 'Unexpected root 3MF.'
    total=0
    for title,row in catalog.items():
        path=ROOT/row['project'];assert sha(path)==row['sha256'],path
        assert sha(ROOT/row['cad'])==row['cad_sha256'],row['cad']
        for obj in row['objects']:
            for part in obj['parts']:assert sha(ROOT/part['file'])==part['sha256'],part['file']
        with zipfile.ZipFile(path) as z:
            assert z.testzip() is None
            names=set(z.namelist());s=json.loads(z.read('Metadata/project_settings.config'))
            cfg=ET.fromstring(z.read('Metadata/model_settings.config'));info=ET.fromstring(z.read('Metadata/slice_info.config'))
            model=ET.fromstring(z.read('3D/3dmodel.model'))
            assert s['printer_model']==row['printer']
            stencil='Stencils' in title
            locks=dict(sparse_infill_density='0%' if stencil else '8%',sparse_infill_pattern='gyroid',
                       nozzle_diameter=['0.4'],layer_height='0.2',initial_layer_print_height='0.2',
                       wall_loops='2' if stencil else '4',top_shell_layers='4' if stencil else '5',
                       bottom_shell_layers='4' if stencil else '5',curr_bed_type='Textured PEI Plate')
            for k,v in locks.items():assert s[k]==v,(title,k,s[k],v)
            if title in ['Knot','Letter']:assert s['is_infill_first']==('1' if title=='Knot' else '0')
            sliced=row.get('sliced',True)
            assert len(cfg.findall('plate'))==row['plates']
            assert len(info.findall('plate'))==(row['plates'] if sliced else 0)
            if not sliced:assert not any(n.endswith('.gcode') for n in names)
            assert len(cfg.findall('object'))==len(row['objects'])
            resources={o.get('id') for o in model.find(C+'resources')}
            assert {i.get('objectid') for i in model.find(C+'build')}==resources
            for c in model.iter(C+'component'):assert c.get(P+'path').lstrip('/') in names
            if title=='Knot':
                skin=json.loads((ROOT/row['validation']).read_text())
                assert skin['project_sha256']==row['sha256']
                if skin.get('white_show_face_pattern')=='hilbertcurve':
                    assert skin['brown_blue_joint_and_pin_toolpath_geometry_preserved']
                    assert skin['screw_modifiers_preserved_at_z12_4']
                    ranges=ET.fromstring(z.read('Metadata/layer_config_ranges.xml'))
                    assert len(ranges.findall('object'))==10
                    for obj in ranges.findall('object'):
                        rr=obj.findall('range');assert len(rr)==1
                        assert (float(rr[0].get('min_z')),float(rr[0].get('max_z')))==(13,13.6)
                        assert {o.get('opt_key'):o.text for o in rr[0].findall('option')}=={
                            'layer_height':'0.2','extruder':'0','top_surface_pattern':'hilbertcurve'}
                    for obj in cfg.findall('object'):
                        for part in obj.findall('part'):
                            if props(part).get('extruder')=='4':assert props(part)['top_surface_pattern']=='monotonicline'
                            if props(part).get('extruder')=='2':assert 'top_surface_pattern' not in props(part)
                else:
                    assert skin['all_five_top_shell_layers_cross_former_modifier_boundary']
                    assert s['top_surface_pattern']=='monotonicline'
                    assert 'Metadata/layer_config_ranges.xml' not in names
                    assert all(m.get('value')!='hilbertcurve' for m in cfg.iter('metadata'))
                objects={o.get('id'):o for o in model.find(C+'resources')}
                assets={};count=0;blue_count=0
                for obj in cfg.findall('object'):
                    components={c.get('objectid'):c for c in objects[obj.get('id')].find(C+'components')}
                    for part in obj.findall('part'):
                        blue=skin.get('blue_layer_count')==5 and props(part).get('extruder')=='4'
                        reinforcement=props(part).get('name')=='Local solid screw reinforcement'
                        if not (blue or reinforcement):continue
                        assert part.get('subtype')=='modifier_part'
                        if reinforcement:assert props(part)['sparse_infill_density']=='100%'
                        co=components[part.get('id')];asset=co.get(P+'path').lstrip('/')
                        if asset not in assets:assets[asset]=ET.fromstring(z.read(asset))
                        mesh=assets[asset].find(C+'resources').find(f"{C}object[@id='{part.get('id')}']").find(C+'mesh')
                        t=list(map(float,co.get('transform').split()))
                        assert t[:9]==[1,0,0,0,1,0,0,0,1]
                        heights=[float(v.get('z'))+t[11] for v in mesh.find(C+'vertices')]
                        if blue:
                            assert abs(min(heights)-12.5)<1e-6 and abs(max(heights)-13.5)<1e-6
                            blue_count+=1
                        else:
                            assert abs(min(heights))<1e-6 and abs(max(heights)-12.4)<1e-6
                            count+=1
                assert count==skin['modifier_count']==50
                if skin.get('blue_layer_count')==5:assert blue_count==skin['blue_modifier_count']==10
            for i,plate in enumerate(cfg.findall('plate'),1):
                assert props(plate)['plater_id']==str(i)
                for ins in plate.findall('model_instance'):assert props(ins)['object_id'] in resources
                for k,v in props(plate).items():
                    if k.endswith('_file') and v:assert v in names,(title,k,v)
                if not sliced:continue
                name=f'Metadata/plate_{i}.gcode';data=z.read(name)
                if title=='Knot':
                    expected=next(p for p in skin['plates'] if p['plate']==i)
                    assert hashlib.sha256(data).hexdigest()==expected['gcode_sha256']
                    if skin.get('blue_layer_count')==5:
                        assert expected['model_z_by_filament_mm']['4']==[12.8,13.0,13.2,13.4,13.6]
                assert hashlib.md5(data).hexdigest().upper()==z.read(name+'.md5').decode().strip().upper()
                config=data.decode(errors='replace')
                for k in ['sparse_infill_density','sparse_infill_pattern','layer_height','wall_loops']:
                    assert re.search(r'^; '+k+r' = '+re.escape(locks[k])+r'\s*$',config,re.M),(title,i,k)
            for p in info.findall('plate'):
                for warning in p.findall('warning'):
                    assert warning.get('msg')=='not_support_traditional_timelapse', (title,warning.attrib)
        total+=row['plates']
        print(f'{title}: {row["plates"]} plates; project, CAD, STL and settings checks pass; '+('G-code checks pass.' if sliced else 'unsliced, slicing required.'))
    print(f'{len(catalog)} root projects / {total} plates. Slice availability and physical qualification remain as documented.')


if __name__=='__main__':audit()
