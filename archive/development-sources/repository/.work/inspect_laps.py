from pathlib import Path
import sys, ast, re, json
sys.path.insert(0,str(Path('.work/python-libs').resolve()))
import numpy as np
import trimesh, manifold3d as md
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
from shapely.ops import unary_union

def solid(m):
    return md.Manifold(md.Mesh64(np.array(m.vertices),np.array(m.faces,dtype=np.uint64)))

fig, axs=plt.subplots(2,5,figsize=(16,7))
for row,name in enumerate(['straight-tongue','straight-socket']):
    m=trimesh.load_mesh('reference/tested-lap-joints/meshes/'+name+'.stl')
    print(name,'Z levels',np.unique(np.round(m.vertices[:,2],4)).tolist())
    s=solid(m)
    if row: s=s.translate([28.518748855,0,0])
    for ax,z in zip(axs[row],[.1,4.79,4.9,6.2,10]):
        for poly in s.slice(z).to_polygons():
            ax.plot(poly[:,0],poly[:,1])
        ax.set_aspect('equal');ax.grid();ax.set_title(name+' z='+str(z))
    print(name,'positive-x vertices at joint',np.unique(np.round(m.vertices[(m.vertices[:,2]>4.81)&(m.vertices[:,2]<8)],4),axis=0).tolist()[:100])
fig.tight_layout();fig.savefig('.work/lap-sections.png',dpi=130)
