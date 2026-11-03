"""Retain the user's saved PLA project and block supports only at four threads."""
exec((__import__('pathlib').Path(__file__).parent/'audit.py').read_text().split('results={}')[0])
from development_3mf import mesh_xml
from build_jointed_bambu_project import model,xml,uid,meta,IDENTITY
import hashlib,re
P='{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}'
S=228.6/162.5
OUT=ROOT/'output/Sanding-Block-Quarter-Sheet-A1-PLA-r2'
OUT.mkdir(exist_ok=True)
SOURCE_R1=ROOT/'output/Sanding-Block-Quarter-Sheet-A1-PETG/Sanding-Block-Quarter-Sheet-A1-PETG-r1.3mf'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
protected={str(p):sha(p) for p in [ROOT/'Dara.3mf',SOURCE,SOURCE_R1]}
with zipfile.ZipFile(SOURCE_R1) as z:files={n:z.read(n) for n in z.namelist()}
settings=json.loads(files['Metadata/project_settings.config'])
assert settings['filament_type']==['PLA']
TITLE='Quarter sheet sanding block - A1 PLA - 8% gyroid - r2'
settings['print_settings_id']=TITLE
files['Metadata/project_settings.config']=json.dumps(settings,indent=2).encode()
r=E.fromstring(files['3D/3dmodel.model'])
c=E.fromstring(files['Metadata/model_settings.config'])
for k,v in [('Title',TITLE),('Description','Support correction r2. Same five printable meshes as r1; support-blocking paint on four threaded areas. PLA. Physical fit unverified.')]:
 el=r.find(f"{C}metadata[@name='{k}']")
 if el is None:el=E.SubElement(r,C+'metadata',name=k)
 el.text=v
resources=r.find(C+'resources');top={o.get('id'):o for o in resources}
build={i.get('objectid'):tf(i.get('transform')) for i in r.find(C+'build')}
oldrels=E.fromstring(files['3D/_rels/3dmodel.model.rels'])
rels=E.Element('Relationships',xmlns='http://schemas.openxmlformats.org/package/2006/relationships')
for link in oldrels:E.SubElement(rels,'Relationship',attrib=link.attrib)
oldzip=zipfile.ZipFile(ROOT/'.work/sanding-block/editable-validated.3mf')
oldroot=E.fromstring(oldzip.read('3D/3dmodel.model'))
oldposes={int(i.get('objectid')):tf(i.get('transform')) for i in oldroot.find(C+'build')}
offsets={}
origids={}
for o in cfg.findall('object'):
 p={m.get('key'):m.get('value') for m in o.find('part').findall('metadata')}
 name=p['name'].replace('.stl','');origids[name]=int(o.get('id'))
 offsets[name]=np.array([float(p['source_offset_'+a]) for a in 'xyz'])*S
ns={'__file__':str(ROOT/'.work/sanding-block/finalize.py')}
exec((ROOT/'.work/sanding-block/finalize.py').read_text().split('path=OUT/')[0],ns)
oldbed=ns['read_geometry'](ns['load'](ROOT/'.work/sanding-block/editable-validated.3mf'))
newbed=ns['read_geometry'](files)
specs={'Base':(top_axis,top_center,-14.5,.5,6.8),
       'Screw':(top_axis,top_center,-14.5,.5,6.8),
       'Nut':(np.array([1.,0,0]),rear_center,-15,-4,8),
       'Tighteneer':(np.array([1.,0,0]),rear_center,-18,.5,8)}
records=[]
for o in c.findall('object'):
 name=o.find('part/metadata[@key="name"]').get('value')
 if name not in specs:continue
 oid=o.get('id');bid=100+int(oid)
 axis,center,lo,hi,radius=specs[name]
 m=trimesh.creation.cylinder(radius=radius*S,height=(hi-lo)*S,sections=128)
 align=trimesh.geometry.align_vectors([0,0,1],axis)
 m.apply_transform(align);m.apply_translation(center*S+axis*(hi+lo)*S/2)
 # Assembly -> original part -> bed -> current object coordinates.
 m.apply_translation(-offsets[name]);m.apply_transform(oldposes[origids[name]])
 shift=newbed[name+' - quarter sheet'].bounds.mean(0)-oldbed[name+' - quarter sheet'].bounds.mean(0)
 m.apply_translation(shift)
 records.append(dict(part=name,axis=axis.tolist(),center_assembly_mm=(center*S).tolist(),
                     axial_bounds_mm=[lo*S,hi*S],radius_mm=radius*S,
                     bed_bounds_mm=m.bounds.tolist(),bed_shift_mm=shift.tolist()))
 # Native face painting avoids any additional printable or modifier volumes.
 bed=newbed[name+' - quarter sheet']
 pv=bed.triangles_center-shift
 oldt=oldposes[origids[name]]
 av=(pv-oldt[:3,3])@np.linalg.inv(oldt[:3,:3]).T+offsets[name]
 delta=av-center*S;axial=delta@axis
 radial=np.linalg.norm(delta-axial[:,None]*axis,axis=1)
 selected=(axial>=lo*S)&(axial<=hi*S)&(radial<=radius*S)
 comp=top[oid].find(C+'components/'+C+'component')
 path=comp.get(P+'path').lstrip('/')
 count=[0]
 def paint(match):
  i=count[0];count[0]+=1
  tag=match.group(0)
  if selected[i]:
   tag=re.sub(rb'\s+paint_supports="[^"]*"',b'',tag)
   tag=tag.replace(b'/>',b' paint_supports="8"/>')
  return tag
 files[path]=re.sub(rb'<triangle\s[^>]*?/>',paint,files[path])
 assert count[0]==len(selected)
 records[-1]['painted_triangles']=int(selected.sum())
for e in c.findall('plate/metadata'):
 if e.get('key')=='plater_name':e.set('value','r2 PLA - threads without supports')
files['3D/3dmodel.model']=xml(r);files['Metadata/model_settings.config']=xml(c)
files['3D/_rels/3dmodel.model.rels']=xml(rels)
for n in list(files):
 if n.endswith(('.gcode','.gcode.md5')) or n=='Metadata/slice_info.config':del files[n]
p=W/'r2-editable.3mf'
with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED) as z:
 for n,v in files.items():z.writestr(n,v)
report=dict(source_project=str(SOURCE_R1),source_sha256=sha(SOURCE_R1),
    editable_sha256=sha(p),protected_hashes=protected,blockers=records,
    changed_settings={'print_settings_id':TITLE},geometry_changes='None to printable parts',
    physical_fit_verified=False,reported_failure='Both threaded connections start, then bind in user PLA print. Exact printed artifact hash unconfirmed. Cause not physically established.')
(W/'r2-build.json').write_text(json.dumps(report,indent=2))
assert protected=={p:sha(Path(p)) for p in protected}
print('Built',p,flush=True)
print(json.dumps(records,indent=2),flush=True)
