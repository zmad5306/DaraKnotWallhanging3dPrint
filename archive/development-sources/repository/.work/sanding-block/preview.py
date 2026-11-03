from pathlib import Path
import numpy as np
import trimesh
import manifold3d as mf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
W=Path(__file__).resolve().parent
OUT=W.parents[1]/'output/Sanding-Block-Quarter-Sheet-A1-PETG'
fig=plt.figure(figsize=(11,8),facecolor='#f5f6f7')
ax=fig.add_subplot(111,projection='3d',computed_zorder=False)
ax.set_facecolor('#f5f6f7')
colors={'Base':'#546d7e','Tighteneer':'#546d7e','Lock':'#d3a544','Nut':'#d3a544','Screw':'#d3a544'}
for name,col in colors.items():
    m=trimesh.load_mesh(W/(name+'-placed.stl'))
    body=mf.Manifold(mf.Mesh64(m.vertices,m.faces.astype(np.uint64))).simplify(.025)
    raw=body.to_mesh64()
    tm=trimesh.Trimesh(raw.vert_properties,raw.tri_verts,process=False)
    light=np.array([-.5,-.4,1]);light/=np.linalg.norm(light)
    shade=.55+.45*np.maximum(0,tm.face_normals@light)
    from matplotlib.colors import to_rgb
    cs=shade[:,None]*np.array(to_rgb(col))[None,:]
    coll=Poly3DCollection(tm.triangles,facecolors=cs,edgecolor='none',linewidth=0,rasterized=True)
    ax.add_collection3d(coll)
ax.set_xlim(15,235);ax.set_ylim(15,230);ax.set_zlim(0,65)
ax.set_box_aspect((220,215,65));ax.view_init(55,-65);ax.set_axis_off()
fig.suptitle('Quarter-sheet sanding block',fontsize=22,fontweight='bold',y=.95)
fig.text(.5,.89,'9 × 2¾ in paper • Bambu A1 • PETG',ha='center',fontsize=14,color='#344955')
fig.text(.5,.07,'Five separate parts on one plate. Colors distinguish parts in this preview only.',ha='center',fontsize=11,color='#344955')
fig.text(.5,.035,'Resized from DeepDiverDude’s Compact Sanding Block • physical fit not yet verified',ha='center',fontsize=10,color='#65747c')
plt.savefig(OUT/'preview.png',dpi=150,bbox_inches='tight')
print(OUT/'preview.png')
