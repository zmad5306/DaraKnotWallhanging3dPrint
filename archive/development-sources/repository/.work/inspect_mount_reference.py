from pathlib import Path
import sys,re,ast
sys.path.insert(0,str(Path('.work/python-libs').resolve()))
import numpy as np,manifold3d as md
from shapely.geometry import Polygon
text=Path('reference/tested-lap-joints/Tested-Lap-Joints.scad').read_text()
def solid(name):
    block=text.split('module '+name+'() {')[1].split('\n}')[0]
    a,b=re.search(r'polyhedron\(points=(\[.*?\]),\s*faces=(\[.*?\]), convexity',block,re.S).groups()
    return md.Manifold(md.Mesh64(np.array(ast.literal_eval(a)),np.array(ast.literal_eval(b),dtype=np.uint64)[:,::-1].copy()))
for name in ['m_boss','straight_tongue','curved_tongue','washer']:
    s=solid(name)
    print(name,'bounds',s.bounding_box(),'volume',s.volume())
    for z in ([.5,2.9,3.1,4.9,5.1,8,12,16.9]if name=='m_boss'else[.5,1.5,3,5,7,8.5,9,9.5,10,11,12,13,13.9]):
        rings=s.slice(z).to_polygons()
        small=[]
        for r in rings:
            p=Polygon(r)
            if p.area<160:
                x,y,X,Y=p.bounds
                if .8<(X-x)/(Y-y)<1.2:small.append({'xy':list(p.centroid.coords[0]),'size':[X-x,Y-y],'area':p.area})
        print(z,small)
