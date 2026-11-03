"""Isolate veneer plates for project-level acceleration correction and native audit."""
import sys,json,re,copy,subprocess
from pathlib import Path
import xml.etree.ElementTree as ET
sys.path[:0]=['.work/python-libs','scripts']
import numpy as np
import organize_root_projects as org
from development_3mf import sha
WORK=Path.cwd()/'.work/veneer-face-r9';source=WORK/'Letter-edge-candidate.3mf'
files=org.read(source);cfg=ET.fromstring(files['Metadata/model_settings.config']);model=ET.fromstring(files['3D/3dmodel.model']);settings=json.loads(files['Metadata/project_settings.config'])
plates=cfg.findall('plate');retained=plates[3:6];mapping={4:1,5:2,6:3}
ids={org.props(ins)['object_id']:i for i,p in enumerate(retained) for ins in p.findall('model_instance')}
assets=set();resources=model.find(org.tag('resources'))
for obj in list(resources):
 if obj.get('id') not in ids:resources.remove(obj)
 else:assets.update(c.get('{'+org.P+'}path').lstrip('/') for c in obj.find(org.tag('components')))
for obj in cfg.findall('object'):
 if obj.get('id') not in ids:cfg.remove(obj)
for p in plates:
 if p not in retained:cfg.remove(p)
for i,p in enumerate(retained):
 org.setmeta(p,'plater_id',i+1);org.setmeta(p,'plater_name',f'{i+1} - V{i+1} carrier edge and acceleration correction r9')
 for md in list(p.findall('metadata')):
  if md.get('key') in ['gcode_file','thumbnail_file','thumbnail_no_light_file','top_file','pick_file']:p.remove(md)
for it in list(model.find(org.tag('build'))):
 oid=it.get('objectid')
 if oid not in ids:model.find(org.tag('build')).remove(it)
 else:
  i=ids[oid];t=org.transform(it.get('transform'));t[:2,3]+=org.grid(i,3,org.pitch(settings))-org.grid(i+3,6,org.pitch(settings));it.set('transform',org.matrix_text(t))
assembly=cfg.find('assemble')
if assembly is not None:
 for it in list(assembly):
  if it.get('object_id') not in ids:assembly.remove(it)
  elif it.get('instance_id') is not None:
   i=ids[it.get('object_id')];t=org.transform(it.get('transform'));t[:2,3]+=org.grid(i,3,org.pitch(settings))-org.grid(i+3,6,org.pitch(settings));it.set('transform',org.matrix_text(t))
for n in list(files):
 if (n.startswith('3D/Objects/') and n not in assets) or org.ASSET.fullmatch(n) or n in ['Metadata/slice_info.config','Metadata/filament_sequence.json','Metadata/cut_information.xml']:del files[n]
for k in ('wipe_tower_x','wipe_tower_y'):settings[k]=settings[k][3:6]
# Apply the existing intended object values where Studio actually uses them.
# Explicit feature accelerations must also obey the 1500 printing limit.
changed={}
for k,v in dict(default_acceleration=['1500'],outer_wall_acceleration=['1500'],top_surface_acceleration=['1500'],travel_acceleration=['2500'],initial_layer_travel_acceleration=['2500']).items():
 changed[k]=[settings[k],v];settings[k]=v
files['Metadata/project_settings.config']=json.dumps(settings,indent=2).encode();files['Metadata/model_settings.config']=org.xml(cfg);files['3D/3dmodel.model']=org.xml(model)
org.clean_relations(files);dest=WORK/'Letter-veneers-r9-editable.3mf';org.write(dest,files)
(WORK/'candidate-settings.json').write_text(json.dumps(dict(source_sha256=sha(source),candidate_sha256=sha(dest),plate_mapping=mapping,changed_settings=changed),indent=2))
print('prepared',dest,flush=True)
out=WORK/'native-veneers-r9';out.mkdir(exist_ok=True);exe=Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe')
attempts=[]
for attempt in range(3):
 with (out/f'slice-{attempt+1}.log').open('w') as log:
  p=subprocess.run([str(exe),'--slice','0','--export-3mf','sliced.3mf','--outputdir',str(out),str(dest)],cwd=exe.parent,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
 attempts.append(p.returncode)
 if p.returncode==0:break
(out/'process-exits.json').write_text(json.dumps(attempts));print('exits',attempts,flush=True)
assert p.returncode==0
print((out/'result.json').read_text(),flush=True)
