"""Promote the full r2 design after the user's successful t1 thread test."""
from pathlib import Path
import hashlib,json,zipfile,xml.etree.ElementTree as E,subprocess
ROOT=Path(__file__).resolve().parents[2];W=Path(__file__).resolve().parent
SOURCE=ROOT/'output/Sanding-Block-Quarter-Sheet-A1-PLA-r2/Sanding-Block-Quarter-Sheet-A1-PLA-r2.3mf'
TEST=ROOT/'output/Sanding-Block-Thread-Test-A1-PLA-t1/Sanding-Block-Thread-Test-A1-PLA-t1.3mf'
OUT=ROOT/'output/Sanding-Block-Quarter-Sheet-A1-PLA-r3';OUT.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
protected={str(p):sha(p) for p in [SOURCE,TEST,ROOT/'Dara.3mf']}
assert sha(SOURCE)=='7e3044f0cbbe86d1433af9828e127911246f36e0bb493922b7bf8f44ec9d4d31'
assert sha(TEST)=='62b7e140b8f00fa3c8da04b471b63b61aa12c8d88aa5733384dde2dd835547c6'
tr=json.loads(TEST.with_name('validation.json').read_text())
assert tr['source_sha256']==sha(SOURCE) and tr['project_sha256']==sha(TEST)
evidence=dict(date='2026-10-22',user_quote='Threads are good make the updates to the full project.',
 test_project=str(TEST),test_sha256=sha(TEST),result='User reports the thread test passed; both thread pairs accepted in context.',
 saved_printer='Bambu Lab A1',saved_material='Generic PLA @BBL A1',
 saved_settings_source=str(TEST.with_name('validation.json')),
 scope='Thread fit on supplied t1 crops. This is not a reported full-block print or paper-grip test.')
with zipfile.ZipFile(SOURCE) as z:files={n:z.read(n) for n in z.namelist()}
title='Quarter sheet sanding block - A1 PLA - 8% gyroid - r3'
s=json.loads(files['Metadata/project_settings.config']);s['print_settings_id']=title
files['Metadata/project_settings.config']=json.dumps(s,indent=2).encode()
# Change only descriptive metadata; retain all mesh/paint XML byte-for-byte.
root=files['3D/3dmodel.model'].decode()
import re
for key,value in [('Title',title),('Description','Full quarter-sheet sanding block. Same threads and support exclusion as t1, reported good by the user on 2026-10-22. Full-block print performance not yet reported.')]:
 pattern=rf'(<metadata name="{key}">).*?(</metadata>)'
 root,n=re.subn(pattern,lambda m:m[1]+value+m[2],root,flags=re.S);assert n==1
files['3D/3dmodel.model']=root.encode()
cfg=E.fromstring(files['Metadata/model_settings.config'])
cfg.find("plate/metadata[@key='plater_name']").set('value','r3 - Full block - t1 threads passed')
files['Metadata/model_settings.config']=E.tostring(cfg,encoding='utf-8',xml_declaration=True)
for n in list(files):
 if n.endswith(('.gcode','.gcode.md5')) or n=='Metadata/slice_info.config':del files[n]
files['Metadata/thread-fit-result.json']=json.dumps(evidence,indent=2).encode()
editable=W/'r3-editable.3mf'
with zipfile.ZipFile(editable,'w',zipfile.ZIP_DEFLATED) as z:
 for n,v in files.items():z.writestr(n,v)
record=dict(source_project=str(SOURCE),source_sha256=sha(SOURCE),test_project=str(TEST),test_sha256=sha(TEST),
 protected_before=protected,physical_thread_test=evidence,
 printable_geometry_changes='None: t1 was cropped directly from r2. Full geometry, positions and support paint retained.',
 settings_changes={'print_settings_id':title},editable_sha256=sha(editable))
(W/'promotion.json').write_text(json.dumps(record,indent=2))
out=W/'slice';out.mkdir(exist_ok=True)
exe=Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe')
with (W/'slice.log').open('w',encoding='utf8') as f:
 result=subprocess.run([str(exe),'--slice','1','--export-3mf','sliced.3mf','--outputdir',str(out),str(editable)],
  cwd=exe.parent,stdout=f,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
assert result.returncode==0, result.returncode
sl=json.loads((out/'result.json').read_text());assert sl['return_code']==0
print(json.dumps({'return_code':sl['return_code'],'seconds':sl['sliced_plates'][0]['total_predication'],
 'filaments':sl['sliced_plates'][0]['filaments'],'warnings':sl['sliced_plates'][0]['warning_message']},indent=2))
