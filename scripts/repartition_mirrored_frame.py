"""Build and verify the approved mirrored 20-section, 32-lap knot revision.

Manufacturing profiles and the continuous artwork are preserved. The immutable
migration input is .work/mirrored-joints/baseline; the final layout is also saved
under working/geometry so the design does not depend on a chat visualization.
"""
import argparse,ast,copy,graphlib,hashlib,json,math,re,shutil,subprocess,time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from build_jointed_bambu_project import ROOT,read_array
from add_blue_ribbon_edge import artwork
from repair_curve_artifacts import serialize
from export_jointed_stls import verify
import numpy as np
from scipy.optimize import linear_sum_assignment,minimize_scalar
from shapely import affinity,union_all
from shapely.geometry import Point,Polygon,LineString,box,shape,mapping
from shapely.geometry.polygon import orient
from shapely.ops import polygonize

WORK=ROOT/'.work/mirrored-joints'
BASE=WORK/'baseline'
CAD=ROOT/'working/Dara-Photo-Frame-A1-Jointed.scad'
STLS=ROOT/'working/stl/Dara-Photo-Frame-A1-Jointed'
REVIEW=ROOT/'working/review/mirrored-joints'
PLAN=ROOT/'working/geometry/mirrored-frame-layout.json'
REL=Path('working/Dara-Photo-Frame-A1-Jointed.scad')

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def polys(g):return [g] if g.geom_type=='Polygon' else [p for p in g.geoms if p.geom_type=='Polygon']
def axes(j):
    a=math.radians(j[3]);n=np.array([math.cos(a),math.sin(a)])
    return n,np.array([-n[1],n[0]])
def line(j,extra=4):
    n,t=axes(j);c=np.array(j[2]);h=j[4]/2+extra
    return LineString([c-t*h,c+t*h])
def locate(g,j):return affinity.translate(affinity.rotate(g,j[3],origin=(0,0)),*j[2])
def domain(j,whole):
    d=whole.intersection(locate(box(-1.5,-j[4]/2-22,20,j[4]/2+22),j))
    return max(polys(d),key=lambda p:p.intersection(line(j)).length).buffer(.1,join_style=2)
def fit(g):
    v=np.asarray(g.convex_hull.exterior.coords)[:-1];aa=np.deg2rad(np.arange(0,90,.25))
    def dims(a):
        c,s=np.cos(a),np.sin(a)
        return np.array([np.ptp(v[:,0,None]*c-v[:,1,None]*s,axis=0),np.ptp(v[:,0,None]*s+v[:,1,None]*c,axis=0)]).T
    k=np.argmin(dims(aa).max(axis=1));opt=minimize_scalar(lambda a:max(dims(np.array([a]))[0]),bounds=(aa[k]-math.pi/720,aa[k]+math.pi/720),method='bounded',options={'xatol':1e-10})
    angle=float(math.degrees(opt.x));rot=affinity.rotate(g,angle,origin=(0,0));lo=np.array(rot.bounds[:2]);hi=np.array(rot.bounds[2:])
    return angle,((lo+hi)/2).tolist(),(hi-lo).tolist()
def replace_array(s,name,value):
    s,n=re.subn(r'^'+name+r'\s*=\s*\[.*?\];',lambda _:name+' = '+json.dumps(value,separators=(',',':'))+';',s,count=1,flags=re.M|re.S)
    assert n==1,name
    return s
def replace_module(s,name,g):
    body=serialize(name,affinity.scale(g,.75,.75,origin=(0,0)))
    s,n=re.subn(r'module '+name+r'\(\) \{.*?\n\}',lambda _:body,s,count=1,flags=re.S)
    assert n==1,name
    return s

def plan():
    REVIEW.mkdir(parents=True,exist_ok=True)
    text=(BASE/REL).read_text();raw=json.loads((WORK/'approved-concept.json').read_text())
    knot=artwork(text,'knot_outline');letter=artwork(text,'letter_outline')
    whole=knot.union(artwork(text,'fabric_outline').buffer(.1125,join_style=2))
    ps=[shape(p) for p in raw['parts']];js=copy.deepcopy(raw['joints'])
    old=[affinity.scale(artwork(text,f'frame_mask_{i}'),1/.75,1/.75,origin=(0,0)) for i in range(20)]
    cost=np.array([[-p.intersection(q).area for q in old] for p in ps])
    ii,jj=linear_sum_assignment(cost);remap=dict(zip(map(int,ii),map(int,jj)))
    parts=[ps[next(k for k,v in remap.items() if v==i)] for i in range(20)]
    for j in js:j[:2]=[remap[j[0]],remap[j[1]]]
    domains=[domain(j,whole) for j in js];all_domains=union_all(domains)
    screws=read_array(text,'screw_mounts');pins=read_array(text,'dowel_mounts');walls=read_array(text,'wall_mounts')
    old_screws=copy.deepcopy(screws);old_pins=copy.deepcopy(pins)
    anchors=np.array(read_array(text,'photo_anchors'))*.75;normals=np.array(read_array(text,'photo_normals'))
    old_anchors=anchors.copy();old_normals=normals.copy();moves=[]
    photos=[artwork(text,f'photo_loop_{i+1}') for i in range(8)]

    def owner(xy):
        ids=[i for i,p in enumerate(parts) if p.covers(Point(xy))]
        assert len(ids)==1,(xy,ids)
        return ids[0]
    # Relocate only attachment regions that conflict with a new lap; preserve
    # actual hardware sizes, hole depths, and the original M section ownership.
    for family,rows,oldrows,radius in [('screw',screws,old_screws,8.5),('locator',pins,old_pins,4.0)]:
        for index,row in enumerate(rows):
            original=np.array(row[2],float)
            if all_domains.distance(Point(original))<radius+.2:
                safe=knot.buffer(-radius).intersection(letter.buffer(-(7 if family=='screw' else 3.5))).difference(all_domains.buffer(radius+.5))
                # Keep each hole in its existing historical M piece. Actual
                # hammered-part ownership is independently checked in 3D.
                historical=affinity.scale(artwork(text,f'M_mask_{row[0]}'),1/.75,1/.75,origin=(0,0))
                safe=safe.intersection(historical.buffer(-8 if family=='screw' else -4))
                occupied=[]
                for kind,rr in [('screw',screws),('locator',pins)]:
                    for k,other in enumerate(rr):
                        if kind==family and k==index:continue
                        occupied.append(Point(other[2]).buffer(radius+(8.5 if kind=='screw' else 4)+1))
                safe=safe.difference(union_all(occupied))
                candidates=[]
                for dx in np.arange(-25,25.01,.5):
                    for dy in np.arange(-25,25.01,.5):
                        p=original+[dx,dy]
                        if safe.contains(Point(p)):candidates.append((dx*dx+dy*dy,p))
                assert candidates,(family,index,'No nearby safe mounting site')
                _,p=min(candidates,key=lambda item:item[0]);row[2]=p.tolist()
                moves.append(dict(kind=family,index=index+1,old_xy=original.tolist(),new_xy=row[2],distance_mm=float(np.linalg.norm(p-original))))
            row[1]=owner(row[2])
    for mi in range(6):
        pair=[p for p in pins if p[0]==mi];assert len(pair)==2
        if any(p[2]!=q[2] for p,q in zip(pins,old_pins) if p[0]==mi):
            d=np.array(pair[1][2])-pair[0][2];angle=math.degrees(math.atan2(d[1],d[0]))
            for p in pair:p[4]=angle

    fixed_guard=union_all([Point(r[2]).buffer(10) for r in screws]+[Point(r[2]).buffer(5) for r in pins])
    for pi in range(8):
        ring=LineString(orient(photos[pi],1).exterior.coords)
        for slot in range(4):
            pivot=anchors[pi,slot]+normals[pi,slot]*9.5
            if all_domains.distance(Point(pivot))>=5:continue
            start=ring.project(Point(anchors[pi,slot]));candidates=[]
            for delta in np.arange(-40,40.01,.5):
                d=(start+delta)%ring.length
                a=np.array(ring.interpolate(d).coords[0]);u=np.array(ring.interpolate((d-.05)%ring.length).coords[0]);v=np.array(ring.interpolate((d+.05)%ring.length).coords[0])
                t=(v-u)/np.linalg.norm(v-u);n=np.array([t[1],-t[0]]);p=a+n*9.5
                if all_domains.distance(Point(p))<5.2 or not knot.buffer(-4.6).contains(Point(p)) or fixed_guard.distance(Point(p))<4.6:continue
                if any(np.linalg.norm(p-(anchors[pi,s]+normals[pi,s]*9.5))<25 for s in range(4) if s!=slot):continue
                candidates.append((np.linalg.norm(p-pivot),a,n,p))
            assert candidates,('photo tab',pi,slot)
            dist,a,n,p=min(candidates,key=lambda item:item[0]);anchors[pi,slot]=a;normals[pi,slot]=n
            moves.append(dict(kind='photo_tab',index=pi*4+slot+1,old_xy=pivot.tolist(),new_xy=p.tolist(),distance_mm=float(dist)))
    pivots=(anchors+normals*9.5).reshape(-1,2)
    for w in walls:
        w[0]=owner(w[1])
        protected=affinity.translate(box(-72,-21,72,21),*w[1])
        assert not all_domains.intersects(protected),('wall block',w)
    masks=[];places=[];footprints=[];fabric_bounds=[];photo_ids=[];retainer_ids=[]
    for i,p in enumerate(parts):
        rest=union_all([q for k,q in enumerate(parts) if k!=i])
        mask=p.buffer(.15,join_style=2).difference(rest.buffer(.0375,join_style=2));masks.append(mask)
        # The CAD intersects every lap with the continuous body. Its trimming
        # domain has a 0.1 mm tolerance halo, which is not printable material.
        extensions=[d.intersection(whole).intersection(locate(box(-1,-1000,18,1000),j)) for j,d in zip(js,domains) if j[0]==i]
        env=union_all([p,*extensions]);angle,centre,dims=fit(env)
        assert max(dims)+.3<=253,(i,dims)
        places.append([angle,centre,list(p.representative_point().coords)[0],0])
        footprints.append([dims[0]+.3,dims[1]+.3,16.5 if any(r[1]==i for r in pins) else 13.5])
        stock=union_all([mask,*[d for j,d in zip(js,domains) if j[0]==i]])
        x,y,X,Y=stock.bounds;fabric_bounds.append([[(x-1)/.75,(y-1)/.75],[(X+1)/.75,(Y+1)/.75]])
        photo_ids.append([k for k,q in enumerate(photos) if stock.intersects(q.buffer(4.5))])
        retainer_ids.append([k for k,xy in enumerate(pivots) if owner(xy)==i])
    assert sorted(k for row in retainer_ids for k in row)==list(range(32))
    graph={i:set() for i in range(20)}
    for j in js:graph[j[1]].add(j[0])
    order=[i+1 for i in graphlib.TopologicalSorter(graph).static_order()]
    assert max(d.intersection(e).area for k,d in enumerate(domains) for e in domains[k+1:])<1e-7
    assert union_all(parts).symmetric_difference(whole).area<1e-7
    result=dict(version=1,baseline_cad_sha256=sha(BASE/REL),baseline_project_sha256=sha(BASE/'Dara.3mf'),
                intent='Mirrored short seams, aesthetics first, same tested keyed-lap profiles.',
                parts=[mapping(p) for p in parts],masks=[mapping(p) for p in masks],domains=[mapping(p) for p in domains],
                frame_joints=js,frame_placements=places,frame_print_footprints=footprints,frame_assembly_order=order,
                frame_photos=photo_ids,frame_retainers=retainer_ids,frame_fabric_bounds=fabric_bounds,
                screw_mounts=screws,dowel_mounts=pins,wall_mounts=walls,
                photo_anchors=(anchors/.75).tolist(),photo_normals=normals.tolist(),
                old_screw_mounts=old_screws,old_dowel_mounts=old_pins,hardware_moves=moves,
                min_seam_length_mm=min(j[4] for j in js),max_seam_length_mm=max(j[4] for j in js),
                min_seam_spacing_mm=min(line(j).intersection(whole).distance(line(q).intersection(whole)) for k,j in enumerate(js) for q in js[k+1:]))
    PLAN.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k in ['hardware_moves','frame_assembly_order','min_seam_length_mm','max_seam_length_mm','min_seam_spacing_mm']},indent=2))

def write_cad():
    d=json.loads(PLAN.read_text());s=(BASE/REL).read_text();assert sha(BASE/REL)==d['baseline_cad_sha256']
    for name in ['frame_joints','frame_placements','frame_print_footprints','frame_assembly_order','frame_photos','frame_retainers','frame_fabric_bounds','screw_mounts','dowel_mounts','wall_mounts','photo_anchors','photo_normals']:
        s=replace_array(s,name,d[name])
    s=replace_array(s,'mount_cache_screws',d['screw_mounts']);s=replace_array(s,'mount_cache_dowels',d['dowel_mounts'])
    for i,p in enumerate(d['masks']):s=replace_module(s,f'frame_mask_{i}',shape(p))
    for i,p in enumerate(d['domains'][:31]):s=replace_module(s,f'frame_joint_domain_{i}',shape(p))
    new=serialize('frame_joint_domain_31',affinity.scale(shape(d['domains'][31]),.75,.75,origin=(0,0)))
    s=s.replace('module joint_domain(kind,i) {','module joint_domain(kind,i) {\n    if(kind=="frame" && i==31) frame_joint_domain_31();',1)
    s+='\n'+new+'\n'
    s=s.replace('// Repartitioned from continuous outlines: 31 frame laps + 5 M laps (previously 42 + 5).','// Mirrored short-seam revision: 32 frame laps, 67.3-75.1 mm; 20 frame sections.')
    s=s.replace('// Irregular angled seams, with no grid or four-way seam intersections.','// Left/right and top/bottom mirrored seams with repeated staggering; no crossing laps.')
    s=s.replace('// Largest native footprint: F6, 252.392 x 252.470 mm; minimum placed edge clearance 1.758 mm.','// Native print footprints and fit checks are recorded in working/review/mirrored-joints/.')
    s=s.replace('// No neighboring pair can be combined into one 253 mm piece, including retained lap extensions.','// Existing artwork, backer outlines, tested lap profiles and wall blocks are preserved.')
    s=s.replace('// Partition search minimizes joints first, then pieces; no claim of a proven global minimum.','// Priority: intentional visible seam pattern, then assembly/strength and bed fit.')
    s=s.replace('joint_index = 1; // [1:31]','joint_index = 1; // [1:32]')
    s=s.replace('fast_preview = true;','fast_preview = false;',1)
    CAD.write_text(s)
    print('Wrote CAD with 20 sections / 32 short joints.')

def export():
    out=WORK/'native';out.mkdir(exist_ok=True)
    exe=Path(r'C:\Program Files (x86)\OpenSCAD\openscad.exe')
    source_hash=sha(CAD);manifest=json.loads((BASE/'working/stl/Dara-Photo-Frame-A1-Jointed/manifest.json').read_text())
    def job(name):
        file=out/(name+'.stl');log=out/(name+'.log');family='frame' if name[0]=='F' else 'M'
        marker=out/(name+'.source.json')
        if not (file.exists() and marker.exists() and json.loads(marker.read_text()).get('source_sha256')==source_hash):
            cmd=[str(exe),'--hardwarnings','--export-format=binstl','--camera=0,0,0,0,0,0,700','-o',str(file),'-D','fast_preview=false','-D','view_mode="section"','-D',f'part_family="{family}"','-D',f'section_index={int(name[1:])}',str(CAD)]
            t=time.monotonic();p=subprocess.run(cmd,capture_output=True,text=True,timeout=1500)
            log.write_text(p.stdout+p.stderr)
            assert p.returncode==0 and 'WARNING:' not in log.read_text() and 'ERROR:' not in log.read_text(),name
            print(name,'rendered',round(time.monotonic()-t,1),'s',flush=True)
        proof=verify(file);assert sha(CAD)==source_hash
        marker.write_text(json.dumps(dict(source_sha256=source_hash,**proof),indent=2))
        return name,proof
    names=[f'F{i}' for i in range(1,21)]+[f'M{i}' for i in range(1,7)]
    with ThreadPoolExecutor(max_workers=3) as pool:records=dict(pool.map(job,names))
    for r in manifest['parts']:
        if r['part'] in records:
            shutil.copy2(out/r['file'],STLS/r['file']);r.update(records[r['part']])
    manifest.update(source_sha256=source_hash,revision='Mirrored short seams; historical flat M has revised rear attachments. Production hammered M is in Dara.3mf.')
    (STLS/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (REVIEW/'native-export.json').write_text(json.dumps(dict(source_sha256=source_hash,parts=records),indent=2)+'\n')

def refresh_cache():
    import trimesh
    cad=CAD.read_text();proof=json.loads((REVIEW/'native-export.json').read_text())
    assert sha(CAD)==proof['source_sha256'],'Refresh only immediately after the native export.'
    for family,count,prefix in [('frame',20,'F'),('M',6,'M')]:
        for i in range(count):
            mesh=trimesh.load_mesh(STLS/f'{prefix}{i+1}.stl')
            body=(f'module preview_{family}_{i}() {{\n polyhedron(points='+json.dumps(np.round(mesh.vertices,7).tolist(),separators=(',',':'))+',\n faces='+json.dumps(mesh.faces[:,::-1].tolist(),separators=(',',':'))+',convexity=50);\n}')
            cad,n=re.subn(r'module preview_'+family+'_'+str(i)+r'\(\) \{.*?\n\}',lambda _:body,cad,flags=re.S);assert n==1
    dims=[proof['parts'][f'F{i+1}']['size_mm'] for i in range(20)]
    cad=replace_array(cad,'frame_print_footprints',dims)
    cad=cad.replace('fast_preview = false; // Exact embedded default-shape preview; F6 always evaluates the CAD.','fast_preview = true; // Exact embedded preview refreshed from verified native sections.')
    CAD.write_text(cad)
    manifest=json.loads((STLS/'manifest.json').read_text());manifest['source_sha256']=sha(CAD)
    (STLS/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    proof['native_geometry_source_sha256']=proof['source_sha256'];proof['source_sha256']=sha(CAD)
    proof['post_export_changes']='Preview meshes, measured print footprint metadata and preview toggle only.'
    (REVIEW/'native-export.json').write_text(json.dumps(proof,indent=2)+'\n')
    print('Preview cache and measured footprints refreshed.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['plan','cad','export','cache']);args=p.parse_args()
    {'plan':plan,'cad':write_cad,'export':export,'cache':refresh_cache}[args.action]()
