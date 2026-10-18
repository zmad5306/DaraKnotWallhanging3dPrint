"""Bed-grown sacrificial fins with repeated cut-away rear teeth.

The visible face, veneer seams, and seating pockets are excluded from attachment.
All dimensions below are trial dimensions, pending the copper-silk coupon.
"""
import math
import manifold3d as mf
import numpy as np
import shapely
from shapely.geometry import Point, LineString, Polygon, box
from shapely import union_all
from shapely.ops import nearest_points
import trimesh
from development_3mf import solid, mesh
from add_blue_ribbon_edge import section

PITCH=12.0
THICKNESS=1.6
BACK_GAP=1.5
TOOTH_PITCH=8.0  # maximum assembly-X spacing; projected vertical spacing is smaller
TOOTH_WIDTH=1.2
POCKET_DEPTH=.4


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


def fin_carrier(m,region,bottom,pose,exclusion,height_mesh):
    # Keep knife/sanding scars on the hidden rear, with their remnants below the
    # seating surface. Positive-area embedding makes real bonds, not tangencies.
    safe=region.buffer(-3).difference(exclusion)
    interior=region.buffer(-2)
    y0,y1=interior.bounds[1],interior.bounds[3]
    ys=np.linspace(y0+.2,y1-.2,max(2,math.ceil((y1-y0)/PITCH)+1))
    fins=[];cuts=[];teeth=[];records=[];feet=[];probes=[]
    R=pose[:3,:3];shift=pose[:3,3]
    for y in ys:
        for seg in line_parts(interior,y):
            x0,_,x1,_=seg.bounds
            xx=np.linspace(x0+.8,x1-.8,max(2,math.ceil((x1-x0-1.6)/TOOTH_PITCH)+1))
            xx=[x for x in xx if safe.contains(Point(x,y))]
            if not xx:continue
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
                pocket=box(x-1.,y-.85,x+1.,y+.85)
                cut=solid(height_mesh(pocket,lambda q:bottom(q)-.1,lambda q:bottom(q)+POCKET_DEPTH)[0])
                cuts.append(cut)
                tooth=box(x-.75,y-TOOTH_WIDTH/2,x+.75,y+TOOTH_WIDTH/2)
                tab=solid(height_mesh(tooth,lambda q:bottom(q)-2.8,lambda q:bottom(q)+.6)[0])
                tm=mesh(tab);tm.apply_transform(pose);teeth.append(solid(tm))
                probe=np.array([x,y,float(bottom(np.array([[x,y]]))[0])-.75])
                probes.append((R@probe+shift).tolist())
                row.append([float(x),float(y)])
            records.append(dict(assembly_y_mm=float(y),print_y_mm=py,profile_xz_mm=list(profile.exterior.coords),
                                contacts_xy_mm=row,maximum_height_mm=float(trace[:,2].max())))
    assert fins and teeth,'No fin attachments possible'
    raw=solid(m)
    # Anchor the very first veneer layers too. Fins whose first tooth sits a
    # few millimetres up cannot hold silk that has already detached from trees.
    xmin,ymin,_,ymax=region.bounds
    starter_region=region.intersection(box(xmin-1,ymin-1,xmin+4,ymax+1)).difference(exclusion)
    assert not starter_region.is_empty
    cuts.append(solid(height_mesh(starter_region,lambda q:bottom(q)-.1,
                                 lambda q:bottom(q)+POCKET_DEPTH)[0]))
    starter=mesh(solid(height_mesh(starter_region,lambda q:bottom(q)-20,
                                  lambda q:bottom(q)+.9)[0]))
    starter.apply_transform(pose)
    bed_clip=section(box(-1000,-1000,1000,1000)).extrude(260)
    starter=solid(starter)^bed_clip
    assert all(abs(c.bounding_box()[2])<1e-6 for c in starter.decompose())
    for patch in shapely.get_parts(starter_region):
        p=patch.representative_point();x,y=p.x,p.y
        probe=np.array([x,y,float(bottom(np.array([[x,y]]))[0])-.75])
        probes.append((R@probe+shift).tolist())
    pockets=mf.Manifold.batch_boolean(cuts,mf.OpType.Add)
    body=raw-pockets
    # Every recess must leave real skin, and no cut may emerge on the show face.
    for cut in cuts:
        # A pocket ceiling has a complete .6 mm roof above it; this is checked
        # against actual material rather than a nominal veneer thickness.
        upper=mesh(cut);upper.vertices[:,2]+=.7
        assert (solid(upper)-raw).volume()<1e-5,'Insufficient roof over trim pocket'
    bm=mesh(body);bm.apply_transform(pose);body=solid(bm)
    start_z=body.bounding_box()[2]
    first_layer=body^section(box(-1000,-1000,1000,1000)).extrude(.2).translate([0,0,start_z])
    unanchored_start=(first_layer-starter).volume()
    assert unanchored_start<1e-5,('Earliest veneer layer misses bonded starter shoe',unanchored_start)
    for tooth in teeth:
        assert (tooth^body).volume()>.15,'A tooth misses the veneer'
    braces=[]
    # Diagonal cross ties brace the fins across their weak direction. Each grows
    # at 45 degrees and intersects two solid fin walls; no long flat bridge.
    for i,a in enumerate(records):
        for j,b in enumerate(records[:i]):
            dy=a['print_y_mm']-b['print_y_mm']
            if not 5<abs(dy)<=PITCH+.01:continue
            pa,pb=Polygon(a['profile_xz_mm']),Polygon(b['profile_xz_mm'])
            common=pa.intersection(pb)
            if common.is_empty:continue
            x=common.representative_point().x
            vertical=common.intersection(LineString([(x,0),(x,260)]))
            if vertical.is_empty:continue
            ceiling=vertical.bounds[3]
            for z in np.arange(2,ceiling-abs(dy)-2,24):
                braces.append(rod([x,a['print_y_mm'],z],[x,b['print_y_mm'],z+abs(dy)]))
    footprint=union_all(feet)
    hull=footprint.convex_hull.buffer(2,join_style=2)
    base=hull.difference(hull.buffer(-3))
    for p in feet:
        mid=p.representative_point();edge=nearest_points(mid,hull.boundary)[1]
        base=base.union(LineString([mid,edge]).buffer(1.5))
    base_solid=section(base).extrude(1.6)
    support=mf.Manifold.batch_boolean(fins+teeth+braces+[base_solid,starter],mf.OpType.Add)
    result=body+support
    # Coincident outside faces at the open starter recess can leave numerical
    # zero-volume sheets. Discard only those; any real loose chunk is a failure.
    components=result.decompose()
    sheets=[q for q in components if abs(q.volume())<1e-8]
    material=[q for q in components if abs(q.volume())>=1e-8]
    assert len(material)==1,('Disconnected carrier material',[(q.volume(),q.bounding_box()) for q in material])
    result=material[0]
    # Supports must not silently weld to any unplanned part of the veneer.
    contacts=mf.Manifold.batch_boolean(teeth+[starter],mf.OpType.Add)
    assert ((support-contacts)^body).volume()<1e-5,'Fin body touches veneer outside its teeth'
    out=mesh(result)
    assert np.all(out.bounds[0,:2]>2) and np.all(out.bounds[1,:2]<254),out.bounds
    # Preserve the exact face above trim pockets, including every dimple.
    report=dict(type='Solid sacrificial fins with repeated bonded cut-away teeth',fin_count=len(fins),
        bonded_tooth_count=len(teeth),cross_braces=len(braces),fin_pitch_max_mm=PITCH,fin_thickness_mm=THICKNESS,
        rear_fin_clearance_mm=BACK_GAP,tooth_width_mm=TOOTH_WIDTH,tooth_length_along_assembly_x_mm=1.5,
        tooth_pitch_max_along_assembly_x_mm=TOOTH_PITCH,trim_pocket_depth_mm=POCKET_DEPTH,
        minimum_checked_roof_above_pocket_mm=.6,body_connected_to_bed=True,
        starter_shoe_assembly_x_width_mm=4,starter_shoe_contact_patches=len(shapely.get_parts(starter_region)),
        starter_shoe_directly_grounded=True,
        first_veneer_layer_height_checked_mm=.2,unanchored_first_veneer_layer_mm3=float(unanchored_start),
        zero_volume_boolean_shells_removed=len(sheets),
        unplanned_fin_to_skin_contact_mm3=float(((support-contacts)^body).volume()),
        tree_supports_still_required=True,physical_confirmation_pending=True,
        assembly_to_printer=pose.tolist(),bond_probes_print_xyz_mm=probes,
        fins=[{**{k:v for k,v in row.items() if k!='profile_xz_mm'},
               'fin_xz_bounds_mm':list(Polygon(row['profile_xz_mm']).bounds)} for row in records])
    return out,report
