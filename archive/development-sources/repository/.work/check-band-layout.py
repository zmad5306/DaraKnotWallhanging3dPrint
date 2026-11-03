import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'scripts'))
from prepare_hammered_m_project import *
from shapely.ops import split
from shapely.geometry import Point,box as box2d
cad=(ROOT/'working/Dara-Photo-Frame-A1-Jointed.scad').read_text()
outline=artwork(cad,'letter_outline')
def locate(g,p,a):return affinity.translate(affinity.rotate(g,a,origin=(0,0)),*p)
def partition(y):
    js=[(2,3,[32.336138117987566,136.58266699147163],57.06125907870988,35),
        (2,1,[-32.336138117987566,136.58266699147163],122.93874092129012,35),
        (4,1,[-257,y],90,65),(6,3,[257,y],90,65),(2,5,[0,0],270,48)]
    regions=[outline]
    for j in js:
        line=locate(LineString([(0,-j[4]),(0,j[4])]),j[2],j[3]);new=[]
        for r in regions:new.extend(split(r,line).geoms)
        regions=new
    refs=[[-230,110],[0,90],[230,110],[-220,-130],[0,-100],[220,-130]]
    regions=[next(r for r in regions if r.contains(Point(*p))) for p in refs]
    assert len({r.wkb for r in regions})==6
    return js,regions
for y in [-35,-40,-45,-50,-55,-60,-65]:
    js,regions=partition(y);allbest=[]
    for n,r in enumerate(regions,1):
        plan=r
        for j in js:
            if j[0]==n:plan=plan.union(locate(box2d(-1,-j[4],18,j[4]),j[2],j[3]).intersection(outline))
        xy=np.array(plan.convex_hull.exterior.coords);v=np.concatenate([np.column_stack([xy,np.full(len(xy),z)]) for z in [0,13.5]])
        base=v@((rotation(55,(1,0,0))@rotation(1.5))[:3,:3].T)
        best=None
        for yaw in np.arange(0,180,.5):
            rotated=base@rotation(yaw)[:3,:3].T;ext=rotated.max(axis=0)-rotated.min(axis=0)
            score=max(ext[:2])
            if best is None or score<best[0]:best=(score,float(yaw),ext.tolist())
        allbest.append(best)
    distances=[]
    for j in js:
        normal=rotation(j[3])[:2,0]
        relevant=[s for s in read_array(cad,'screw_mounts') if abs(s[2][0]-j[2][0])<80]
        distances.append(min(abs(np.dot(np.array(s[2])-j[2],normal)) for s in relevant))
    print(json.dumps(dict(y=y,parts=allbest,min_screw_plane_distances=distances)))
