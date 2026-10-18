"""Coupon-only straight sides and bed-printed Z datums for the upper lap.

Supported underside texture is given clearance, never used as a hard stop.
The receiving coupon's hidden rear is recessed .8 mm so its three datum feet
print directly on the bed. Their bottoms seat on upward-printed pocket floors.
White tops and wood crests are aligned to the .2 mm layer grid; full production
is not regenerated here. This avoids half-layer rounding after the rear offset.
"""
import copy
import numpy as np
import shapely
import manifold3d as mf
from shapely.geometry import box, Point
from shapely import union_all
from development_3mf import solid,mesh
from develop_m_veneer import prism

BACK=.8
ROOF=5.4
FOOT_RADIUS=1.8
POCKET_RADIUS=2.15
SIDE_END=21.0  # carry straight edges through the old crop's return to the stub
SHOW=13.6


def section(body,z):
    from develop_cosmetic_joints import cross_section
    return cross_section(body,z)


def revise(pair,report):
    parts=copy.deepcopy(pair)
    a,b=[solid(p[0]['mesh']) for p in parts]
    # The original cropped artwork narrows inside wider straight coupon ends.
    # Straighten the outermost 2 mm consistently in body and color modifiers;
    # do not move the joint plane, keys, weave or inner rail boundaries.
    for entries in parts:
        for part in entries:
            original=solid(part['mesh']);revised=original
            for sign in [-1,1]:
                profile=section(original.rotate([sign*90,0,0]),32)
                if profile.is_empty:continue
                rail=prism(profile,31.99999,34).rotate([-sign*90,0,0])
                ymin,ymax=(31.99999,35) if sign>0 else (-35,-31.99999)
                zone=prism(box(-.1,ymin,SIDE_END,ymax),-.1,15)
                revised=(revised-zone)+(rail^zone)
            part['mesh']=mesh(revised)
    a,b=[solid(p[0]['mesh']) for p in parts]
    # Remove the earlier pads, replacing their heights with three deep pockets.
    points=report['seating_pads_xy']
    pockets=union_all([Point(*p).buffer(POCKET_RADIUS,quad_segs=16) for p in points])
    a-=prism(pockets,BACK,6.8)
    # Keep supported bulk well clear of the tongue. The three feet, not that
    # underside, establish the assembled height.
    b-=prism(box(-.1,-35,18.6,35),4.8,ROOF)
    b-=prism(box(-100,-100,100,100),-.1,BACK)
    for p in points:
        b+=mf.Manifold.cylinder(ROOF+.02-BACK,FOOT_RADIUS,circular_segments=64).translate([*p,BACK])
    # Extra headroom prevents supported key-pocket roofs becoming false stops.
    keys=section(a,5.8).intersection(box(1,-32,17,32))
    openings=section(b,7).difference(section(b,6.2)).intersection(keys.buffer(1))
    b-=prism(openings,6.25,6.6)
    # Hide the extra bulk clearance behind bed-grown outer skirts. Their lower
    # edges share the same Z0.8 datum as the three feet. An open groove along
    # the outside walls would be visible even with a flush top face.
    for sign in [-1,1]:
        ymin,ymax=(33.2,34) if sign>0 else (-34,-33.2)
        skirt=box(0,ymin,SIDE_END,ymax)
        recess=box(0,ymin-.25 if sign>0 else ymin,SIDE_END,ymax if sign>0 else ymax+.25)
        a-=prism(recess,BACK,14)
        b+=prism(skirt,BACK,13.5)
        a+=prism(box(-.1,ymin,0,ymax),0,13.5)
    assert (a^b).volume()<1e-5
    assert len([q for q in a.decompose() if q.volume()>1e-8])==1
    assert len([q for q in b.decompose() if q.volume()>1e-8])==1
    parts[0][0]['mesh']=mesh(a);parts[1][0]['mesh']=mesh(b)
    # Half-layer surfaces can round in opposite directions after the .8 mm
    # placement offset (13.5 -> 13.6, but 12.7 -> 12.6 in the first native
    # trial). Put both roofs and their color masks on unambiguous layer planes.
    for entries in parts:
        for part in entries:
            m=part['mesh'];v=m.vertices
            for old,new in [(9.9,10.0),(13.5,SHOW)]:
                v[np.abs(v[:,2]-old)<1e-4,2]=new
            part['mesh']=mesh(solid(m))
    a,b=[solid(p[0]['mesh']) for p in parts]
    proof=dict(revision='bed-datum-ribbon-v1',coupon_width_mm=68,
        former_lap_width_mm=67.306,datum_foot_bottom_assembly_z_mm=BACK,
        datum_pocket_floor_assembly_z_mm=BACK,foot_diameter_mm=2*FOOT_RADIUS,
        pocket_diameter_mm=2*POCKET_RADIUS,datum_feet_xy_mm=points,
        socket_back_recess_mm=BACK,socket_supported_bulk_underside_z_mm=ROOF,
        tongue_glue_floor_z_mm=4.6,bulk_vertical_clearance_mm=ROOF-4.6,
        nominal_front_step_mm=0,cosmetic_gap_mm=0,production_geometry_unchanged=True,
        side_skirt_width_mm=.8,side_skirt_hidden_lateral_clearance_mm=.25,
        side_wall_nominal_gap_mm=0,
        white_show_height_mm=SHOW,wood_crest_height_mm=10,
        half_layer_heights_normalized_to_layer_grid=True,
        physical_fit_and_flushness_confirmation_pending=True)
    # Check actual continuous side edges throughout the lap at two solid levels.
    widths=[]
    for z in [1,4.7,5,5.3,8.5,SHOW-.01]:
        s=section(a,z).union(section(b,z))
        for x in np.linspace(.1,SIDE_END-.1,209):
            cut=s.intersection(shapely.LineString([(x,-40),(x,40)]))
            lo,hi=cut.bounds[1],cut.bounds[3]
            assert max(abs(lo+34),abs(hi-34))<.001,(x,z,lo,hi)
            widths.append(hi-lo)
    for lo,hi in [(-34,-33.9),(33.9,34)]:
        column=prism(box(.1,lo,24,hi),BACK,SHOW)
        assert (column-(a+b)).volume()<1e-5,'Visible groove in outer joint wall'
    # The datum contacts must be planar, downward on the feet and upward on
    # the tongue floor; both occur on exact native .2 mm layer boundaries.
    contacts=[]
    for p in points:
        for m,nz,label in [(mesh(a),1,'tongue_floor'),(mesh(b),-1,'socket_foot')]:
            tri=m.triangles;cent=m.triangles_center
            sel=(m.face_normals[:,2]*nz>.999)&(abs(cent[:,2]-BACK)<1e-7)&(np.linalg.norm(cent[:,:2]-p,axis=1)<FOOT_RADIUS)
            area=float(m.area_faces[sel].sum());assert area>5,(label,p,area)
            contacts.append(dict(point=p,face=label,planar_area_mm2=area))
    proof.update(side_width_min_mm=min(widths),side_width_max_mm=max(widths),datum_contact_planes=contacts)
    report=dict(report,bed_datum_revision=proof,seating_pad_top_mm=BACK,
        nominal_glue_clearance_mm=ROOF-4.6,seating_reference='Bed-printed feet on upward-printed pocket floors')
    return parts,report
