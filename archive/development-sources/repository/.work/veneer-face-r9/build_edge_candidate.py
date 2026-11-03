"""Remove three inherited 0.15 mm carrier-outline jogs; no process edits."""
import sys,json,shutil,copy,zipfile,hashlib
from pathlib import Path
import xml.etree.ElementTree as ET
sys.path[:0]=['.work/python-libs','scripts']
import numpy as np,trimesh,manifold3d as mf
from shapely.geometry import shape,Polygon
from shapely.geometry.polygon import orient
from development_3mf import solid,mesh,sha,xml,tag,transform
from promote_veneer_wall_cradle import read,write
from validate_production_split import Project
ROOT=Path.cwd();WORK=ROOT/'.work/veneer-face-r9'
source=ROOT/'Letter.3mf';baseline=WORK/'Letter-before.3mf'
if not baseline.exists():shutil.copyfile(source,baseline)
assert sha(source)==sha(baseline)=='8e391762ecb8415b77680a7bd4825e94afe37951d831bcfe41f6a43f31b16d4a'
p=Project(source);files=read(source);cfg=ET.fromstring(files['Metadata/model_settings.config']);model=ET.fromstring(files['3D/3dmodel.model']);records=[]
P='{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}'
for i in (1,2,3):
 name=next(n for n in p.rows if n.startswith(f'V{i} '));r=p.rows[name];d=np.load(WORK/f'V{i}-mesh.npz');pose=d['pose']
 footprint=shape(json.loads((WORK/f'V{i}-panel-footprint.json').read_text()));xy=np.array(footprint.exterior.coords)
 # Only local convex-hull deficits on the straight extremal side edges.
 if i==1:
  changes=[footprint.convex_hull.difference(footprint)]
 elif i==3:
  changes=[]
  for sign in (-1,1):
   side=xy[sign*xy[:,0]>125.3];ys=np.sort(np.unique(side[:,1]))
   narrow=side[abs(side[:,0]-sign*125.4)<.01];wide=side[abs(side[:,0]-sign*125.55)<.01]
   a=narrow[np.argmin(narrow[:,1])];b=narrow[np.argmax(narrow[:,1])];c=wide[np.argmin(abs(wide[:,1]-b[1]))]
   changes.append(Polygon([a,b,c]).difference(footprint))
 else:
  records.append(dict(veneer=i,plate=5,changed=False,reason='No corresponding carrier side-edge jog; geometry retained byte-for-byte.'));continue
 changes=[p for q in changes for p in (list(q.geoms) if hasattr(q,'geoms') else [q]) if p.area>1e-3]
 assert len(changes)==(1 if i==1 else 2)
 current=r['parts'][0]['mesh'].copy();current.apply_transform(r['T']);current.apply_transform(np.linalg.inv(pose))
 vv,inv=np.unique(current.vertices,axis=0,return_inverse=True);ff=inv[current.faces]
 assert np.all((ff[:,0]!=ff[:,1])&(ff[:,1]!=ff[:,2])&(ff[:,0]!=ff[:,2]))
 body=mf.Manifold(mf.Mesh64(vv,ff.astype(np.uint64),face_id=np.arange(len(ff),dtype=np.uint64)))
 assert body.status()==mf.Error.NoError
 original_ids=set(body.to_mesh64().run_original_id);assert len(original_ids)==1
 original_id=original_ids.pop()
 additions=[]
 for q in changes:
  assert .1<q.area<2
  # Small overlap is entirely within existing panel; it prevents tangent-only union.
  poly=orient(q.buffer(.0001,join_style=2),sign=1)
  additions.append(mf.CrossSection([np.array(poly.exterior.coords)[:-1]]).extrude(1.2).translate([0,0,3.2]))
 candidate=body+mf.Manifold.batch_boolean(additions,mf.OpType.Add)
 added=candidate-body;removed=body-candidate
 assert abs(removed.volume())<1e-5
 assert 0<added.volume()<5,(added.volume(),removed.volume(),[a.volume() for a in additions])
 slab=mf.Manifold.cube([2000,2000,1.2004]).translate([-1000,-1000,3.1998])
 outside=abs((added-slab).volume());assert outside<1e-5,outside
 bb=np.array((added^slab).bounding_box()).reshape(2,3)
 assert len(candidate.decompose())==1
 raw=candidate.to_mesh64();cm=mesh(candidate);assert len(cm.faces)==len(raw.tri_verts)
 origins=np.repeat(raw.run_original_id,np.diff(raw.run_index)//3);faceids=np.array(raw.face_id)
 cm.apply_transform(pose);cm.apply_transform(np.linalg.inv(r['T']))
 oid=next(k for k,v in p.configs.items() if v.find("metadata[@key='name']").get('value')==name)
 co=model.find(tag('resources')).find(f"{tag('object')}[@id='{oid}']").find(tag('components'))[0]
 asset=co.get(P+'path').lstrip('/');child=ET.fromstring(files[asset]);obj=child.find(tag('resources')).find(f"{tag('object')}[@id='{co.get('objectid')}']");old=obj.find(tag('mesh'))
 cm.apply_transform(np.linalg.inv(transform(co.get('transform'))))
 ov=np.array([[float(v.get(k)) for k in ('x','y','z')] for v in old.find(tag('vertices'))]);ot=list(old.find(tag('triangles')))
 of=np.array([[int(f.get(k)) for k in ('v1','v2','v3')] for f in ot])
 def key(tri):return tuple(sorted(tuple(x) for x in np.round(tri,6)))
 attrs={key(ov[f]):{k:v for k,v in t.attrib.items() if k not in ('v1','v2','v3')} for f,t in zip(of,ot)}
 # Preserve original support/seam paint on every untouched triangle.
 # Changed triangles lie only on the carrier; identify newly triangulated faces by parent plane.
 new=ET.Element(tag('mesh'));vs=ET.SubElement(new,tag('vertices'));fs=ET.SubElement(new,tag('triangles'));matched=0;changedfaces=0
 for v in cm.vertices:ET.SubElement(vs,tag('vertex'),**dict(zip(('x','y','z'),map(lambda x:format(float(x),'.12g'),v))))
 asm=(cm.vertices@transform(co.get('transform'))[:3,:3].T+transform(co.get('transform'))[:3,3])
 asm=(asm@r['T'][:3,:3].T+r['T'][:3,3]-pose[:3,3])@pose[:3,:3]
 for idx,f in enumerate(cm.faces):
  k=key(cm.vertices[f]);a=attrs.get(k)
  if origins[idx]==original_id:
   a={k:v for k,v in ot[int(faceids[idx])].attrib.items() if k not in ('v1','v2','v3')}
   matched+=1
  else:
   changedfaces+=1
   # No front/neck alteration or paint reassignment is allowed.
   assert asm[f,2].max()<4.4002,(i,asm[f].tolist())
   asm_normal=np.cross(asm[f[1]]-asm[f[0]],asm[f[2]]-asm[f[0]])
   a={'paint_supports':'8'} if asm_normal[2]/np.linalg.norm(asm_normal)>.01 else {}
  ET.SubElement(fs,tag('triangle'),**dict(zip(('v1','v2','v3'),map(str,f))),**a)
 obj.remove(old);obj.append(new);files[asset]=xml(child)
 stat=cfg.find(f"object[@id='{oid}']/part/mesh_stat");stat.set('face_count',str(len(cm.faces)))
 records.append(dict(veneer=i,plate=i+3,changed=True,asset=asset,additions_assembly_xy=[list(q.exterior.coords) for q in changes],added_mm3=added.volume(),removed_mm3=removed.volume(),change_bounds_assembly_mm=bb.tolist(),preserved_triangles=matched,retriangulated_carrier_triangles=changedfaces,new_faces=len(cm.faces),new_volume_mm3=candidate.volume()))
 print(records[-1],flush=True)
files['Metadata/model_settings.config']=xml(cfg)
for n in list(files):
 if n.endswith('.gcode') or n.endswith('.gcode.md5'):del files[n]
write(WORK/'Letter-edge-candidate.3mf',files)
(WORK/'edge-geometry.json').write_text(json.dumps(dict(source_sha256=sha(source),candidate_sha256=sha(WORK/'Letter-edge-candidate.3mf'),objects=records,process_changed=False,physical_shift_cause_unresolved=True),indent=2))
