exec((__import__('pathlib').Path(__file__).parent/'audit.py').read_text().split('results={}')[0])
import re,hashlib
S=228.6/162.5
saved=ROOT/'.work/sanding-block/editable-validated.3mf'
f=zipfile.ZipFile(saved)
r=E.fromstring(f.read('3D/3dmodel.model'))
printposes={int(i.get('objectid')):tf(i.get('transform')) for i in r.find(C+'build')}
offsets={}
for o in cfg.findall('object'):
 p={e.get('key'):e.get('value') for e in o.find('part').findall('metadata')}
 offsets[int(o.get('id'))]=np.array([float(p['source_offset_'+k]) for k in 'xyz'])
g=zipfile.ZipFile(ROOT/'.work/sanding-block/slice-clean/sliced.3mf').read('Metadata/plate_1.gcode').decode()
xyz=np.zeros(3);e=0.;rel_e=False;feature='Custom';samples=[]
for raw in g.splitlines():
 if raw.startswith('; FEATURE: '):feature=raw.split(': ',1)[1]
 line=raw.split(';',1)[0].strip()
 if not line:continue
 cmd=line.split()[0];v={k:float(n) for k,n in re.findall(r'([XYZE])(-?(?:\d+\.?\d*|\.\d+))',line)}
 if cmd=='M83':rel_e=True
 elif cmd=='M82':rel_e=False
 elif cmd=='G92':
  if 'E' in v:e=v['E']
 elif cmd in ['G0','G1','G2','G3']:
  dest=np.array([v.get(k,xyz[i]) for i,k in enumerate('XYZ')]);de=v.get('E',0) if rel_e else v.get('E',e)-e
  if de>0 and feature in ['Support','Support interface','Support transition'] and ('X' in v or 'Y' in v):
   samples.extend([(feature,pt.copy()) for pt in [xyz,(xyz+dest)/2,dest]])
  xyz=dest;e=e+v.get('E',0) if rel_e else v.get('E',e)
points=np.array([s[1] for s in samples]);kinds=np.array([s[0] for s in samples])
out={}
for name,oid,axis,center,lo,hi,radius in [
 ('top_female_in_base',2,top_axis,top_center,-14,0,6.3),
 ('top_male_screw',8,top_axis,top_center,-14,0,6.3),
 ('rear_female_nut',6,np.array([1.,0,0]),rear_center,-14.5,-4.5,7.3),
 ('rear_male_tensioner',4,np.array([1.,0,0]),rear_center,-17.5,-.5,7.3)]:
 t=printposes[oid];a=(points-t[:3,3])@np.linalg.inv(t[:3,:3]).T+offsets[oid]*S
 delta=a-center*S;axial=delta@axis;rad=np.linalg.norm(delta-axial[:,None]*axis,axis=1)
 ok=(axial>lo*S)&(axial<hi*S)&(rad<radius*S)
 counts={k:int(np.sum(ok&(kinds==k))) for k in np.unique(kinds)}
 out[name]=dict(support_samples_in_thread_envelope=counts,radial_max_mm=radius*S)
 print(name,counts,flush=True)
 np.save(W/(name+'-support-points.npy'),a[ok])
(W/'support-audit.json').write_text(json.dumps(out,indent=2))
# Radial slack in source CAD, with the two mating threads in a clear phase.
clearance={}
for name,male,female,axis,center,major in [
 ('rear',parts['Tighteneer'],rotate_about(parts['Nut'],202.5,[1,0,0],rear_center),np.array([1.,0,0]),rear_center,7),
 ('top',rotate_about(parts['Screw'],157.5,top_axis,top_center),parts['Base'],top_axis,top_center,6)]:
 vals=[]
 for d in [0,.025,.05,.075,.1,.125,.15,.175,.2,.25]:
  A=np.eye(3)+(d/major)*(np.eye(3)-np.outer(axis,axis));T=np.c_[A,center-A@center]
  vol=(male.transform(T)^female).volume();vals.append([d,vol])
 print(name,'radial expansion / interference',vals,flush=True)
 clearance[name]=vals
(W/'clearance-audit.json').write_text(json.dumps(clearance,indent=2))
