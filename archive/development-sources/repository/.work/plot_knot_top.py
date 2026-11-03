import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import add_knot_glue_sample as s
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from shapely.plotting import plot_polygon
fig,ax=plt.subplots()
for name in s.NAMES:
 m=s.load_body(name)
 for z,col in [(1,'#ccc'),(7,'#eea'),(9.85,'#b85'),(13.49,'#eee')]:
  p=s.mesh_slice(m,z)
  for poly in getattr(p,'geoms',[p]):plot_polygon(poly,ax=ax,add_points=False,color=col,alpha=1,linewidth=.3)
 blue=s.mesh_slice(s.trimesh.load_mesh(s.WORK/f'{name}-color-4.ply'),13.2)
 for poly in getattr(blue,'geoms',[blue]):plot_polygon(poly,ax=ax,add_points=False,color='#236abb',alpha=1)
ax.set_aspect('equal');fig.savefig(s.WORK/'top-debug.png',dpi=140)
