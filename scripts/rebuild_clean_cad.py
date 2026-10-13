"""Replay the verified line/arc artwork into both editable production CAD files."""
import json,math,re
from pathlib import Path
from validate_print_project import ROOT,CAD,digest
from add_blue_ribbon_edge import artwork
from repair_curve_artifacts import serialize
import numpy as np
from shapely.geometry import Polygon
from shapely import union_all

SOURCE=ROOT/'working/geometry/clean-frame-primitives.json'
REVIEW=ROOT/'working/review/clean-edges'
PHOTO_RINGS=[12,10,5,2,1,7,8,13]

def unit(v):
    return v/np.linalg.norm(v)

def sample_ring(primitives):
    samples=[];proof=[]
    for p in primitives:
        a,b=np.asarray(p['start']),np.asarray(p['end'])
        if p['type']=='line':
            samples.append(a[None]);u=v=unit(b-a);error=0
        else:
            c=np.asarray(p['center']);r=p['radius'];sign=p['sign']
            angle=math.atan2(a[1]-c[1],a[0]-c[0]);sweep=math.radians(p['sweep_degrees'])
            step=min(1/r,2*math.acos(max(-1,1-.002/r)))
            n=math.ceil(sweep/step)
            angles=angle+sign*np.linspace(0,sweep,n+1)[:-1]
            samples.append(c+r*np.column_stack([np.cos(angles),np.sin(angles)]))
            u=sign*unit(np.array([-(a-c)[1],(a-c)[0]]));v=sign*unit(np.array([-(b-c)[1],(b-c)[0]]))
            error=r*(1-math.cos(sweep/n/2))
            assert max(abs(np.linalg.norm(a-c)-r),abs(np.linalg.norm(b-c)-r))<1e-6
        proof.append(dict(start=a,end=b,start_tangent=u,end_tangent=v,chord_error_mm=error))
    gaps=[];angles=[]
    for i,p in enumerate(proof):
        q=proof[(i+1)%len(proof)];gaps.append(np.linalg.norm(p['end']-q['start']))
        u,v=p['end_tangent'],q['start_tangent'];angles.append(abs(math.degrees(math.atan2(u[0]*v[1]-u[1]*v[0],u@v))))
    assert max(gaps)<1e-6 and max(angles)<1e-5,(max(gaps),max(angles))
    points=np.vstack(samples)
    assert Polygon(points).is_valid
    return points,dict(primitives=len(primitives),max_join_gap_mm=float(max(gaps)),max_tangent_discontinuity_degrees=float(max(angles)),
                       max_chord_error_mm=max(p['chord_error_mm'] for p in proof),vertices=len(points))

def clean_shapes():
    data=json.loads(SOURCE.read_text());rings=[];checks=[]
    for r in data:
        xy,proof=sample_ring(r['primitives']);rings.append(xy);checks.append(dict(ring=r['ring'],**proof))
    knot=Polygon(rings[0],rings[1:]);fabric=union_all([Polygon(r) for r in rings[14:]])
    assert knot.is_valid and fabric.is_valid and len(knot.interiors)==25
    assert knot.intersection(fabric).area<1e-7
    assert np.allclose(knot.bounds,[-457.2,-457.2,457.2,457.2],atol=1e-6)
    return knot,fabric,rings,checks

def main():
    knot,fabric,rings,checks=clean_shapes()
    original=CAD.read_text();before=artwork(original,'knot_outline')
    replacements={'knot_outline':knot,'fabric_outline':fabric}
    replacements.update({f'photo_loop_{i}':Polygon(rings[ri]) for i,ri in enumerate(PHOTO_RINGS,1)})
    files=[]
    for path in [CAD,ROOT/'working/Dara-Photo-Frame.scad']:
        text=path.read_text();prior_hash=digest(path)
        for name,shape in replacements.items():
            text,n=re.subn(r'module '+name+r'\(\) \{.*?\n\}',lambda _:serialize(name,shape),text,count=1,flags=re.S)
            assert n==1,(path,name)
        note='// Clean frame outlines: tangent lines/circles from working/geometry/clean-frame-primitives.json.\n// Sampled chord error <=0.002 mm. Small artwork corners use 1.5 mm fillets.\n'
        if note not in text:text=note+text
        path.write_text(text);files.append(dict(file=str(path.relative_to(ROOT)),prior_sha256=prior_hash,sha256=digest(path)))
    REVIEW.mkdir(exist_ok=True,parents=True)
    report=dict(primitive_source_sha256=digest(SOURCE),method='Complete tangent line/circle reconstruction; shared fabric edges and photo loops use identical canonical boundaries.',
                loops=26,primitives=sum(c['primitives'] for c in checks),max_chord_error_mm=max(c['max_chord_error_mm'] for c in checks),
                max_tangent_discontinuity_degrees=max(c['max_tangent_discontinuity_degrees'] for c in checks),
                max_boundary_shift_mm=max(r['max_boundary_shift_mm'] for r in json.loads(SOURCE.read_text())),photo_ring_mapping=PHOTO_RINGS,
                overall_bounds_mm=list(knot.bounds),source_cad_sha256=digest(CAD),files=files,ring_checks=checks,
                letter_outline_unchanged=True,manufacturing_parameters_unchanged=True)
    (REVIEW/'cad-rebuild.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['ring_checks','files']},indent=2))

if __name__=='__main__':main()
