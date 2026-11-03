import sys,json,zipfile
from pathlib import Path
sys.path.insert(0,'scripts')
import validate_print_project as v
from add_blue_ribbon_edge import artwork,polygons,in_print_coordinates
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from shapely.geometry import Point,LineString
out=Path('.work/curve-review'); out.mkdir(exist_ok=True)
cad=v.CAD.read_text()
base=json.loads((v.PACKAGE/'project-validation.json').read_text())
import re
placement=json.loads(re.search(r'^frame_placements\s*=\s*(\[.*?\]);',cad,re.M|re.S)[1])
knot=artwork(cad,'knot_outline'); fabric=artwork(cad,'fabric_outline').buffer(.1125,quad_segs=16)
blue=(fabric.buffer(2.75,quad_segs=16)-fabric.buffer(1.25,quad_segs=16)).intersection(knot).simplify(.001)
fig,ax=plt.subplots(figsize=(12,12))
for shape,color in [(knot,'gray'),(fabric,'tan'),(blue,'blue')]:
    local=in_print_coordinates(shape,placement[0])
    for p in polygons(local):
        for ring in [p.exterior,*p.interiors]:
            xy=np.array(ring.coords); ax.plot(*xy.T,color=color,lw=.7)
ax.set(xlim=(-125,125),ylim=(-125,125),aspect='equal');ax.grid()
fig.savefig(out/'f1-contours.png',dpi=180)
# Rank isolated turns flanked by nearly parallel tangents, excluding intentional corners.
records=[]
for name,shape in [('knot',knot),('fabric',fabric),('blue',blue)]:
    for pi,p in enumerate(polygons(shape)):
        for ri,ring in enumerate([p.exterior,*p.interiors]):
            a=np.array(ring.coords)[:-1]; prev=a-np.roll(a,1,axis=0); nxt=np.roll(a,-1,axis=0)-a
            ang=np.degrees(np.arctan2(prev[:,0]*nxt[:,1]-prev[:,1]*nxt[:,0],(prev*nxt).sum(axis=1)))
            for i in np.where(np.abs(ang)>12)[0]:
                records.append(dict(shape=name,poly=pi,ring=ri,index=int(i),xy=a[i].tolist(),angle=round(float(ang[i]),3),previous_length=float(np.linalg.norm(prev[i])),next_length=float(np.linalg.norm(nxt[i]))))
(out/'turns.json').write_text(json.dumps(records,indent=2))
print('turns',len(records));print('first plate',base['plate_layout'][0]); print('knot vertices',sum(len(r.coords) for p in polygons(knot) for r in [p.exterior,*p.interiors]))
suspects=[]
for ri,ring in enumerate([knot.exterior,*knot.interiors]):
    a=np.array(ring.coords)[:-1]; prev=a-np.roll(a,1,axis=0); nxt=np.roll(a,-1,axis=0)-a
    ang=np.degrees(np.arctan2(prev[:,0]*nxt[:,1]-prev[:,1]*nxt[:,0],(prev*nxt).sum(axis=1)))
    for i in np.where((np.abs(ang)>6)&(np.abs(ang)<35))[0]:
        if min(np.linalg.norm(prev[i]),np.linalg.norm(nxt[i]))<.7: continue
        if any(np.linalg.norm(a[i]-np.array(s['xy']))<5 for s in suspects):continue
        suspects.append(dict(ring=ri,index=int(i),xy=a[i].tolist(),angle=round(float(ang[i]),3)))
(out/'suspects.json').write_text(json.dumps(suspects,indent=2))
print('suspects',len(suspects))
for page in range((len(suspects)+11)//12):
    fig,axs=plt.subplots(3,4,figsize=(16,12))
    for ax,rec in zip(axs.flat,suspects[page*12:(page+1)*12]):
        x,y=rec['xy']
        for shape,color in [(knot,'black'),(fabric,'#b99352'),(blue,'#295d8a')]:
            for p in polygons(shape):
                for ring in [p.exterior,*p.interiors]:
                    xy=np.array(ring.coords);ax.plot(*xy.T,color=color,lw=1,marker='.',ms=2)
        ax.plot(x,y,'ro',ms=5); ax.set(xlim=(x-7,x+7),ylim=(y-7,y+7),aspect='equal')
        ax.set_title(f"#{suspects.index(rec)+1}: {x:.2f}, {y:.2f}\nturn {rec['angle']:.1f} deg",fontsize=9);ax.grid(alpha=.2)
    fig.tight_layout();fig.savefig(out/f'suspects-{page+1}.png',dpi=140);plt.close(fig)
