import sys,json
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'scripts'))
import validate_print_project
from add_blue_ribbon_edge import artwork,polygons
import numpy as np
from scipy.ndimage import gaussian_filter1d,maximum_filter1d
from scipy.optimize import least_squares
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def circle_fit(xy):
    origin=xy.mean(axis=0); q=xy-origin
    a=np.column_stack([2*q,np.ones(len(q))]); b=(q*q).sum(axis=1)
    x=np.linalg.lstsq(a,b,rcond=None)[0]; c=x[:2]+origin
    opt=least_squares(lambda c: np.linalg.norm(xy-c,axis=1)-np.linalg.norm(xy-c,axis=1).mean(),c)
    c=opt.x; r=np.linalg.norm(xy-c,axis=1).mean()
    return c,r,np.linalg.norm(xy-c,axis=1)-r

def spans(ring):
    xy=np.asarray(ring.coords); ds=np.linalg.norm(np.diff(xy,axis=0),axis=1)
    s=np.r_[0,np.cumsum(ds)]; n=int(np.ceil(s[-1]/.25)); step=s[-1]/n
    ss=np.arange(n)*step
    p=np.column_stack([np.interp(ss,s,xy[:,i]) for i in range(2)])
    k=int(round(2/step)); v=np.roll(p,-k,axis=0)-p; u=p-np.roll(p,k,axis=0)
    cross=u[:,0]*v[:,1]-u[:,1]*v[:,0]
    turn=np.arctan2(cross,(u*v).sum(axis=1))
    protected=maximum_filter1d(np.abs(turn)>.2,size=17,mode='wrap')
    for j in np.flatnonzero(ds>15):
        protected|=(ss>=s[j])&(ss<=s[j+1])
    shift=np.flatnonzero(protected)[0]
    free=np.roll(~protected,-shift)
    starts=np.flatnonzero(free&~np.roll(free,1)); ends=np.flatnonzero(free&~np.roll(free,-1))+1
    result=[]
    for a,b in zip(starts,ends):
        idx=(np.arange(a-1,b+1)+shift)%n; points=p[idx]
        length=(b-a)*step
        if length<4:continue
        c,r,err=circle_fit(points)
        result.append(dict(points=points,start_s=float(ss[idx[0]]),end_s=float(ss[idx[-1]]),length=length,
                          radius=r,center=c,max_error=float(abs(err).max()),rms=float(np.sqrt(np.mean(err**2)))))
    return result

if __name__=='__main__':
    cad=Path('.work/edge-quality/baseline.scad').read_text(); records=[]
    for name in ['knot','letter']:
        for pi,poly in enumerate(polygons(artwork(cad,name+'_outline'))):
            for ri,ring in enumerate([poly.exterior,*poly.interiors]):
                for i,r in enumerate(spans(ring)):
                    if r['length']>15:
                        r.update(name=name,ring=ri,span=i);records.append(r)
    print('SPANS',len(records))
    for r in records:
        print(r['name'],r['ring'],r['span'],'len',round(r['length'],1),'R',round(r['radius'],2),'max',round(r['max_error'],3),'rms',round(r['rms'],3))
    fig,axs=plt.subplots(int(np.ceil(len(records)/8)),8,figsize=(24,3*int(np.ceil(len(records)/8))))
    for ax,r in zip(axs.flat,records):
        p=r['points'];c=r['center'];a=np.unwrap(np.arctan2(p[:,1]-c[1],p[:,0]-c[0]));q=c+r['radius']*np.column_stack([np.cos(a),np.sin(a)])
        ax.plot(*p.T,color='#b04d25',lw=1);ax.plot(*q.T,color='#137caa',lw=.8)
        ax.set(aspect='equal',title=f"{r['name']} {r['ring']}:{r['span']} / err {r['max_error']:.2f}");ax.tick_params(labelsize=6)
    for ax in list(axs.flat)[len(records):]:ax.set_visible(False)
    fig.tight_layout();fig.savefig('.work/edge-quality/circle-fit-atlas.png',dpi=110)
