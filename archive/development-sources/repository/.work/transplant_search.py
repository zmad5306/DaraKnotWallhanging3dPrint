from quadrant_v2 import *
import itertools

def transplant(q,filename):
    template=json.loads(filename.read_text());ps=[BASE[q]];seams=[]
    # Rotate/reflection of a fresh five-part quadrant template, clipped again
    # against the original outline. Initial cross-rail seams remain staggered.
    tq=template['quadrant'];signs=[(-1,1),(-1,-1),(1,1),(1,-1)];sx=signs[q][0]/signs[tq][0];sy=signs[q][1]/signs[tq][1]
    prev=None
    for j in template['joints']:
        a=math.radians(j['angle']);n=np.array([math.cos(a)*sx,math.sin(a)*sy]);c=np.array(j['centre'])*[sx,sy];proj=float(c@n)
        if prev is not None and abs(proj-prev[1])<.01 and abs(n@prev[0])>.999999:continue
        prev=(n,proj);t=np.array([-n[1],n[0]]);cut=LineString([n*proj-t*1500,n*proj+t*1500]);probe=Point(c)
        ix=min(range(len(ps)),key=lambda i:ps[i].distance(probe));p=ps[ix];pp=geoms(split(p,cut))
        if len(pp)<2:return None
        angle=math.degrees(math.atan2(n[1],n[0]));new=make_seams(p,cut,angle,PHOTO_GUARD)
        if not new:return None
        ps[ix:ix+1]=pp;seams+=new
    if len(ps)!=5:return None
    if any(shape(j['domain']).intersection(shape(k['domain'])).area>.001 for j in seams for k in INITIAL):return None
    if any(fast_fit(envelope(p,seams+INITIAL),True)[0]>LIMIT for p in ps):return None
    for j in seams:
        d=local(shape(j['domain']),j);safe=[float(y)for y in np.arange(-j['span']/2+4,j['span']/2-3,.5)if d.covers(affinity.translate(PROFILES['pocket'].buffer(2),yoff=y))]
        if not safe:return None
        j['keys']=[min(safe,key=lambda y:abs(y-j['span']*v))for v in [-1/3,1/3]]
    return {'parts':[mapping(p)for p in ps],'joints':seams,'count':5,'joint_count':len(seams),'quadrant':q,'template':str(filename)}

if __name__=='__main__':
    for q in range(4):
        for f in OUT.glob('quad-v2-*.json'):
            if json.loads(f.read_text())['count']!=5:continue
            r=transplant(q,f)
            if r:
                out=OUT/f'transplant-{q}-{f.stem}.json';out.write_text(json.dumps(r));print(q,f.name,'success',flush=True)
