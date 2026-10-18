"""Keep short cosmetic crown seams and stagger broad structural core joints."""
import argparse,copy,json,math,zipfile
import xml.etree.ElementTree as ET
import numpy as np
from shapely import union_all
from shapely.geometry import Point,shape,mapping
import analyze_a2l_m_joints as study
import build_a2l_project as b
from development_3mf import ROOT,save_json,sha,write_project,centered,z_rotation,tag,P,R,props,transform
from build_jointed_bambu_project import xml

CFG=ROOT/'working/review/a2l-m-joints/staggered-layout.json'

def seam_checks(p):
 checks=[];lines=[shape(s['line']) for s in p['core_seams']];vlines=[shape(s['line']) for s in p['skin_seams']]
 for i,a in enumerate(lines):
  for q in lines[:i]:assert a.distance(q)>=18-1e-6
  u=np.array(a.coords[-1])-a.coords[0]
  for j,vline in enumerate(vlines):
   v=np.array(vline.coords[-1])-vline.coords[0]
   angle=math.degrees(math.acos(np.clip(abs(u@v)/np.linalg.norm(u)/np.linalg.norm(v),0,1)))
   assert a.intersection(vline).length<1e-6
   assert a.distance(vline)>=20
   checks.append(dict(core_joint=i+1,veneer_joint=j+1,aligned_length_mm=a.intersection(vline).length,
      distance_mm=a.distance(vline),angle_deg=angle,isolated_crossing=a.intersects(vline)))
 narrow=study.box(-235,140,-50,220).union(study.box(50,140,235,220))
 assert all(not q.intersects(narrow) for q in lines)
 # Each complete cosmetic seam has one continuous structural core behind it.
 assert all(any(shape(g).buffer(1e-6).covers(v) for g in p['core_footprints']) for v in vlines)
 for i,g in enumerate([shape(g) for g in p['core_footprints']]):
  for other in [shape(g) for g in p['core_footprints']][:i]:assert g.intersection(other).area<1e-6
 return checks,lines

def apply():
 c=json.loads(CFG.read_text());old=b.load_plan();p=copy.deepcopy(old)
 outline=study.planar.artwork(b.CAD.read_text(),'letter_outline')
 cp=study.partition(outline,[shape(g) for g in c['core_cuts']],5)
 # Veneer cuts cross only the narrow crowns, minimizing visible seam length.
 from shapely.ops import split
 vp=[outline]
 for cut in c['veneer_cuts']:vp=[g for q in vp for g in split(q,shape(cut)).geoms if g.area>1e-6]
 assert len(vp)==3 and union_all(vp).symmetric_difference(outline).area<1e-6
 # Preserve readable C1 upper-left, C2 upper-right, C3 stem, C4/C5 feet.
 upper=sorted([g for g in cp if g.bounds[3]>150],key=lambda g:g.centroid.x)
 stem=[g for g in cp if abs(g.centroid.x)<60 and g.bounds[3]<100]
 feet=sorted([g for g in cp if g.bounds[3]<0 and abs(g.centroid.x)>100],key=lambda g:g.centroid.x)
 assert len(upper)==len(feet)==2 and len(stem)==1
 cp=upper+stem+feet
 vp=sorted([g for g in vp if abs(g.centroid.x)>60],key=lambda g:g.centroid.x)+[g for g in vp if abs(g.centroid.x)<=60]
 assert len(vp)==3
 vs=union_all([l for _,_,l in study.planar.shared_seams(vp)])
 hardware=union_all([Point(r[2]).buffer(6) for r in p['screw_mounts']+p['dowel_mounts']])
 env,fit,keys=study.keyed_cores(cp,outline,minimum_head_wall=10,hardware_exclusion=hardware.union(vs.buffer(8)))
 p.update(core_regions=[mapping(g) for g in cp],core_footprints=[mapping(g) for g in env],core_fits=fit,
   core_seams=study.summary(cp,fit)['seams'],core_keys=[{k:v for k,v in q.items() if k!='keys'} for q in keys],
   skin_regions=[mapping(g) for g in vp],skin_seams=study.summary(vp,[study.veneer_allowance(g,np.array(p['veneer_rotation'])) for g in vp])['seams'],
   M_layout_revision=c['revision'],M_layout_specification_sha256=sha(CFG),core_plate_groups=[[1],[2],[3],[4,5]])
 for rows in [p['screw_mounts'],p['dowel_mounts']]:
  for row in rows:row[0]=b.owner(cp,row[2])
 # Retain every frame pin at its exact location; choose datums within each new
 # core. A one-pin foot is also located by its keyed core joint and veneer.
 locator_roles=[]
 for ci in range(5):
  rows=[r for r in p['dowel_mounts'] if r[0]==ci];assert rows
  for j,row in enumerate(rows):
   row[3]=0 if j==0 else 1
   if j:row[4]=math.degrees(math.atan2(row[2][1]-rows[0][2][1],row[2][0]-rows[0][2][0]))
   locator_roles.append(dict(core=ci+1,xy_mm=row[2],role='round datum' if j==0 else 'radial relief slot'))
 p['counts'].update(M_cores=5,M_core_joints=4,M_veneers=3,visible_M_seams=2)
 # Changes to core ownership or bore relief cannot change any frame geometry.
 for typ in ['screw_mounts','dowel_mounts']:
  assert [(r[1],r[2]) for r in old[typ]]==[(r[1],r[2]) for r in p[typ]]
 allowed={'core_regions','core_footprints','core_fits','core_seams','core_keys','skin_regions','skin_seams','M_layout_revision','M_layout_specification_sha256','core_plate_groups','counts','screw_mounts','dowel_mounts'}
 assert all(p[k]==v for k,v in old.items() if k not in allowed)
 checks,lines=seam_checks(p)
 previous=sha(b.PLAN);b.save(b.PLAN,p)
 # Frame meshes are retained exactly, with their cache binding moved to the
 # new plan only after the complete list of frame-affecting values is checked.
 for name in [f'F{i}{suffix}' for i in range(1,11) for suffix in ['', '-wood','-blue']]:
  path=b.WORK/(name+'.cache.json');proof=json.loads(path.read_text());assert proof['production_plan_sha256']==previous
  proof['production_plan_sha256']=sha(b.PLAN);b.save(path,proof)
 evidence=dict(revision=p['M_layout_revision'],previous_plan_sha256=previous,production_plan_sha256=sha(b.PLAN),
   frame_geometry_mount_coordinates_and_veneer_rotation_preserved=True,locator_roles=locator_roles,
   minimum_key_head_wall_mm=10,key_heads_clear_of_veneer_seams_mm=8,cross_layer_seam_checks=checks,minimum_core_joint_separation_mm=min(a.distance(q) for i,a in enumerate(lines) for q in lines[:i]),cores=5,core_plates=4,veneers=3,visible_veneer_seams=2,
   old_visible_seam_length_mm=sum(s['length_mm'] for s in old['skin_seams']),visible_seam_length_mm=vs.length,
   narrow_structural_arches_have_no_seams=True,minimum_cross_layer_seam_separation_mm=min(a.distance(v) for a in lines for v in [shape(s['line']) for s in p['skin_seams']]),physical_confirmation_pending=True)
 b.save(b.OUT/'M-joint-layout-validation.json',evidence)
 print('M plan: five cores on four plates, three veneers; short crown seams staggered from broad core joints',flush=True)


def core_plates(p):
 groups=p.get('core_plate_groups',[[i+1] for i in range(len(p['core_regions']))]);plates=[]
 for group in groups:
  entries=[]
  if len(group)==1:
   i=group[0]-1;m=b.cached(f'C{i+1}');f=p['core_fits'][i];yaw=f.get('rotation_deg',f.get('angle_deg'));poses=[centered(m,z_rotation(yaw),xy=(165,160))]
  else:
   assert group==[4,5]
   meshes=[b.cached(f'C{k}') for k in group];rot=z_rotation(90);dims=[np.ptp(m.vertices@rot.T,axis=0) for m in meshes]
   width=sum(d[0] for d in dims)+8;assert width<324 and max(d[1] for d in dims)<314
   x=(330-width)/2;poses=[]
   for m,d in zip(meshes,dims):poses.append(centered(m,rot,xy=(x+d[0]/2,160)));x+=d[0]+8
  for k,T in zip(group,poses):
   parts=[dict(mesh=b.cached(f'C{k}'))]+[b.reinforcement(xy) for ci,fi,xy in p['screw_mounts'] if ci==k-1]
   entries.append(dict(name=f'C{k} A2L flat M core',object_id=2000+(k-1)*100 if k<=4 else 9000,parts=parts,transform=T,
     settings=dict(extruder='3',enable_support='0',brim_width='1')))
  plates.append(entries)
 return plates


def package_M():
 p=b.load_plan();plates=core_plates(p)
 for i in range(3):plates.append([dict(name=f'V{i+1} A2L hammered veneer and sacrificial fins',object_id=2400+i*100,
   parts=[dict(mesh=b.cached(f'V{i+1}'))],transform=np.eye(4),block_front=True,front_normal=np.array(p['veneer_rotation'])[:,2],
   settings=dict(extruder='3',enable_support='1',sparse_infill_density='100%',brim_width='0',tree_support_branch_angle='30',support_critical_regions_only='0',outer_wall_speed='40',inner_wall_speed='80',default_acceleration='1500',travel_acceleration='2500'))])
 temp=b.WORK/'M-repartitioned.3mf';records=write_project(temp,plates,'Dara A2L M - short veneer seams, staggered cores',settings_update=b.settings())
 with zipfile.ZipFile(b.EDIT) as z:files={n:z.read(n) for n in z.namelist()}
 with zipfile.ZipFile(temp) as z:mf={n:z.read(n) for n in z.namelist()}
 root=ET.fromstring(files['3D/3dmodel.model']);cfg=ET.fromstring(files['Metadata/model_settings.config'])
 nr=ET.fromstring(mf['3D/3dmodel.model']);nc=ET.fromstring(mf['Metadata/model_settings.config']);resources=root.find(tag('resources'));build=root.find(tag('build'))
 oldplates=cfg.findall('plate');oids={props(inst)['object_id'] for pl in oldplates[10:17] for inst in pl.findall('model_instance')}
 for oid in oids:
  obj=resources.find(f"{tag('object')}[@id='{oid}']")
  for co in obj.find(tag('components')):files.pop(co.get('{'+P+'}path').lstrip('/'),None)
  resources.remove(obj);cfg.remove(cfg.find(f"object[@id='{oid}']"));build.remove(build.find(f"{tag('item')}[@objectid='{oid}']"))
 for obj in nr.find(tag('resources')):
  resources.append(copy.deepcopy(obj))
  for co in obj.find(tag('components')):
   path=co.get('{'+P+'}path').lstrip('/');files[path]=mf[path]
 for obj in nc.findall('object'):cfg.append(copy.deepcopy(obj))
 for item in nr.find(tag('build')):
  oid=item.get('objectid');rec=next(r for r in records if str(r['object_id'])==oid);a=rec['plate']-1;bpi=a+10
  T=transform(item.get('transform'));T[:2,3]+=np.array([bpi%5*396,-(bpi//5)*384])-np.array([a%3*396,-(a//3)*384]);item.set('transform',' '.join(format(float(v),'.12g') for v in T[:3].T.reshape(-1)));build.append(item)
 for old,new in zip(oldplates[10:17],nc.findall('plate')):
  pi=int(props(new)['plater_id'])+10
  for md in new.findall('metadata'):
   if md.get('key')=='plater_id':md.set('value',str(pi))
   if md.get('key')=='plater_name':md.set('value',f"{pi} - "+md.get('value').split(' - ',1)[1])
  pos=list(cfg).index(old);cfg.remove(old);cfg.insert(pos,copy.deepcopy(new))
 rels=ET.Element('Relationships',xmlns=R)
 for obj in resources:
  for co in obj.find(tag('components')):
   path=co.get('{'+P+'}path')
   if not any(r.get('Target')==path for r in rels):ET.SubElement(rels,'Relationship',Target=path,Id='rel-'+str(len(rels)+1),Type='http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel')
 files.update({'3D/3dmodel.model':xml(root),'Metadata/model_settings.config':xml(cfg),'3D/_rels/3dmodel.model.rels':xml(rels)})
 with zipfile.ZipFile(b.EDIT,'w',zipfile.ZIP_DEFLATED) as z:
  for name,data in files.items():z.writestr(name,data)
 planpath=b.OUT/'plate-plan.json';pp=json.loads(planpath.read_text());pp['records']=[r for r in pp['records'] if not 11<=r['plate']<=17]+[{**r,'plate':r['plate']+10} for r in records];pp['records'].sort(key=lambda r:r['plate']);pp.update(editable_sha256=sha(b.EDIT),production_plan_sha256=sha(b.PLAN));b.save(planpath,pp)
 print('Replaced only plates 11-17; every other mesh, setting and plate pose retained',flush=True)

def validate():
 p=b.load_plan();checks,lines=seam_checks(p);path=b.OUT/'M-joint-layout-validation.json';r=json.loads(path.read_text());r.update(cross_layer_seam_checks=checks,minimum_core_joint_separation_mm=min(a.distance(q) for i,a in enumerate(lines) for q in lines[:i]));b.save(path,r)
 print('Seam checks: core joints outside narrow arches, veneer/core seams >=20 mm apart, core joints >=18 mm apart',flush=True)

if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('action',choices=['plan','package','validate']);v=a.parse_args();{'plan':apply,'package':package_M,'validate':validate}[v.action]()
