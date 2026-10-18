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
