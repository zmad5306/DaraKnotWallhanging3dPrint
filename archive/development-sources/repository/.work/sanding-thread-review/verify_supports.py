exec((__import__('pathlib').Path(__file__).parent/'audit.py').read_text().split('results={}')[0])
import re,math
S=228.6/162.5
f=zipfile.ZipFile(ROOT/'.work/sanding-block/editable-validated.3mf')
r=E.fromstring(f.read('3D/3dmodel.model'))
printposes={int(i.get('objectid')):tf(i.get('transform')) for i in r.find(C+'build')}
offsets={}
for o in cfg.findall('object'):
 p={e.get('key'):e.get('value') for e in o.find('part').findall('metadata')}
 offsets[int(o.get('id'))]=np.array([float(p['source_offset_'+k]) for k in 'xyz'])
regions=[('top_female_in_base',2,top_axis,top_center,-14,0,6.3),
 ('top_male_screw',8,top_axis,top_center,-14,0,6.3),
 ('rear_female_nut',6,np.array([1.,0,0]),rear_center,-14.5,-4.5,7.3),
 ('rear_male_tensioner',4,np.array([1.,0,0]),rear_center,-17.5,-.5,7.3)]
allresults={}
for variant in ['r1','r2']:
 g=zipfile.ZipFile(W/(variant+'-slice/sliced.3mf')).read('Metadata/plate_1.gcode').decode()
 xyz=np.zeros(3);e=0.;rel_e=False;rel_xyz=False;feature='Custom';samples=[];width=.5;maxwidth=0
 for raw in g.splitlines():
  if raw.startswith('; FEATURE: '):feature=raw.split(': ',1)[1]
  if raw.startswith('; LINE_WIDTH: '):width=float(raw.split(': ',1)[1])
  line=raw.split(';',1)[0].strip()
  if not line:continue
  cmd=line.split()[0];v={k:float(n) for k,n in re.findall(r'([XYZIJE])(-?(?:\d+\.?\d*|\.\d+))',line)}
  if cmd=='M83':rel_e=True
  elif cmd=='M82':rel_e=False
  elif cmd=='G90':rel_xyz=False
  elif cmd=='G91':rel_xyz=True
  elif cmd=='G92':
   if 'E' in v:e=v['E']
   for i,k in enumerate('XYZ'):
    if k in v:xyz[i]=v[k]
  elif cmd in ['G0','G1','G2','G3']:
   dest=np.array([xyz[i]+v.get(k,0) if rel_xyz else v.get(k,xyz[i]) for i,k in enumerate('XYZ')])
   de=v.get('E',0) if rel_e else v.get('E',e)-e
   if de>0 and feature in ['Support','Support interface','Support transition'] and ('X' in v or 'Y' in v):
    maxwidth=max(maxwidth,width)
    if cmd in ['G2','G3'] and ('I' in v or 'J' in v):
     c=xyz[:2]+np.array([v.get('I',0),v.get('J',0)])
     rad=np.linalg.norm(xyz[:2]-c);a=math.atan2(xyz[1]-c[1],xyz[0]-c[0]);b=math.atan2(dest[1]-c[1],dest[0]-c[0])
     da=-((a-b)%(2*math.pi)) if cmd=='G2' else ((b-a)%(2*math.pi))
     n=max(2,int(math.ceil(abs(da)*rad/.2))+1);t=np.linspace(0,1,n)
     pts=np.c_[c[0]+rad*np.cos(a+da*t),c[1]+rad*np.sin(a+da*t),xyz[2]+(dest[2]-xyz[2])*t]
    else:
     n=max(2,int(math.ceil(np.linalg.norm(dest-xyz)/.2))+1)
     pts=xyz+(dest-xyz)*np.linspace(0,1,n)[:,None]
    samples.append(pts)
   xyz=dest;e=e+v.get('E',0) if rel_e else v.get('E',e)
 points=np.concatenate(samples)
 out={'support_sample_count':len(points),'sampling_step_mm':.2,'max_support_width_mm':maxwidth,'regions':{}}
 for name,oid,axis,center,lo,hi,radius in regions:
  t=printposes[oid];a=(points-t[:3,3])@np.linalg.inv(t[:3,:3]).T+offsets[oid]*S
  delta=a-center*S;axial=delta@axis;rad=np.linalg.norm(delta-axial[:,None]*axis,axis=1)
  pad=maxwidth/2+.11
  ok=(axial>lo*S-pad)&(axial<hi*S+pad)&(rad<radius*S+pad)
  out['regions'][name]={'samples_within_expanded_envelope':int(ok.sum()),'padding_mm':pad}
  print(variant,name,int(ok.sum()),flush=True)
  if np.any(ok):np.save(W/(variant+'-'+name+'-support.npy'),a[ok])
 allresults[variant]=out
(W/'r2-support-check.json').write_text(json.dumps(allresults,indent=2))
