"""Allocate fins from rear surface coverage, rather than thinning rows blindly.

The limits below are geometric trial criteria, not measured silk-PLA stiffness
limits. Actual bonds, bracing and printing must also be checked.
"""
import math
import numpy as np
import shapely
from scipy.spatial import cKDTree
from shapely.geometry import LineString, Point, box

TOOTH_PITCH=8.
NOMINAL_SERVICE_WIDTH=24.
SERVICE_AREA_MULTIPLIER=2.
MAX_BOND_DISTANCE=math.sqrt(2)*NOMINAL_SERVICE_WIDTH/2
SAMPLE=1.5


def segments(g):
    return [p for p in shapely.get_parts(g) if p.geom_type=='LineString' and p.length>1e-6]


def row_candidates(region,safe,y):
    """Find teeth within each safe interval, including short curved returns."""
    interior=region.buffer(-2)
    line=LineString([(region.bounds[0]-1,y),(region.bounds[2]+1,y)])
    rows=[]
    for seg in segments(interior.intersection(line)):
        x0,_,x1,_=seg.bounds
        if x1-x0<=3:continue
        contacts=[]
        for interval in segments(safe.intersection(seg)):
            lo,_,hi,_=interval.bounds
            # Midpoint placement cannot discard a narrow interval merely
            # because the old regular grid missed it at both ends.
            xx=np.linspace(lo+.1,hi-.1,max(1,math.ceil((hi-lo-.2)/TOOTH_PITCH)+1)) if hi-lo>TOOTH_PITCH else [(lo+hi)/2]
            if len(xx)==1:xx=[(lo+hi)/2]
            contacts.extend(float(x) for x in xx)
        if contacts:
            rows.append(dict(y=float(y),x0=float(x0),x1=float(x1),kind='full',
                             contacts=np.column_stack([contacts,np.full(len(contacts),y)])))
    return rows


def old_rows(region,safe):
    interior=region.buffer(-2);y0,y1=interior.bounds[1],interior.bounds[3]
    result=[]
    for y in np.linspace(y0+.2,y1-.2,max(2,math.ceil((y1-y0)/12)+1)):
        cut=interior.intersection(LineString([(region.bounds[0]-1,y),(region.bounds[2]+1,y)]))
        for seg in segments(cut):
            x0,_,x1,_=seg.bounds
            if x1-x0<=6:continue
            xx=np.linspace(x0+.8,x1-.8,max(2,math.ceil((x1-x0-1.6)/8)+1))
            xx=[x for x in xx if safe.contains(Point(x,y))]
            if xx:result.append(dict(y=float(y),x0=x0,x1=x1,contacts=np.column_stack([xx,np.full(len(xx),y)])))
    return result


def area_samples(region):
    x0,y0,x1,y1=region.bounds
    xx,yy=np.meshgrid(np.arange(x0,x1,SAMPLE),np.arange(y0,y1,SAMPLE))
    cells=shapely.intersection(shapely.box(xx.ravel(),yy.ravel(),xx.ravel()+SAMPLE,yy.ravel()+SAMPLE),region)
    cells=cells[shapely.area(cells)>1e-8]
    # Representatives remain inside small clipped boundary cells.
    pts=shapely.point_on_surface(cells)
    xy=shapely.get_coordinates(pts)
    weights=shapely.area(cells)
    assert abs(weights.sum()-region.area)<1e-5
    allowance=MAX_BOND_DISTANCE+np.maximum(0,3-shapely.distance(pts,region.boundary))
    return xy,weights,allowance


def coverage(rows,xy,weights,allowance,starter_distance,keep=False,limits=None):
    points=np.concatenate([r['contacts'] for r in rows]) if rows else np.empty((0,2))
    owners=np.concatenate([np.full(len(r['contacts']),i) for i,r in enumerate(rows)]) if rows else np.empty(0,int)
    if len(points):dist,which=cKDTree(points).query(xy)
    else:dist=np.full(len(xy),1000.);which=np.zeros(len(xy),int)
    on_fin=dist<starter_distance
    dist=np.minimum(dist,starter_distance)
    bond_area=np.bincount(which[on_fin],weights=weights[on_fin],minlength=len(points))
    fin_area=np.bincount(owners,weights=bond_area,minlength=len(rows)) if rows else np.empty(0)
    lengths=np.array([np.ptp(r['contacts'][:,0])+TOOTH_PITCH for r in rows])
    widths=fin_area/lengths if rows else np.empty(0)
    result=dict(veneer_area_mm2=float(weights.sum()),sample_count=len(xy),sample_grid_mm=SAMPLE,
        maximum_distance_to_bond_or_starter_mm=float(dist.max()),
        area_outside_distance_limit_mm2=float(weights[dist>allowance+1e-7].sum()),
        maximum_area_per_bond_mm2=float(bond_area.max()) if len(points) else 0,
        maximum_tributary_width_mm=float(widths.max()) if rows else 0,
        fin_count=len(rows),bond_count=len(points),
        fin_service_areas_mm2=fin_area.tolist(),fin_tributary_widths_mm=widths.tolist())
    if keep:
        overloaded=np.zeros(len(xy),bool)
        if len(points):
            area_limit,width_limit=limits
            overloaded[on_fin]=(bond_area[which[on_fin]]>area_limit+1e-7)|(widths[owners[which[on_fin]]]>width_limit+1e-7)
        return result,dist,overloaded
    return result


def plan(region,exclusion,starter_region,pose=None):
    safe=region.buffer(-3).difference(exclusion)
    xy,weights,allowance=area_samples(region)
    starter_distance=shapely.distance(shapely.points(xy),starter_region)
    baseline=old_rows(region,safe)
    before=coverage(baseline,xy,weights,allowance,starter_distance)
    supported_area=sum(before['fin_service_areas_mm2'])
    reference_width=supported_area/sum(np.ptp(r['contacts'][:,0])+TOOTH_PITCH for r in baseline)
    reference_bond_area=supported_area/before['bond_count']
    area_limit=SERVICE_AREA_MULTIPLIER*reference_bond_area
    width_limit=SERVICE_AREA_MULTIPLIER*reference_width
    limits=(area_limit,width_limit)
    y0,y1=safe.bounds[1],safe.bounds[3]
    # A dense candidate pool is cheap geometry; only selected fins are built.
    ys=np.linspace(y0+.5,y1-.5,max(2,math.ceil((y1-y0)/6)+1))
    candidates=[r for y in ys for r in row_candidates(region,safe,y)]
    assert candidates
    distances=np.array([cKDTree(r['contacts']).query(xy)[0] for r in candidates])
    costs=np.array([(r['x1']-r['x0']) for r in candidates])
    if pose is not None:
        pose=np.asarray(pose)
        costs*=np.array([max(1,pose[2,0]*(r['x0']+r['x1'])/2+pose[2,2]*7.1+pose[2,3]) for r in candidates])
    selected=[];available=np.ones(len(candidates),bool)
    target=max(2,math.ceil(len(baseline)/2))
    for _ in range(len(candidates)):
        rows=[candidates[k] for k in selected]
        stats,dist,overloaded=coverage(rows,xy,weights,allowance,starter_distance,True,limits)
        good=(stats['area_outside_distance_limit_mm2']<1e-7 and
              stats['maximum_area_per_bond_mm2']<=area_limit+1e-7 and
              stats['maximum_tributary_width_mm']<=width_limit+1e-7)
        if good:break
        improvement=np.maximum(0,dist[None,:]**2-np.minimum(distances,dist[None,:])**2)
        # Prioritize patches outside the coverage limit, then overloaded area.
        focus=(dist>allowance).astype(float)*8+overloaded.astype(float)*2+.05
        scores=(improvement*(weights*focus)[None,:]).sum(axis=1)/np.sqrt(costs)
        scores[~available]=-1
        best=int(np.argmax(scores));assert scores[best]>0,'No legal fin can satisfy rear coverage'
        selected.append(best);available[best]=False
    else:raise AssertionError('Candidate pool exhausted before coverage passed')
    # Delete redundant fins only when ALL distance and service-area limits pass.
    # A half-population target never overrides the coverage requirements.
    for idx in sorted(selected,key=lambda k:(candidates[k]['x1']-candidates[k]['x0']),reverse=True):
        trial=[k for k in selected if k!=idx]
        if len(trial)<2:continue
        s=coverage([candidates[k] for k in trial],xy,weights,allowance,starter_distance)
        if (s['area_outside_distance_limit_mm2']<1e-7 and s['maximum_area_per_bond_mm2']<=area_limit+1e-7
                and s['maximum_tributary_width_mm']<=width_limit+1e-7):selected=trial
    rows=sorted([candidates[k] for k in selected],key=lambda r:(r['y'],r['x0']))
    after=coverage(rows,xy,weights,allowance,starter_distance)
    assert after['area_outside_distance_limit_mm2']<1e-7
    assert after['maximum_area_per_bond_mm2']<=area_limit+1e-7
    assert after['maximum_tributary_width_mm']<=width_limit+1e-7
    return rows,dict(method='Area-weighted rear coverage and tributary-area constrained fin allocation',
        target_fin_count=target,baseline=before,revised=after,
        reference=dict(average_area_per_bond_mm2=reference_bond_area,
                       average_effective_tributary_width_mm=reference_width),
        trial_geometric_limits=dict(nominal_service_width_mm=NOMINAL_SERVICE_WIDTH,
            maximum_tributary_width_mm=width_limit,
            maximum_rear_area_per_bond_mm2=area_limit,
            supported_area_multiplier=SERVICE_AREA_MULTIPLIER,
            interior_distance_to_bond_mm=MAX_BOND_DISTANCE,boundary_allowance_mm=3),
        physical_stiffness_and_bond_strength_not_established=True,
        half_population_is_target_not_constraint=True)
