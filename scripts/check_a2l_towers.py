"""Check Studio's convex-hull rule and actual prime-tower bead clearance.

Studio source: libslic3r/Print.cpp::layered_print_cleareance_valid uses each
model volume's convex XY projection, even when the artwork is concave. The
additional toolpath check includes emitted supports, brims and the tower brim.
"""
import math
import numpy as np
import shapely
from shapely.geometry import MultiPoint,box,mapping
from validate_print_project import TOKEN


def check_tower(text,model_hulls,reserved):
    feature='Custom';x=y=z=e=0.;relative=False;xyz=False;width=.5
    tower=[];others=[];tower_width=0.;other_width=0.
    for raw in text.splitlines():
        if raw.startswith('; FEATURE: '):feature=raw.split(': ',1)[1]
        if raw.startswith('; WIDTH: '):width=float(raw.split(': ',1)[1])
        code=raw.split(';',1)[0].strip()
        if not code:continue
        cmd=code.split()[0];v={k:float(n) for k,n in TOKEN.findall(code)}
        if cmd=='M83':relative=True
        elif cmd=='M82':relative=False
        elif cmd in ['G90','G91']:xyz=cmd=='G91'
        elif cmd=='G92':x,y,z,e=[v.get(k,o) for k,o in zip('XYZE',(x,y,z,e))]
        elif cmd in ['G0','G1','G2','G3']:
            nx,ny,nz=[o+v.get(k,0) if xyz else v.get(k,o) for k,o in zip('XYZ',(x,y,z))]
            de=v.get('E',0) if relative else v.get('E',e)-e
            if de>0 and feature!='Custom' and math.hypot(nx-x,ny-y)>1e-7:
                # A2L production has arc fitting disabled. Fail rather than
                # treating an arc's end points as its full swept extrusion.
                assert cmd=='G1',('Unhandled extrusion arc',cmd)
                if feature=='Prime tower':
                    tower.append([[x,y],[nx,ny]]);tower_width=max(tower_width,width)
                else:
                    others.append([[x,y],[nx,ny]]);other_width=max(other_width,width)
            x,y,z=nx,ny,nz;e=e+v.get('E',0) if relative else v.get('E',e)
    assert tower and others,'Missing tower or model extrusion'
    envelope=MultiPoint(np.asarray(tower).reshape(-1,2)).convex_hull.buffer(tower_width/2)
    rect=box(*reserved);assert rect.buffer(.001).covers(envelope),('Tower exceeds planned envelope',envelope.bounds,reserved)
    gaps=[float(g.distance(envelope)) for g in model_hulls]
    assert min(gaps)>8,('Tower enters Studio model hull clearance',gaps)
    other_lines=shapely.linestrings(np.asarray(others))
    printed_gap=float(shapely.distance(other_lines,envelope).min()-other_width/2)
    assert printed_gap>3,('Tower too close to model/support/brim extrusion',printed_gap)
    lo=np.array(envelope.bounds[:2]);hi=np.array(envelope.bounds[2:])
    bed_gap=float(min(*lo,*(np.array([330,320])-hi)));assert bed_gap>.5
    return dict(studio_model_convex_hull_clearance_mm=min(gaps),actual_tower_bead_bounds_mm=[lo.tolist(),hi.tolist()],
        actual_tower_to_other_extrusion_clearance_mm=printed_gap,actual_tower_bed_clearance_mm=bed_gap,
        tower_extrusion_segments=len(tower),other_extrusion_segments=len(others),
        support_and_brim_extrusions_included=True,reserved_envelope_contains_actual_tower=True,
        actual_tower_convex_envelope=mapping(envelope))


def check_startup_tower(settings, model_hulls, filament_count, max_height, plate):
    """Match 2.8.2.61's unsliced estimate, including single-color plates.

    Print::wipe_tower_data sets non-rib tower depth to zero when only one
    filament is used and smooth timelapse is off. Rib towers instead retain
    a height-dependent square even though no tower is emitted on that plate.
    Use all project slots for a conservative multicolor estimate.
    """
    # N9 forces Y=160 and clamps X to [15, 330-width-15] on load.
    x=float(settings['wipe_tower_x'][plate-1]);y=float(settings['wipe_tower_y'][plate-1])
    assert y==160 and 15<=x<=330-float(settings['prime_tower_width'])-15,('Studio would reset tower position',plate,x,y)
    assert settings['prime_tower_rib_wall']=='0'
    assert settings['timelapse_type']=='0'
    assert len(settings['nozzle_diameter'])==1
    if filament_count==1:
        return dict(plate=plate,filament_count=1,estimated_depth_mm=0,
            estimated_footprint_area_mm2=0,intersects_model=False,
            reason='Conventional tower: no single-color tower or smooth timelapse')
    count=max(filament_count,len(settings['filament_diameter']))
    volume=15. if settings['prime_volume_mode']=='Saving' else max(map(float,settings['filament_prime_volume']))
    width=float(settings['prime_tower_width']);layer=float(settings['layer_height'])
    depth=volume*(count-1)/(layer*width)*float(settings['prime_tower_infill_gap'].rstrip('%'))/100
    minimum=float(np.interp(max_height,[5,100,250,350],[5,20,40,60]))
    depth=max(depth,minimum)
    x=float(settings['wipe_tower_x'][plate-1]);y=float(settings['wipe_tower_y'][plate-1]);brim=float(settings['prime_tower_brim_width'])
    footprint=box(x-brim,y-brim,x+width+brim,y+depth+brim)
    gap=min(g.distance(footprint) for g in model_hulls)
    assert gap>8,('Unsliced tower overlaps model hull',plate,gap)
    assert box(.5,.5,329.5,319.5).covers(footprint)
    return dict(plate=plate,filament_count=filament_count,conservative_estimated_filament_count=count,
        estimated_depth_mm=depth,estimated_footprint_area_mm2=footprint.area,
        conservative_model_convex_hull_clearance_mm=gap,intersects_model=False)
