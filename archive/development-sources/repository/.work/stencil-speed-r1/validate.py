from pathlib import Path
import zipfile,json,hashlib,re,collections,xml.etree.ElementTree as ET,sys,subprocess
root=Path.cwd();w=root/'.work/stencil-speed-r1';sys.path.insert(0,str(root/'scripts'))
from organize_root_projects import compare
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
changes={'initial_layer_infill_speed':[['105'],['50']],'internal_solid_infill_speed':[['250'],['80']],'top_surface_speed':[['200'],['80']]}
check=compare(w/'input.3mf',w/'native/sliced.3mf');assert not check['settings_changes']
def read(p):
 with zipfile.ZipFile(p) as z:return {n:z.read(n) for n in z.namelist()}
a=read(w/'before.3mf');edited=read(w/'input.3mf');native=read(w/'native/sliced.3mf')
# Keep all original geometry, object/volume overrides, poses and previews byte for byte.
final=dict(edited)
for n,data in native.items():
 if n.endswith('.gcode') or n.endswith('.gcode.md5') or n=='Metadata/slice_info.config':final[n]=data
cfg=lambda data:dict(re.findall(r'^; ([a-zA-Z0-9_]+) = (.*)$',data.decode(),re.M))
plates=[]
result=json.loads((w/'native/result.json').read_text());assert result['return_code']==0
assert [p['id'] for p in result['sliced_plates']]==list(range(1,7))
for i in range(1,7):
 n=f'Metadata/plate_{i}.gcode';g=final[n];old=cfg(a[n]);new=cfg(g)
 assert {k:[old.get(k),new.get(k)] for k in set(old)|set(new) if old.get(k)!=new.get(k)}=={k:[v[0][0],v[1][0]] for k,v in changes.items()}
 assert hashlib.md5(g).hexdigest()==final[n+'.md5'].decode().strip().lower()
 assert re.findall(r'^; Z_HEIGHT: (.*)$',g.decode(),re.M)==['0.2','0.4','0.6','0.8']
 feature='';layer=0;f=0;stats=collections.defaultdict(list)
 for l in g.decode().splitlines():
  if l.startswith('; Z_HEIGHT:'):layer+=1
  if l.startswith('; FEATURE:'):feature=l.split(': ',1)[1]
  if re.match(r'^G[123] ',l):
   v={k:float(x) for k,x in re.findall(r'([XYZEF])(-?[\d.]+)',l.split(';')[0])};f=v.get('F',f)
   if v.get('E',0)>0 and ('X' in v or 'Y' in v) and feature in ['Bottom surface','Internal solid infill','Top surface']:stats[(layer,feature)].append(f/60)
 assert set(stats)=={(1,'Bottom surface'),(2,'Internal solid infill'),(3,'Internal solid infill'),(4,'Top surface')}
 for (layer,feature),values in stats.items():assert all(abs(v-(50 if layer==1 else 80))<.001 for v in values)
 est=result['sliced_plates'][i-1];assert not est.get('warning_message')
 plates.append(dict(plate=i,gcode_sha256=hashlib.sha256(g).hexdigest(),estimated_seconds=est['total_predication'],material_g=sum(f['total_used_g'] for f in est['filaments']),verified_fill_speeds_mm_s={'first_layer':50,'internal_solid':80,'top_surface':80}))
info=ET.fromstring(final['Metadata/slice_info.config'])
warnings=[x.attrib for x in info.iter('warning')];assert all(x['msg']=='not_support_traditional_timelapse' for x in warnings)
for p in info.findall('plate'):assert next(m.get('value') for m in p.findall('metadata') if m.get('key')=='outside')=='false'
allowed={'Metadata/project_settings.config','Metadata/slice_info.config'}|{f'Metadata/plate_{i}.gcode{s}' for i in range(1,7) for s in ['','.md5']}
assert set(a)==set(final)
assert all(a[n]==final[n] for n in a if n not in allowed)
assert {k:[json.loads(a['Metadata/project_settings.config']).get(k),v] for k,v in json.loads(final['Metadata/project_settings.config']).items() if json.loads(a['Metadata/project_settings.config']).get(k)!=v}==changes
candidate=w/'candidate.3mf'
with zipfile.ZipFile(candidate,'w',zipfile.ZIP_DEFLATED) as z:
 for n,data in final.items():z.writestr(n,data)
reopen=w/'reopen';reopen.mkdir(exist_ok=True)
with (reopen/'log.txt').open('w') as log:
 p=subprocess.run([r'C:/Program Files/Bambu Studio/bambu-studio.exe','--info','--outputdir',str(reopen),str(candidate)],stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
assert p.returncode==0,p.returncode
assert json.loads((reopen/'result.json').read_text())['return_code']==0
protected=json.loads((w/'protected.json').read_text());assert all(sha(root/p)==v for p,v in protected.items())
report=dict(revision='stencil-speed-r1',date='2026-10-23',source_project='Small Parts - Crate Stencils.3mf',source_sha256=sha(w/'before.3mf'),project_sha256=sha(candidate),settings_changes=changes,native_comparison=check,geometry_and_object_settings_byte_identical=True,other_archive_entries_byte_identical=True,native_reopen_passed=True,plates=plates,slicer_warnings=warnings,protected_projects=protected,physical_status='Not printed. Speed-only trial after user reported continuous grinding and bed detachment with SUNLU bone-white PLA on A1. Cause not established.')
(w/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'candidate_sha256':sha(candidate),'total_seconds':sum(p['estimated_seconds'] for p in plates),'total_g':sum(p['material_g'] for p in plates),'plates':plates},indent=2))
