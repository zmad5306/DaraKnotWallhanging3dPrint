"""Measure saved perimeter arcs against the canonical circular CAD edges.

This detects broad ripples that a per-vertex angle threshold misses. It runs
alongside the full mask/bed/assembly audit, not as a substitute for those checks.
"""
import argparse,json,math,zipfile
from pathlib import Path
from validate_print_project import ROOT,CAD,digest
from build_jointed_bambu_project import read_array
from review_curve_artifacts import surface_paths
from rebuild_clean_cad import clean_shapes,SOURCE
import numpy as np

def arc_error(points,primitive,radii):
    c=np.asarray(primitive['center']);q=points-c
    theta=np.arctan2(q[:,1],q[:,0]);a=math.atan2(primitive['start'][1]-c[1],primitive['start'][0]-c[0])
    sweep=math.radians(primitive['sweep_degrees']);position=((theta-a)*primitive['sign'])%(2*math.pi)
    margin=4/primitive['radius'];keep=(position>margin)&(position<sweep-margin)
    if keep.sum()<3:return None
    distance=np.linalg.norm(q[keep],axis=1)
    errors=abs(distance[:,None]-radii)
    # Every retained point in one extrusion arc must follow the same radius.
    best=np.argmin(np.median(errors,axis=0));err=errors[:,best]
    if np.median(err)>1.5:return None
    return float(err.max()),int(keep.sum()),float(np.max(distance)-np.min(distance))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',type=Path,required=True);parser.add_argument('--baseline',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=ROOT/'working/review/clean-edges/perimeter-review.json')
    parser.add_argument('--plates',type=int,nargs='*',default=list(range(1,21)))
    args=parser.parse_args();base=json.loads(args.baseline.read_text());cad=CAD.read_text();placements=read_array(cad,'frame_placements')
    primitive_data=json.loads(SOURCE.read_text());circles=[dict(p,ring=r['ring'],index=i) for r in primitive_data for i,p in enumerate(r['primitives']) if p['type']=='circle' and not p['fillet']]
    _,_,_,joins=clean_shapes();results=[];covered=set()
    with zipfile.ZipFile(args.project) as archive:
        for number in args.plates:
            paths,_,_=surface_paths(archive.read(f'Metadata/plate_{number}.gcode').decode())
            p=placements[number-1];angle=math.radians(-p[0]);rot=np.array([[math.cos(angle),-math.sin(angle)],[math.sin(angle),math.cos(angle)]])
            origin=np.asarray(base['plate_layout'][number-1]['items'][0]['xy']);rows=[]
            for path in paths:
                if path['feature']!='Outer wall' or path['tool'] not in [1,4] or path['z']!=13.6 or len(path['xy'])<3:continue
                xy=(path['xy']-origin+np.asarray(p[1]))@rot.T;half=path['width']/2;choices=[]
                for c in circles:
                    if path['tool']==4 and c['ring']<14:continue
                    offsets=([1.3625+half,2.8625-half] if path['tool']==4 else
                             ([half,1.3625-half,2.8625+half] if c['ring']>=14 else [half]))
                    radii=c['radius']-c['sign']*np.asarray(offsets)
                    result=arc_error(xy,c,radii)
                    if result is not None:choices.append((result,c))
                if not choices:continue
                result,c=min(choices,key=lambda x:x[0][0]);covered.add((c['ring'],c['index']))
                rows.append(dict(gcode_line=path['line'],filament=path['tool'],ring=c['ring'],primitive=c['index'],max_radial_error_mm=result[0],samples=result[1],radial_range_mm=result[2]))
            maximum=max((r['max_radial_error_mm'] for r in rows),default=0)
            records=dict(plate=number,perimeter_arcs_checked=len(rows),samples=sum(r['samples'] for r in rows),max_radial_error_mm=maximum,
                         over_0_06_mm=[r for r in rows if r['max_radial_error_mm']>.06])
            results.append(records);print(number,len(rows),'arcs, maximum radial error',round(maximum,6),'outliers',len(records['over_0_06_mm']),flush=True)
    report=dict(project_sha256=digest(args.project),source_cad_sha256=digest(CAD),canonical_geometry_sha256=digest(SOURCE),
                scope='All canonical line/arc joins plus saved top-face white/blue perimeter arcs on every production frame plate; native mesh and full-layer color checks are separate.',
                acceptance_radial_error_mm=.06,join_checks=joins,plates=results,
                summary=dict(plates_checked=len(results),canonical_loops_checked=len(joins),canonical_large_arcs=len(circles),large_arcs_covered=len(covered),
                             perimeter_arcs_checked=sum(r['perimeter_arcs_checked'] for r in results),
                             max_radial_error_mm=max(r['max_radial_error_mm'] for r in results),
                             passed=all(not r['over_0_06_mm'] for r in results)))
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['summary'],indent=2))

if __name__=='__main__':main()
