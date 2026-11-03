from pathlib import Path
import sys,json,math,shutil,hashlib
sys.path.insert(0,str(Path('work/python-libs').resolve()))
import numpy as np,trimesh,manifold3d as md
from shapely.geometry import shape,Polygon,box,Point,LineString
from shapely.ops import unary_union
from shapely import affinity
s=Path('work/build_smooth_joints.py').read_text(encoding='utf-8').replace('range(20)','range(200)').replace('>.0002','>.001').replace('digits_vertex=4','digits_vertex=6');exec(s[s.index('def mesh_of(m):'):s.index('def tm(m):')]);exec(s[s.index('def extr(g,h,z):'):s.index('def rect(')].replace('.simplify(.005,preserve_topology=True)', ''))
src=Path('outputs/Dara-Smooth-Face-Up-v13');out=Path('outputs/Dara-Reinforced-Project-v25');out.mkdir(exist_ok=True)
for folder in ['STL/knot','STL/letter','STL/hardware','CAD','source','drawings','Bambu-Studio/Grouped-Projects','Bambu-Studio/Profiles']:(out/folder).mkdir(parents=True,exist_ok=True)
shutil.copytree(src/'templates',out/'templates',dirs_exist_ok=True)
for file in (src/'drawings').glob('*.svg'):shutil.copy2(file,out/'drawings'/file.name)
d=json.loads((src/'project-data.json').read_text());rails0=shape(json.loads(Path('work/smooth-master/approved-knot-master.geojson').read_text()));holes=sorted([Polygon(q) for q in rails0.interiors],key=lambda p:p.area,reverse=True);grooves0=unary_union([holes[i] for i in list(range(1,9))+list(range(21,25))]);outline=rails0.union(grooves0)
base=[(True,271.5518021849426,-69.5,1,8),(False,24.01110382197192,316.8,1,8),(True,361.35001221105495,-69.5,-1,365.68-361.35001221105495),(False,114.03927919843565,316.8,-1,121.84-114.03927919843565)]
# Find every channel end: six distinct positions repeated around the knot.
base += [(True,361.29,316.8,-1,365.68-361.29),(True,271.539,316.8,1,8)]
grooves=grooves0;zones=[];endties=[];capchecks=[]
for rotation in [0,90,180,270]:
 localgrooves=affinity.rotate(grooves0,-rotation,origin=(0,0))
 for horizontal,end,c,direction,depth in base:
  comp=next(g for g in localgrooves.geoms if g.contains(Point(end-direction*3,c) if horizontal else Point(c,end-direction*3)))
  angle=(0 if horizontal else -90)+(180 if direction==-1 else 0);local=affinity.rotate(comp,angle,origin=(0,0));tip=direction*end;start=tip-depth;transverse=direction*(c if horizontal else -c)
  section=local.intersection(LineString([(start,-700),(start,700)]));pieces=list(section.geoms) if hasattr(section,'geoms') else [section];section=min(pieces,key=lambda g:g.distance(Point(start,transverse)));lo,hi=section.bounds[1],section.bounds[3]
  cap=box(start-2,lo,tip,hi).buffer(-2).buffer(2,quad_segs=16);zone=box(start,lo-3,tip+3,hi+3);cap=cap.intersection(zone)
  assert cap.symmetric_difference(affinity.scale(cap,xfact=1,yfact=-1,origin=(0,(lo+hi)/2))).area<1e-5
  cap=affinity.rotate(cap,rotation-angle,origin=(0,0));zone=affinity.rotate(zone,rotation-angle,origin=(0,0));grooves=grooves.difference(zone).union(cap);zones.append(zone)
  if direction==1:
   tie=box(tip-2.4,transverse-50,tip,transverse+50);endties.append(affinity.rotate(tie,rotation-angle,origin=(0,0)))
  capchecks.append({'quadrant_rotation':rotation,'axis':'X' if horizontal else 'Y','radius_mm':2,'short_return':direction==-1})
# Remove the two traced contour kinks on the left curved channels. These
# are in the master boundary, not Bambu seam-display marks. Preserve the rest.
curve_checks=[]
for centre in [(-303.54,-478.6),(-303.54,478.6)]:
 comp=min(grooves.geoms,key=lambda q:q.boundary.distance(Point(centre)))
 # Match the existing mesh wall at the patch boundary, avoiding a new join kink.
 part='K52' if centre[1]<0 else 'K12';record=next(q for q in d['parts'] if q['part']==part)
 source_mesh=trimesh.load_mesh(src/record['file']);source_mesh.apply_transform(record['assembly_transform']);source_solid=md.Manifold(md.Mesh64(np.array(source_mesh.vertices),np.array(source_mesh.faces,dtype=np.uint64)))
 high=Polygon()
 for aa in sorted(source_solid.slice(17).to_polygons(),key=lambda q:Polygon(q).area,reverse=True):
  aa=np.array(aa);poly=Polygon(aa);sign=np.sum(aa[:,0]*np.roll(aa[:,1],-1)-aa[:,1]*np.roll(aa[:,0],-1));high=high.union(poly) if sign>0 else high.difference(poly)
 original_comp=comp;expanded=box(centre[0]-20,centre[1]-20,centre[0]+20,centre[1]+20)
 comp=comp.difference(expanded).union(expanded.difference(high).intersection(outline))
 if comp.geom_type=='MultiPolygon':comp=max(comp.geoms,key=lambda q:q.area)
 a=np.array(comp.exterior.coords);lengths=np.r_[0,np.cumsum(np.linalg.norm(np.diff(a,axis=0),axis=1))];count=math.ceil(lengths[-1]/.35);ss=np.arange(count)*lengths[-1]/count
 pts=np.column_stack([np.interp(ss,lengths,a[:,i]) for i in [0,1]])
 sigma=3/(lengths[-1]/count);shifts=np.arange(-math.ceil(3*sigma),math.ceil(3*sigma)+1);weights=np.exp(-.5*(shifts/sigma)**2);weights/=weights.sum()
 smooth=sum(w*np.roll(pts,int(k),axis=0) for k,w in zip(shifts,weights))
 distance=np.linalg.norm(pts-np.array(centre),axis=1);blend=np.clip((13-distance)/5,0,1);fixed=Polygon(pts+(smooth-pts)*blend[:,None]).simplify(.01,preserve_topology=True)
 region=Point(centre).buffer(14,quad_segs=32);replacement=comp.difference(region).union(fixed.intersection(region))
 grooves=grooves.difference(original_comp).union(replacement);zones.append(box(centre[0]-15,centre[1]-15,centre[0]+15,centre[1]+15))
 curve_checks.append({'centre':centre,'maximum_boundary_change_mm':comp.hausdorff_distance(replacement)})
rails=outline.difference(grooves);allzones=unary_union(zones);allties=unary_union(endties);texture=grooves.buffer(-.8)
warp=unary_union([box(x-1,-620,x+1,620) for x in np.arange(-608,609,8)]);weft=unary_union([box(-620,y-1,620,y+1) for y in np.arange(-608,609,8)]);weave=warp.union(weft).intersection(texture);pads=[]
for ix,x in enumerate(np.arange(-608,609,8)):
 for iy,y in enumerate(np.arange(-608,609,8)):
  pad=box(x-1,y-2.2,x+1,y+2.2) if (ix+iy)%2 else box(x-2.2,y-1,x+2.2,y+1)
  if texture.contains(pad):pads.append(pad)
pads=unary_union(pads)
def rect(x,y,a,x0,y0,x1,y1):return affinity.translate(affinity.rotate(box(x0,y0,x1,y1),a,origin=(0,0)),x,y)
def ext(g,h,z):
 if g.is_empty:return md.Manifold()
 return extr(g,h,z)
def mf(t):return md.Manifold(md.Mesh64(np.array(t.vertices),np.array(t.faces,dtype=np.uint64)))
def clean(m):
 m=m.warp(lambda v: tuple(round(float(x),3) for x in v)).set_tolerance(.005).simplify(.005)
 cs=[q for q in m.decompose() if abs(q.volume())>1e-7];assert len(cs)==1,[(q.volume(),q.bounding_box()) for q in cs]
 for tol in [.005,.01,.02,.03]:
  t=mesh_of(cs[0].simplify(tol));components=t.split(only_watertight=False);big=[q for q in components if abs(q.volume)>1e-6]
  if len(big)==1 and big[0].is_watertight:return big[0]
 mm=cs[0].to_mesh64()
 for digits in [7,6,5,4]:
  t=trimesh.Trimesh(np.array(mm.vert_properties[:,:3]).astype(np.float32),np.array(mm.tri_verts),process=False)
  t.merge_vertices(digits_vertex=digits);t.update_faces(t.nondegenerate_faces());t.update_faces(t.unique_faces());t.remove_unreferenced_vertices();trimesh.repair.fill_holes(t)
  if t.is_watertight and len(t.split())==1:return t
  pieces=t.split(only_watertight=False);main=max(pieces,key=lambda q:len(q.faces))
  if main.is_watertight and all(q is main or min(q.extents)<.001 for q in pieces):return main
 np.savez('work/bad-manifold.npz',v=np.array(mm.vert_properties[:,:3]),f=np.array(mm.tri_verts));print('BAD',name,[(len(q.faces),q.is_watertight,q.volume) for q in t.split(only_watertight=False)],flush=True)
 t.export('work/problem-export.stl')
 raise RuntimeError('Mesh export not watertight')
checks=[]
for r in d['parts']:
 name=r['part'];file=out/r['file'];file.parent.mkdir(parents=True,exist_ok=True)
 if not ('/knot/' in r['file'] or '/letter/' in r['file']):shutil.copy2(src/r['file'],file);continue
 if name=='K34':
  running=Path('outputs/Dara-All-Ends-v23-Test/K34-ALL-ENDS.stl');shutil.copy2(running,file);t=trimesh.load_mesh(file);r['solid_volume_cm3']=t.volume/1000;checks.append({'part':name,'exact_running_v23_STL':True,'sha256':hashlib.sha256(file.read_bytes()).hexdigest()});print(name,'preserved byte-for-byte',flush=True);continue
 t=trimesh.load_mesh(src/r['file']);T=np.array(r['assembly_transform']);t.apply_transform(T);t.vertices[:,2]=np.round(t.vertices[:,2],4);original=mf(t);bed=float(t.bounds[0,2]);is_m=name.startswith('M_');z0=18 if is_m else 0
 projected=unary_union([Polygon(tri[:,:2]) for tri,n in zip(t.triangles,t.face_normals) if n[2]>.5 and tri[:,2].mean()>(30.9 if is_m else 10.9) and Polygon(tri[:,:2]).area>1e-6]).buffer(-.05).simplify(.01,preserve_topology=True)
 foot=projected if is_m else outline.intersection(projected)
 tile=None
 if not is_m and len(name)==3:
  row,col=int(name[1]),int(name[2]);x0=(col-3.5)*243.84+.08;y0=(2.5-row)*243.84+.08;tile=box(x0,y0,x0+243.68,y0+243.68)
 joints=[j for j in d['locating_joints'] if name in j['parts']];joint_areas=[]
 for j in joints:joint_areas.append(rect(j['x'],j['y'],j['angle'],-4.1,-j['tongue_spacing_mm']/2-4.6,8.1,j['tongue_spacing_mm']/2+4.6))
 reserved=[Point(q['x'],q['y']).buffer(5) for q in d['letter_mounts']]
 if not is_m:
  reserved += [rect(q['x'],q['y'],q['angle'],-18,-6,7,6) for q in d['photo_clips']]+[h.buffer(8.2) for h in holes[13:21]]
  reserved += [box(q['x']-27,q['y']-19,q['x']+27,q['y']+19) for q in d['wall_mounts']]
  reserved += [rect(q['x'],q['y'],q['angle'],-56,-16,56,16) for q in d['adhesive_pad_sites']]
 guard2=unary_union(reserved).intersection(foot.buffer(1));guard=ext(guard2,40,bed-.1)
 label=r['hidden_label'];x,y,z=label['print_position_mm'];w=(6*len(name)-1)*.65
 pp=np.array([[x-.5,y+.5,z,1],[x+w+.5,y+.5,z,1],[x+w+.5,y-5.05,z,1],[x-.5,y-5.05,z,1]])@T.T
 label_guard=ext(Polygon(pp[:,:2]),.65,pp[0,2]-.5);guard+=label_guard
 original_before=original
 if not is_m:
  zone=allzones.intersection(outline.intersection(tile) if tile is not None else foot)
  if not zone.is_empty:
   original-=ext(zone,10,10.8);high=rails.intersection(zone)
   original+=ext(zone,1.2,10.8)+ext(high.difference(rails.buffer(-2.4)),6.6,10.8)+ext(high,.6,16.8)+ext(rails.buffer(-.65).intersection(zone),.6,17.4)+ext(weave.intersection(zone),.8,12)+ext(pads.intersection(zone),.4,12.8)
  channel=grooves.intersection(foot);walls=channel.difference(channel.buffer(-2.4));ties=allties.intersection(foot)
  addition=ext(walls.union(ties),10.95-bed,bed)+ext(ties.intersection(rails.buffer(-.05)),16.95-bed,bed)
  if bed<-.1:
   slab=original_before^md.Manifold.cube((1400,1400,.1)).translate((-700,-700,0));addition+=slab.scale((1,1,(.1-bed)/.1)).translate((0,0,bed))
  addition=addition-guard-ext(unary_union(joint_areas),40,bed-.1)
 else:addition=md.Manifold()
 braces=[]
 for j in joints:
  male=j['male']==name;bx=(-10,-7.6) if male else (10,12.4);bar=rect(j['x'],j['y'],j['angle'],bx[0],-50,bx[1],50).intersection(foot);links=[]
  for offset in ([-j['tongue_spacing_mm']/2,j['tongue_spacing_mm']/2] if j['tongue_spacing_mm'] else [0]):
   lx=(-10,-3) if male else (7,12.4);links.append(rect(j['x'],j['y'],j['angle'],lx[0],offset-1.2,lx[1],offset+1.2).intersection(foot))
  if is_m:brace=ext(bar,30.95-bed,bed)
  else:brace=ext(bar,10.95-bed,bed)+ext(bar.intersection(rails.buffer(-.05)),16.95-bed,bed)
  brace+=ext(unary_union(links),z0+7-bed,bed);braces.append(brace-guard)
 new=original+addition+md.Manifold.batch_boolean(braces,md.OpType.Add)
 assert ((new^guard)-(original^guard)).volume()<.03,(name,'guard')
 world=clean(new.transform(np.linalg.inv(T)[:3,:]));world.export(file);reloaded=trimesh.load_mesh(file);assert reloaded.is_watertight and len(reloaded.split())==1
 assert max(abs(reloaded.extents-np.array([r['x_mm'],r['y_mm'],r['z_mm']])))<.03,(name,reloaded.extents)
 r['solid_volume_cm3']=reloaded.volume/1000;r['notes']='v25: face-up; permanent channel walls/end ties on knot, connector bracing, protected interfaces/labels; K34 physical trial pending.'
 checks.append({'part':name,'watertight':True,'connected':True,'interfaces_protected':True,'new_solid_cm3':r['solid_volume_cm3']});print(name,'complete',flush=True)
 (out/'build-progress.json').write_text(json.dumps(checks,indent=2))
d['revision']='v25 full reinforced project; K34 identical to running v23';d['status']='Saved production revision; physical K34 trial pending. Do not start remaining plates until K34 result is checked.';d['validation']={'meshes_checked':True,'physical_K34_trial':'running; result pending','full_project_sliced':False};(out/'project-data.json').write_text(json.dumps(d,indent=2));(out/'mesh-validation.json').write_text(json.dumps({'parts':checks,'symmetric_ends':capchecks,'curved_channel_corrections':curve_checks},indent=2));print('COMPLETE',len(checks),flush=True)












