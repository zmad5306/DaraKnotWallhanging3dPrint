"""Fresh M partition study; does not modify production meshes or print projects.

Run with the geometry dependencies used by develop_m_veneer.py. The veneer
carrier bounds are a conservative engineering allowance, not a native slice.
"""
import hashlib
import itertools
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from shapely import affinity, union_all
from shapely.geometry import LineString, Point, box, mapping, shape
from shapely.ops import split

import analyze_a2l_partitions as planar
from development_3mf import common_m_rotation, z_rotation
from build_jointed_bambu_project import read_array

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'working/review/a2l-m-joints'
CAD = ROOT / 'working/Dara-Photo-Frame-A1-Jointed.scad'
PLAN = ROOT / 'output/development/m-veneer-cosmetic-fit/M-geometry-validation.json'


def partition(outline, cuts, count):
    parts = [outline]
    for cut in cuts:
        parts = [q for p in parts for q in split(p, cut).geoms]
    assert len(parts) == count
    assert all(p.geom_type == 'Polygon' and p.is_valid for p in parts)
    assert union_all(parts).symmetric_difference(outline).area < 1e-7
    assert abs(sum(p.area for p in parts) - outline.area) < 1e-7
    return parts


def fit_core(g):
    # 1 mm brim plus 1 mm free space per edge, on the actual 330 x 320 bed.
    old = planar.USABLE
    planar.USABLE = np.array([326., 316.])
    try:
        return planar.fit(g, refine=True)
    finally:
        planar.USABLE = old


def line(center, angle, half=140):
    t = np.array([math.cos(math.radians(angle)), math.sin(math.radians(angle))])
    c = np.array(center)
    return LineString([c-half*t, c+half*t])


def keyed_cores(parts, outline, minimum_head_wall=3, hardware_exclusion=None):
    """Retain 18 mm mushroom geometry, .15 socket relief and >=3 mm head wall.

    Check both tongue directions, including real key extents in the bed fit.
    Single key on short seams; two on the longer outer-leg seam.
    """
    options = []
    for i, j, seam in planar.shared_seams(parts):
        t = np.array(seam.coords[-1])-np.array(seam.coords[0])
        t /= np.linalg.norm(t)
        n = np.array([-t[1], t[0]])
        choices = []
        for sign in [-1, 1]:
            nn = n*sign
            available = []
            for f in np.linspace(.2, .8, 25):
                q = np.array(seam.interpolate(f, normalized=True).coords[0])
                head = Point(*(q+12*nn)).buffer(6, quad_segs=12)
                neck = affinity.translate(affinity.rotate(box(-.5,-3.5,12,3.5),
                    math.degrees(math.atan2(nn[1],nn[0])),origin=(0,0)),*q)
                key = head.union(neck)
                if not outline.buffer(-minimum_head_wall).covers(head) or not outline.covers(key):
                    continue
                if hardware_exclusion is not None and key.buffer(.2).intersects(hardware_exclusion):
                    continue
                available.append((f, q, key))
            if not available:
                continue
            if seam.length > 60:
                pairs = [(a,b) for a in available for b in available
                         if (b[0]-a[0])*seam.length >= 20]
                if not pairs:
                    continue
                selected = min(pairs, key=lambda ab: abs(ab[0][0]-.32)+abs(ab[1][0]-.68))
            else:
                selected = [min(available,key=lambda row:abs(row[0]-.5))]
            receiver = i if parts[i].contains(Point(*(selected[0][1]+nn))) else j
            donor = j if receiver == i else i
            keys = union_all([q[2] for q in selected])
            choices.append(dict(donor=donor, receiver=receiver, keys=keys,
                centers=[q[1].tolist() for q in selected], length=seam.length))
        assert choices, ('No complete key with the required outer wall',i,j,minimum_head_wall)
        options.append(choices)
    results = []
    for choices in itertools.product(*options):
        envelopes = list(parts)
        for item in choices:
            donor, receiver, keys = item['donor'],item['receiver'],item['keys']
            envelopes[donor] = envelopes[donor].union(keys)
            envelopes[receiver] = envelopes[receiver].difference(keys.buffer(.15,quad_segs=8))
        if not all(g.geom_type == 'Polygon' and g.is_valid for g in envelopes):
            continue
        fits = [fit_core(g) for g in envelopes]
        if max(f['utilization'] for f in fits) <= 1:
            results.append((max(f['utilization'] for f in fits),envelopes,fits,choices))
    assert results, 'Keyed candidate fails the reserved bed envelope'
    return min(results,key=lambda row:row[0])[1:]


def veneer_allowance(g, rotation=None):
    """Conservative prism bounds at the unchanged common rotation.

    The entire 4.1 mm thickness is assumed at every XY point, overestimating
    the crown's extents. Reserve 3 mm per XY side for frame/brim/support roots,
    then require a further 2 mm free space per bed edge. Native support layout
    and an actual regenerated fin carrier must still be checked before release.
    """
    R = common_m_rotation() if rotation is None else rotation
    xy = np.asarray(g.convex_hull.exterior.coords)
    vertices = np.vstack([np.column_stack([xy,np.full(len(xy),z)]) for z in [8.6,12.7]])
    d = np.ptp(vertices@R.T,axis=0)
    envelope = d + np.array([6.,6.,2.4])
    return dict(body_prism_extents_mm=d.tolist(),
        carrier_brim_allowance_per_xy_side_mm=3,
        reserved_print_envelope_mm=envelope.tolist(),
        utilization=float(max(envelope/np.array([326.,316.,323.]))))


def summary(parts, fits):
    seams = planar.shared_seams(parts)
    return dict(sections=len(parts), joints=len(seams),
        seam_length_mm=sum(l.length for i,j,l in seams),
        parts=[dict(name=str(i+1),region=mapping(g),fit=f) for i,(g,f) in enumerate(zip(parts,fits))],
        seams=[dict(parts=[i+1,j+1],length_mm=l.length,line=mapping(l)) for i,j,l in seams])


def draw(report):
    im = Image.new('RGB',(1900,1230),'#f5f2ec')
    d = ImageDraw.Draw(im)
    def font(n,bold=False):
        return ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial'+(' Bold' if bold else '')+'.ttf',n)
    def text(x,y,s,n=24,bold=False,fill='#263d4c'):
        d.text((x,y),s,font=font(n,bold),anchor='mm',fill=fill)
    text(950,40,'M joint study — A1 versus A2L',36,True)
    text(475,100,'Current A1: production layout',27,True)
    text(1425,100,'A2L: fresh geometry candidate',27,True)
    palette=['#d0b180','#97b5c6','#acbfa1','#c8abb4','#b5a7c8','#d4c38c']
    for row,kind in enumerate(['veneer','core']):
        cy = 370+row*485
        for col,machine in enumerate(['a1','a2l']):
            cx = 475+col*950
            layout = report[machine][kind]
            def px(coords):
                return [(cx+x*1.08,cy-y*1.08) for x,y in coords]
            for i,p in enumerate(layout['parts']):
                g=shape(p['region']);d.polygon(px(g.exterior.coords),fill=palette[i])
                for hole in g.interiors:d.polygon(px(hole.coords),fill='#f5f2ec')
                pt=g.representative_point()
                text(cx+pt.x*1.08,cy-pt.y*1.08,('V' if kind=='veneer' else 'C')+p['name'],20,True)
            for seam in layout['seams']:
                d.line(px(shape(seam['line']).coords),fill='#9e3431' if kind=='veneer' else '#17618a',width=4)
            label='Visible veneer seams' if kind=='veneer' else 'Hidden core joints'
            text(cx,cy-222,f"{label}: {layout['joints']} / {layout['sections']} pieces",25,True)
            if kind=='veneer':
                text(cx,cy+213,f"Total face seam: {layout['seam_length_mm']:.0f} mm",23)
            else:
                text(cx,cy+213,'Flat on bed; keys included in A2L fit check',21)
    text(950,1140,'A2L veneers share one new rotation: 90° within the 55° tilted plane. Show planes stay parallel to bed Y.',23)
    text(950,1182,'A2L candidate needs carrier regeneration, mounting checks and native slicing before printing.',23,fill='#784838')
    im.save(OUT/'A1-vs-A2L-M-joints.png')


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    cad=CAD.read_text();plan=json.loads(PLAN.read_text())
    outline=planar.artwork(cad,'letter_outline')
    a1v=[shape(g) for g in plan['skin_regions']]
    a1c=[shape(g['region']) for g in plan['cores']]
    n=np.array([math.cos(math.radians(57.06125907870988)),math.sin(math.radians(57.06125907870988))])
    fork_center=np.array([32.336138117987566,136.58266699147163])
    # Four flat cores: fresh top-left cut, shifted fork cut, right leg cut.
    ccuts=[line(fork_center-15*n,147.06125907870988,70),
           line([-200,105],65),line([250,0],0,90)]
    cp=partition(outline,ccuts,4)
    envelopes,cfits,keys=keyed_cores(cp,outline)
    # Conservative alternative with the complete current rotation unchanged.
    left=line([-255,120],-20,145)
    vcuts=[line(fork_center,147.06125907870988,70),line([0,0],0,70),
           left,affinity.scale(left,-1,1,origin=(0,0))]
    vp_current=partition(outline,vcuts,5)
    current_fits=[veneer_allowance(g) for g in vp_current]
    assert all(f['utilization'] <= 1 for f in current_fits)
    # Better optical layout: turn ALL artwork 90 degrees within the tilted
    # plane, keeping the normal, 55-degree lean and Y-parallel show planes.
    # Assembly Y now rises in Z. A2L height permits whole 359 mm sweeps.
    rotation=common_m_rotation()@z_rotation(90)
    vp=partition(outline,[line([-125,150],90,100),line([125,150],90,100)],3)
    vfits=[veneer_allowance(g,rotation) for g in vp]
    assert all(f['utilization'] <= 1 for f in vfits)
    approved=ROOT/'working/bambu/Dara-Photo-Frame-A2L/production-plan.json'
    current=json.loads(approved.read_text()) if approved.exists() else {}
    if current.get('M_layout_revision')=='staggered-wide-fork-v1':
        spec=OUT/'staggered-layout.json'
        assert current['M_layout_specification_sha256']==hashlib.sha256(spec.read_bytes()).hexdigest()
        cp=[shape(g) for g in current['core_regions']];envelopes=[shape(g) for g in current['core_footprints']]
        cfits=current['core_fits'];keys=current['core_keys'];vp=[shape(g) for g in current['skin_regions']]
        vfits=[veneer_allowance(g,rotation) for g in vp]
    csummary=summary(cp,cfits)
    for row,g in zip(csummary['parts'],envelopes):row['keyed_footprint']=mapping(g)
    csummary['keys']=[{k:v for k,v in item.items() if k!='keys'} for item in keys]
    csummary['key_dimensions_mm']=dict(depth=18,head_radius=6,neck_width=7,socket_relief=.15,minimum_head_outer_wall=10 if current.get('M_layout_revision') else 3)
    # Flag, rather than silently relocate, the original mounting hardware.
    cseams=union_all([l for i,j,l in planar.shared_seams(cp)])
    vseams=union_all([l for i,j,l in planar.shared_seams(vp)])
    hardware=[]
    for typ in ['screw_mounts','dowel_mounts']:
        for index,row in enumerate(read_array(cad,typ)):
            pt=Point(*row[2])
            hardware.append(dict(type=typ,index=index+1,xy_mm=row[2],
                core_seam_distance_mm=cseams.distance(pt),veneer_seam_distance_mm=vseams.distance(pt)))
    profiles={}
    profile_dir=Path.home()/'Library/Application Support/BambuStudio/system/BBL/machine'
    for machine in ['A1','A2L']:
        path=profile_dir/f'Bambu Lab {machine} 0.4 nozzle.json'
        data=json.loads(path.read_text())
        profiles[machine]=dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            printable_area=data.get('printable_area','inherited'),printable_height=data['printable_height'],bed_exclude_area=data['bed_exclude_area'])
    result=dict(M_layout_revision=current.get('M_layout_revision'),status='GEOMETRY STUDY — not a production print project',
        seam_length_basis='Front-view XY projection, not textured 3D surface arc length',
        cad_sha256=hashlib.sha256(CAD.read_bytes()).hexdigest(),
        baseline_geometry_sha256=hashlib.sha256(PLAN.read_bytes()).hexdigest(),
        bed_mm=dict(A1=[256,256,256],A2L=[330,320,325]),local_profiles=profiles,
        a1_veneer_rotation=common_m_rotation().tolist(),
        a2l_veneer_rotation=rotation.tolist(),
        a1=dict(core=summary(a1c,[{}]*6),veneer=summary(a1v,[{}]*6)),
        a2l=dict(core=csummary,veneer=summary(vp,vfits)),
        a2l_current_pose_alternative=dict(veneer=summary(vp_current,current_fits),rotation=common_m_rotation().tolist()),
        mounting_distances=hardware,
        required_before_print=['Regenerate all matching 3D cores, locators, veneer pockets and fin carriers.',
          'Resolve screw/locator clearances against keyed seams and the selected A2L knot hardware.',
          'Native-slice using A2L profiles; check actual beads, brims, trees, height and carrier connectivity.',
          'Verify fit and silk finish physically. No measured strength or print-time claim.'],
        search_scope='Fresh straight cross-stroke cuts in the continuous outline; candidate counts, not a proof of global optimality.')
    assert np.allclose(rotation[:,2],common_m_rotation()[:,2])
    assert abs(rotation[1,2])<1e-12  # Face plane still contains bed Y.
    assert result['a2l']['core']['joints']==(4 if current.get('M_layout_revision') else 3) and result['a2l']['veneer']['joints']==2
    (OUT/'evaluation.json').write_text(json.dumps(result,indent=2)+'\n')
    draw(result)
    print(json.dumps(dict(core_fits=cfits,veneer_fits=vfits,
        a1_visible_mm=result['a1']['veneer']['seam_length_mm'],a2l_visible_mm=result['a2l']['veneer']['seam_length_mm'],
        hardware_within_8mm=[r for r in hardware if min(r['core_seam_distance_mm'],r['veneer_seam_distance_mm'])<8]),indent=2))


if __name__=='__main__':main()
