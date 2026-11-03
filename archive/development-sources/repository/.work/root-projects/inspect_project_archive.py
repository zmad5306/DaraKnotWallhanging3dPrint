import json,zipfile,xml.etree.ElementTree as E
from pathlib import Path
ps=json.loads(Path('.work/root-projects/sources.json').read_text())
for key in ['Letter','Small Parts','Center','Crate','Photo']:
 with zipfile.ZipFile(ps[key]) as z:
  print('\n',key)
  c=E.fromstring(z.read('Metadata/model_settings.config'))
  print(E.tostring(c.findall('plate')[0],encoding='unicode')[:2200])
  print('top tags', [x.tag for x in c])
  print('assets', [n for n in z.namelist() if not n.startswith('3D/')][:45])
  if key=='Letter':
   print('slice',z.read('Metadata/slice_info.config')[:2400])
   print('seq',z.read('Metadata/filament_sequence.json')[:600])
  if key in ['Photo','Crate']:
   print('objects',[(o.get('id'),[(m.get('key'),m.get('value')) for m in o.findall('metadata') if m.get('key') in ['name','extruder']]) for o in c.findall('object')])
   print('size',Path(ps[key]).stat().st_size)
