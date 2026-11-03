from pathlib import Path
import sys, re, ast, json, math, hashlib
sys.path.insert(0,str(Path('.work/python-libs').resolve()))
import numpy as np
from shapely.geometry import Polygon, Point, LineString, box, mapping, shape
from shapely.ops import unary_union, split
from shapely import affinity, set_precision
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MP
from shapely.geometry.polygon import orient

SOURCE=Path('working/Dara-Photo-Frame.scad').read_text()
def outline(name):
    body=SOURCE.split('module '+name+'() {')[1].split('\n}')[0]
    polys=[]
    for a,b in re.findall(r'polygon\(points = (\[.*?\]), paths = (\[.*?\]), convexity',body,re.S):
        pts=ast.literal_eval(a); paths=ast.literal_eval(b)
        polys.append(Polygon([pts[j] for j in paths[0]],[[pts[j] for j in p] for p in paths[1:]]))
    return affinity.scale(unary_union(polys),.75,.75,origin=(0,0))

KNOT=outline('knot_outline'); FABRIC=outline('fabric_outline').buffer(.1125)
FRAME=unary_union([KNOT,FABRIC]); LETTER=outline('letter_outline')
anchors=np.array(ast.literal_eval(re.search(r'photo_anchors = (.*?);',SOURCE).group(1)))*.75
normals=np.array(ast.literal_eval(re.search(r'photo_normals = (.*?);',SOURCE).group(1)))
TRACKS=[]
for a,n in zip(anchors.reshape(-1,2),normals.reshape(-1,2)):
    b=affinity.rotate(box(4.8,-5.7,14.2,5.7),math.degrees(math.atan2(n[1],n[0])),origin=(0,0))
    TRACKS.append(affinity.translate(b,*a))
PROTECT=unary_union(TRACKS).buffer(2)

def geoms(g,kind='Polygon'):
    if g.is_empty:return []
    return [g] if g.geom_type==kind else [p for p in g.geoms if p.geom_type==kind and not p.is_empty]

def fit(p):
    # Favor the shortest square envelope; rotations keep flat printing.
    best=None
    for a in range(0,180,3):
        r=affinity.rotate(p,a,origin=(0,0)); x,y,X,Y=r.bounds
        v=(max(X-x,Y-y), (X-x)*(Y-y),a,[x,y,X,Y])
        if best is None or v[:2]<best[:2]:best=v
    return best

def draw(ax,g,color,edge='white',lw=.5):
    for p in geoms(g):
        vertices=[];codes=[]
        for r in [orient(p,1).exterior,*orient(p,1).interiors]:
            c=list(r.coords); vertices+=c;codes +=[MP.MOVETO]+[MP.LINETO]*(len(c)-2)+[MP.CLOSEPOLY]
        ax.add_patch(PathPatch(MP(vertices,codes),facecolor=color,edgecolor=edge,lw=lw))

def design(whole,protect,label,seed):
    rng=np.random.default_rng(seed); parts=[whole]; seams=[]
    for iteration in range(70):
        sizes=[fit(p)[0] for p in parts]
        idx=int(np.argmax(sizes))
        if sizes[idx]<=224:break
        p=parts[idx]; centre=np.array(p.centroid.coords[0]); hull=np.array(p.convex_hull.exterior.coords)
        candidates=[]
        for _ in range(1600):
            ang=float(rng.uniform(0,math.pi)); n=np.array([math.cos(ang),math.sin(ang)]); t=np.array([-n[1],n[0]])
            limits=hull@n; c=float(rng.uniform(limits.min()+.2*np.ptp(limits),limits.max()-.2*np.ptp(limits)))
            line=LineString([n*c-t*1500,n*c+t*1500])
            shared=p.intersection(line)
            segments=geoms(shared,'LineString')
            if not segments or any(s.length<(32 if label=='M' else 15) for s in segments):continue
            if not protect.is_empty and any(s.distance(protect)<19 for s in segments):continue
            if seams and any(shared.distance(s)<24 for s in seams):continue
            pp=geoms(split(p,line))
            if len(pp)<2 or min(q.area for q in pp)<(2800 if label=='M' else 800):continue
            # Reject sliver tips and lap regions that would touch an unrelated edge.
            if any(q.minimum_rotated_rectangle.area/q.area>18 for q in pp):continue
            areas=sorted(q.area for q in pp)
            ratio=areas[-1]/p.area
            if ratio>.90:continue
            score=shared.length + ratio*150 + max(0,len(pp)-2)*100
            candidates.append((score,pp,segments))
        if not candidates:raise RuntimeError((label,'No cut',iteration,sizes[idx],p.bounds))
        _,pp,segments=min(candidates,key=lambda x:x[0])
        parts[idx:idx+1]=pp;seams+=segments
        print(label,iteration+1,'parts',len(parts),'max base',round(sizes[idx],1),'cut lengths',[round(s.length,1) for s in segments],flush=True)
    else:raise RuntimeError('too many parts')
    # Recombine neighboring pieces where one bed-sized connected solid suffices.
    while True:
        choices=[]
        for i,p in enumerate(parts):
            for j in range(i+1,len(parts)):
                q=parts[j]
                if p.distance(q)>1e-6:continue
                merged=unary_union([p,q])
                if merged.geom_type!='Polygon':continue
                size=fit(merged)[0]
                if size<=224: choices.append((merged.area,i,j,merged))
        if not choices:break
        _,i,j,p=max(choices,key=lambda v:v[0]);parts[i]=p;parts.pop(j)
    parts.sort(key=lambda p:(-round(p.centroid.y/80),p.centroid.x))
    joints=[]
    for i,p in enumerate(parts):
        for j in range(i+1,len(parts)):
            # Shared geometry inherited from identical split arithmetic, tolerance repairs it.
            q=parts[j]
            ss=p.boundary.intersection(q.boundary)
            # GEOS can return multiple collinear line fragments along one cut.
            from shapely.ops import linemerge
            if ss.geom_type=='MultiLineString':ss=linemerge(ss)
            for s in geoms(ss,'LineString'):
                if s.length<1:continue
                a=np.array(s.coords[0]);b=np.array(s.coords[-1]);t=(b-a)/np.linalg.norm(b-a);n=np.array([t[1],-t[0]])
                mid=(a+b)/2
                if not p.contains(Point(mid-n*1)):n=-n;t=-t
                joints.append({'male':i,'female':j,'centre':mid.tolist(),'angle':math.degrees(math.atan2(n[1],n[0])),'span':s.length,'line':mapping(s)})
    return parts,joints

if __name__=='__main__':
    results={}
    for name,whole,protect,seed in [('frame',FRAME,PROTECT,173),('M',LETTER,Polygon(),279)]:
        parts,joints=design(whole,protect,name,seed)
        results[name]={'parts':[mapping(p) for p in parts],'joints':joints}
        print(name,len(parts),'parts',len(joints),'joints',flush=True)
        Path('.work/sections-'+name+'.json').write_text(json.dumps(results[name]))
    fig,axs=plt.subplots(1,2,figsize=(16,9))
    for ax,(name,r) in zip(axs,results.items()):
        for i,p in enumerate(r['parts']):
            p=shape(p);draw(ax,p,plt.cm.tab20(i%20));c=p.representative_point();ax.text(c.x,c.y,f'{name[0]}{i+1}',ha='center',fontsize=8)
        for j in r['joints']:
            l=shape(j['line']);ax.plot(*l.xy,color='red',lw=1)
        if name=='frame':draw(ax,PROTECT,'none','black',.8)
        ax.set_aspect('equal');ax.autoscale();ax.set_title(name);ax.grid(alpha=.2)
    fig.tight_layout();fig.savefig('.work/section-plan.png',dpi=120)



