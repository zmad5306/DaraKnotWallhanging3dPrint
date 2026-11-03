import sys, json
from pathlib import Path
sys.path.insert(0, str(Path('.work/python-libs').resolve()))
import numpy as np
import trimesh
from shapely.geometry import shape, Polygon
from shapely.ops import unary_union
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MPath

base = Path(r'C:\Users\Zach\Nextcloud\3D prints\Dara-Solid-Joint-Backs-v26')
d = json.loads((base/'project-data.json').read_text())
rails = shape(json.loads((base/'source/approved-knot-master.geojson').read_text()))
holes = sorted([Polygon(q) for q in rails.interiors], key=lambda p:p.area, reverse=True)
print('rails',rails.is_valid,rails.bounds, len(holes),len(rails.exterior.coords))
for i,h in enumerate(holes):
    print('hole',i,round(h.area,2),[round(x,1) for x in h.centroid.coords[0]])

def draw(ax,g,face):
    for p in [g] if g.geom_type=='Polygon' else g.geoms:
        vertices=[]; codes=[]
        from shapely.geometry.polygon import orient
        p=orient(p,1)
        for ring in [p.exterior,*p.interiors]:
            points=list(ring.coords)
            vertices.extend(points); codes.extend([MPath.MOVETO]+[MPath.LINETO]*(len(points)-2)+[MPath.CLOSEPOLY])
        ax.add_patch(PathPatch(MPath(vertices,codes),facecolor=face,edgecolor='none'))

letter_parts=[]
for r in d['parts']:
    if '/letter/' not in r['file']:continue
    mesh=trimesh.load_mesh(base/r['file']); mesh.apply_transform(r['assembly_transform'])
    print(r['part'],mesh.bounds.tolist(),np.unique(np.round(mesh.vertices[:,2],2))[-15:])
    face=unary_union([Polygon(t[:,:2]) for t,n in zip(mesh.triangles,mesh.face_normals) if n[2]>.9 and t[:,2].mean()>30.9 and Polygon(t[:,:2]).area>1e-7])
    letter_parts.append(face)
letter=unary_union(letter_parts).buffer(.12,join_style=2).buffer(-.12,join_style=2).simplify(.02,preserve_topology=True)
print('letter',letter.geom_type,letter.is_valid,letter.bounds,len(letter.interiors) if letter.geom_type=='Polygon' else len(letter.geoms))
fig,ax=plt.subplots(figsize=(10,10),facecolor='#f6f5f0')
draw(ax,rails,'#666e65')
for i in list(range(1,9))+list(range(21,25)):draw(ax,holes[i],'#c6b798')
draw(ax,letter,'#bd8c4c')
for i,h in enumerate(holes):
    x,y=h.representative_point().coords[0]; ax.text(x,y,str(i),ha='center',va='center',fontsize=10,color='black')
ax.set(xlim=(-650,650),ylim=(-650,650),aspect='equal');ax.axis('off')
fig.savefig('.work/outline-inspection.png',dpi=140)
from shapely.geometry import mapping
Path('.work/letter.json').write_text(json.dumps(mapping(letter)))
