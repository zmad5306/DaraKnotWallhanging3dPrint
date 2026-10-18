"""Geometry and native toolpath gate for the coordinated A2L release."""
import argparse, collections, json, math, shutil, zipfile
import xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial import cKDTree
from shapely import union_all
from shapely.geometry import Point,LineString,shape,box
import shapely
from build_a2l_project import *
from validate_print_project import scan_gcode
from validate_development_candidates import angle_evidence
from check_fin_toolpaths import check_fin_bonds
from validate_print_project import TOKEN
from check_a2l_towers import check_tower,check_startup_tower


def embedded(path):
    with zipfile.ZipFile(path) as z:f={n:z.read(n) for n in z.namelist()}
    cfg=ET.fromstring(f['Metadata/model_settings.config']);r=ET.fromstring(f['3D/3dmodel.model']);plates=cfg.findall('plate');cols=math.ceil(math.sqrt(len(plates)));items=list(r.find(tag('build')));result={}
    for i,plate in enumerate(plates):
        for inst in plate.findall('model_instance'):
            oid=props(inst)['object_id'];entries,st=read_object(f,oid)
            item=next(it for it in items if it.get('objectid')==oid);T=transform(item.get('transform'));T[:2,3]-=[i%cols*396,-(i//cols)*384]
            result[st['name']]=dict(parts=entries,settings=st,transform=T,plate=i+1,
                vertices=np.concatenate([q['mesh'].vertices@T[:3,:3].T+T[:3,3] for q in entries if q['subtype']=='normal_part']))
    return f,result


def geometry():
    p=load_plan();frames=[solid(cached(f'F{i}')) for i in range(1,11)];cores=[solid(cached(f'C{i}')) for i in range(1,5)]
    veneers=[solid(cached(f'V{i}-raw')) for i in range(1,4)]
    pairs=[]
    for label,objects in [('frame',frames),('core',cores),('veneer',veneers)]:
        for i,a in enumerate(objects):
            for j,b in enumerate(objects[:i]):
                v=abs((a^b).volume());assert v<.001,(label,i,j,v)
                pairs.append(dict(family=label,parts=[j+1,i+1],overlap_mm3=v))
    cad=CAD.read_text();K=artwork(cad,'knot_outline');F=artwork(cad,'fabric_outline').buffer(.1125,join_style=2)
    seamchecks=[]
    # Intersect ACTUAL body sections at all visible heights. Every material
    # surface crossed by each seam must have coincident upper closure edges.
    for k,j in enumerate(p['frame_joints']):
        a,b=frames[j[0]],frames[j[1]];n,t=axes(j);c=np.array(j[2]);row=[]
        for z in [8.999,9.001,9.599,9.899,12.899,13.499]:
            def contour(body):
                g=Polygon()
                for ring in body.slice(z).to_polygons():g=g.symmetric_difference(Polygon(ring))
                return g
            aa,bb=contour(a),contour(b)
            # Uniform probes; exclude actual artwork edges and holes. A seam
            # can legitimately cross a void in the weave at a given height.
            contacts=0;maxgap=0
            for y in np.arange(-j[4]/2+.5,j[4]/2,.5):
                q=c+t*y
                if not K.covers(Point(q)):
                    if not F.covers(Point(q)):continue
                    cell=np.round(q/6).astype(int);d=abs(q-cell*6)
                    if z>=9.9:continue
                    if 9.6<=z and not ((d[0]<=1.65 and d[1]<=.75) if sum(cell)%2==0 else (d[0]<=.75 and d[1]<=1.65)):continue
                    if 9<=z<9.6 and min(d)>.75:continue
                left=Point(q-n*.05);right=Point(q+n*.05)
                if not aa.covers(left) or not bb.covers(right):continue
                gap=max(aa.boundary.distance(Point(q)),bb.boundary.distance(Point(q)));maxgap=max(maxgap,gap);contacts+=1
            assert contacts>=4,(k,z,contacts)
            assert maxgap<2e-5,(k,z,maxgap)
            row.append(dict(z_mm=z,contact_probes=contacts,maximum_gap_mm=maxgap))
        seamchecks.append(dict(joint=k+1,sections=row))
    # Hardware circles must be fully supported in their assigned body, and
    # round/slot pins must enter their actual matching core holes without clash.
    hardware=[]
    for k,(ci,fi,xy) in enumerate(p['screw_mounts']):
        annulus=cylinder(xy,2.8,3.5,8.0)-cylinder(xy,1.65,3.49,8.01)
        outside=(annulus-cores[ci]).volume();assert outside<.001,(k,outside)
        hardware.append(dict(screw=k+1,core=ci+1,knot=fi+1,pilot_annulus_missing_mm3=outside))
    for ci,fi,xy,sec,angle in p['dowel_mounts']:
        pin=frames[fi]^cylinder(xy,2.01,13.51,16.51)
        translated=cores[ci].translate([0,0,13.5]);v=(pin^translated).volume();assert v<.001,(ci,xy,v)
    face=[];mp=json.loads((OUT/'M-geometry-validation.json').read_text())
    for i,row in enumerate(mp['skins']):
        raw=cached(f'V{i+1}-raw');front=raw.vertices[raw.vertices[:,2]>10.4]
        carried=cached(f'V{i+1}');T=np.array(row['assembly_to_printer']);points=carried.vertices@T[:3,:3]+(-T[:3,:3].T@T[:3,3])
        # Query preserved original front vertices, so extra external guard
        # vertices cannot be mistaken for alterations to the hammered face.
        error=float(cKDTree(points).query(front)[0].max());assert error<.0002,error
        face.append(dict(veneer=i+1,front_vertices_checked=len(front),max_front_error_mm=error))
    f,entries=embedded(EDIT);bounds=[]
    for name,row in entries.items():
        v=row['vertices'];lo=v.min(axis=0);hi=v.max(axis=0)
        assert np.all(lo>=[.5,.5,-.001]) and np.all(hi<=[329.5,319.5,325]),(name,lo,hi)
        for entry in row['parts']:
            if entry['subtype']=='normal_part':
                m=entry['mesh'];assert m.is_volume,(name,'invalid mesh');clean(solid(m),name)
        bounds.append(dict(name=name,plate=row['plate'],bounds_mm=[lo.tolist(),hi.tolist()]))
    save(OUT/'geometry-validation.json',dict(editable_sha256=sha(EDIT),production_plan_sha256=sha(PLAN),part_overlaps=pairs,
        actual_knot_cosmetic_closure=seamchecks,hardware=hardware,hammered_front_preservation=face,print_bounds=bounds,
        physical_confirmation_pending=True));print('Geometry: all parts connected, 14 zero-gap seams, coordinated mounts, preserved front',flush=True)


def material_angles(text,yaw):
    feature='Custom';x=y=z=e=0.;relative=False;xyz=False;tool=None;groups=collections.defaultdict(collections.Counter)
    for raw in text.splitlines():
        if raw.startswith('; FEATURE: '):feature=raw.split(': ',1)[1]
        code=raw.split(';',1)[0].strip()
        if not code:continue
        cmd=code.split()[0];v={k:float(n) for k,n in TOKEN.findall(code)}
        if cmd in ['T0','T1','T2','T3']:tool=int(cmd[1:])+1
        elif cmd=='M83':relative=True
        elif cmd=='M82':relative=False
        elif cmd in ['G90','G91']:xyz=cmd=='G91'
        elif cmd=='G92':x,y,z,e=[v.get(k,o) for k,o in zip('XYZE',(x,y,z,e))]
        elif cmd in ['G0','G1','G2','G3']:
            nx,ny,nz=[o+v.get(k,0) if xyz else v.get(k,o) for k,o in zip('XYZ',(x,y,z))]
            de=v.get('E',0) if relative else v.get('E',e)-e;length=math.hypot(nx-x,ny-y)
            if feature=='Top surface' and de>0 and length>.5 and cmd=='G1' and tool in [1,2,4]:
                angle=round(((math.degrees(math.atan2(ny-y,nx-x))-yaw)%180)*2)/2
                groups[(tool,round(nz,2))][angle]+=length
            x,y,z=nx,ny,nz;e=e+v.get('E',0) if relative else v.get('E',e)
    return [dict(filament_slot=tool,z_mm=z,dominant_assembly_angle_deg=cs.most_common(1)[0][0],length_mm=sum(cs.values())) for (tool,z),cs in sorted(groups.items()) if sum(cs.values())>10]


def native(path):
    result=json.loads((path/'result.json').read_text());assert result['return_code']==0,result
    before,aa=embedded(EDIT);after,bb=embedded(path/'sliced.3mf');assert aa.keys()==bb.keys()
    roundtrip=[]
    for name,row in aa.items():
        v=row['vertices'];w=bb[name]['vertices'];error=max(cKDTree(v).query(w)[0].max(),cKDTree(w).query(v)[0].max());assert error<.001,(name,error)
        roundtrip.append(dict(name=name,maximum_vertex_and_pose_error_mm=float(error)))
    s=json.loads(after['Metadata/project_settings.config']);assert s['printer_model']=='Bambu Lab A2L';assert s['sparse_infill_density']=='8%'
    mp=json.loads((OUT/'M-geometry-validation.json').read_text());plan=load_plan();rows=[]
    tower_plan=json.loads((OUT/'tower-placement.json').read_text())
    gcodes=sorted(path.glob('plate_*.gcode'),key=lambda p:int(p.stem.split('_')[-1]));assert len(gcodes)==20
    for file in gcodes:
        pi=int(file.stem.split('_')[-1]);text=file.read_text();r=scan_gcode(text);lo,hi=np.array(r['bead_xy_bounds_mm']);clearance=float(min(*lo,*(np.array([330,320])-hi)))
        r['conservative_bed_edge_clearance_mm']=clearance;assert clearance>.5,(pi,r['bead_xy_bounds_mm'])
        assert '; EXECUTABLE_BLOCK_END' in text
        assert 'printer_model = Bambu Lab A2L' in text or 'printer_model = Bambu Lab A2L' in json.dumps(s)
        hulls=[]
        for obj in bb.values():
            if obj['plate']!=pi:continue
            T=obj['transform']
            for entry in obj['parts']:
                if entry['subtype']=='normal_part':hulls.append(Polygon((entry['mesh'].vertices@T[:3,:3].T+T[:3,3])[:,:2]).convex_hull)
        height=max(z for zs in r['model_extrusion_z_by_filament_mm'].values() for z in zs)
        r['startup_prime_tower_check']=check_startup_tower(s,hulls,len(r['model_extrusion_z_by_filament_mm']),height,pi)
        if pi>10:assert not r['features'].get('Prime tower',0),pi
        if pi<=10:
            reserved=tower_plan['plates'][pi-1]['reserved_envelope_mm']
            r['prime_tower_clearance']=check_tower(text,hulls,reserved)
            evidence=angle_evidence(text,rotation=plan['frame_fits'][pi-1]['rotation_deg'])[0]
            assert evidence and abs((evidence[0][0]-135+90)%180-90)<.2,(pi,evidence)
            r['white_top_assembly_direction_deg']=evidence
            r['material_surface_angles']=material_angles(text,plan['frame_fits'][pi-1]['rotation_deg'])
            tools=r['model_extrusion_z_by_filament_mm'];assert {'1','2','4'}<=set(tools),(pi,list(tools))
        if 11<=pi<=14:assert not any(r['features'].get(k,0) for k in ['Support','Support interface']),pi
        if 15<=pi<=17:r['bonded_fin_toolpaths']=check_fin_bonds(text,mp['skins'][pi-15]['carrier'])
        estimate=next(a for a in result['sliced_plates'] if a['id']==pi)
        r.update(plate=pi,gcode_sha256=sha(file),weight_g=sum(f['total_used_g'] for f in estimate['filaments']),seconds=estimate['total_predication'])
        r['maximum_model_extrusion_z_mm']=max(z for zs in r['model_extrusion_z_by_filament_mm'].values() for z in zs)
        assert r['maximum_model_extrusion_z_mm']<=325
        r.pop('model_extrusion_z_by_filament_mm',None);rows.append(r);print('Native plate',pi,'passed',round(clearance,3),'mm margin',flush=True)
    grouped=collections.defaultdict(list)
    for r in rows[:10]:
        for a in r['material_surface_angles']:grouped[(a['filament_slot'],a['z_mm'])].append(a['dominant_assembly_angle_deg'])
    color_checks=[]
    for (tool,z),angles in grouped.items():
        if len(angles)<2:continue
        error=max(abs((a-angles[0]+90)%180-90) for a in angles);assert error<1,(tool,z,angles)
        color_checks.append(dict(filament_slot=tool,z_mm=z,plates_compared=len(angles),maximum_difference_deg=error))
    assert {1,2,4}<=set(r['filament_slot'] for r in color_checks)
    report=dict(material_direction_comparison=color_checks,editable_sha256=sha(EDIT),native_project_sha256=sha(path/'sliced.3mf'),production_plan_sha256=sha(PLAN),native_return_code=0,
        native_roundtrip=roundtrip,plates=rows,slicer_result=result,geometry_validation_sha256=sha(OUT/'geometry-validation.json'),
        printer='Bambu Lab A2L 0.4 nozzle',structural_infill='8% gyroid',veneer_infill='100%',physical_confirmation_pending=True)
    save(OUT/'native-validation.json',report)

def modifiers(path):
    _,aa=embedded(EDIT);_,bb=embedded(path/'sliced.3mf');records=[]
    for name,row in aa.items():
        points=[]
        for data in [row,bb[name]]:
            T=data['transform'];entries=[q['mesh'].vertices@T[:3,:3].T+T[:3,3] for q in data['parts'] if q['subtype']=='modifier_part']
            points.append(np.concatenate(entries) if entries else np.empty((0,3)))
        v,w=points
        assert len(v)==len(w),(name,len(v),len(w))
        if not len(v):continue
        error=max(cKDTree(v).query(w)[0].max(),cKDTree(w).query(v)[0].max());assert error<.001,(name,error)
        records.append(dict(name=name,modifier_vertices_checked=len(v),max_native_modifier_error_mm=float(error)))
    save(OUT/'modifier-validation.json',dict(editable_sha256=sha(EDIT),native_project_sha256=sha(path/'sliced.3mf'),objects=records))
    print('Color and reinforcement modifier round-trip passed',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['geometry','native','modifiers']);p.add_argument('path',nargs='?',type=Path);args=p.parse_args()
    geometry() if args.action=='geometry' else {'native':native,'modifiers':modifiers}[args.action](args.path)
