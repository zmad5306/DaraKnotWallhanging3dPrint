from design_sections import *

D=json.loads(Path('.work/jointed-data.json').read_text())
FP=[shape(x)for x in D['frame']['parts']];MP=[shape(x)for x in D['M']['parts']]
JOINTS=unary_union([shape(j['domain'])for d in D.values()for j in d['joints']])
PHOTO=unary_union([outline('photo_loop_'+str(i)).buffer(4.5) for i in range(1,9)])
TRACK=unary_union(TRACKS).buffer(3)
# A radial 6 mm counterbore plus >=2.5 mm continuous parent material.
NO_SCREW=unary_union([JOINTS.buffer(9),PHOTO.buffer(9),TRACK.buffer(9)])
NO_PIN=unary_union([JOINTS.buffer(6),PHOTO.buffer(6),TRACK.buffer(6)])
SCREWS=[];PINS=[];STATS=[]
for mi,mp in enumerate(MP):
    regions=[]; pinregions=[]
    for fi,fp in enumerate(FP):
        overlap=mp.buffer(-9).intersection(fp.buffer(-9)).intersection(KNOT.buffer(-9)).difference(NO_SCREW)
        pin_area=mp.buffer(-5).intersection(fp.buffer(-5)).intersection(KNOT.buffer(-5)).difference(NO_PIN)
        if not overlap.is_empty:regions.append((fi,overlap))
        if not pin_area.is_empty:pinregions.append((fi,pin_area))
    candidates=[]
    for fi,g in regions:
        x,y,X,Y=g.bounds
        for xx in np.arange(math.ceil(x),X,2):
            for yy in np.arange(math.ceil(y),Y,2):
                pt=Point(xx,yy)
                if g.contains(pt):
                    # Prefer distributed screws in the original raised ribbons.
                    score=min(mp.boundary.distance(pt),FP[fi].boundary.distance(pt),KNOT.boundary.distance(pt),JOINTS.distance(pt),PHOTO.distance(pt),TRACK.distance(pt))
                    candidates.append((fi,pt,score))
    assert candidates,('no screw seat',mi+1)
    count=2 if mi in [0,2,3,5] else 1
    chosen=[]
    if count==2:
        # Optimize separation across the section, with healthy wall margins.
        best=None
        for a in candidates[::max(1,len(candidates)//200)]:
            for b in candidates[::max(1,len(candidates)//200)]:
                dist=a[1].distance(b[1])
                if dist<40:continue
                score=dist+.5*(a[2]+b[2])
                if best is None or score>best[0]:best=(score,a,b)
        assert best,('need separated screws',mi+1)
        chosen=list(best[1:])
    else:chosen=[max(candidates,key=lambda a:a[2]-.02*a[1].distance(mp.centroid))]
    screws=[{'m':mi,'frame':fi,'xy':list(pt.coords[0]),'stock_radius':score}for fi,pt,score in chosen]
    SCREWS+=screws
    pincandidates=[]
    for fi,g in pinregions:
        for sc in screws:g=g.difference(Point(sc['xy']).buffer(14))
        x,y,X,Y=g.bounds if not g.is_empty else [0,0,0,0]
        for xx in np.arange(math.ceil(x),X,2):
            for yy in np.arange(math.ceil(y),Y,2):
                pt=Point(xx,yy)
                if g.contains(pt):pincandidates.append((fi,pt))
    assert pincandidates,('no locating pins',mi+1)
    best=None
    for a in pincandidates[::max(1,len(pincandidates)//250)]:
        for b in pincandidates[::max(1,len(pincandidates)//250)]:
            dist=a[1].distance(b[1])
            if dist<30:continue
            # Keep both locators on one frame section when possible.
            score=dist + (20 if a[0]==b[0] else 0)
            if best is None or score>best[0]:best=(score,a,b)
    assert best,('no pin baseline',mi+1)
    _,a,b=best
    ang=math.degrees(math.atan2(b[1].y-a[1].y,b[1].x-a[1].x))
    for slot,(fi,pt)in enumerate([a,b]):PINS.append({'m':mi,'frame':fi,'xy':list(pt.coords[0]),'slot':bool(slot),'angle':ang})
    STATS.append({'m':mi+1,'screws':len(screws),'dowels':2,'dowel_spacing':a[1].distance(b[1])})
    print(STATS[-1],screws,[list(a[1].coords[0]),list(b[1].coords[0])],flush=True)

# Do not let a feature assigned to one M section approach another section's pin.
all_features=[(Point(r['xy']),6 if 'stock_radius'in r else 4)for r in SCREWS+PINS]
for i,(p,r)in enumerate(all_features):
    for q,s in all_features[i+1:]:assert p.distance(q)>r+s+2

fig,ax=plt.subplots(figsize=(13,10))
draw(ax,FRAME,'#f8f8f8','#e0e0e0');draw(ax,KNOT,'#c7d7d0','#a0aca8')
for mi,mp in enumerate(MP):
    draw(ax,mp,plt.cm.Pastel1(mi),edge='#595959',lw=.5)
    p=mp.representative_point();ax.text(p.x,p.y,'M'+str(mi+1),fontsize=14,ha='center')
draw(ax,JOINTS,'none','#eea4a4',.5)
for k,r in enumerate(SCREWS):
    p=Point(r['xy']);draw(ax,p.buffer(6),'#b54636');ax.text(p.x+9,p.y,'S'+str(k+1),fontsize=9)
for k,r in enumerate(PINS):
    p=Point(r['xy']);draw(ax,p.buffer(4),'#277ca1');ax.text(p.x+7,p.y,'D'+str(k+1),fontsize=8,color='#175570')
ax.set(xlim=(-330,330),ylim=(-220,220),aspect='equal',title='Flat-back M mounts: full-height knot rails only');ax.grid(alpha=.2)
fig.tight_layout();fig.savefig('.work/flat-mount-plan.png',dpi=130)
Path('.work/flat-mount-plan.json').write_text(json.dumps({'screws':SCREWS,'pins':PINS,'summary':STATS},indent=2))
