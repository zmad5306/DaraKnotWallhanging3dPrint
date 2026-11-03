from pathlib import Path
import json,zipfile,xml.etree.ElementTree as E,copy,subprocess,shutil,math
E.register_namespace('','http://schemas.microsoft.com/3dmanufacturing/core/2015/02')
E.register_namespace('p','http://schemas.microsoft.com/3dmanufacturing/production/2015/06')
p=Path('outputs/Dara-Solid-Joint-Backs-v26').resolve();d=json.loads((p/'project-data.json').read_text());parts={r['part']+'.stl':r for r in d['parts']};w=Path('work/slicer').resolve();dest=w/'v26-separated-knot';dest.mkdir(exist_ok=True)
source=w/'v26-batch-01-Knot/01-Knot.3mf'
with zipfile.ZipFile(source) as z:entries={n:z.read(n) for n in z.namelist()}
config=E.fromstring(entries['Metadata/model_settings.config']);model=E.fromstring(entries['3D/3dmodel.model'])
names={o.get('id'):next(m.get('value') for m in o.findall('metadata') if m.get('key')=='name') for o in config.findall('object')}
instances={next(m.get('value') for m in i.findall('metadata') if m.get('key')=='object_id'):copy.deepcopy(i) for pl in config.findall('plate') for i in pl.findall('model_instance')}
for pl in config.findall('plate'):config.remove(pl)
items=model.findall('.//{*}build/{*}item');assert len(items)==28
for n,item in enumerate(items):
 oid=item.get('objectid');r=parts[names[oid]];x=(256-r['x_mm'])/2+(n%6)*307.2;y=(256-r['y_mm'])/2-(n//6)*307.2
 item.set('transform',f'1 0 0 0 1 0 0 0 1 {x} {y} 0')
 pl=E.SubElement(config,'plate')
 for k,v in [('plater_id',str(n+1)),('plater_name',r['part']),('locked','false'),('filament_map_mode','Auto For Flush')]:E.SubElement(pl,'metadata',key=k,value=v)
 pl.append(instances[oid])
entries['Metadata/model_settings.config']=E.tostring(config,encoding='utf-8',xml_declaration=True);entries['3D/3dmodel.model']=E.tostring(model,encoding='utf-8',xml_declaration=True)
f=dest/'arranged.3mf'
with zipfile.ZipFile(f,'w',zipfile.ZIP_DEFLATED) as z:
 for name,data in entries.items():
  if name.startswith('Metadata/plate_') or name.startswith('Metadata/top_') or name.startswith('Metadata/pick_'):continue
  z.writestr(name,data)
cmd=['C:/Program Files/Bambu Studio/bambu-studio.exe','--datadir',str(dest/'app-data'),'--load-settings',str(w/'machine.json')+';'+str(w/'process-v26.json'),'--load-filaments',str(w/'filament.json'),'--arrange','0','--orient','0','--slice','0','--export-3mf','01-Knot.3mf','--outputdir',str(dest),str(f)]
with (dest/'cli.log').open('w') as log:result=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=600,creationflags=0x08000000)
report=json.loads((dest/'result.json').read_text());count=sum(len(pl['objects']) for pl in report['sliced_plates']);report.update(project_name='01-Knot',expected_objects=28,actual_objects=count,success=report['return_code']==0 and count==28)
assert report['success'],report.get('error_string')
shutil.copy2(dest/'01-Knot.3mf',p/'Bambu-Studio/Grouped-Projects/01-Knot.3mf')
groups=json.loads((p/'grouped-project-validation.json').read_text());groups=[report if g['project_name']=='01-Knot' else g for g in groups];(p/'grouped-project-validation.json').write_text(json.dumps(groups,indent=2));print('Separated knot plates passed:',count)
