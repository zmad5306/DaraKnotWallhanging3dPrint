"""Fit a complete tangent line/circle reconstruction to the pre-cleanup knot.

The saved working/geometry/clean-frame-primitives.json is the authoritative
portable result. This fitting step retains the original traced source locally
under .work/edge-quality/baseline.scad; rebuild_clean_cad.py replays the saved
primitives without refitting or requiring that historical source.
"""
import sys,math,json
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'scripts'))
import validate_print_project
from add_blue_ribbon_edge import artwork,polygons
from outline_curve_analysis import spans,circle_fit
import numpy as np
from scipy.optimize import least_squares
from shapely.geometry import Polygon,LineString
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt

def tangent(p,side):
    if p['type']=='line':return p['u']
    q=p['points'][0 if side=='start' else -1]-p['c'];q/=np.linalg.norm(q)
    return p['sign']*np.array([-q[1],q[0]])

def rebuild(ring,ri):
    xy=np.asarray(ring.coords);ds=np.linalg.norm(np.diff(xy,axis=0),axis=1);s=np.r_[0,np.cumsum(ds)];total=s[-1]
    prim=[]
    for i in np.flatnonzero(ds>15):
        u=(xy[i+1]-xy[i])/ds[i];u=np.eye(2)[np.argmax(abs(u))]*np.sign(u[np.argmax(abs(u))]);n=np.array([-u[1],u[0]])
        points=np.linspace(xy[i],xy[i+1],max(5,int(ds[i]/2)))
        prim.append(dict(type='line',start=s[i],end=s[i+1],points=points,u=u,n=n,d=float(np.mean(points@n))))
    for span in spans(ring):
        if span['length']<15:continue
        p=span['points'];a=int(len(p)*.1);q=p[a:-a]
        c,r,e=circle_fit(q)
        assert r<500,(ri,r)
        angles=np.unwrap(np.arctan2(q[:,1]-c[1],q[:,0]-c[0]));sign=1 if angles[-1]>angles[0] else -1
        prim.append(dict(type='circle',start=(span['start_s']+span['length']*.1)%total,
                         end=(span['end_s']-span['length']*.1)%total,points=q[::4],c=c,r=r,sign=sign,fillet=False))
    prim.sort(key=lambda p:p['start'])
    expanded=[]
    for i,p in enumerate(prim):
        nxt=prim[(i+1)%len(prim)];expanded.append(p)
        u=tangent(p,'end');v=tangent(nxt,'start');turn=math.atan2(u[0]*v[1]-u[1]*v[0],np.dot(u,v))
        if abs(turn)<math.radians(40):continue
        a=p['end'];b=nxt['start'];gap=(b-a)%total
        ts=(a+np.linspace(0,gap,max(20,int(gap/.05))))%total
        pts=np.column_stack([np.interp(ts,s,xy[:,j]) for j in range(2)])
        # Select the actual small corner using concentrated signed turning.
        delta=np.diff(pts,axis=0);angles=np.unwrap(np.arctan2(delta[:,1],delta[:,0]));turns=np.diff(angles)
        sign=1 if turn>0 else -1
        weights=np.maximum(turns*sign,0)
        window=max(3,round(1.6/(gap/(len(pts)-1))))
        center_index=int(np.clip(np.convolve(weights,np.ones(window),mode='same').argmax()+1,2,len(pts)-3))
        center_s=ts[center_index]
        tiny_s=(center_s+np.linspace(-.55,.55,25))%total
        points=np.column_stack([np.interp(tiny_s,s,xy[:,j]) for j in range(2)])
        c,r,e=circle_fit(points)
        if not .3<r<5:
            r=1.5;c=pts[center_index]+sign*r*np.array([-math.sin(angles[center_index]),math.cos(angles[center_index])])
        expanded.append(dict(type='circle',start=center_s,end=center_s,points=points,c=c,r=r,sign=sign,fillet=True))
    prim=expanded
    x0=[];lo=[];hi=[]
    for p in prim:
        p['idx']=len(x0)
        if p['type']=='line':x0.append(p['d']);lo.append(p['d']-1);hi.append(p['d']+1)
        else:
            x0.extend([*p['c'],p['r']]);lo.extend([p['c'][0]-5,p['c'][1]-5,.2 if p['fillet'] else p['r']-5]);hi.extend([p['c'][0]+5,p['c'][1]+5,5 if p['fillet'] else p['r']+5])
    def params(p,x):
        k=p['idx'];return (x[k:k+2],x[k+2]*p['sign']) if p['type']=='circle' else x[k]
    def constraints(x):
        result=[]
        for p in prim:
            if p['type']=='circle' and p['fillet']:
                result.append(x[p['idx']+2]-1.5)
            if ri==0 and p['type']=='line' and abs(p['d'])>450:
                result.append(x[p['idx']]-np.sign(p['d'])*457.2)
        for i,p in enumerate(prim):
            q=prim[(i+1)%len(prim)];a=params(p,x);b=params(q,x)
            if p['type']=='circle' and q['type']=='circle':
                c,r=a;d,t=b;result.append(np.linalg.norm(d-c)-abs(t-r))
            elif p['type']=='line' and q['type']=='circle':
                c,r=b;result.append(np.dot(p['n'],c)-a-r)
            elif p['type']=='circle' and q['type']=='line':
                c,r=a;result.append(np.dot(q['n'],c)-b-r)
            else:
                assert np.dot(p['u'],q['u'])>.9,('unrounded corner',ri,i)
                result.append(a-b)
        return np.array(result)
    def residual(x):
        result=[]
        for p in prim:
            if p['type']=='circle' and p['fillet']:continue
            a=params(p,x)
            if p['type']=='line':err=p['points']@p['n']-a
            else:
                c,r=a;err=np.linalg.norm(p['points']-c,axis=1)-abs(r)
            result.extend(err/np.sqrt(len(err)))
        return np.r_[result,constraints(x)*10000]
    opt=least_squares(residual,x0,bounds=(lo,hi),xtol=1e-12,ftol=1e-12,gtol=1e-12,max_nfev=1000)
    x=opt.x;joins=[]
    for i,p in enumerate(prim):
        q=prim[(i+1)%len(prim)];a=params(p,x);b=params(q,x)
        if p['type']=='circle' and q['type']=='circle':
            c,r=a;d,t=b;point=c-r*(d-c)/(t-r)
        elif p['type']=='line' and q['type']=='circle':
            c,r=b;point=c-r*p['n']
        elif p['type']=='circle' and q['type']=='line':
            c,r=a;point=c-r*q['n']
        else:
            point=p['points'][-1]-(np.dot(p['points'][-1],p['n'])-a)*p['n']
        joins.append(point)
    samples=[];records=[]
    for i,p in enumerate(prim):
        start,end=joins[i-1],joins[i]
        if p['type']=='line':
            assert np.dot(end-start,p['u'])>0,(ri,'reversed line',i)
            samples.append(start[None]);records.append(dict(type='line',start=start.tolist(),end=end.tolist()))
        else:
            c,r=params(p,x);a,b=[math.atan2(v[1]-c[1],v[0]-c[0]) for v in [start,end]]
            sweep=((b-a)*p['sign'])%(2*math.pi)
            assert sweep<math.pi+.1,(ri,'long arc',i,sweep)
            # <=0.002 mm chord error, cap each chord at 1 mm.
            step=min(1/abs(r),2*math.acos(max(-1,1-.002/abs(r))))
            angles=a+p['sign']*np.linspace(0,sweep,math.ceil(sweep/step)+1)[:-1]
            samples.append(c+abs(r)*np.column_stack([np.cos(angles),np.sin(angles)]))
            records.append(dict(type='circle',start=start.tolist(),end=end.tolist(),center=c.tolist(),radius=abs(r),sign=p['sign'],sweep_degrees=math.degrees(sweep),fillet=p['fillet']))
    new=np.vstack(samples);new=np.vstack([new,new[0]])
    proof=dict(ring=ri,primitives=records,tangency_residual_mm=float(abs(constraints(x)).max()),
               max_boundary_shift_mm=LineString(xy).hausdorff_distance(LineString(new)),valid=Polygon(new).is_valid)
    return new,proof

if __name__=='__main__':
    cad=Path('.work/edge-quality/baseline.scad').read_text();shape=artwork(cad,'knot_outline');records=[];rings=[]
    for ri,ring in enumerate([shape.exterior,*shape.interiors]):
        try:
            new,proof=rebuild(ring,ri);rings.append(new);records.append(proof)
            print(ri,'primitives',len(proof['primitives']),'shift',round(proof['max_boundary_shift_mm'],4),'residual',proof['tangency_residual_mm'],'valid',proof['valid'],flush=True)
        except Exception as e: print('FAIL',ri,str(e),flush=True);raise
    new=Polygon(rings[0],rings[1:]);print('FINAL',new.is_valid,new.bounds)
    Path('.work/edge-quality/analytic.json').write_text(json.dumps(records,indent=2))
    Path('.work/edge-quality/analytic-rings.json').write_text(json.dumps([r.tolist() for r in rings]))
    fig,axs=plt.subplots(4,7,figsize=(21,12))
    for ax,ri,r in zip(axs.flat,range(len(rings)),[shape.exterior,*shape.interiors]):
        ax.plot(*np.asarray(r.coords).T,color='#d35c30',lw=1);ax.plot(*rings[ri].T,color='#1875a0',lw=.8)
        ax.set(aspect='equal',title=f"Ring {ri} / shift {records[ri]['max_boundary_shift_mm']:.3f} mm");ax.tick_params(labelsize=6)
    for ax in list(axs.flat)[len(rings):]:ax.set_visible(False)
    fig.tight_layout();fig.savefig('.work/edge-quality/analytic-atlas.png',dpi=130)
