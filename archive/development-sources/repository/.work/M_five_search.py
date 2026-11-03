from repartition_search import *
import itertools

def trial(seed):
    rng=np.random.default_rng(seed);best=None
    for it in range(12000):
        # Three independent leg cuts, then an off-centre cut through one arch.
        yl,yr,yc=rng.uniform(80,140),rng.uniform(80,140),rng.uniform(25,110)
        slopes=rng.uniform(-.3,.3,3)
        cuts=[LineString([(-380,yl-100*slopes[0]),(-165,yl+115*slopes[0])]),LineString([(165,yr-115*slopes[1]),(380,yr+100*slopes[1])]),LineString([(-80,yc-80*slopes[2]),(80,yc+80*slopes[2])])]
        x=rng.uniform(50,125)*rng.choice([-1,1]);sx=rng.uniform(-.4,.4)
        cuts.append(LineString([(x-60*sx,80),(x+100*sx,240)]))
        ps=[LETTER];basic=[]
        valid=True
        for cut in cuts:
            affected=[(i,p)for i,p in enumerate(ps)if len(geoms(split(p,cut)))>1]
            if len(affected)!=1:valid=False;break
            idx,p=affected[0];pp=geoms(split(p,cut))
            if len(pp)!=2:valid=False;break
            shared=p.intersection(cut)
            if len(lines(shared))!=1 or shared.length<25 or any(shared.distance(shape(j['line']))<24 for j in basic):valid=False;break
            dx,dy=np.array(cut.coords[-1])-np.array(cut.coords[0]);angle=math.degrees(math.atan2(-dx,dy))
            new=make_seams(p,cut,angle,Polygon())
            if not new:valid=False;break
            basic+=new;ps[idx:idx+1]=pp
        if not valid or len(ps)!=5:continue
        base=[fast_fit(p)[0]for p in ps]
        mx=max(base)
        if best is None or mx<best:best=mx;print('seed',seed,'iteration',it,'best base',round(best,3),flush=True)
        if mx>LIMIT:continue
        for flips in itertools.product([False,True],repeat=4):
            seams=[]
            for cut,j,flip in zip(cuts,basic,flips):
                if not flip:seams.append(j);continue
                # Domain based on full original stock; clips to the same local stroke.
                jj=make_seams(LETTER,cut,j['angle']+180,Polygon())
                if jj is None or len(jj)!=1:break
                seams+=jj
            if len(seams)!=4:continue
            if any(shape(j['domain']).intersection(shape(k['domain'])).area>.001 for j,k in itertools.combinations(seams,2)):continue
            if any(fast_fit(envelope(p,seams),True)[0]>LIMIT for p in ps):continue
            if any(not viable_mount(p,seams)for p in ps):continue
            for j in seams:
                d=local(shape(j['domain']),j);safe=[float(y)for y in np.arange(-j['span']/2+4,j['span']/2-3,.5)if d.covers(affinity.translate(PROFILES['pocket'].buffer(2),yoff=y))]
                if not safe:break
                j['keys']=[min(safe,key=lambda y:abs(y-j['span']*v))for v in [-1/3,1/3]]
                j['male']=next(i for i,p in enumerate(ps)if p.contains(Point(j['male_probe'])));j['female']=next(i for i,p in enumerate(ps)if p.contains(Point(j['female_probe'])))
            else:
                out={'parts':[mapping(p)for p in ps],'joints':seams,'count':5,'joint_count':4,'family':'M','seed':seed,'maxdim':max(fast_fit(envelope(p,seams),True)[0]for p in ps)}
                (OUT/f'M-five-{seed}.json').write_text(json.dumps(out));print('SUCCESS',seed,out['maxdim'],flush=True);return out['maxdim']
    return best

if __name__=='__main__':print(trial(41))
