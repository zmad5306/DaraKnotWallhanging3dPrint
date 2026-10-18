"""Shared sample/production carrier: separate starter ribs and flush-cut necks.

The visible face, veneer seams, and seating pockets are excluded from attachment.
All dimensions below are trial dimensions, pending the copper-silk coupon.
"""
import math
import manifold3d as mf
import numpy as np
import shapely
from shapely.geometry import Point, LineString, Polygon, box, mapping
from shapely import union_all
from shapely.ops import nearest_points
import trimesh
from development_3mf import solid, mesh
from add_blue_ribbon_edge import section

PITCH=24.0  # nominal only; coverage and supported area determine actual rows
THICKNESS=1.6
BACK_GAP=3.0
TOOTH_PITCH=8.0  # maximum assembly-X spacing; projected vertical spacing is smaller
TOOTH_WIDTH=1.2
POCKET_DEPTH=.4
STARTER_PITCH=6.0


def slab_xz(profile,y,thickness):
    m=mesh(section(profile).extrude(thickness))
    t=np.array([[1,0,0,0],[0,0,1,y-thickness/2],[0,1,0,0],[0,0,0,1.]])
    m.apply_transform(t)
    if m.volume<0:m.invert()
    return solid(m)


def rod(a,b,radius=.9):
    a,b=np.asarray(a),np.asarray(b);delta=b-a
    m=mesh(mf.Manifold.cylinder(float(np.linalg.norm(delta)),radius,circular_segments=12))
    t=trimesh.geometry.align_vectors([0,0,1],delta/np.linalg.norm(delta));t[:3,3]=a
    m.apply_transform(t)
    return solid(m)


def line_parts(region,y):
    cut=region.intersection(LineString([(region.bounds[0]-1,y),(region.bounds[2]+1,y)]))
    return [p for p in shapely.get_parts(cut) if p.geom_type=='LineString' and p.length>6]


def fin_carrier(m,region,bottom,pose,exclusion,height_mesh,bed=(256,256),height=260,force_guard=False):
    # Keep knife/sanding scars on the hidden rear, with their remnants below the
    # seating surface. Positive-area embedding makes real bonds, not tangencies.
    from plan_veneer_fins import plan
    xmin,ymin,_,ymax=region.bounds
    # Follow the low/rising edge with individual ribs, never a continuous shoe.
    # Each 1.2 mm neck has a 2.6 mm pocket, accessible from the flat rear.
    starter_contacts=[]
    for y in np.linspace(ymin+.65,ymax-.65,max(2,math.ceil((ymax-ymin-1.3)/STARTER_PITCH)+1)):
        intervals=line_parts(region,float(y))
        if not intervals:continue
        x=min(q.bounds[0] for q in intervals)+.8
        neck=region.intersection(box(x-.6,y-.6,x+.6,y+.6))
        if neck.area<.5 or neck.intersects(exclusion):continue
        starter_contacts.append((float(x),float(y),neck))
    assert starter_contacts,'No grounded low-edge necks'
    starter_region=union_all([r[2] for r in starter_contacts])
    import plan_veneer_fins as planner
    old_sample=planner.SAMPLE;planner.SAMPLE=.75
    try:locations,coverage=plan(region,exclusion,starter_region,pose)
    finally:planner.SAMPLE=old_sample
    fins=[];cuts=[];teeth=[];records=[];feet=[];probes=[]
    R=pose[:3,:3];shift=pose[:3,3]
    for location in locations:
        y=location['y'];x0=location['x0'];x1=location['x1']
        xx=location['contacts'][:,0]
        # Trace the rear in the actual saved print pose. The broad, solid
        # fin has no lightening holes and grows continuously from the bed.
        xs=np.linspace(x0,x1,max(3,math.ceil((x1-x0)/.5)+1))
        xy=np.column_stack([xs,np.full(len(xs),y)])
        asm=np.column_stack([xy,bottom(xy)-BACK_GAP])
        trace=asm@R.T+shift
        trace=trace[np.argsort(trace[:,0])]
        assert trace[:,2].min()>0
        profile=Polygon([(trace[0,0],0),*trace[:,[0,2]].tolist(),(trace[-1,0],0)])
        py=float(trace[0,1]);fins.append(slab_xz(profile,py,THICKNESS))
        foot=box(trace[0,0],py-THICKNESS/2,trace[-1,0],py+THICKNESS/2)
        feet.append(foot)
        row=[]
        for x in xx:
            pocket=box(x-1.3,y-1.3,x+1.3,y+1.3)
            cut=solid(height_mesh(pocket,lambda q:bottom(q)-.1,lambda q:bottom(q)+POCKET_DEPTH)[0])
            cuts.append(cut)
            tooth=box(x-.6,y-TOOTH_WIDTH/2,x+.6,y+TOOTH_WIDTH/2)
            tab=solid(height_mesh(tooth,lambda q:bottom(q)-4.3,lambda q:bottom(q)+.6)[0])
            tm=mesh(tab);tm.apply_transform(pose);teeth.append(solid(tm))
            probe=np.array([x,y,float(bottom(np.array([[x,y]]))[0])-.75])
            probes.append((R@probe+shift).tolist())
            row.append([float(x),float(y)])
        records.append(dict(assembly_y_mm=float(y),print_y_mm=py,profile_xz_mm=list(profile.exterior.coords),
                            contacts_xy_mm=row,maximum_height_mm=float(trace[:,2].max())))
    assert fins and teeth,'No fin attachments possible'
    raw=solid(m)
    starter_fins=[];starter_records=[]
    for x,y,neck in starter_contacts:
        # Let an edge recess cut past the actual mesh perimeter. Clipping its
        # tool to a second polygon approximation can leave microscopic slivers
        # of the original side wall across the cutter opening.
        pocket=box(x-1.3,y-1.3,x+1.3,y+1.3)
        cuts.append(solid(height_mesh(pocket,lambda q:bottom(q)-.1,lambda q:bottom(q)+POCKET_DEPTH)[0]))
        tab=mesh(solid(height_mesh(neck,lambda q:bottom(q)-4.3,lambda q:bottom(q)+.6)[0]))
        tab.apply_transform(pose);teeth.append(solid(tab))
        xx=np.linspace(neck.bounds[0],neck.bounds[2],5)
        xy=np.column_stack([xx,np.full(len(xx),y)])
        trace=np.column_stack([xy,bottom(xy)-BACK_GAP])@R.T+shift
        trace=trace[np.argsort(trace[:,0])]
        assert trace[:,2].min()>0
        profile=Polygon([(trace[0,0],0),*trace[:,[0,2]].tolist(),(trace[-1,0],0)])
        py=float(trace[0,1]);starter_fins.append(slab_xz(profile,py,THICKNESS))
        feet.append(box(trace[0,0],py-THICKNESS/2,trace[-1,0],py+THICKNESS/2))
        starter_records.append(dict(assembly_y_mm=float(y),print_y_mm=py,profile_xz_mm=list(profile.exterior.coords),
            maximum_height_mm=float(trace[:,2].max()),contacts_xy_mm=[[float(x),float(y)]]))
        probe=np.array([x,y,float(bottom(np.array([[x,y]]))[0])-.75])
        probes.append((R@probe+shift).tolist())
    pockets=mf.Manifold.batch_boolean(cuts,mf.OpType.Add)
    body=raw-pockets
    # Every recess must leave real skin, and no cut may emerge on the show face.
    for cut in cuts:
        # A pocket ceiling has a complete .6 mm roof above it; this is checked
        # against actual material rather than a nominal veneer thickness.
        upper=mesh(cut^raw);upper.vertices[:,2]+=.7
        assert (solid(upper)-raw).volume()<1e-5,'Insufficient roof over trim pocket'
    bm=mesh(body);bm.apply_transform(pose);body=solid(bm)
    start_z=body.bounding_box()[2]
    first_layer=body^section(box(-1000,-1000,1000,1000)).extrude(.2).translate([0,0,start_z])
    start_mesh=mesh(first_layer)
    # Short gaps between grounded ribs replace the broad welded strip. Check
    # the actual earliest layer, including curved perimeter and recess edges.
    neck_xy=[]
    for _,_,neck in starter_contacts:
        lo=mesh(solid(height_mesh(neck,lambda q:bottom(q),lambda q:bottom(q)+.6)[0]))
        lo.apply_transform(pose);neck_xy.append(Polygon(lo.vertices[:,:2]).convex_hull)
    early_distance=shapely.distance(shapely.points(start_mesh.vertices[:,:2]),union_all(neck_xy))
    assert early_distance.max()<4,('Low edge too far from a grounded rib',early_distance.max())
    for tooth in teeth:
        assert (tooth^body).volume()>.15,'A tooth misses the veneer'
    braces=[];braced=set();offset_braces=0
    main_records=records
    # Full-size curved edges can place starter ribs well above the bed. Give
    # these the same diagonal-restraint checks as the broad fin sheets.
    records=main_records+starter_records
    # Diagonal cross ties brace the fins across their weak direction. Each grows
    # at 45 degrees and intersects two solid fin walls; no long flat bridge.
    for i,a in enumerate(records):
        for j,b in enumerate(records[:i]):
            dy=a['print_y_mm']-b['print_y_mm']
            if not 5<abs(dy)<=48:continue
            pa,pb=Polygon(a['profile_xz_mm']),Polygon(b['profile_xz_mm'])
            common=pa.intersection(pb)
            if common.is_empty:continue
            x=common.representative_point().x
            # Connect neighboring sheets at this X. Dense cross-ties between
            # every possible pair would undo the material savings.
            middle=[c for c in records if min(a['print_y_mm'],b['print_y_mm'])<c['print_y_mm']<max(a['print_y_mm'],b['print_y_mm'])]
            if any(Polygon(c['profile_xz_mm']).intersection(LineString([(x,0),(x,height)])).length>2 for c in middle):continue
            vertical=common.intersection(LineString([(x,0),(x,height)]))
            if vertical.is_empty:continue
            ceiling=vertical.bounds[3]
            for z in np.arange(2,ceiling-abs(dy)-2,24):
                braces.append(rod([x,a['print_y_mm'],z],[x,b['print_y_mm'],z+abs(dy)]))
                braced.update([i,j])
    # A fin under a curved crown can sit between both neighboring X ranges.
    # Same-X ties cannot reach it. Brace across that offset at 45 degrees,
    # rather than leaving a tall new sheet free to sway with bed Y travel.
    for i,a in enumerate(records):
        if i in braced or a['maximum_height_mm']<=48:continue
        pa=Polygon(a['profile_xz_mm']);ax0,_,ax1,_=pa.bounds;options=[]
        for j,b in enumerate(records):
            if i==j:continue
            pb=Polygon(b['profile_xz_mm']);bx0,_,bx1,_=pb.bounds
            lo,hi=max(ax0,bx0)+1,min(ax1,bx1)-1
            if lo<hi:xa=xb=(lo+hi)/2
            elif ax1<bx0:xa,xb=ax1-.5,bx0+.5
            else:xa,xb=ax0+.5,bx1-.5
            rise=math.hypot(xb-xa,b['print_y_mm']-a['print_y_mm'])
            if rise<1:continue
            ha=pa.intersection(LineString([(xa,0),(xa,260)])).bounds[3]
            hb=pb.intersection(LineString([(xb,0),(xb,260)])).bounds[3]
            ceiling=min(ha,hb-rise)-2
            if ceiling>2:options.append((rise,j,xa,xb,ceiling))
        for rise,j,xa,xb,ceiling in sorted(options)[:2]:
            b=records[j]
            for z in np.arange(2,ceiling,24):
                braces.append(rod([xa,a['print_y_mm'],z],[xb,b['print_y_mm'],z+rise]))
                braced.update([i,j]);offset_braces+=1
    # Narrow coupons may require only one full fin. Brace that sheet to two
    # separate ground feet instead of depending on a nonexistent neighbor.
    for i,a in enumerate(records):
        if i in braced or a['maximum_height_mm']<=48:continue
        pa=Polygon(a['profile_xz_mm']);lo,_,hi,_=pa.bounds
        candidates=np.linspace(lo+.5,hi-.5,40)
        x=max(candidates,key=lambda q:pa.intersection(LineString([(q,0),(q,height)])).bounds[3])
        ceiling=pa.intersection(LineString([(x,0),(x,height)])).bounds[3]
        z=min(36,ceiling-3)
        for side in [-1,1]:
            foot_y=a['print_y_mm']+side*8
            braces.append(rod([x,foot_y,.9],[x,a['print_y_mm'],z]))
            feet.append(box(x-1.2,foot_y-1.2,x+1.2,foot_y+1.2))
        braced.add(i)
    unbraced=[i for i,r in enumerate(records) if i not in braced and r['maximum_height_mm']>48]
    assert not unbraced,('Tall fins lack diagonal restraint',unbraced)
    tall_starters=[i-len(main_records) for i in braced if i>=len(main_records) and records[i]['maximum_height_mm']>48]
    records=main_records
    footprint=union_all(feet)
    hull=footprint.convex_hull.buffer(2,join_style=2)
    base=hull.difference(hull.buffer(-3))
    for p in feet:
        mid=p.representative_point();edge=nearest_points(mid,hull.boundary)[1]
        base=base.union(LineString([mid,edge]).buffer(1.5))
    guard=None
    if force_guard or np.ptp(m.vertices@R.T,axis=0)[1]>bed[1]-16:
        # Physical, per-object keep-out for supplementary tree feet. The broad
        # shallow ring is sacrificial and connected to the carrier. Unlike a
        # global bed exclusion it cannot affect the knot's edge-fitting plates.
        outside=box(1.5,1.5,bed[0]-1.5,bed[1]-1.5)
        ring=outside.difference(outside.buffer(-2,join_style=2))
        a,b=nearest_points(base,ring)
        base=base.union(ring).union(LineString([a,b]).buffer(1.5))
        guard=dict(outside_xy_mm=[1.5,1.5,bed[0]-1.5,bed[1]-1.5],width_mm=2,height_mm=1.6,
                   connected_to_carrier=True,model_brim_disabled=True)
    base_solid=section(base).extrude(1.6)
    bulk=mf.Manifold.batch_boolean(fins+starter_fins+braces+[base_solid],mf.OpType.Add)
    support=mf.Manifold.batch_boolean([bulk]+teeth,mf.OpType.Add)
    result=body+support
    # Coincident outside faces at the open starter recess can leave numerical
    # zero-volume sheets. Discard only those; any real loose chunk is a failure.
    components=result.decompose()
    sheets=[q for q in components if abs(q.volume())<1e-8]
    material=[q for q in components if abs(q.volume())>=1e-8]
    assert len(material)==1,('Disconnected carrier material',[(q.volume(),q.bounding_box()) for q in material])
    result=material[0]
    # Supports must not silently weld to any unplanned part of the veneer.
    contacts=mf.Manifold.batch_boolean(teeth,mf.OpType.Add)
    assert ((support-contacts)^body).volume()<1e-5,'Fin body touches veneer outside its teeth'
    # Simulate trimming on the rear seating plane, independently of the list
    # of "intentional" welds. Remaining material must fit inside the raw cap:
    # no perimeter lip and nothing proud of its flat bonding back.
    plane=float(bottom(np.array([[xmin,ymin]]))[0])
    rear_half=section(region).extrude(30).translate([0,0,plane])
    rm=mesh(rear_half);rm.apply_transform(pose);rear_half=solid(rm)
    raw_print=m.copy();raw_print.apply_transform(pose);raw_print=solid(raw_print)
    trimmed=result^rear_half
    excess=(trimmed-raw_print).volume()
    assert excess<1e-5,('Carrier leaves a lip after flush trimming',excess)
    # Verify a narrow cutter can reach every neck through the recess at the
    # rear plane; the fin sheets/feet/braces cannot occupy that cutting space.
    access_checks=[]
    for x,y in [p for r in records for p in r['contacts_xy_mm']]+[(x,y) for x,y,_ in starter_contacts]:
        window=region.intersection(box(x-1,y-1,x+1,y+1))
        # Stay inside the pocket's lower cut plane instead of making a large
        # Boolean on coincident faces. Blade thickness remains .20 mm.
        tool=mesh(solid(height_mesh(window,plane-.08,plane+.12)[0]));tool.apply_transform(pose);tool=solid(tool)
        blocked=(tool^(body+bulk)).volume()
        assert blocked<1e-5,('Cutter access blocked',x,y,blocked)
        access_checks.append(float(blocked))
    out=mesh(result)
    limit=.79 if guard else 2
    assert np.all(out.bounds[0,:2]>limit) and np.all(out.bounds[1,:2]<np.array(bed)-limit),out.bounds
    # Preserve the exact face above trim pockets, including every dimple.
    report=dict(type='Open-back fins with discrete grounded starter ribs and flush-cut necks',revision='clean-trim-production-v2',fin_count=len(fins),
        bonded_tooth_count=len(teeth),cross_braces=len(braces),fin_pitch_nominal_mm=PITCH,
        fin_pitch_max_mm=float(np.diff(sorted(set(r['print_y_mm'] for r in records))).max()) if len(set(r['print_y_mm'] for r in records))>1 else 0,
        fin_thickness_mm=THICKNESS,area_coverage=coverage,offset_crown_braces=offset_braces,
        support_foot_guard=guard,
        tall_fins_without_diagonal_restraint=unbraced,
        rear_fin_clearance_mm=BACK_GAP,tooth_width_mm=TOOTH_WIDTH,tooth_length_along_assembly_x_mm=1.2,
        tooth_pitch_max_along_assembly_x_mm=TOOTH_PITCH,trim_pocket_depth_mm=POCKET_DEPTH,
        minimum_checked_roof_above_pocket_mm=.6,body_connected_to_bed=True,
        starter_shoe_assembly_x_width_mm=0,continuous_starter_shoe=False,
        starter_rib_count=len(starter_fins),starter_ribs_directly_grounded=True,starter_rib_pitch_max_mm=STARTER_PITCH,
        starter_contact_region=mapping(starter_region),tall_starter_ribs_diagonally_restrained=sorted(tall_starters),
        starter_rib_heights_mm=[r['maximum_height_mm'] for r in starter_records],
        first_veneer_layer_height_checked_mm=.2,maximum_first_layer_distance_to_starter_mm=float(early_distance.max()),
        flush_trim_excess_outside_finished_veneer_mm3=float(excess),
        cutter_access_necks_checked=len(access_checks),maximum_cutter_access_obstruction_mm3=max(access_checks),
        cutter_access_window_mm=[2,2,.2],trim_plane_assembly_z_mm=plane,
        cleanup='Cradle face in lined caul. Cut 1.2 mm necks individually through rear pockets, flush with rear lands; remove ribs progressively, then sand rear lands on flat plate.',
        zero_volume_boolean_shells_removed=len(sheets),
        unplanned_fin_to_skin_contact_mm3=float(((support-contacts)^body).volume()),
        tree_supports_still_required=True,physical_confirmation_pending=True,
        assembly_to_printer=pose.tolist(),bond_probes_print_xyz_mm=probes,
        fins=[{**{k:v for k,v in row.items() if k!='profile_xz_mm'},
               'fin_xz_bounds_mm':list(Polygon(row['profile_xz_mm']).bounds)} for row in records])
    return out,report
