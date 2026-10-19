"""Production A2L build from continuous artwork and the approved fresh partitions.

Commands: plan, frame, M, package. See validate_a2l_project.py for release gates.
Cached meshes are bound to the production-plan hash; no A1 section meshes are merged.
"""
import argparse, copy, hashlib, json, math, os, shutil, sys, zipfile
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
import shapely
import manifold3d as mf
import trimesh
from scipy.spatial import cKDTree
from shapely import affinity, union_all
from shapely.geometry import Point, LineString, Polygon, box, shape, mapping
from shapely.ops import nearest_points
from development_3mf import *
from build_jointed_bambu_project import read_array
from add_blue_ribbon_edge import artwork, section
from develop_m_veneer import prism, mesh, solid, axes, locate, xz_prism, profile, key, height_mesh, texture, skin_bottom, top_section
from analyze_a2l_partitions import fit
from develop_cosmetic_joints import refine_pair

OUT=ROOT/'working/bambu/Dara-Photo-Frame-A2L'
WORK=ROOT/'.work/a2l-production'
PLAN=OUT/'production-plan.json'
CAD=ROOT/'working/Dara-Photo-Frame-A1-Jointed.scad'
PROFILE=Path(os.environ.get('DARA_BAMBU_PROFILE_DIR',str(Path.home()/'Library/Application Support/BambuStudio/system/BBL')))
EDIT=OUT/'Dara-A2L-Editable.3mf'
FINAL=OUT/'Dara-A2L-Complete.3mf'

def load_plan():return json.loads(PLAN.read_text())
def cache(name,m):
    assert m.is_volume,name
    m.export(WORK/(name+'.stl'))
    np.savez_compressed(WORK/(name+'.npz'),vertices=m.vertices,faces=m.faces)
    save_json(WORK/(name+'.cache.json'),dict(production_plan_sha256=sha(PLAN),mesh_cache_sha256=sha(WORK/(name+'.npz'))))
def cached(name):
    proof=json.loads((WORK/(name+'.cache.json')).read_text())
    assert proof['production_plan_sha256']==sha(PLAN),'Regenerate meshes after changing the A2L plan'
    assert proof['mesh_cache_sha256']==sha(WORK/(name+'.npz')),'Mesh cache changed; regenerate it'
    a=np.load(WORK/(name+'.npz'));return trimesh.Trimesh(a['vertices'],a['faces'],process=False)
def clean(body,label):
    material=[q for q in body.decompose() if abs(q.volume())>1e-7]
    assert len(material)==1,(label,[(q.volume(),q.bounding_box()) for q in material])
    return mesh(material[0])
def joint_record(row):
    return [row['tongue']-1,row['socket']-1,row['xy_mm'],row['normal_deg'],row['length'],[-row['length']/3,row['length']/3]]
def domain(j,whole,pad=22):return whole.intersection(locate(box(-1.5,-j[4]/2-pad,20,j[4]/2+pad),j)).buffer(.00001)
def owner(parts,xy):
    ids=[i for i,p in enumerate(parts) if p.buffer(1e-6).covers(Point(xy))];assert len(ids)==1,(xy,ids)
    return ids[0]
def save(path,d):save_json(path,d)

def plan():
    OUT.mkdir(parents=True,exist_ok=True);WORK.mkdir(parents=True,exist_ok=True)
    cad=CAD.read_text();study=json.loads((ROOT/'working/review/a2l-hidden-joints/lean-candidate.json').read_text())
    ms=json.loads((ROOT/'working/review/a2l-m-joints/evaluation.json').read_text())
    K=artwork(cad,'knot_outline');M=artwork(cad,'letter_outline');F=artwork(cad,'fabric_outline').buffer(.1125,join_style=2);whole=K.union(F)
    parts=[shape(g) for g in study['parts']];cp=[shape(r['keyed_footprint']) for r in ms['a2l']['core']['parts']]
    cr=[shape(r['region']) for r in ms['a2l']['core']['parts']];vp=[shape(r['region']) for r in ms['a2l']['veneer']['parts']]
    js=[joint_record(r) for r in study['joints']];domains=[domain(j,parts[j[0]].union(parts[j[1]]),r['padding_mm']) for j,r in zip(js,study['joints'])];allD=union_all(domains)
    cs=union_all([shape(r['line']) for r in ms['a2l']['core']['seams']])
    screws=read_array(cad,'screw_mounts');old=copy.deepcopy(screws);moves=[];occupied=[]
    # Keep holes away from every frame lap and full-thickness M key/pocket.
    guards=allD.buffer(9).union(cs.buffer(9))
    for k,row in enumerate(screws):
        q=Point(row[2]);safe=K.buffer(-8.5).intersection(M.buffer(-7)).difference(guards)
        if occupied:safe=safe.difference(union_all(occupied))
        assert not safe.is_empty
        p=q if safe.covers(q) else nearest_points(q,safe.buffer(-.05))[1]
        xy=list(p.coords[0]);row[:]=[owner(cr,xy),owner(parts,xy),xy];occupied.append(p.buffer(18))
        moves.append(dict(kind='M screw',index=k+1,old_xy_mm=old[k][2],xy_mm=xy,moved_mm=p.distance(q)))
    # Two locators per NEW core: one round datum and one axial relief slot.
    # Reusing historical six pairs on four cores would overconstrain seating.
    pins=[];oldpins=read_array(cad,'dowel_mounts')
    for ci,c in enumerate(cp):
        safe=c.buffer(-5).intersection(K.buffer(-4)).difference(allD.buffer(5)).difference(cs.buffer(6))
        safe=safe.difference(union_all([Point(r[2]).buffer(13) for r in screws]))
        x,y,X,Y=safe.bounds
        grid=np.array([(a,b) for a in np.arange(x,X,2) for b in np.arange(y,Y,2)])
        pts=grid[shapely.contains(safe,shapely.points(grid))];assert len(pts)>2,ci
        # Favor historical locations where they fit; then maximize baseline.
        targets=[np.array(r[2]) for r in oldpins if c.covers(Point(r[2]))]
        p0=pts[np.argmin(np.linalg.norm(pts-(targets[0] if targets else np.array(c.representative_point().coords[0])),axis=1))]
        p1=pts[np.argmax(np.linalg.norm(pts-p0,axis=1))];angle=math.degrees(math.atan2(*(p1-p0)[::-1]))
        assert np.linalg.norm(p1-p0)>25
        for sec,p in enumerate([p0,p1]):pins.append([ci,owner(parts,p),p.tolist(),sec,angle])
    walls=read_array(cad,'wall_mounts')
    for w,r in zip(walls,study['wall_mount_candidates']):
        w[0]=r['section']-1;w[1]=r['candidate_xy_mm']
        sites=union_all([affinity.translate(box(-10.5,-5.5,10.5,5.5),w[1][0]+x,w[1][1]+w[2]) for x in w[3]]+[Point(np.array(w[1])+[x,w[4]]).buffer(3.6) for x in w[5]])
        assert allD.distance(sites)>1.99
    photos=[artwork(cad,f'photo_loop_{i}') for i in range(1,9)]
    anchors=np.array(read_array(cad,'photo_anchors'))*.75;normals=np.array(read_array(cad,'photo_normals'))
    for pi in range(8):
        ring=LineString(photos[pi].exterior.coords)
        for slot in range(4):
            pivot=anchors[pi,slot]+normals[pi,slot]*9.5
            if allD.distance(Point(pivot))>=5:continue
            start=ring.project(Point(anchors[pi,slot]));options=[]
            for delta in np.arange(-60,60.1,.5):
                s=(start+delta)%ring.length;a=np.array(ring.interpolate(s).coords[0])
                t=np.array(ring.interpolate((s+.05)%ring.length).coords[0])-np.array(ring.interpolate((s-.05)%ring.length).coords[0]);t/=np.linalg.norm(t)
                for sign in [-1,1]:
                    n=np.array([t[1],-t[0]])*sign;p=a+n*9.5
                    if allD.distance(Point(p))<5.2 or not K.buffer(-4.6).contains(Point(p)):continue
                    if min(Point(p).distance(Point(r[2])) for r in screws+pins)<14:continue
                    if any(np.linalg.norm(p-(anchors[pi,s]+normals[pi,s]*9.5))<25 for s in range(4) if s!=slot):continue
                    options.append((np.linalg.norm(p-pivot),a,n,p))
            assert options,('photo pilot',pi,slot)
            dist,a,n,p=min(options,key=lambda o:o[0]);anchors[pi,slot]=a;normals[pi,slot]=n
            moves.append(dict(kind='photo pilot',index=pi*4+slot+1,old_xy_mm=pivot.tolist(),xy_mm=p.tolist(),moved_mm=float(dist)))
    visibility=[]
    for i,row in enumerate(study['joints']):
        l=shape(row['line']);visibility.append(dict(joint=i+1,exposed_mm=l.difference(M).length,
            fully_hidden=l.difference(M.buffer(-2)).length<.001,front_margin_mm=l.distance(M.boundary) if M.covers(l) else 0))
    assert sum(r['fully_hidden'] for r in visibility)==6
    result=dict(machine='Bambu Lab A2L 0.4 nozzle',bed_mm=[330,320,325],layer_height_mm=.2,body_infill='8% gyroid',veneer_infill='100%',
        cad_sha256=sha(CAD),knot_study_sha256=sha(ROOT/'working/review/a2l-hidden-joints/lean-candidate.json'),
        M_study_sha256=sha(ROOT/'working/review/a2l-m-joints/evaluation.json'),parts=[mapping(p) for p in parts],frame_joints=js,
        domains=[mapping(d) for d in domains],frame_fits=study['part_fits'],frame_assembly_order=study['assembly_order'],
        core_regions=[mapping(p) for p in cr],core_footprints=[mapping(p) for p in cp],core_fits=[r['fit'] for r in ms['a2l']['core']['parts']],
        core_seams=ms['a2l']['core']['seams'],core_keys=ms['a2l']['core']['keys'],skin_regions=[mapping(p) for p in vp],skin_seams=ms['a2l']['veneer']['seams'],
        veneer_rotation=ms['a2l_veneer_rotation'],screw_mounts=screws,dowel_mounts=pins,wall_mounts=walls,
        photo_anchors_mm=anchors.tolist(),photo_normals=normals.tolist(),hardware_moves=moves,band_free_M_visibility=visibility,
        core_plate_groups=([[1],[2],[3],[4,5]] if len(cr)==5 else [[i+1] for i in range(len(cr))]),
        M_layout_revision=ms.get('M_layout_revision'),
        counts=dict(knot_sections=10,knot_joints=14,fully_hidden_knot_joints=6,partly_covered_knot_joints=2,fully_exposed_knot_joints=6,M_cores=len(cr),M_core_joints=len(ms['a2l']['core']['seams']),M_veneers=3,visible_M_seams=2))
    save(PLAN,result);print('A2L plan: coordinated mounts; 10 frame, 4 core, 3 veneer parts',flush=True)

def prism(g,bottom,top):
    g=shapely.set_precision(g,1e-7)
    if g.is_empty:return mf.Manifold()
    b=section(g).extrude(top-bottom).translate([0,0,bottom])
    assert b.status()==mf.Error.NoError,('Prism failure',g.geom_type,g.is_valid,g.area)
    return b

def cylinder(xy,r,z0,z1):return mf.Manifold.cylinder(z1-z0,r,circular_segments=64).translate([*xy,z0])
def frame():
    p=load_plan();cad=CAD.read_text();K=artwork(cad,'knot_outline');F=artwork(cad,'fabric_outline').buffer(.1125,join_style=2)
    parts=[shape(g) for g in p['parts']];domains=[shape(g) for g in p['domains']];joints=p['frame_joints']
    photos=[artwork(cad,f'photo_loop_{i}') for i in range(1,9)]
    rabbet=union_all([g.buffer(4,join_style=2) for g in photos]);pivots=(np.array(p['photo_anchors_mm'])+np.array(p['photo_normals'])*9.5).reshape(-1,2)
    # The source weave has 6 mm pitch, 1.5 mm threads, alternating 3.3 mm caps.
    entries=[];proof=[]
    for i,region in enumerate(parts):
        env=region.union(union_all([domains[k] for k,j in enumerate(joints) if j[0]==i]));kf=K.intersection(env);ff=F.intersection(env)
        x,y,X,Y=ff.bounds;xx=np.arange(math.floor(x/6)-1,math.ceil(X/6)+2)*6;yy=np.arange(math.floor(y/6)-1,math.ceil(Y/6)+2)*6
        pattern=union_all([box(a-.75,y-1,a+.75,Y+1) for a in xx]+[box(x-1,b-.75,X+1,b+.75) for b in yy]).intersection(ff)
        caps=union_all([box(a-(1.65 if (round(a/6)+round(b/6))%2==0 else .75),b-(.75 if (round(a/6)+round(b/6))%2==0 else 1.65),a+(1.65 if (round(a/6)+round(b/6))%2==0 else .75),b+(.75 if (round(a/6)+round(b/6))%2==0 else 1.65)) for a in xx for b in yy]).intersection(pattern)
        body=prism(kf,0,13.5)+prism(ff,0,9)+prism(pattern,8.99,9.6)+prism(caps,9.5985,9.9)
        body-=prism(rabbet.intersection(env.buffer(1)),-.02,2.4)
        for q in pivots:
            if env.covers(Point(q)):body-=cylinder(q,3.175/2,-.02,10.7)
        # Closing faces have zero nominal clearance above Z8; old lower joint
        # clearance is retained below that cosmetic wall.
        mask=prism(region,-.1,25)
        for k,j in enumerate(joints):
            if j[0]!=i:continue
            ext=(xz_prism(profile(cad,'tested_tongue_xz'),j)+key(j,j[5][0])+key(j,j[5][1]))^prism(domains[k],-.1,7)
            mask+=ext
        body^=mask
        for k,j in enumerate(joints):
            if j[1]!=i:continue
            tool=(xz_prism(profile(cad,'tested_socket_void_xz'),j)+key(j,j[5][0],True)+key(j,j[5][1],True))^prism(domains[k],-.1,7)
            body-=tool
        entries.append([dict(mesh=clean(body,f'F{i+1}'))]);print(f'F{i+1} continuous artwork built',flush=True)
    for k,j in enumerate(joints):
        pair,r=refine_pair(entries[j[0]],entries[j[1]],j,gap=0,seating_pads=False)
        entries[j[0]],entries[j[1]]=pair;proof.append(dict(joint=k+1,**r));print(f'J{k+1} seating and adhesive relief built',flush=True)
    for i,es in enumerate(entries):
        b=solid(es[0]['mesh'])
        for _,fi,xy in p['screw_mounts']:
            if fi==i:b-=cylinder(xy,6,-.02,9.5)+cylinder(xy,2,9.49,13.52)
        for _,fi,xy,sec,angle in p['dowel_mounts']:
            if fi==i:b+=cylinder(xy,2,13.48,16)+mf.Manifold.cylinder(.5,2,1.7,circular_segments=64).translate([*xy,16])
        for w in p['wall_mounts']:
            if w[0]!=i:continue
            for x in w[3]:
                xy=np.array(w[1])+[x,w[2]]
                rr=box(-9,-4,9,4).buffer(1.2,quad_segs=12)
                b-=prism(affinity.translate(rr,*xy),-.02,3.3)
                mouth=box(-9,-4,9,4).buffer(1.5,quad_segs=12);b-=prism(affinity.translate(mouth,*xy),-.02,.45)
            for x in w[5]:b-=cylinder(np.array(w[1])+[x,w[4]],3.175/2,-.02,10.7)
        m=clean(b,f'F{i+1} mounted');cache(f'F{i+1}',m)
        # Color masks intersect the finished model, preserving all glue/key cuts.
        wood=prism(F.intersection(parts[i].buffer(.001)),8.4,9.9)^b
        blue=((F.buffer(2.75)-F.buffer(1.25)).intersection(K)).simplify(.001,preserve_topology=True)
        accent=prism(blue.intersection(parts[i]),12.9,13.5)^b
        cache(f'F{i+1}-wood',mesh(wood));cache(f'F{i+1}-blue',mesh(accent))
    save(OUT/'frame-geometry-validation.json',dict(joints=proof,zero_cosmetic_gap_above_z_mm=8,assembly_order=p['frame_assembly_order'],
        continuous_artwork=True,weave_pitch_mm=6,source_cad_sha256=sha(CAD),production_plan_sha256=sha(PLAN),physical_confirmation_pending=True))

def build_M():
    p=load_plan();outline=artwork(CAD.read_text(),'letter_outline');roof=texture(outline)
    cp=[shape(g) for g in p['core_footprints']];vp=[shape(g) for g in p['skin_regions']];screws=p['screw_mounts'];pins=p['dowel_mounts']
    cores=[];skins=[];records=[]
    for i,g in enumerate(cp):
        b=prism(g,0,8.4)
        for ci,fi,xy in screws:
            if ci==i:b-=cylinder(xy,3.175/2,-.02,8.72)
        for ci,fi,xy,sec,angle in pins:
            if ci!=i:continue
            hole=LineString([(-.4,0),(.4,0)]).buffer(2.1,quad_segs=16) if sec else Point(0,0).buffer(2.1,quad_segs=16)
            hole=affinity.translate(affinity.rotate(hole,angle,origin=(0,0)),*xy)
            b-=prism(hole,-.02,3.3);b-=cylinder(xy,2.4,-.02,.3)
        cores.append(b)
    seats=[top_section(b).buffer(-2.6) for b in cores];cs=union_all([shape(g['line']) for g in p['core_seams']]);hardware=union_all([Point(r[2]).buffer(7) for r in screws+pins])
    for i,region in enumerate(vp):
        v,stats=height_mesh(region,skin_bottom,roof);b=solid(v)
        for r in screws:b-=cylinder(r[2],2.1,8.39,9.1)
        safe=region.buffer(-5).difference(cs.buffer(8)).difference(hardware).intersection(union_all(seats)).intersection(outline.buffer(-20))
        x,y,X,Y=safe.bounds;grid=np.array([(a,b) for a in np.arange(x,X,4) for b in np.arange(y,Y,4)]);points=grid[shapely.contains(safe,shapely.points(grid))];assert len(points)>3
        q0=points[np.argmin(np.linalg.norm(points-np.array(region.centroid.coords[0]),axis=1))];q1=points[np.argmax(np.linalg.norm(points-q0,axis=1))];d=q1-q0;delta=points-q0;q2=points[np.argmax(abs(d[0]*delta[:,1]-d[1]*delta[:,0]))];angle=math.degrees(math.atan2(d[1],d[0]));anchors=[]
        for k,q in enumerate([q0,q1,q2]):
            ci=next(j for j,s in enumerate(seats) if s.covers(Point(q)));cores[ci]+=cylinder(q,2.5,8.35,8.6)
            if k<2:
                cores[ci]+=cylinder(q,1.2,8.55,9.0)
                pocket=LineString([(-.4,0),(.4,0)]).buffer(1.35,quad_segs=12) if k else Point(0,0).buffer(1.35,quad_segs=12)
                pocket=affinity.translate(affinity.rotate(pocket,angle,origin=(0,0)),*q);b-=prism(pocket,8.5,9.1)
            anchors.append(dict(xy_mm=q.tolist(),core=ci+1,role=['primary_round','secondary_slot','seat_only'][k]))
        skins.append(b);records.append(dict(name=f'V{i+1}',anchors=anchors,**stats));cache(f'V{i+1}-raw',mesh(b))
    collision=max([(a^b).volume() for i,a in enumerate(cores+skins) for b in (cores+skins)[:i]])
    assert collision<.001,collision
    for i,b in enumerate(cores):cache(f'C{i+1}',clean(b,f'C{i+1}'))
    # Re-express assembly in the common preturned plane. The established fin
    # generator then follows the rising axis without changing texture phase.
    from veneer_fin_carrier import fin_carrier
    import plan_veneer_fins as planner
    pre=z_rotation(90);rot=common_m_rotation();fullR=np.array(p['veneer_rotation']);assert np.allclose(rot@pre,fullR)
    for i,(b,region) in enumerate(zip(skins,vp)):
        raw=mesh(b);pose=centered(raw,fullR,z=2.4,xy=(165,160));records[i]['assembly_to_printer']=pose.tolist()
        local=raw.copy();T=np.eye(4);T[:3,:3]=pre;local.apply_transform(T)
        rg=affinity.rotate(region,90,origin=(0,0));ex=union_all([Point(a['xy_mm']).buffer(7) for a in records[i]['anchors']]).union(hardware)
        ex=affinity.rotate(ex,90,origin=(0,0));toolpose=pose.copy();toolpose[:3,:3]=rot
        carried,evidence=fin_carrier(local,rg,skin_bottom,toolpose,ex,height_mesh,bed=(330,320),height=325,force_guard=True)
        # Independent audit of the actual generated contact allocation.
        oldsample=planner.SAMPLE;planner.SAMPLE=.75
        xy,weights,allowance=planner.area_samples(rg)
        rows=[dict(contacts=np.array(r['contacts_xy_mm'])) for r in evidence['fins']]
        starter=shape(evidence['starter_contact_region'])
        fine=planner.coverage(rows,xy,weights,allowance,shapely.distance(shapely.points(xy),starter));planner.SAMPLE=oldsample
        limits=evidence['area_coverage']['trial_geometric_limits']
        assert fine['area_outside_distance_limit_mm2']<1e-6
        assert fine['maximum_area_per_bond_mm2']<=limits['maximum_rear_area_per_bond_mm2']+1e-6
        assert fine['maximum_tributary_width_mm']<=limits['maximum_tributary_width_mm']+1e-6
        evidence['independent_fine_grid']=fine;evidence['contact_coordinate_basis']='assembly rotated 90 degrees about Z before 55 degree lean'
        records[i]['carrier']=evidence;cache(f'V{i+1}',carried)
        print(f'V{i+1}: {evidence["fin_count"]} area-allocated fins; {len(carried.faces)} triangles',flush=True)
    # Compare every seam's actual front vertex coordinates; not bounding boxes.
    seamchecks=[]
    for seam in p['skin_seams']:
        line=shape(seam['line']);ends=[]
        for k in seam['parts']:
            m=cached(f'V{k}-raw');v=m.vertices;sel=(shapely.distance(shapely.points(v[:,:2]),line)<1e-6)&(v[:,2]>10.4);ends.append(v[sel])
        error=max(cKDTree(ends[0]).query(ends[1])[0].max(),cKDTree(ends[1]).query(ends[0])[0].max());assert error<1e-6,error
        seamchecks.append(dict(parts=seam['parts'],front_vertex_error_mm=float(error),visible_length_mm=seam['length_mm']))
    save(OUT/'M-geometry-validation.json',dict(production_plan_sha256=sha(PLAN),core_flat_top_mm=8.4,veneer_flat_back_mm=8.6,glue_gap_mm=.2,cosmetic_gap_mm=0,
        all_convex_crown_in_veneer=True,maximum_finished_local_z_mm=12.7,core_veneer_interference_mm3=collision,seamchecks=seamchecks,
        skins=records,common_complete_rotation=fullR.tolist(),show_plane_parallel_to_bed_Y=bool(abs(fullR[1,2])<1e-8),physical_confirmation_pending=True))


def resolved_profile(kind,name):
    path=PROFILE/kind/(name+'.json');d=json.loads(path.read_text());out={}
    if d.get('inherits'):out.update(resolved_profile(kind,d['inherits']))
    for include in d.get('include',[]):out.update(resolved_profile(kind,include))
    out.update({k:v for k,v in d.items() if k not in ['inherits','include','name','type','from','instantiation','description','compatible_printers','setting_id']})
    return out

def settings():
    s=json.loads(source()['Metadata/project_settings.config']);machine=resolved_profile('machine','Bambu Lab A2L 0.4 nozzle');process=resolved_profile('process','0.20mm Standard @BBL A2L')
    s.update(machine);s.update(process)
    fil=[resolved_profile('filament',name) for name in ['Generic PLA @BBL A2L','Generic PLA @BBL A2L','Generic PLA Silk @BBL A2L','Generic PLA @BBL A2L']]
    for k in set().union(*(f.keys() for f in fil)):
        values=[f.get(k) for f in fil]
        if all(isinstance(v,list) and len(v)==1 for v in values):s[k]=[v[0] for v in values]
    s.update(printer_settings_id='Bambu Lab A2L 0.4 nozzle',printer_model='Bambu Lab A2L',printer_variant='0.4',
        print_settings_id='Dara A2L - 8% gyroid - cosmetic zero-gap',print_compatible_printers=['Bambu Lab A2L 0.4 nozzle'],filament_settings_id=['Generic PLA @BBL A2L','Generic PLA @BBL A2L','Generic PLA Silk @BBL A2L','Generic PLA @BBL A2L'],
        filament_colour=['#FFFFFF','#C2AB84','#B87333','#295D8A'],layer_height='0.2',wall_loops='4',top_shell_layers='5',bottom_shell_layers='5',
        sparse_infill_density='8%',sparse_infill_pattern='gyroid',print_sequence='by layer',enable_prime_tower='1',prime_tower_width='30',prime_tower_rib_wall='0',
        curr_bed_type='Textured PEI Plate',brim_width='1',brim_type='outer_only',enable_arc_fitting='0',bed_exclude_area=[],
        enable_support='0',support_type='tree(auto)',support_style='default',support_on_build_plate_only='1',support_top_z_distance='0.2',raft_first_layer_expansion='0')
    # Preserve established conservative appearance/flow settings on these colors.
    s['textured_plate_temp']=['65','65','55','65'];s['textured_plate_temp_initial_layer']=s['textured_plate_temp']
    s['filament_max_volumetric_speed']=['12','12','7.5','7.5']
    return s

def reinforcement(xy,r=7,height=17):return dict(mesh=mesh(cylinder(xy,r,0,height)),subtype='modifier_part',settings=dict(sparse_infill_density='100%',name='Local solid screw reinforcement'))
def n9_knot_volumes(m,T):
    """Honor Studio's forced N9 tower Y without introducing physical seams.

    Partition only the model representation around the empty tower envelope.
    Same-material volumes in the same object are unioned by the slicer.
    The boolean union is required to equal the original printable solid.
    """
    body=solid(m).transform(T[:3,:]);rings=body.project().to_polygons()
    projection=shapely.build_area(union_all([LineString(np.vstack([r,r[0]])) for r in rings]))
    choices=[]
    for x in range(15,286):
        rect=box(x-3,157,x+33,197);choices.append((projection.distance(rect),x,rect))
    gap,x,rect=max(choices,key=lambda r:r[0]);assert gap>8.5,('No fixed-Y tower clearance',gap)
    x0,y0,x1,y1=rect.buffer(8.5,join_style=2).bounds
    regions=[(-2000,-2000,x0,2000),(x1,-2000,2000,2000),(x0,-2000,x1,y0),(x0,y1,x1,2000)]
    pieces=[];world=[]
    for a,b,c,d in regions:
        piece=body ^ mf.Manifold.cube([c-a,d-b,100]).translate([a,b,-1])
        if piece.volume()<1e-7:continue
        for connected in piece.decompose():
            if connected.volume()<1e-7:continue
            world.append(connected);pieces.append(dict(mesh=mesh(connected.transform(np.linalg.inv(T)[:3,:])),settings=dict(name='Continuous knot volume')))
    combined=mf.Manifold.batch_boolean(world,mf.OpType.Add)
    removed=(body-combined).volume();added=(combined-body).volume()
    assert abs(removed)<1e-5 and abs(added)<1e-5,(removed,added)
    hulls=[Polygon(mesh(piece).vertices[:,:2]).convex_hull for piece in world]
    assert min(g.distance(rect) for g in hulls)>8
    return pieces,dict(anchor_xy_mm=[x,160],reserved_envelope_mm=list(rect.bounds),
        physical_projection_gap_mm=gap,model_volume_convex_hull_gap_mm=min(g.distance(rect) for g in hulls),
        model_convex_hulls=[mapping(g) for g in hulls],model_volume_count=len(pieces),
        original_volume_mm3=body.volume(),removed_volume_mm3=removed,added_volume_mm3=added,
        same_material_volumes_in_one_object=True,no_new_physical_joints=True)

def package():
    if load_plan().get('M_layout_revision') and EDIT.exists():
        from repartition_a2l_M import package_M
        return package_M()
    p=load_plan();mp=json.loads((OUT/'M-geometry-validation.json').read_text());plates=[];tower_rows=[]
    anchors=(np.array(p['photo_anchors_mm'])+np.array(p['photo_normals'])*9.5).reshape(-1,2)
    for i in range(10):
        m=cached(f'F{i+1}');yaw=p['frame_fits'][i]['rotation_deg'] if 'rotation_deg' in p['frame_fits'][i] else p['frame_fits'][i]['angle_deg']
        T=centered(m,z_rotation(yaw),xy=(165,160));volumes,tower=n9_knot_volumes(m,T);tower_rows.append(dict(plate=i+1,**tower))
        parts=volumes+[dict(mesh=cached(f'F{i+1}-wood'),subtype='modifier_part',settings=dict(extruder='2')),dict(mesh=cached(f'F{i+1}-blue'),subtype='modifier_part',settings=dict(extruder='4'))]
        for ci,fi,xy in p['screw_mounts']:
            if fi==i:parts.append(reinforcement(xy,8))
        for xy in anchors:
            if shape(p['parts'][i]).covers(Point(xy)):parts.append(reinforcement(xy))
        for w in p['wall_mounts']:
            if w[0]==i:
                for x in w[5]:parts.append(reinforcement(np.array(w[1])+[x,w[4]]))
        plates.append([dict(name=f'F{i+1} A2L knot',parts=parts,transform=T,
            settings=dict(extruder='1',enable_support='1',infill_direction=str((45+yaw)%180),brim_width='1'))])
    from repartition_a2l_M import core_plates
    plates.extend(core_plates(p))
    for i in range(3):
        plates.append([dict(name=f'V{i+1} A2L hammered veneer and sacrificial fins',parts=[dict(mesh=cached(f'V{i+1}'))],transform=np.eye(4),block_front=True,front_normal=np.array(p['veneer_rotation'])[:,2],
            settings=dict(extruder='3',enable_support='1',sparse_infill_density='100%',brim_width='0',tree_support_branch_angle='30',support_critical_regions_only='0',
                outer_wall_speed='40',inner_wall_speed='80',default_acceleration='1500',travel_acceleration='2500'))])
    # Unchanged photo backers and block meshes: only wall block center moved,
    # its mating pattern stayed identical. Retainers are universal.
    files=source();cfg=ET.fromstring(files['Metadata/model_settings.config']);hardware={}
    for co in cfg.findall('object'):
        name=props(co).get('name','')
        if name.startswith('Backer') or name in ['B1','B2','B3','B4','Retainer']:hardware[name]=co.get('id')
    for group in [[3,1,5,7],[4,2,6,8]]:
        objects=[]
        for corner,k in enumerate(group):
            name=f'Backer{k}';parts,st=read_object(files,hardware[name]);m=parts[0]['mesh'];low,high=m.bounds[:,:2]
            t=np.eye(4);t[2,3]=-m.bounds[0,2];t[:2,3]=[330-3-high[0] if corner&1 else 3-low[0],320-3-high[1] if corner&2 else 3-low[1]]
            objects.append(dict(name=name,parts=parts,transform=t,settings=dict(extruder='1',brim_width='0',enable_support='0')))
        plates.append(objects)
    objects=[]
    for k in range(1,5):
        parts,st=read_object(files,hardware[f'B{k}']);objects.append(dict(name=f'B{k} A2L wall block',parts=parts,transform=centered(parts[0]['mesh'],xy=(90,48+55*(k-1))),settings=dict(extruder='1',enable_support='1',support_on_build_plate_only='0',brim_width='1')))
    ret=hardware.get('Retainer') or next(co.get('id') for co in cfg.findall('object') if 'Retainer' in props(co).get('name',''))
    for k in range(32):
        parts,st=read_object(files,ret);objects.append(dict(name=f'R{k+1} photo retainer',parts=parts,transform=centered(parts[0]['mesh'],xy=(205+(k%4)*26,40+(k//4)*22)),settings=dict(extruder='1',enable_support='0',brim_width='0')))
    plates.append(objects)
    ss=settings()
    ss.update(wipe_tower_x=[str(r['anchor_xy_mm'][0]) for r in tower_rows]+['15']*10,
        wipe_tower_y=['160']*20,prime_tower_brim_width='2')
    save(OUT/'tower-placement.json',dict(method='A2L N9 forced Y160; exact union of adjoining same-material model volumes',
        minimum_reserved_gap_mm=8,plates=tower_rows,
        rule_source='https://github.com/bambulab/BambuStudio/blob/v02.08.02.61/src/slic3r/GUI/PartPlate.cpp',
        rule_function='PartPlateList::set_default_wipe_tower_pos_for_plate',
        actual_native_footprint_check_required=True,GUI_overrides_previous_corner_positions=True))
    records=write_project(EDIT,plates,'Dara A2L complete - 14 knot joints - flat core M',settings_update=ss)
    save(OUT/'plate-plan.json',dict(plates=len(plates),records=records,production_plan_sha256=sha(PLAN),editable_sha256=sha(EDIT)))
    print(f'Packaged {len(plates)} A2L plates',flush=True)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('action',choices=['plan','frame','M','package']);args=a.parse_args();{'plan':plan,'frame':frame,'M':build_M,'package':package}[args.action]()
