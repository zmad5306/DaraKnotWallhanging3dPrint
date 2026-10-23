# Diagnostic screening only; results do not establish physical printability.
# Review input paths and settings for the current release before use.
"""Read-only screening of veneer toolpaths against earlier printed material.

This is a geometric screen, not a calibrated silk overhang/bridge acceptance
test. Sample centerlines at <=0.25 mm; allow bead-width overlap with the prior
model layer and support printed up to 0.6 mm lower. Adjacent lines laid in the
same layer are not counted as vertical support. No project is modified.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'.work/python-libs'),str(ROOT/'scripts')]
import numpy as np
import shapely
from shapely.geometry import shape
from shapely.strtree import STRtree
from validate_print_project import TOKEN

OUT=ROOT/'working/review/veneer-layer-overlap'
STEP=.25
MODEL_EXCLUDE={'Custom','Prime tower','Support','Support interface','Brim','Skirt'}


def parse(text):
    model=defaultdict(list);support=defaultdict(list)
    x=y=z=e=0.; rel=False; relxyz=False; width=.5; feature='Custom'
    for line in text.splitlines():
        if line.startswith('; FEATURE: '):feature=line.split(': ',1)[1]
        elif line.startswith('; LINE_WIDTH: ') or line.startswith('; WIDTH: '):width=float(line.split(': ',1)[1])
        code=line.split(';',1)[0].strip()
        if not code:continue
        cmd=code.split()[0]
        if cmd not in {'M83','M82','G90','G91','G92','G0','G1','G2','G3'}:continue
        v={k:float(n) for k,n in TOKEN.findall(code)}
        if cmd=='M83':rel=True
        elif cmd=='M82':rel=False
        elif cmd in {'G90','G91'}:relxyz=cmd=='G91'
        elif cmd=='G92':x,y,z,e=[v.get(k,o) for k,o in zip('XYZE',(x,y,z,e))]
        else:
            nx,ny,nz=[o+v.get(k,0) if relxyz else v.get(k,o) for k,o in zip('XYZ',(x,y,z))]
            de=v.get('E',0) if rel else v.get('E',e)-e
            if de>0 and np.hypot(nx-x,ny-y)>1e-7 and feature!='Custom':
                assert cmd=='G1','Arc extrusion not supported by this screen'
                row=(x,y,nx,ny,width,feature)
                if feature in {'Support','Support interface'}:support[round(nz,4)].append(row)
                elif feature not in MODEL_EXCLUDE:model[round(nz,4)].append(row)
            x,y,z=nx,ny,nz;e=e+v.get('E',0) if rel else v.get('E',e)
    return model,support


def coverage(points,widths,rows):
    if not rows:return np.zeros(len(points),dtype=bool),np.full(len(points),np.inf)
    v=np.array([r[:5] for r in rows],dtype=float)
    tree=STRtree(shapely.linestrings(v[:,:4].reshape(-1,2,2)))
    # Ask for every line inside the maximum possible bead-overlap radius.
    # The nearest narrow line need not provide more coverage than a wider line.
    radius=(float(v[:,4].max())+float(widths.max()))/2+.002
    pairs=tree.query(shapely.points(points),predicate='dwithin',distance=radius)
    covered=np.zeros(len(points),dtype=bool)
    margins=np.full(len(points),np.inf)
    if pairs.shape[1]:
        a,b=pairs
        d=shapely.distance(shapely.points(points[a]),tree.geometries[b])
        gap=d-(v[b,4]+widths[a])/2
        np.minimum.at(margins,a,gap)
        covered[a[gap<=.002]]=True
    return covered,margins


def run(plate):
    OUT.mkdir(parents=True,exist_ok=True)
    source=ROOT/'Dara.3mf'
    with zipfile.ZipFile(source) as archive:raw=archive.read(f'Metadata/plate_{plate}.gcode')
    model,support=parse(raw.decode())
    print('Parsed plate',plate,'model layers',len(model),'support layers',len(support),flush=True)
    report=json.loads((ROOT/'working/bambu/Dara-Photo-Frame-A2L/M-geometry-validation.json').read_text())
    plan=json.loads((ROOT/'working/bambu/Dara-Photo-Frame-A2L/production-plan.json').read_text())
    pose=np.array(report['skins'][plate-15]['assembly_to_printer'])
    region=shape(plan['skin_regions'][plate-15]).buffer(.3)
    sz=np.array(sorted(support))
    totals=np.zeros(3)
    layers=[];runs=[];feature_totals=defaultdict(lambda:np.zeros(2))
    previous_z=None
    for index,z in enumerate(sorted(model)):
        rows=model[z];v=np.array([r[:5] for r in rows],dtype=float)
        ends=v[:,:4].reshape(-1,2,2);delta=ends[:,1]-ends[:,0]
        length=np.linalg.norm(delta,axis=1);n=np.maximum(1,np.ceil(length/STEP).astype(int))
        segment=np.repeat(np.arange(len(rows)),n)
        offsets=np.arange(n.sum())-np.repeat(np.cumsum(n)-n,n)
        along=(offsets+.5)/n[segment]
        points=ends[segment,0]+along[:,None]*delta[segment]
        xyz=np.column_stack([points,np.full(len(points),z-.1)])
        asm=(xyz-pose[:3,3])@pose[:3,:3]
        is_veneer=(asm[:,2]>=8.55)&(asm[:,2]<=13.0)
        is_veneer &= shapely.contains_xy(region,asm[:,0],asm[:,1])
        if not is_veneer.any():previous_z=z;continue
        points=points[is_veneer];segment=segment[is_veneer]
        weights=length[segment]/n[segment];widths=v[segment,4]
        previous=model.get(round(z-.2,4),[])
        on_model,gaps=coverage(points,widths,previous)
        unsupported=~on_model
        on_support=np.zeros(len(points),dtype=bool)
        support_rows=[]
        for level in sz[(sz<z-.05)&(sz>=z-.6001)]:support_rows.extend(support[float(level)])
        if unsupported.any() and support_rows:
            on_support[unsupported]=coverage(points[unsupported],widths[unsupported],support_rows)[0]
        neither=~(on_model|on_support)
        totals += [weights.sum(),weights[~on_model].sum(),weights[neither].sum()]
        for f in set(r[5] for r in rows):
            mask=np.array([rows[i][5]==f for i in segment])
            feature_totals[f] += [weights[mask].sum(),weights[mask&neither].sum()]
        # Consecutive sampled toolpath portions lacking vertical overlap.
        # Restart at travel jumps, excluded non-veneer samples, or supported points.
        run=[];run_length=0.
        for k,bad in enumerate(neither):
            connected=(k>0 and np.linalg.norm(points[k]-points[k-1])<=STEP*1.51)
            if run and (not bad or not connected):
                if run_length>=1:
                    ids=np.array(run)
                    runs.append(dict(z_mm=z,length_mm=run_length,start_xy_mm=points[ids[0]].tolist(),
                        end_xy_mm=points[ids[-1]].tolist(),feature=rows[int(segment[ids[0]])][5]))
                run=[];run_length=0.
            if bad:run.append(k);run_length+=weights[k]
        if run and run_length>=1:
            runs.append(dict(z_mm=z,length_mm=run_length,start_xy_mm=points[run[0]].tolist(),
                end_xy_mm=points[run[-1]].tolist(),feature=rows[int(segment[run[0]])][5]))
        if neither.any():
            layers.append(dict(z_mm=z,veneer_path_length_mm=float(weights.sum()),
                no_previous_model_overlap_mm=float(weights[~on_model].sum()),
                no_model_or_support_overlap_mm=float(weights[neither].sum())))
        if index%250==0:print('Plate',plate,'at layer',index,'/',len(model),flush=True)
        previous_z=z
    runs.sort(key=lambda r:r['length_mm'],reverse=True)
    result=dict(status='GEOMETRIC_SCREEN_NOT_PHYSICAL_QUALIFICATION',plate=plate,
        gcode_sha256=hashlib.sha256(raw).hexdigest(),sample_step_mm=STEP,
        preceding_model_layer_mm=.2,support_search_depth_mm=.6,
        veneer_path_length_mm=float(totals[0]),
        length_without_previous_model_overlap_mm=float(totals[1]),
        length_without_model_or_support_overlap_mm=float(totals[2]),
        fraction_with_previous_model_overlap=float(1-totals[1]/totals[0]),
        fraction_with_model_or_support_overlap=float(1-totals[2]/totals[0]),
        unoverlapped_runs_over_1mm=len(runs),longest_unoverlapped_runs=runs[:60],
        features={k:dict(total_length_mm=float(v[0]),no_model_or_support_overlap_mm=float(v[1])) for k,v in feature_totals.items()},
        flagged_layers=layers,
        limitations=['Centerline samples and nominal widths, not deposited material.',
        'Support footprints within 0.6 mm are treated generously as potential support.',
        'Same-layer adjacent strands and path anchoring are not evaluated.',
        'Veneer region includes small embedded carrier necks near the rear.',
        'An unoverlapped run may be a supported-ended bridge, a cantilever, or a screening artifact; inspect before classifying.'])
    (OUT/f'plate-{plate}.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['plate','fraction_with_previous_model_overlap','fraction_with_model_or_support_overlap','longest_unoverlapped_runs']})[:1800],flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('plate',type=int,choices=[15,16,17]);a=p.parse_args();run(a.plate)
