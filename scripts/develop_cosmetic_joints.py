"""Cosmetic lap comparison coupons and the corresponding full A1 candidate.

Preserve the tested 18 mm envelope, primary key, artwork and .075 mm reference
gap. Added relief is deliberately confined to hidden regions. Coupon variants
must be physically compared before using the full-frame development candidate.
"""
import argparse
import copy
import json
import math
import xml.etree.ElementTree as ET
import numpy as np
import manifold3d as mf
from shapely import affinity, union_all
from shapely.geometry import Point, Polygon, box, LineString

from development_3mf import *
from develop_m_veneer import prism, locate, axes, xz_prism
from build_jointed_bambu_project import read_array
from validate_print_project import scan_gcode

CAD=ROOT/'working/Dara-Photo-Frame-A1-Jointed.scad'
ASSEMBLED_GRAIN=135.0
NATIVE_TOP_OFFSET=90.0  # Measured on the release's 13.5 mm white rail top.


def cross_section(body,z):
    result=Polygon()
    for ring in body.slice(z).to_polygons():
        p=Polygon(ring)
        if p.is_valid and p.area>1e-10: result=result.symmetric_difference(p)
    return result


def refine_pair(male, female, j, gap=.075):
    """Parts are in common assembly space, j's positive X is the lap direction."""
    n,t=axes(j);c=np.array(j[2]);parts=[copy.deepcopy(male),copy.deepcopy(female)]
    # Move only the upper cosmetic closing plane. Lap/key coordinates are fixed.
    for side, entries in enumerate(parts):
        old=(-1 if side==0 else 1)*.0375;new=(-1 if side==0 else 1)*gap/2
        for p in entries:
            v=p['mesh'].vertices;d=(v[:,:2]-c)@n;y=(v[:,:2]-c)@t
            select=(np.abs(d-old)<.0005)&(v[:,2]>6.599)&(np.abs(y)<j[4]/2+4)
            v[select,:2]+=(new-old)*n
    a,b=[solid(p[0]['mesh']) for p in parts]
    support_region=cross_section(a,4.79).intersection(cross_section(b,5.01))
    # Pick contact sites with enough real material in both halves; avoid keys.
    primary_keys=union_all([locate(box(1.8,y-2,16.2,y+2),j) for y in j[5]])
    safe=support_region.buffer(-2).intersection(locate(box(2,-j[4]/2+4,16,j[4]/2-4),j)).difference(primary_keys.buffer(.5))
    candidates=[]
    for x in [4,9,14]:
        for y in np.arange(-j[4]/2+5,j[4]/2-4,3):
            p=c+n*x+t*y
            if safe.contains(Point(*p)):candidates.append(p)
    q=np.array(candidates);assert len(q)>=3,('No contact pads',j)
    p0=q[np.argmin(np.linalg.norm(q-c,axis=1))];p1=q[np.argmax(np.linalg.norm(q-p0,axis=1))]
    d=p1-p0;dd=q-p0;p2=q[np.argmax(np.abs(d[0]*dd[:,1]-d[1]*dd[:,0]))]
    assert abs(np.linalg.det(np.array([p1-p0,p2-p0])))>10,('Collinear pads',j)
    pads=union_all([Point(*p).buffer(1.5,quad_segs=12) for p in [p0,p1,p2]])
    # Pad tops land on an exact .2 mm layer. Local socket roofs clear to Z5.0.
    a+=prism(pads,4.79,5.0)
    b-=prism(pads.buffer(.2),4.90,5.0)
    pocket=locate(box(1.75,-j[4]/2+3,16.5,j[4]/2-3),j).intersection(support_region)
    pocket=pocket.difference(pads.buffer(1)).difference(primary_keys.buffer(.7))
    a-=prism(pocket,4.60,4.81)
    # The secondary pocket is lengthened along the key-spacing axis only (Y).
    y=j[5][1]
    slot=locate(box(3.0,y-.9-.4,15.0,y+.9+.4).buffer(.9,quad_segs=8),j)
    b-=prism(slot,4.94,6.30)
    # Internal squeeze-out reservoirs below the lowest show surface (weave Z9).
    reservoir=locate(box(-.45,-j[4]/2+3,.45,j[4]/2-3),j)
    a-=prism(reservoir,6.8,7.8);b-=prism(reservoir,6.8,7.8)
    # Hidden first-layer lead-in at the tongue tip; upper lap geometry retained.
    lead=Polygon([(17.7,-.02),(18.2,-.02),(18.2,.48)])
    a-=xz_prism(lead,j)
    parts[0][0]['mesh']=mesh(a);parts[1][0]['mesh']=mesh(b)
    collision=(a^b).volume();assert collision<.001,collision
    return parts,dict(show_gap_mm=gap,seating_pad_top_mm=5.0,seating_pads_xy=[p.tolist() for p in [p0,p1,p2]],
                      adhesive_recess_mm=.2,secondary_axial_relief_mm=.8,lap_length_mm=18,
                      cosmetic_land_above_reservoir_to_weave_mm=1.2,assembled_interference_mm3=collision)


def coupons():
    files=source();a,sa=read_object(files,'209');b,sb=read_object(files,'213')
    for st in [sa,sb]:st.pop('name',None);st.pop(None,None)
    j=[0,1,[0,0],0,68,[-22.6530323,22.3469677]]
    plates=[];reports=[]
    for label,gap,refined in [('A reference',.075,False),('B refined 0.075',.075,True),('C refined 0.05',.05,True),('D refined 0.10',.10,True)]:
        if refined:pair,report=refine_pair(a,b,j,gap)
        else:pair,report=[copy.deepcopy(a),copy.deepcopy(b)],dict(reference=True,show_gap_mm=.075)
        objs=[]
        # Intentionally different bed rotations; compensate to one assembly angle.
        for k,(entries,settings,yaw,xy) in enumerate(zip(pair,[sa,sb],[17,67],[(74,125),(177,125)])):
            t=centered(entries[0]['mesh'],z_rotation(yaw),xy=xy)
            settings=dict(settings,infill_direction=str((ASSEMBLED_GRAIN+yaw-NATIVE_TOP_OFFSET)%180),brim_width='1',sparse_infill_density='8%')
            objs.append(dict(name=f'{label} {"tongue" if k==0 else "socket"}',parts=entries,transform=t,settings=settings))
        plates.append(objs);reports.append(dict(label=label,**report))
    # White-only contact pads hold both show faces at Z6. A 4 mm open clearance
    # above the base accommodates 3 mm M locating pins without contacting weave.
    combined=solid(a[0]['mesh'])+solid(b[0]['mesh'])
    white=cross_section(combined,13.49)
    for p in a[1:]+b[1:]:
        if p['settings'].get('extruder')=='4':white=white.difference(cross_section(solid(p['mesh']),13.49))
    safe=white.buffer(-2.5);pts=[]
    for x in [-24,30]:
        for y in [-30,30]:
            target=Point(x,y)
            if safe.covers(target):pts.append([x,y])
            else:
                import shapely.ops
                pts.append(list(shapely.ops.nearest_points(target,safe)[1].coords[0]))
    base=prism(box(-42,-44,52,44),0,2)
    for p in pts:base+=mf.Manifold.cylinder(4.01,2,circular_segments=40).translate([*p,1.99])
    jig=mesh(base);jig_settings=dict(extruder='1',enable_support='0',brim_width='0',sparse_infill_density='20%',wall_loops='4')
    plates.append([dict(name='Show-face glue jig - use release film',parts=[dict(mesh=jig)],transform=centered(jig),settings=jig_settings)])
    write_project(OUT/'Frame-Cosmetic-Comparison-A1.3mf',plates,'DEVELOPMENT - full-color baseline and refined lap comparisons')
    save_json(OUT/'Frame-coupon-validation.json',dict(variants=reports,jig_white_contact_xy=pts,jig_reference_height_mm=6,
                jig_open_clearance_mm=4,projecting_pin_clearance_mm=1,physical_confirmation_pending=True,
                compare=['Dry seating gap under light pressure','White face step in grazing light','Wood and blue continuity',
                         'Seam after controlled epoxy cure','Same assembly grain despite different bed rotations']))
    print('Four full-color comparison pairs and show-face jig staged',flush=True)


def full_frame():
    files=source();cad=CAD.read_text();placements=read_array(cad,'frame_placements');joints=read_array(cad,'frame_joints')
    cfg=ET.fromstring(files['Metadata/model_settings.config']);objects={}
    for co in cfg.findall('object'):
        name=props(co).get('name','').split(' - ')[0]
        if name in [f'F{i}' for i in range(1,21)]:objects[int(name[1:])-1]=co.get('id')
    entries={};settings={};transforms={};reports=[]
    for i,p in enumerate(placements):
        es,st=read_object(files,objects[i]);st.pop('name',None);st.pop(None,None)
        t=np.eye(4);t[:3,:3]=z_rotation(p[0]);t[:2,3]=-np.array(p[1]);transforms[i]=t
        for e in es:e['mesh'].apply_transform(np.linalg.inv(t))
        entries[i]=es;settings[i]=st
    for k,j in enumerate(joints):
        pair,report=refine_pair(entries[j[0]],entries[j[1]],j)
        entries[j[0]],entries[j[1]]=pair;reports.append(dict(joint=k+1,**report))
        print('Frame joint',k+1,'refined',flush=True)
    plates=[];direction=[]
    for i,p in enumerate(placements):
        # Restore exactly the source print rotation; center from the actual body.
        t=centered(entries[i][0]['mesh'],z_rotation(p[0]))
        angle=(ASSEMBLED_GRAIN+p[0]-NATIVE_TOP_OFFSET)%180;st=dict(settings[i],infill_direction=str(angle))
        plates.append([dict(name=f'F{i+1} cosmetic development',parts=entries[i],transform=t,settings=st)])
        direction.append(dict(part=f'F{i+1}',bed_rotation_deg=p[0],infill_direction_deg=angle,desired_assembly_direction_deg=ASSEMBLED_GRAIN,native_top_offset_deg=NATIVE_TOP_OFFSET))
    write_project(OUT/'Frame-Cosmetic-Candidate-A1.3mf',plates,'DEVELOPMENT - all 20 frame sections with refined hidden laps and aligned grain')
    save_json(OUT/'Frame-full-validation.json',dict(joints=reports,directions=direction,source_sha256=sha(ROOT/'Dara.3mf'),
                physical_coupon_gate=True,seam_centerlines_unchanged=True,artwork_and_color_assignments_retained=True,
                native_gcode_surface_direction_validation_pending=True))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['coupons','frame']);args=ap.parse_args()
    {'coupons':coupons,'frame':full_frame}[args.action]()
