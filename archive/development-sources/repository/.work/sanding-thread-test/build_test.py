"""Quick four-piece thread test cropped from the saved r2 sanding project."""
from pathlib import Path
import json,sys,hashlib,zipfile,xml.etree.ElementTree as E
import numpy as np
import trimesh
import manifold3d as mf
ROOT=Path(__file__).resolve().parents[2];W=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'scripts'))
from build_jointed_bambu_project import model,xml,meta,uid,IDENTITY
from development_3mf import mesh_xml,solid
C='{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}'
P='{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}'
R='http://schemas.openxmlformats.org/package/2006/relationships'
SOURCE=ROOT/'output/Sanding-Block-Quarter-Sheet-A1-PLA-r2/Sanding-Block-Quarter-Sheet-A1-PLA-r2.3mf'
OUT=ROOT/'output/Sanding-Block-Thread-Test-A1-PLA-t1';OUT.mkdir(exist_ok=True)
TITLE='Sanding block thread test t1 - r2 geometry - A1 PLA - 8% gyroid'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
protected={str(p):sha(p) for p in [SOURCE,ROOT/'Dara.3mf']}
assert protected[str(SOURCE)]=='7e3044f0cbbe86d1433af9828e127911246f36e0bb493922b7bf8f44ec9d4d31'
with zipfile.ZipFile(SOURCE) as z:src={n:z.read(n) for n in z.namelist()}
settings=json.loads(src['Metadata/project_settings.config']);settings['print_settings_id']=TITLE
def tf(s):
 t=np.eye(4)
 if s:t[:3]=np.array(list(map(float,s.split()))).reshape(4,3).T
 return t
root=E.fromstring(src['3D/3dmodel.model']);cfg=E.fromstring(src['Metadata/model_settings.config'])
sourceobjs={o.get('id'):o for o in root.find(C+'resources')}
poses={i.get('objectid'):tf(i.get('transform')) for i in root.find(C+'build')}
objects={}
for o in cfg.findall('object'):
 name=o.find('part/metadata[@key="name"]').get('value')
 if name=='Lock':continue
 oid=o.get('id');comp=sourceobjs[oid].find(C+'components/'+C+'component')
 child=E.fromstring(src[comp.get(P+'path').lstrip('/')])
 ob=child.find(f"{C}resources/{C}object[@id='{comp.get('objectid')}']")
 vs=np.array([[float(v.get(k)) for k in 'xyz'] for v in ob.find(C+'mesh/'+C+'vertices')])
 triangles=list(ob.find(C+'mesh/'+C+'triangles'))
 fs=np.array([[int(f.get(k)) for k in ['v1','v2','v3']] for f in triangles])
 paint=np.array([f.get('paint_supports','') for f in triangles])
 t=poses[oid]@tf(comp.get('transform'));vs=vs@t[:3,:3].T+t[:3,3]
 objects[name]=(trimesh.Trimesh(vs,fs,process=False),paint,o,oid)
# Crop in the SOURCE PLATE coordinate frame. Lower unthreaded stock is
# removed in whole 0.2 mm layer increments, then seated on the bed.
crops={'Base':[[58.5,59,4],[81.5,90,35]],
       'Tighteneer':[[58.6,142,6],[81.4,184,45]],
       'Screw':[[180,45,8.4],[220,85,40]]}
layout={'Base':[104,104],'Screw':[150,104],'Tighteneer':[104,152],'Nut':[150,152]}
names={'Base':'1A - Top threaded socket','Screw':'1B - Top screw',
       'Tighteneer':'2A - Rear threaded shaft','Nut':'2B - Rear thumbwheel nut'}
records=[];testmeshes={};testpaint={}
for name,(m,paint,config,oid) in objects.items():
 old=m.copy();orig=solid(old)
 crop=crops.get(name)
 if crop:
  v,inv=np.unique(m.vertices,axis=0,return_inverse=True);f=inv[m.faces]
  valid=(f[:,0]!=f[:,1])&(f[:,1]!=f[:,2])&(f[:,0]!=f[:,2]);faceids=np.flatnonzero(valid)
  mid=mf.Manifold.reserve_ids(1)
  raw=mf.Mesh64(v,f[valid].astype(np.uint64),run_index=np.array([0,3*len(faceids)],np.uint64),
    run_original_id=np.array([mid],np.uint32),face_id=faceids.astype(np.uint64))
  original=mf.Manifold(raw);assert original.status()==mf.Error.NoError
  lo,hi=np.array(crop);box=mf.Manifold.cube(tuple(hi-lo)).translate(tuple(lo))
  clipped=original^box
  assert clipped.status()==mf.Error.NoError and len(clipped.decompose())==1
  raw=clipped.to_mesh64();parents=np.arange(len(raw.vert_properties))
  def find(i):
   while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
   return i
  for a,b in zip(raw.merge_from_vert,raw.merge_to_vert):parents[find(int(a))]=find(int(b))
  ids=np.array([find(i) for i in range(len(parents))]);used,idx=np.unique(ids,return_inverse=True)
  f=idx[raw.tri_verts];valid=(f[:,0]!=f[:,1])&(f[:,1]!=f[:,2])&(f[:,0]!=f[:,2])
  copied=np.zeros(len(f),dtype=bool)
  for a,b,i in zip(raw.run_index[:-1],raw.run_index[1:],raw.run_original_id):
   if i==mid:copied[int(a)//3:int(b)//3]=True
  annotations=np.full(len(f),'',dtype='<U16');faceids=np.asarray(raw.face_id)
  annotations[copied]=paint[faceids[copied]]
  m=trimesh.Trimesh(raw.vert_properties[used,:3],f[valid],process=False);paint=annotations[valid]
  assert m.is_volume
  crop_error=((solid(m)-(orig^box)).volume() + ((orig^box)-solid(m)).volume())
  assert abs(crop_error)<1e-5
 else:crop_error=0.
 # Retain the complete padded thread envelope. Some large coplanar painted
 # body faces extend outside it; clipping those retains their paint via face ID.
 original_paint=objects[name][1]
 if crop:
  source_validation=json.loads(SOURCE.with_name('validation.json').read_text())
  region=next(x for x in source_validation['blockers'] if x['part']==name)
  assert np.all(np.array(region['bed_bounds_mm'][0])>=np.array(crop[0]))
  assert np.all(np.array(region['bed_bounds_mm'][1])<=np.array(crop[1]))
 shift=np.r_[np.array(layout[name])-m.bounds.mean(0)[:2],-max(0.,m.bounds[0,2])]
 m.apply_translation(shift)
 assert m.is_volume and abs(m.bounds[0,2])<1e-4
 assert m.section(plane_origin=[0,0,.1],plane_normal=[0,0,1]) is not None
 testmeshes[name]=m;testpaint[name]=paint
 records.append(dict(source_part=name,name=names[name],source_object_id=oid,
  source_crop_bounds_mm=crop,source_to_test_translation_mm=shift.tolist(),
  crop_symmetric_difference_mm3=crop_error,watertight=bool(m.is_volume),
  source_thread_paint_faces=int(np.sum(original_paint=='8')),test_thread_paint_faces=int(np.sum(paint=='8')),
  size_mm=m.extents.tolist(),bounds_mm=m.bounds.tolist(),volume_mm3=m.volume))
 print(name,records[-1],flush=True)
 m.export(W/(name+'-test.stl'))
files={'[Content_Types].xml':src['[Content_Types].xml'],'_rels/.rels':src['_rels/.rels'],
 'Metadata/project_settings.config':json.dumps(settings,indent=2).encode()}
root=model();del root.attrib['xmlns:p']
for k,v in [('Application','BambuStudio-02.08.02.61'),('BambuStudio:3mfVersion','1'),('Title',TITLE),
 ('Designer','DeepDiverDude; personal size adaptation and thread crop'),('License','Standard Digital File License'),
 ('Description','Four-piece test cropped from quarter-sheet r2. Thread geometry and orientations unchanged. Physical fit unverified.')]:
 E.SubElement(root,C+'metadata',name=k).text=v
res=E.SubElement(root,C+'resources');build=E.SubElement(root,C+'build',attrib={P+'UUID':uid()})
cfg=E.Element('config');rels=E.Element('Relationships',xmlns=R)
plate=E.SubElement(cfg,'plate')
for k,v in [('plater_id','1'),('plater_name','t1 - Both thread pairs - r2 geometry'),('locked','false'),('filament_maps','1'),('filament_volume_maps','0')]:meta(plate,k,v)
for j,name in enumerate(['Base','Screw','Tighteneer','Nut']):
 oid=2*j+2;pid=oid-1;m=testmeshes[name]
 child=model();cr=E.SubElement(child,C+'resources');mesh_xml(cr,pid,m)
 tris=child.find(C+'resources/'+C+'object/'+C+'mesh/'+C+'triangles')
 for t,p in zip(tris,testpaint[name]):
  if p:t.set('paint_supports',p)
 path=f'3D/Objects/{name}.model';files[path]=xml(child)
 top=E.SubElement(res,C+'object',id=str(oid),type='model',attrib={P+'UUID':uid()})
 comps=E.SubElement(top,C+'components')
 E.SubElement(comps,C+'component',objectid=str(pid),transform=IDENTITY,attrib={P+'path':'/'+path,P+'UUID':uid()})
 E.SubElement(rels,'Relationship',Target='/'+path,Id=f'rel-{oid}',Type='http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel')
 co=E.SubElement(cfg,'object',id=str(oid));meta(co,'name',names[name]);meta(co,'extruder','1')
 part=E.SubElement(co,'part',id=str(pid),subtype='normal_part');meta(part,'name',name);meta(part,'extruder','1')
 sourceconfig=objects[name][2]
 # Preserve all effective object and volume overrides, excluding source bookkeeping.
 for old,new in [(sourceconfig,co),(sourceconfig.find('part'),part)]:
  for el in old.findall('metadata'):
   k=el.get('key')
   if k in settings and k not in ('name','extruder'):meta(new,k,el.get('value'))
 E.SubElement(part,'mesh_stat',face_count=str(len(m.faces)),edges_fixed='0',degenerate_facets='0',facets_removed='0',facets_reversed='0',backwards_edges='0')
 E.SubElement(build,C+'item',objectid=str(oid),transform=IDENTITY,printable='1',attrib={P+'UUID':uid()})
 ins=E.SubElement(plate,'model_instance')
 for k,v in [('object_id',oid),('instance_id',0),('identify_id',oid)]:meta(ins,k,v)
files['3D/3dmodel.model']=xml(root);files['Metadata/model_settings.config']=xml(cfg);files['3D/_rels/3dmodel.model.rels']=xml(rels)
p=W/'test-editable.3mf'
with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED) as z:
 for n,v in files.items():z.writestr(n,v)
report=dict(source=str(SOURCE),source_sha256=sha(SOURCE),editable_sha256=sha(p),protected_before=protected,
 test_revision='t1',thread_design_revision='r2',parts=records,
 changed_variable='Same r2 threads and support blocking; crop away unrelated body stock for a smaller fit test.',
 print_orientation='Source bed orientation preserved; XY arrangement and whole-layer Z translations seat the crops on the bed.',
 settings_changes={'print_settings_id':TITLE},physical_fit_verified=False)
assert protected=={p:sha(Path(p)) for p in protected}
(W/'build.json').write_text(json.dumps(report,indent=2))
print('Built',p,flush=True)
