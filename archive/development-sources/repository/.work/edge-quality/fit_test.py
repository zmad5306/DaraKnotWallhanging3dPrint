import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'scripts'))
import validate_print_project
from add_blue_ribbon_edge import artwork,polygons
from explore import spans
import numpy as np
from scipy.optimize import minimize,lsq_linear
from shapely.geometry import LineString
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt

def bernstein(t,n):
    t=np.asarray(t)
    return np.column_stack([math.comb(n,i)*t**i*(1-t)**(n-i) for i in range(n+1)])

def bezier_fit(points,start_direction,end_direction):
    p=np.asarray(points); a,b=p[0],p[-1]
    u=start_direction/np.linalg.norm(start_direction);v=end_direction/np.linalg.norm(end_direction)
    length=np.linalg.norm(np.diff(p,axis=0),axis=1).sum()
    t=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]/length
    # Six unknowns: tangent handle lengths and two inner control points.
    def controls(x):return np.array([a,a+u*x[0],a+x[2:4],a+x[4:6],b-v*x[1],b])
    def evaluate(x,t):return bernstein(t,5)@controls(x)
    ts=np.linspace(0,1,151)
    def curvature(x):
        cp=controls(x);d=bernstein(ts,4)@(5*np.diff(cp,axis=0));dd=bernstein(ts,3)@(20*np.diff(cp,n=2,axis=0))
        return (d[:,0]*dd[:,1]-d[:,1]*dd[:,0])/np.maximum(np.linalg.norm(d,axis=1)**3,1e-15)
    base=evaluate(np.zeros(6),t);mat=np.stack([(evaluate(np.eye(6)[i],t)-base).ravel() for i in range(6)],axis=1)
    low=np.array([0,0,-np.inf,-np.inf,-np.inf,-np.inf]);hi=np.full(6,np.inf)
    x=lsq_linear(mat,(p-base).ravel(),bounds=(low,hi)).x
    cross=u[0]*v[1]-u[1]*v[0];sign=1 if cross>0 else -1
    weights=np.ones(len(t)); weights[[0,-1]]=100
    # A convex arc may change curvature smoothly, but may never reverse it.
    objective=lambda z: np.mean(np.sum((evaluate(z,t)-p)**2,axis=1)*weights)
    opt=minimize(objective,x,method='SLSQP',bounds=[(0,None),(0,None)]+[(None,None)]*4,
                 constraints=[{'type':'ineq','fun':lambda z: sign*curvature(z)*length}],
                 options={'ftol':1e-11,'maxiter':500})
    x=opt.x;new=evaluate(x,np.linspace(0,1,max(20,math.ceil(length/.25)+1)))
    return new,dict(success=bool(opt.success),max_error=LineString(p).hausdorff_distance(LineString(new)),
                    rms=math.sqrt(objective(x)),minimum_signed_curvature=float((sign*curvature(x)).min()),
                    maximum_curvature=float(abs(curvature(x)).max()))

if __name__=='__main__':
    cad=Path('.work/edge-quality/baseline.scad').read_text();shape=artwork(cad,'knot_outline');records=[]
    for ri,ring in enumerate([shape.exterior,*shape.interiors]):
        for si,r in enumerate(spans(ring)):
            if r['length']<15:continue
            p=r['points'];new,proof=bezier_fit(p,p[1]-p[0],p[-1]-p[-2]);r.update(new=new,proof=proof,ri=ri,si=si);records.append(r)
            print(ri,si,round(r['length'],1),proof,flush=True)
    fig,axs=plt.subplots(7,8,figsize=(24,21))
    for ax,r in zip(axs.flat,records):
        ax.plot(*r['points'].T,color='#b04d25',lw=1);ax.plot(*r['new'].T,color='#137caa',lw=.8)
        ax.set(aspect='equal',title=f"{r['ri']}:{r['si']} err {r['proof']['max_error']:.3f}");ax.tick_params(labelsize=6)
    fig.tight_layout();fig.savefig('.work/edge-quality/bezier-fit-atlas.png',dpi=110)
    Path('.work/edge-quality/bezier-fit.json').write_text(json.dumps([{k:v for k,v in r.items() if k not in ['points','new','center']} for r in records],indent=2))
