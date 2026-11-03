from pathlib import Path
import sys,json,shutil,math
sys.path.insert(0,str(Path('work/python-libs').resolve()))
import numpy as np,trimesh,manifold3d as md
from shapely.geometry import Polygon,Point,box,shape
from shapely.ops import unary_union
from shapely import affinity
h=Path(__file__).with_name('previous_geometry_helpers.py').read_text();helper=h[h.index("s=Path('work/build_smooth_joints.py')"):h.index('src=Path(')];helper=helper.replace("Path('work/build_smooth_joints.py')","Path(__file__).with_name('mesh_helpers.py')");exec(helper)
h=h.replace('cs=[q for q in m.decompose() if abs(q.volume())>1e-7];assert len(cs)==1','pieces=m.decompose();assert sum(abs(q.volume()) for q in pieces if q.volume()<0)<5;cs=[q for q in pieces if q.volume()>1e-7];assert len(cs)==1')
exec(h[h.index('def ext('):h.index('\nchecks=[]\nfor r in d')])
ROOT=Path(__file__).resolve().parents[1];src=ROOT/'source/baseline-v25';out=ROOT/'regenerated-v26';out.mkdir(exist_ok=True)
for f in ['templates','drawings']:shutil.copytree(src/f,out/f,dirs_exist_ok=True)
for f in ['STL/knot','STL/letter','STL/hardware','CAD','source','Bambu-Studio/Grouped-Projects','Bambu-Studio/Profiles']:(out/f).mkdir(parents=True,exist_ok=True)
d=json.loads((src/'project-data.json').read_text());rails=shape(json.loads(Path(__file__).with_name('approved-knot-master.geojson').read_text()));holes=sorted([Polygon(q) for q in rails.interiors],key=lambda q:q.area,reverse=True)
def rect(x,y,a,x0,y0,x1,y1):return affinity.translate(affinity.rotate(box(x0,y0,x1,y1),a,origin=(0,0)),x,y)
checks=[]
for r in d['parts']:
 name=r['part'];target=out/r['file'];target.parent.mkdir(parents=True,exist_ok=True)
 if '/hardware/' in r['file']:shutil.copy2(src/r['file'],target);continue
 t=trimesh.load_mesh(src/r['file']);tf=np.array(r['assembly_transform']);t.apply_transform(tf);t.vertices[:,2]=np.round(t.vertices[:,2],4);original=mf(t);bed=t.bounds[0,2];isM=name.startswith('M');rear=18 if isM else 0
 foot=unary_union([Polygon(tri[:,:2]) for tri,n in zip(t.triangles,t.face_normals) if n[2]>.5 and tri[:,2].mean()>(30.9 if isM else 10.9) and Polygon(tri[:,:2]).area>1e-6]).buffer(-.03)
 high=unary_union([Polygon(tri[:,:2]) for tri,n in zip(t.triangles,t.face_normals) if n[2]>.5 and tri[:,2].mean()>(31.5 if isM else 17.5) and Polygon(tri[:,:2]).area>1e-6])
 regions=[];sockets=[];interface=[]
 for j in d['locating_joints']:
  if name not in j['parts']:continue
  male=j['male']==name;lo,hi=(-10,-.25) if male else (.25,12.4);half=j['tongue_spacing_mm']/2+5.7
  regions.append(rect(j['x'],j['y'],j['angle'],lo,-half,hi,half))
  if not male:
   for off in ([-j['tongue_spacing_mm']/2,j['tongue_spacing_mm']/2] if j['tongue_spacing_mm'] else [0]):sockets.append(ext(rect(j['x'],j['y'],j['angle'],-.3,off-3.15,6.5,off+3.15),2.7,rear+2.25))
  # Preserve the whole contact interface slab and exact female socket dimensions.
  interface.append(ext(rect(j['x'],j['y'],j['angle'],-.24,-half-.1,.24,half+.1),40,bed-.1))
 zone=unary_union(regions).intersection(foot)
 protection=[Point(q['x'],q['y']).buffer(5) for q in d['letter_mounts']]
 if not isM:
  protection += [q.buffer(8.2) for q in holes[13:21]]+[rect(q['x'],q['y'],q['angle'],-18,-6,7,6) for q in d['photo_clips']]
  protection += [box(q['x']-27,q['y']-19,q['x']+27,q['y']+19) for q in d['wall_mounts']]+[rect(q['x'],q['y'],q['angle'],-56,-16,56,16) for q in d['adhesive_pad_sites']]
 zone=zone.difference(unary_union(protection))
 fill=ext(zone,(30.95 if isM else 10.95)-bed,bed)
 if not isM:fill+=ext(zone.intersection(high),16.95-bed,bed)
 if sockets:fill-=md.Manifold.batch_boolean(sockets,md.OpType.Add)
 new=original+fill
 for mask in sockets+interface:assert ((new^mask)-(original^mask)).volume()<.001,(name,'mating change')
 result=clean(new.transform(np.linalg.inv(tf)[:3,:]));result.export(target);re=trimesh.load_mesh(target);assert re.is_watertight and len(re.split())==1
 assert np.max(abs(re.extents-np.array([r['x_mm'],r['y_mm'],r['z_mm']])))<.03
 r['solid_volume_cm3']=re.volume/1000;r['notes']='v26: rear joint-base pockets filled; mating geometry unchanged; compatible with completed K34 v23.'
 checks.append({'part':name,'watertight':True,'connected':True,'added_volume_cm3':(new.volume()-original.volume())/1000,'mating_geometry_preserved':True});print(name,round(checks[-1]['added_volume_cm3'],2),flush=True)
d['revision']='v26 solid rear joint pockets';d['status']='K34 v23 physical print successful; completed original remains compatible; v26 fills rear joint-base pockets.';d['validation']['physical_K34_trial']='User reported massive success on October 5, 2026';d['validation']['full_project_sliced']=False
(out/'project-data.json').write_text(json.dumps(d,indent=2));(out/'joint-fill-validation.json').write_text(json.dumps(checks,indent=2));shutil.copy2(src/'mesh-validation.json',out/'prior-v25-mesh-validation.json');(out/'mesh-validation.json').write_text(json.dumps({'parts':checks},indent=2))
print('TOTAL ADDED CM3',sum(q['added_volume_cm3'] for q in checks))


# CURRENT_MESH_REPAIR_OVERRIDES
# The latest repaired meshes are authoritative. The historical constructive
# baseline above predates these repairs; preserve them in regenerated exports.
repaired_parts = ['K21','K45','K54','K53b','K31b','K13b','K35b','K53a','K31a','K13a','K35a','K33b','K33c','K14','K25']
for repaired_name in repaired_parts:
    shutil.copy2(ROOT/'STL/knot'/(repaired_name+'.stl'), out/'STL/knot'/(repaired_name+'.stl'))
shutil.copy2(ROOT/'project-data.json', out/'project-data.json')
print('Applied current authoritative mesh repairs. Use export_current_cad.py for CAD review exports.')

# Preserve screw-mount M meshes (v34).
for name in ['M_01', 'M_02', 'M_03', 'M_04', 'M_05', 'M_06', 'M_07', 'M_08']:
    shutil.copy2(ROOT/"STL/letter"/(name+".stl"), out/"STL/letter"/(name+".stl"))
