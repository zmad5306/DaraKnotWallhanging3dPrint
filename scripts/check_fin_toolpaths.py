"""Check model extrusion near every fin-to-skin tooth, excluding slicer supports."""
import collections
import math
import numpy as np
from validate_print_project import TOKEN


def check_fin_bonds(text,carrier,layer_tolerance_mm=.45):
    feature='Custom';x=y=z=e=0.;rel_e=rel_xyz=False
    layers=collections.defaultdict(list)
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
            if cmd=='G1' and de>0 and feature not in ['Custom','Support','Support interface','Brim','Skirt','Prime tower'] and math.hypot(nx-x,ny-y)>1e-6:
                layers[round(nz,3)].append([[x,y,z],[nx,ny,nz]])
            x,y,z=nx,ny,nz;e=e+v.get('E',0) if rel_e else v.get('E',e)
    layers={z:np.asarray(a) for z,a in layers.items()}
    errors=[]
    for probe in carrier['bond_probes_print_xyz_mm']:
        p=np.asarray(probe)
        nearby=[a for z,a in layers.items() if abs(z-p[2])<layer_tolerance_mm]
        assert nearby,('No printed layer at bonded tooth',probe)
        a=np.concatenate(nearby)
        select=np.all(a.min(axis=1)-.45<=p,axis=1)&np.all(a.max(axis=1)+.45>=p,axis=1)
        a=a[select];assert len(a),('No model extrusion through bonded tooth',probe)
        start=a[:,0];delta=a[:,1]-start
        t=np.clip(np.sum((p-start)*delta,axis=1)/np.sum(delta*delta,axis=1),0,1)
        distance=float(np.linalg.norm(start+t[:,None]*delta-p,axis=1).min())
        assert distance<.45,('Bonded tooth missing from toolpaths',probe,distance)
        errors.append(distance)
    return dict(bond_probes_checked=len(errors),maximum_distance_to_model_extrusion_centerline_mm=max(errors),
                slicer_support_extrusion_excluded=True,physical_bond_strength_pending=True)
