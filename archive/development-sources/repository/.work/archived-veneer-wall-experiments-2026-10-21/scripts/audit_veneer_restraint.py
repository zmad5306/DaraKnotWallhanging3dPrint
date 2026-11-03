"""Read-only comparison of modeled bed ties during growth; not a stiffness test."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'.work/python-libs'),str(ROOT/'scripts')]
import numpy as np
import manifold3d as mf
import trimesh
from build_veneer_wall_cradle import WORK,source_veneer,protected
from development_3mf import solid,save_json,sha

OUT=ROOT/'working/review/veneer-restraint-audit'


def run(revision="r1"):
    work=ROOT/f".work/veneer-wall-cradle-{revision}"
    before=protected();OUT.mkdir(parents=True,exist_ok=True)
    result=dict(purpose='Distinguish modeled bed attachment from detachable slicer support. Connectivity is not stiffness, bond strength or adhesion qualification.',
                source_sha256=sha(ROOT/'Dara.3mf'),revision=revision,physical_restraint_qualified=False,cases=[])
    for i in [1,2,3]:
        source,*_=source_veneer(i)
        a=np.load(work/f'V{i}-candidate.npz')
        candidate=trimesh.Trimesh(a['vertices'],a['faces'],process=False)
        for name,m in [('production',source),(revision,candidate)]:
            body=solid(m);levels=[]
            for z in [.2,2,5,10,25,50,100,200,297.4]:
                partial=body ^ mf.Manifold.cube([330,320,z])
                pieces=[q for q in partial.decompose() if q.volume()>1e-5]
                ungrounded=[];grounded=0
                for q in pieces:
                    bounds=list(q.bounding_box())
                    if bounds[2]<=.001:grounded+=1
                    else:ungrounded.append(dict(volume_mm3=q.volume(),bounds_mm=bounds))
                levels.append(dict(print_z_mm=z,grounded_components=grounded,ungrounded_components=ungrounded))
            record=dict(veneer=f'V{i}',revision=name,levels=levels)
            result['cases'].append(record)
            print(f'V{i} {name}: '+str([(r['print_z_mm'],len(r['ungrounded_components'])) for r in levels]),flush=True)
            save_json(OUT/f'growth-connectivity-{revision}.json',result)
    assert protected()==before
    result['protected_hashes_unchanged']=before
    result['limitations']=['Exact solid geometry at selected heights, not a native bead-connectivity simulation.',
        'A grounded component may remain mechanically flexible or peel off the bed.',
        'Ungrounded model islands may sit on slicer supports; those are intentionally excluded as bonded bed ties.',
        'No physical anti-warp performance is inferred.']
    save_json(OUT/f'growth-connectivity-{revision}.json',result)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--revision',choices=['r1','r2','r3','r4','r5'],default='r1');a=parser.parse_args();run(a.revision)
