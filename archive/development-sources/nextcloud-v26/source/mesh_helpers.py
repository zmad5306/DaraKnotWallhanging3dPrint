import sys,json,math,shutil
from pathlib import Path
sys.path.insert(0,str(Path('work/python-libs').resolve()))
import numpy as np,trimesh,manifold3d as md
from shapely.geometry import Polygon,box,MultiPoint,Point
from shapely.ops import unary_union
from shapely import affinity
src=Path('work/smooth-baseline');out=Path('work/smooth-joints');out.mkdir(exist_ok=True)
d=json.loads((src/'project-data.json').read_text());parts={r['part']:r for r in d['parts']};world={};foot={};solids={}
def manifold(t):return md.Manifold(md.Mesh64(np.array(t.vertices,dtype=np.float64),np.array(t.faces,dtype=np.uint64)))
def mesh_of(m):
    mm=m.to_mesh64()
    t=trimesh.Trimesh(np.array(mm.vert_properties[:,:3]),np.array(mm.tri_verts),process=True)

    t.vertices=t.vertices.astype(np.float32).astype(float)
    t.merge_vertices(digits_vertex=4)
    t.update_faces(t.nondegenerate_faces())
    t.update_faces(t.unique_faces())
    t.remove_unreferenced_vertices()
    if not t.is_watertight:trimesh.repair.fill_holes(t)
    # STL precision can collapse extremely thin triangles into collinear T-junctions.
    # Split the opposing long edge at its existing middle vertex, preserving surface.
    for attempt in range(20):
        if t.is_watertight:break
        edges,counts=np.unique(t.edges_sorted,axis=0,return_counts=True)
        boundary=edges[counts==1];adj={}
        for a,b in boundary:adj.setdefault(int(a),set()).add(int(b));adj.setdefault(int(b),set()).add(int(a))
        repaired=False
        for a,ns in adj.items():
            if len(ns)!=2:continue
            b,c=tuple(ns)
            if b not in adj.get(c,set()):continue
            ids=[a,b,c];pairs=[(i,j) for i in ids for j in ids if i<j]
            aa,bb=max(pairs,key=lambda ij:np.linalg.norm(t.vertices[ij[0]]-t.vertices[ij[1]]))
            middle=next(i for i in ids if i not in [aa,bb]);v=t.vertices[bb]-t.vertices[aa]
            if np.linalg.norm(np.cross(t.vertices[middle]-t.vertices[aa],v))/np.linalg.norm(v)>.0002:continue
            faces=t.faces.tolist()
            for fi,face in enumerate(faces):
                if aa not in face or bb not in face:continue
                for k in range(3):
                    i,j,third=face[k],face[(k+1)%3],face[(k+2)%3]
                    if set([i,j])==set([aa,bb]):
                        faces[fi]=[i,middle,third];faces.append([middle,j,third]);repaired=True;break
                if repaired:break
            if repaired:
                t=trimesh.Trimesh(t.vertices,np.array(faces),process=False);break
        if not repaired:break
    return t


def tm(m):
 t=mesh_of(m.simplify(.005))
 assert t.is_watertight and t.volume>0 and len(t.split())==1,(m.status(),t.is_watertight,[q.volume for q in t.split()])
 return t
def extr(g,h,z):
 g=g.buffer(0).simplify(.005,preserve_topology=True)
 contours=[]
 from shapely.geometry.polygon import orient
 for p in ([g] if g.geom_type=='Polygon' else g.geoms):
  if p.geom_type!='Polygon' or p.area<.001:continue
  p=orient(p,1);contours.append(np.array(p.exterior.coords[:-1]));contours.extend(np.array(q.coords[:-1]) for q in p.interiors)
 return md.CrossSection(contours,md.FillRule.NonZero).extrude(h).translate((0,0,z))
def rect(x,y,a,x0,y0,x1,y1):return affinity.translate(affinity.rotate(box(x0,y0,x1,y1),a,origin=(0,0)),x,y)
main=[r for r in d['parts'] if '/knot/' in r['file'] or '/letter/' in r['file']]
for r in main:
 t=trimesh.load_mesh(src/r['file']);t.apply_transform(r['assembly_transform']);name=r['part'];world[name]=t;solids[name]=manifold(t)
 assert solids[name].status()==md.Error.NoError,name
 foot[name]=unary_union([Polygon(f[:,:2]) for f,n in zip(t.triangles,t.face_normals) if n[2]>.5 and Polygon(f[:,:2]).area>.00001]).buffer(.001)
 print('loaded',name,flush=True)
fixed_joints={j['id']:j for j in json.loads(Path('outputs/Dara-Labeled-v10/project-data.json').read_text())['locating_joints']}
newj=[]
for old in d['joints']+d['M_joints']:
 names=old['parts'];is_m=names[0].startswith('M_');a=0 if (not is_m and old['angle']==0) or (is_m and abs(old['x'])==100) else 90
 direction=np.array([math.cos(math.radians(a)),math.sin(math.radians(a))])
 names=sorted(names,key=lambda n:np.dot(np.array(foot[n].centroid.coords[0]),direction));male,female=names
 union=foot[male].union(foot[female]).buffer(.1)
 j0=fixed_joints[old['id']];x,y,span=j0['x'],j0['y'],j0['tongue_spacing_mm'];a=j0['angle'];male,female=j0['male'],j0['female'];names=[male,female];z=18 if is_m else 0
 # Individual compact roots/collars rather than one wide shelf.
 offsets=[-span/2,span/2] if span else [0]
 for offset in offsets:
  male_root=rect(x,y,a,-4,offset-4.5,.05,offset+4.5)
  female_root=rect(x,y,a,-.05,offset-4.5,8,offset+4.5)
  solids[male]+=extr(male_root.intersection(foot[male]),7,z)
  solids[female]+=extr(female_root.intersection(foot[female]),7,z)
  if is_m:
   for n,x0,x1 in [(male,-2.5,-.05),(female,.05,2.5)]:
    web=rect(x,y,a,x0,offset-4.5,x1,offset+4.5)
    solids[n]+=extr(web.intersection(foot[n]),12.9,z)
  tongue=rect(x,y,a,-1,offset-3,6,offset+3)
  socket=rect(x,y,a,-.2,offset-3.15,6.5,offset+3.15)
  solids[male]+=extr(tongue,2.4,z+2.4)
  solids[female]-=extr(socket,2.7,z+2.25)
  assert solids[male].status()==md.Error.NoError,(old['id'],male,'male construction')
  assert solids[female].status()==md.Error.NoError,(old['id'],female,'female construction')
 j={'id':old['id'],'parts':names,'male':male,'female':female,'x':x,'y':y,'angle':a,'tongue_count':len(offsets),'tongue_spacing_mm':span,'total_clearance_mm':.3,'rear_z':z}
 newj.append(j);print('joint',j['id'],male,'->',female,'tongues',len(offsets),'spacing',span,flush=True)
records=[];scene=trimesh.Scene()
for r in main:
 name=r['part'];t=tm(solids[name]);scene.add_geometry(t.copy(),geom_name=name)
 # Face down, in-plane rotation chosen with room for a 2 mm brim on the 256 mm bed.
 flip=trimesh.transformations.rotation_matrix(math.pi,[1,0,0]);t.apply_transform(flip)
 hull=MultiPoint(t.vertices[:,:2]).convex_hull;choices=[]
 for a in range(0,180,2):
  b=affinity.rotate(hull,a,origin=(0,0)).bounds;w,h=b[2]-b[0],b[3]-b[1];choices.append((max(w,h),w*h,a))
 _,_,a=min(choices);rot=trimesh.transformations.rotation_matrix(math.radians(a),[0,0,1]);t.apply_transform(rot);bottom=t.bounds[0];trans=trimesh.transformations.translation_matrix(-bottom);t.apply_transform(trans)
 assert max(t.extents[:2])<=250.1,(name,t.extents)
 t=mesh_of(manifold(t).simplify(.005))
 f=out/r['file'];f.parent.mkdir(parents=True,exist_ok=True);t.export(f)
 reloaded=trimesh.load_mesh(f);assert reloaded.is_watertight and len(reloaded.split())==1,name
 rec=dict(r);rec.update(x_mm=round(t.extents[0],3),y_mm=round(t.extents[1],3),z_mm=round(t.extents[2],3),solid_volume_cm3=t.volume/1000,assembly_transform=np.linalg.inv(trans@rot@flip).tolist(),print_rotation_deg=a,notes='v9 integral locating tongues, 0.30 mm socket clearance; no rear glue strip')
 records.append(rec);print('saved',name,t.extents,flush=True)
# Keep the confirmed dowels and alternative mounts. Rear splice strips are retired.
for r in d['parts']:
 if r['part'] not in ['M_LOCATING_DOWEL','WALL_KEYHOLE_BLOCK','OPTIONAL_ADHESIVE_PAD_110x30']:continue
 f=out/r['file'];f.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src/r['file'],f);records.append(r)
d['parts']=records;d['locating_joints']=newj;d['legacy_joint_map_positions']=d['joints']+d['M_joints'];d['joints']=[];d['M_joints']=[]
d['assembly_method']='Integral tongues and sockets, total clearance 0.30 mm, glue seam and tongues. Row-first assembly.'
d.setdefault('fit_feedback',{})['locating_socket_total_clearance_mm']=.3;d['fit_feedback']['user_report']='Socket 3 nice and tight; sockets 1 and 2 will not insert.'
d['validation']={'all_meshes_watertight':True,'all_individual_parts_connected':True,'all_print_footprints_within_250mm':True,'physical_fit_tested':'Straight 18 mm coupon only; full-size revised interfaces not yet printed','wall_load_tested':False,'slicer_checked':False}
(out/'project-data.json').write_text(json.dumps(d,indent=2));(out/'drawings').mkdir(exist_ok=True);scene.export(out/'drawings/ASSEMBLED_REFERENCE.glb')
for name in ['CAD-front.png','01-knot-assembly-map.svg','03-letter-assembly-map.svg','04-optional-adhesive-pad-map.svg']:
 if name=='03-letter-assembly-map.svg':continue
 shutil.copy2(src/'drawings'/name,out/'drawings'/name)
shutil.copytree(src/'templates',out/'templates',dirs_exist_ok=True)
print('DONE',len(records),'unique files',len(newj),'joints',flush=True)
