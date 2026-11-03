from pathlib import Path
import json,hashlib,re,subprocess,zipfile,xml.etree.ElementTree as E
import numpy as np,trimesh
ROOT=Path(__file__).resolve().parents[2];W=Path(__file__).resolve().parent
ns={'__file__':str(ROOT/'.work/sanding-block/finalize.py')}
exec((ROOT/'.work/sanding-block/finalize.py').read_text().split('path=OUT/')[0],ns)
load,read_geometry,sha,tf=ns['load'],ns['read_geometry'],ns['sha'],ns['transform'];C,P=ns['C'],ns['P']
SOURCE=ROOT/'output/Sanding-Block-Quarter-Sheet-A1-PLA-r3/Sanding-Block-Quarter-Sheet-A1-PLA-r3.3mf'
TEST=ROOT/'output/Sanding-Block-Thread-Test-A1-PLA-t1/Sanding-Block-Thread-Test-A1-PLA-t1.3mf'
files=load(SOURCE);before=read_geometry(files);m=before['Lock - quarter sheet']
protected={str(p):sha(p) for p in [SOURCE,TEST,ROOT/'Dara.3mf']}
assert sha(SOURCE)=='64b547f906bd7afb818c3d0b7b1922f8e552fde7c868b1c3c1901025dd89014f'
facets=np.where((m.facets_area>300)&(m.facets_normal[:,2]<-.999))[0]
assert len(facets)==2
normal=np.average(m.facets_normal[facets],axis=0,weights=m.facets_area[facets]);normal/=np.linalg.norm(normal)
ids=np.unique(np.concatenate([m.faces[m.facets[i]].ravel() for i in facets]))
axis=np.cross(normal,[0,0,-1]);axis/=np.linalg.norm(axis)
rot=trimesh.transformations.rotation_matrix(np.arccos(-normal[2]),axis);center=m.bounds.mean(axis=0)
rot[:3,3]=center-rot[:3,:3]@center
rotated=m.copy();rotated.apply_transform(rot)
rot[2,3]-=rotated.bounds[0,2];rotated=m.copy();rotated.apply_transform(rot)
assert np.ptp(rotated.vertices[ids,2])<.002, (np.ptp(rotated.vertices[ids,2]),rotated.vertices[ids,2].min(),rotated.vertices[ids,2].max())
assert abs(rotated.vertices[ids,2].mean())<.001
cfg=E.fromstring(files['Metadata/model_settings.config'])
oid=next(o.get('id') for o in cfg.findall('object') if ns['props'](o)['name']=='Lock - quarter sheet')
root=E.fromstring(files['3D/3dmodel.model'])
item=next(e for e in root.find(C+'build') if e.get('objectid')==oid)
old_pose=tf(item.get('transform'));new_pose=rot@old_pose
new_transform=' '.join(f'{n:.12g}' for n in new_pose[:3,:].T.ravel())
# Replace only the Lock build transform in original text, keeping namespace declarations intact.
roottext=files['3D/3dmodel.model'].decode()
pattern=r'(<item\b[^>]*objectid="'+re.escape(oid)+r'"[^>]*transform=")[^"]*(")'
roottext,n=re.subn(pattern,lambda x:x[1]+new_transform+x[2],roottext);assert n==1
title='Quarter sheet sanding block - A1 PLA - 8% gyroid - r4'
for key,value in [('Title',title),('Description','Full quarter-sheet sanding block. Lock underside rotated flat to bed. Working t1 threads and support blocking unchanged. Orientation correction has native slice validation, not a physical print result.')]:
    roottext,n=re.subn(r'(<metadata name="'+key+r'">).*?(</metadata>)',lambda x:x[1]+value+x[2],roottext,flags=re.S);assert n==1
files['3D/3dmodel.model']=roottext.encode()
settings=json.loads(files['Metadata/project_settings.config']);settings['print_settings_id']=title
files['Metadata/project_settings.config']=json.dumps(settings,indent=2).encode()
cfg.find("plate/metadata[@key='plater_name']").set('value','r4 - Clamp flat on bed - t1 threads passed')
files['Metadata/model_settings.config']=E.tostring(cfg,encoding='utf-8',xml_declaration=True)
for name in list(files):
    if name.endswith(('.gcode','.gcode.md5')) or name=='Metadata/slice_info.config':del files[name]
after=read_geometry(files)
for name in before:
    if name!='Lock - quarter sheet':assert np.array_equal(before[name].vertices,after[name].vertices)
assert np.max(np.abs(after['Lock - quarter sheet'].vertices-rotated.vertices))<1e-7
report={'source_project':str(SOURCE),'source_sha256':sha(SOURCE),'protected_before':protected,
        'date':'2026-10-22','part':'Lock - quarter sheet','changed_variable':'Print orientation only: align existing flat underside with bed and seat at Z0. No mesh, dimension, fit, support paint or process setting changes.',
        'rotation_degrees':float(np.degrees(np.arccos(-normal[2]))),'old_pose':old_pose.tolist(),'new_pose':new_pose.tolist(),
        'world_delta_transform':rot.tolist(),'old_flat_face_z_range_mm':[float(m.vertices[ids,2].min()),float(m.vertices[ids,2].max())],
        'new_flat_face_z_range_mm':[float(rotated.vertices[ids,2].min()),float(rotated.vertices[ids,2].max())],
        'old_flat_face_normal':normal.tolist(),'flat_vertex_indices':ids.tolist(),
        'process_metadata_change':{'print_settings_id':title},
        'physical_thread_test':json.loads(SOURCE.with_name('thread-fit-result.json').read_text()),
        'reported_issue':'User reports first PLA print leading edge appeared melted/stringy above sound bed contact. Marked area corresponds to Lock leading bottom edge; printed file hash not independently read.',
        'new_orientation_physical_result':'Not yet printed.'}
editable=W/'r4-editable.3mf'
with zipfile.ZipFile(editable,'w',zipfile.ZIP_DEFLATED) as z:
    for name,value in files.items():z.writestr(name,value)
report['editable_sha256']=sha(editable)
(W/'r4-change.json').write_text(json.dumps(report,indent=2))
out=W/'r4-slice';out.mkdir(exist_ok=True)
exe=Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe')
with (W/'r4-slice.log').open('w',encoding='utf8') as f:
    result=subprocess.run([str(exe),'--slice','1','--export-3mf','sliced.3mf','--outputdir',str(out),str(editable)],cwd=exe.parent,stdout=f,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
assert result.returncode==0,result.returncode
sl=json.loads((out/'result.json').read_text());assert sl['return_code']==0
print(json.dumps({k:report[k] for k in ['rotation_degrees','old_flat_face_z_range_mm','new_flat_face_z_range_mm']},indent=2))
print(json.dumps({'seconds':sl['sliced_plates'][0]['total_predication'],'filaments':sl['sliced_plates'][0]['filaments'],'warnings':sl['sliced_plates'][0]['warning_message']},indent=2))
