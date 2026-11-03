import sys,json
sys.path[:0]=['.work/python-libs','scripts']
import trimesh,numpy as np,shapely
from pathlib import Path
from development_3mf import solid
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,axs=plt.subplots(1,3,figsize=(15,10));root=Path('.work/veneer-face-r9')
for i,ax in enumerate(axs,1):
 g=json.loads(Path(f'.work/veneer-wall-cradle-r5/V{i}-geometry.json').read_text());pose=np.array(g['assembly_to_printer']);m=trimesh.load(f'.work/veneer-wall-cradle-r5/V{i}-panel.ply');m.apply_transform(np.linalg.inv(pose));p=shapely.Polygon()
 for q in solid(m).slice(3.8).to_polygons():p=p.symmetric_difference(shapely.Polygon(q))
 h=p.convex_hull
 print(i,'area',p.area,'hull extra',h.area-p.area,'width',p.bounds,'verts',len(p.exterior.coords),flush=True)
 coords=np.array(p.exterior.coords); print('side coords',coords[(coords[:,0]<p.bounds[0]+1)|(coords[:,0]>p.bounds[2]-1)].tolist(),flush=True)
 ax.fill(*h.exterior.xy,color='salmon');ax.fill(*p.exterior.xy,color='wheat');ax.set_aspect('equal');ax.set_title(f'V{i}; convex addition {(h.area-p.area)*1.2*1.24/1000:.2f} g');ax.grid()
 (root/f'V{i}-panel-footprint.json').write_text(json.dumps(shapely.geometry.mapping(p)))
fig.tight_layout();fig.savefig(root/'panel-outline.png',dpi=140)
