from repartition_search import *
import itertools

def initial():
    ps=[FRAME];seams=[]
    for target,angle,offset in [(0,2,0),(0,88,-6),(2,94,7)]:
        p=ps[target];n=np.array([math.cos(math.radians(angle)),math.sin(math.radians(angle))]);t=np.array([-n[1],n[0]])
        cut=LineString([n*offset-t*1500,n*offset+t*1500]);new=make_seams(p,cut,angle,PHOTO_GUARD)
        if not new:raise RuntimeError('initial seam')
        pp=geoms(split(p,cut));pp.sort(key=lambda g:g.centroid.x if len(ps)==1 else -g.centroid.y)
        ps[target:target+1]=pp;seams+=new
    return ps,seams

BASE,INITIAL=initial()

def trial(job):
    quadrant,seed=job;rng=np.random.default_rng(seed);parts=[BASE[quadrant]];seams=INITIAL.copy()
    for iteration in range(7):
        fits=[fast_fit(envelope(p,seams),True)[0]for p in parts];bad=[i for i,s in enumerate(fits)if s>LIMIT]
        if not bad:break
        if len(parts)>=6:return None
        idx=max(bad,key=lambda i:fits[i]);parent=parts[idx];v=np.asarray(parent.convex_hull.exterior.coords)[:-1];opts=[]
        for _ in range(450):
            ang=float(rng.uniform(0,math.pi));n=np.array([math.cos(ang),math.sin(ang)]);t=np.array([-n[1],n[0]])
            limits=v@n;c=limits.min()+float(rng.uniform(.15,.85))*np.ptp(limits);cut=LineString([n*c-t*1500,n*c+t*1500]);shared=parent.intersection(cut)
            if not lines(shared)or any(l.length<15 for l in lines(shared)):continue
            if any(shared.distance(shape(j['line']))<24 for j in seams):continue
            pp=geoms(split(parent,cut))
            if len(pp)<2 or min(p.area for p in pp)<1800:continue
            for angle in [math.degrees(ang),math.degrees(ang)+180]:
                new=make_seams(parent,cut,angle,PHOTO_GUARD)
                if not new:continue
                if any(shape(j['domain']).intersection(shape(k['domain'])).area>.001 for j in new for k in seams):continue
                spans=[fast_fit(envelope(p,seams+new))[0]for p in pp]
                if max(spans)>=fits[idx]-.5:continue
                score=sum(heuristic(p,s)for p,s in zip(pp,spans))+len(new)*.12+sum(max(0,1-(s/LIMIT)**2)*.6 for s in spans if s<=LIMIT)
                opts.append((score,pp,new))
        if not opts:return None
        opts.sort(key=lambda t:t[0]);_,pp,new=opts[min(int(rng.exponential(.6)),min(2,len(opts)-1))];parts[idx:idx+1]=pp;seams+=new
    else:return None
    if any(fast_fit(envelope(p,seams),True)[0]>LIMIT for p in parts):return None
    new=seams[len(INITIAL):]
    for j in new:
        d=local(shape(j['domain']),j);safe=[float(y)for y in np.arange(-j['span']/2+4,j['span']/2-3,.5)if d.covers(affinity.translate(PROFILES['pocket'].buffer(2),yoff=y))]
        if not safe:return None
        j['keys']=[min(safe,key=lambda y:abs(y-j['span']*v))for v in [-1/3,1/3]]
        if j['keys'][1]-j['keys'][0]<6:return None
    out={'parts':[mapping(p)for p in parts],'joints':new,'count':len(parts),'joint_count':len(new),'quadrant':quadrant,'seed':seed}
    (OUT/f'quadrant-{quadrant}-{seed}.json').write_text(json.dumps(out));return {k:v for k,v in out.items()if k not in ['parts','joints']}

if __name__=='__main__':
    with concurrent.futures.ProcessPoolExecutor(max_workers=3)as pool:
        for r in pool.map(trial,[(q,s)for s in range(700,730)for q in range(4)]):
            if r:print(json.dumps(r),flush=True)
