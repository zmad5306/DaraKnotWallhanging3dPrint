from design_sections import *
from shapely.ops import linemerge
import time,concurrent.futures

OUT=Path('.work/repartition');OUT.mkdir(exist_ok=True)
PROFILES={k:shape(v)for k,v in json.loads(Path('.work/joint-profiles.json').read_text()).items()}
PHOTO_PIVOTS=anchors.reshape(-1,2)+normals.reshape(-1,2)*9.5
PHOTO_GUARD=unary_union([Point(p).buffer(4.6)for p in PHOTO_PIVOTS])
LIMIT=253.0 # 1.5 mm edge allowance on the 256 mm A1 bed.
ANGLES=np.deg2rad(np.arange(0,90,1));C=np.cos(ANGLES);S=np.sin(ANGLES)

def fast_fit(g,refine=False):
    v=np.asarray(g.convex_hull.exterior.coords)[:-1]
    xx=v[:,0,None]*C-v[:,1,None]*S;yy=v[:,0,None]*S+v[:,1,None]*C
    spans=np.stack([np.ptp(xx,axis=0),np.ptp(yy,axis=0)],axis=1)
    k=int(np.argmin(spans.max(axis=1)));a=ANGLES[k]
    if refine:
        aa=np.linspace(a-np.deg2rad(1),a+np.deg2rad(1),81)
        xx=v[:,0,None]*np.cos(aa)-v[:,1,None]*np.sin(aa);yy=v[:,0,None]*np.sin(aa)+v[:,1,None]*np.cos(aa)
        spans=np.stack([np.ptp(xx,axis=0),np.ptp(yy,axis=0)],axis=1);k=int(np.argmin(spans.max(axis=1)));a=aa[k]
    bounds=[xx[:,k].min(),yy[:,k].min(),xx[:,k].max(),yy[:,k].max()]
    return float(max(spans[k])),float(np.rad2deg(a)),bounds

def world(g,j):return affinity.translate(affinity.rotate(g,j['angle'],origin=(0,0)),*j['centre'])
def local(g,j):return affinity.rotate(affinity.translate(g,-j['centre'][0],-j['centre'][1]),-j['angle'],origin=(0,0))
def lines(g):
    if g.geom_type=='MultiLineString':g=linemerge(g)
    return geoms(g,'LineString')

def make_seams(parent,cut,angle,guard):
    result=[]
    n=np.array([math.cos(math.radians(angle)),math.sin(math.radians(angle))])
    for line in lines(parent.intersection(cut)):
        if line.length<15:return None
        a=np.array(line.coords[0]);b=np.array(line.coords[-1]);mid=(a+b)/2
        j={'centre':mid.tolist(),'angle':angle,'span':line.length,'line':mapping(line),'male_probe':(mid-n).tolist(),'female_probe':(mid+n).tolist()}
        lg=local(parent,j)
        d=lg.intersection(box(-1.5,-line.length/2-22,20,line.length/2+22))
        gg=geoms(d)
        if not gg:return None
        d=max(gg,key=lambda p:p.intersection(box(-.1,-line.length/2,.1,line.length/2)).area)
        j['domain']=mapping(world(d,j).buffer(.1,join_style=2))
        if not guard.is_empty and shape(j['domain']).intersects(guard):return None
        j['extra']=mapping(world(d.intersection(box(-1,-1000,18,1000)),j))
        result.append(j)
    return result

def envelope(g,seams):
    additions=[shape(j['extra'])for j in seams if g.contains(Point(j['male_probe']))]
    return unary_union([g,*additions]) if additions else g

def viable_mount(g,seams):
    stock=g.buffer(-8.5).intersection(KNOT.buffer(-8.5))
    for j in seams:
        if stock.is_empty:return False
        stock=stock.difference(shape(j['domain']).buffer(8.5))
    return not stock.is_empty and stock.area>8

def heuristic(g,span):
    # Bounding-square capacity cost penalizes tiny pieces and large residuals.
    # Real joint count and piece count rank complete candidates, not this estimate.
    if span<=LIMIT:return 1.
    _,_,b=fast_fit(g)
    w,h=b[2]-b[0],b[3]-b[1]
    return max(2.,(w/LIMIT)*(h/LIMIT)*1.55,(max(w,h)/LIMIT)**1.6)

def design_trial(job):
    family,seed,variant=job;rng=np.random.default_rng(seed);whole=FRAME if family=='frame'else LETTER
    guard=PHOTO_GUARD if family=='frame'else Polygon()
    parts=[whole];seams=[];t0=time.monotonic()
    for iteration in range(50):
        fits=[fast_fit(envelope(p,seams),True)[0]for p in parts]
        invalid=[i for i,z in enumerate(fits) if z>LIMIT]
        if not invalid:break
        idx=max(invalid,key=lambda i:fits[i]);parent=parts[idx]
        v=np.asarray(parent.convex_hull.exterior.coords)[:-1]
        opts=[];parent_seams=[j for j in seams if parent.distance(shape(j['line']))<.001]
        # Fresh oblique cuts across the current continuous outline. No old cuts
        # or part IDs enter this search.
        for candidate in range(550):
            ang=float(rng.uniform(0,math.pi));n=np.array([math.cos(ang),math.sin(ang)]);t=np.array([-n[1],n[0]])
            limits=v@n;frac=float(rng.uniform(.12,.88));c=limits.min()+frac*np.ptp(limits)
            cut=LineString([n*c-t*1500,n*c+t*1500])
            shared=parent.intersection(cut);ll=lines(shared)
            if not ll or any(l.length<15 for l in ll):continue
            if any(shared.distance(shape(j['line']))<24 for j in seams):continue
            if not guard.is_empty and shared.distance(guard)<1:continue
            pp=geoms(split(parent,cut))
            if len(pp)<2 or min(p.area for p in pp)<(1400 if family=='M'else 1200):continue
            # Keep compact, connected stock. Reject almost tangential slivers.
            if any(p.convex_hull.area/p.area>6 for p in pp):continue
            for angle in [math.degrees(ang),math.degrees(ang)+180]:
                new=make_seams(parent,cut,angle,guard)
                if not new:continue
                if any(shape(j['domain']).intersection(shape(k['domain'])).area>.001 for j in new for k in seams):continue
                all_seams=seams+new
                spans=[fast_fit(envelope(p,all_seams))[0]for p in pp]
                if max(spans)>=fits[idx]-.5:continue
                if family=='M' and any(not viable_mount(p,all_seams) for p,z in zip(pp,spans)if z<=LIMIT):continue
                done=[(p,z)for p,z in zip(pp,spans)if z<=LIMIT]
                # Different objective weights explore both peeling large pieces
                # and balanced subdivisions; score completed layouts by seams.
                est=sum(heuristic(p,z)for p,z in zip(pp,spans))
                fill=sum((z/LIMIT)**2 for p,z in done)
                waste=sum(max(0,1-(z/LIMIT)**2)for p,z in done)
                if variant==0:score=est+len(new)*.18+waste*.35-fill*.12
                elif variant==1:score=est+len(new)*.12+waste*.65-fill*.3
                else:score=est+len(new)*.25+waste*.2-fill*.05
                opts.append((score,pp,new))
        if not opts:
            (OUT/f'failed-{family}-{seed}.json').write_text(json.dumps({'parts':[mapping(p)for p in parts],'joints':seams,'fits':fits,'idx':idx}))
            return {'family':family,'seed':seed,'failed':iteration,'parts':len(parts),'maxdim':fits[idx]}
        opts.sort(key=lambda x:x[0])
        # Select from a small elite set to explore distinct complete layouts.
        chosen=opts[min(int(rng.exponential(.9)),min(4,len(opts)-1))]
        _,pp,new=chosen;parts[idx:idx+1]=pp;seams+=new
    else:return {'family':family,'seed':seed,'failed':'too many'}
    # Verify exact key lands; the profile is identical to the tested sample.
    for j in seams:
        d=local(shape(j['domain']),j);safe=[]
        for y in np.arange(-j['span']/2+4,j['span']/2-3,.5):
            if d.covers(affinity.translate(PROFILES['pocket'].buffer(2),yoff=y)):safe.append(float(y))
        if not safe:return {'family':family,'seed':seed,'failed':'no key land'}
        ys=[min(safe,key=lambda y:abs(y-j['span']*v))for v in [-1/3,1/3]]
        if ys[1]-ys[0]<6:return {'family':family,'seed':seed,'failed':'key spacing'}
        j['keys']=ys
    parts.sort(key=lambda p:(-round(p.centroid.y/80),p.centroid.x))
    for j in seams:
        j['male']=next(i for i,p in enumerate(parts)if p.contains(Point(j['male_probe'])))
        j['female']=next(i for i,p in enumerate(parts)if p.contains(Point(j['female_probe'])))
    sizes=[fast_fit(envelope(p,seams),True)[0]for p in parts]
    result={'family':family,'seed':seed,'variant':variant,'count':len(parts),'joint_count':len(seams),'parts':[mapping(p)for p in parts],'joints':seams,'maxdim':max(sizes),'mean_span':float(np.mean(sizes)),'seconds':round(time.monotonic()-t0,1)}
    (OUT/f'{family}-{seed}.json').write_text(json.dumps(result))
    return {k:v for k,v in result.items()if k not in ['parts','joints']}

if __name__=='__main__':
    family=sys.argv[1]if len(sys.argv)>1 else 'frame'
    start=int(sys.argv[2])if len(sys.argv)>2 else 100
    count=int(sys.argv[3])if len(sys.argv)>3 else 6
    with concurrent.futures.ProcessPoolExecutor(max_workers=3)as pool:
        for r in pool.map(design_trial,[(family,start+i,i%3)for i in range(count)]):print(json.dumps(r),flush=True)
