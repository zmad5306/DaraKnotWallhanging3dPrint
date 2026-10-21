"""Check that native supports do not occupy the modeled lightening openings."""
import math
import numpy as np
import shapely
from shapely.geometry import Polygon
from validate_print_project import TOKEN


def support_segments(text):
    feature='Custom';x=y=z=e=0.;rel_e=rel_xyz=False;segments=[]
    for line in text.splitlines():
        if line.startswith('; FEATURE: '):feature=line.split(': ',1)[1]
        code=line.split(';',1)[0].strip()
        if not code:continue
        cmd=code.split()[0];v={k:float(n) for k,n in TOKEN.findall(code)}
        if cmd=='M83':rel_e=True
        elif cmd=='M82':rel_e=False
        elif cmd in ['G90','G91']:rel_xyz=cmd=='G91'
        elif cmd=='G92':x,y,z,e=[v.get(k,o) for k,o in zip('XYZE',(x,y,z,e))]
        elif cmd in ['G0','G1','G2','G3']:
            nx,ny,nz=[o+v.get(k,0) if rel_xyz else v.get(k,o) for k,o in zip('XYZ',(x,y,z))]
            de=v.get('E',0) if rel_e else v.get('E',e)-e
            if de>0 and feature in ['Support','Support interface'] and math.hypot(nx-x,ny-y)>1e-6:
                assert cmd=='G1','Arc support moves require an arc-aware intersection check'
                segments.append([[x,y,z],[nx,ny,nz]])
            x,y,z=nx,ny,nz;e=e+v.get('E',0) if rel_e else v.get('E',e)
    return np.asarray(segments)


def check_openings(text,openings):
    lines=support_segments(text);results=[]
    assert len(lines)>0
    for opening in openings:
        axis=opening['normal_axis'];plane=opening['plane'];half=opening['thickness']/2+.3
        start=lines[:,0];delta=lines[:,1]-start
        moving=np.abs(delta[:,axis])>1e-10
        lo=np.zeros(len(lines));hi=np.ones(len(lines))
        aa=np.zeros(len(lines));bb=np.zeros(len(lines))
        aa[moving]=(plane-half-start[moving,axis])/delta[moving,axis]
        bb[moving]=(plane+half-start[moving,axis])/delta[moving,axis]
        lo[moving]=np.maximum(0,np.minimum(aa[moving],bb[moving]))
        hi[moving]=np.minimum(1,np.maximum(aa[moving],bb[moving]))
        valid=(lo<=hi)&(moving|(np.abs(start[:,axis]-plane)<=half))
        a=start[valid]+lo[valid,None]*delta[valid]
        b=start[valid]+hi[valid,None]*delta[valid]
        axes=opening['axes'];polygon=Polygon(opening['polygon_mm']).buffer(.25)
        if len(a):
            projected=shapely.linestrings(np.stack([a[:,axes],b[:,axes]],axis=1))
            count=int(np.count_nonzero(shapely.intersects(projected,polygon)))
        else:count=0
        assert count==0,('Generated support inside lightening opening',opening,count)
        results.append(dict(wall=opening['wall'],support_segments_inside=count))
    return dict(openings_checked=len(results),support_segments_examined=len(lines),
        support_segments_inside_openings=0,wall_thickness_search_margin_mm=.3,
        opening_bead_margin_mm=.25,results=results,
        limitation='Toolpaths show no generated support in these openings; physical roof quality remains untested.')
