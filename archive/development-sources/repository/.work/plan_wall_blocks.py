from pathlib import Path
import sys, re, ast, json
sys.path.insert(0,str(Path('.work/python-libs').resolve()))
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
from shapely import affinity
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MP
from shapely.geometry.polygon import orient

SOURCE=Path('working/Dara-Photo-Frame-A1-Jointed.scad').read_text()
def outline(name,scale=.75):
    body=SOURCE.split('module '+name+'() {')[1].split('\n}')[0]
    polys=[]
    for a,b in re.findall(r'polygon\(points = (\[.*?\]), paths = (\[.*?\]), convexity',body,re.S):
        pts=ast.literal_eval(a); paths=ast.literal_eval(b)
        polys.append(Polygon([pts[j] for j in paths[0]],[[pts[j] for j in p] for p in paths[1:]]))
    return affinity.scale(unary_union(polys),scale,scale,origin=(0,0))
def arr(name):return ast.literal_eval(re.search(r'^'+name+r' = (.*?);',SOURCE,re.M).group(1))
KNOT=outline('knot_outline')
FRAME=unary_union([KNOT,outline('fabric_outline').buffer(.1125)])
MASKS=[outline('frame_mask_'+str(i),1)for i in range(20)]
DOMAINS=unary_union([outline('frame_joint_domain_'+str(i),1)for i in range(31)])
ANCHORS=arr('photo_anchors'); NORMALS=arr('photo_normals')
PIVOTS=[[a[0]*.75+n[0]*9.5,a[1]*.75+n[1]*9.5]for aa,nn in zip(ANCHORS,NORMALS)for a,n in zip(aa,nn)]
SWEEP=unary_union([Point(p).buffer(15.01)for p in PIVOTS])
HARDWARE=unary_union([Point(m[2]).buffer(9)for m in arr('screw_mounts')])
PHOTOS=unary_union([outline('photo_loop_'+str(i)).buffer(4)for i in range(1,9)])
BASE=box(-70,-14,70,14).buffer(-2).buffer(2)
KEYS=unary_union([box(y-12,-7,y+12,7).buffer(.2)for y in [-25,25]])
def assess(x,y):
    b=affinity.translate(BASE,x,y);k=affinity.translate(KEYS,x,y-6*(1 if y>0 else -1))
    owners=[i for i,m in enumerate(MASKS)if m.contains(k.buffer(3))]
    if not FRAME.contains(b.buffer(2)) or not KNOT.contains(k.buffer(2)) or b.distance(SWEEP)<3 or b.distance(PHOTOS)<3 or b.distance(HARDWARE)<3 or k.distance(DOMAINS)<3:return None
    return dict(x=x,y=y,owner=owners,edge=KNOT.boundary.distance(b),joint=k.distance(DOMAINS),sweep=b.distance(SWEEP),photo=b.distance(PHOTOS),hardware=b.distance(HARDWARE))
def draw(ax,g,c):
    for p in ([g]if g.geom_type=='Polygon'else g.geoms):
        if p.is_empty:continue
        verts=[];codes=[]
        for r in [orient(p,1).exterior,*orient(p,1).interiors]:
            v=list(r.coords);verts+=v;codes +=[MP.MOVETO]+[MP.LINETO]*(len(v)-2)+[MP.CLOSEPOLY]
        ax.add_patch(PathPatch(MP(verts,codes),facecolor=c,edgecolor='white',lw=.3))
if __name__=='__main__':
    results=[]
    for x in range(80,241,4):
        for y in range(200,281,2):
            checks=[assess(sx*x,sy*y)for sx,sy in [(-1,1),(1,1),(-1,-1),(1,-1)]]
            if all(checks):results.append((x*y,checks))
    results.sort(key=lambda r:r[0],reverse=True)
    print('symmetric options',len(results));print(json.dumps(results[:3],indent=2))
    fig,ax=plt.subplots(figsize=(10,10));draw(ax,KNOT,'#b8c5c0');draw(ax,PHOTOS,'#dde7ee');draw(ax,DOMAINS,'#dcabaa');draw(ax,SWEEP,'#e5b961');draw(ax,HARDWARE,'#b4a1d1')
    if results:
        for r in results[0][1]:draw(ax,affinity.translate(BASE,r['x'],r['y']),'#287b8e');ax.text(r['x'],r['y'],str(r['owner']+1),ha='center',color='white')
    ax.set(xlim=(-470,470),ylim=(-470,470),aspect='equal');ax.grid(alpha=.2)
    Path('.work/wall-blocks').mkdir(exist_ok=True)
    fig.savefig('.work/wall-blocks/plan.png',dpi=150)
    Path('.work/wall-blocks/locations.json').write_text(json.dumps(results[:3],indent=2))
