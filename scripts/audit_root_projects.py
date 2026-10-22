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
    tracked=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
    assert {p for p in tracked if p.lower().endswith('.3mf')}==expected, 'Tracked 3MF inventory differs from the root release.'
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
            assert len(cfg.findall('plate'))==len(info.findall('plate'))==row['plates']
            assert len(cfg.findall('object'))==len(row['objects'])
            resources={o.get('id') for o in model.find(C+'resources')}
            assert {i.get('objectid') for i in model.find(C+'build')}==resources
            for c in model.iter(C+'component'):assert c.get(P+'path').lstrip('/') in names
            for i,plate in enumerate(cfg.findall('plate'),1):
                assert props(plate)['plater_id']==str(i)
                for ins in plate.findall('model_instance'):assert props(ins)['object_id'] in resources
                for k,v in props(plate).items():
                    if k.endswith('_file') and v:assert v in names,(title,k,v)
                name=f'Metadata/plate_{i}.gcode';data=z.read(name)
                assert hashlib.md5(data).hexdigest().upper()==z.read(name+'.md5').decode().strip().upper()
                config=data.decode(errors='replace')
                for k in ['sparse_infill_density','sparse_infill_pattern','layer_height','wall_loops']:
                    assert re.search(r'^; '+k+r' = '+re.escape(locks[k])+r'\s*$',config,re.M),(title,i,k)
            for p in info.findall('plate'):
                for warning in p.findall('warning'):
                    assert warning.get('msg')=='not_support_traditional_timelapse', (title,warning.attrib)
        total+=row['plates']
        print(f'{title}: {row["plates"]} plates; project, CAD, STL, settings and G-code checks pass.')
    print(f'{len(catalog)} root projects / {total} sliced plates. Physical qualification remains as documented.')


if __name__=='__main__':audit()
