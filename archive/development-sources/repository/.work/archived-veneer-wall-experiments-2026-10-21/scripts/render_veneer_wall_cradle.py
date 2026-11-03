"""Preview only: translucent carrier walls reveal the two solid internal webs."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.work/python-libs'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
import trimesh
from build_veneer_wall_cradle import WORK,OUT

fig=plt.figure(figsize=(14,5.8),facecolor='white')
for i in [1,2,3]:
    m=trimesh.load_mesh(WORK/f'V{i}-new-support.ply',process=False)
    ax=fig.add_subplot(1,3,i,projection='3d')
    web=np.abs(m.face_normals[:,1])>.99
    colors=np.tile([.65,.38,.18,.25],(len(m.faces),1));colors[web]=[.08,.35,.50,.90]
    ax.add_collection3d(Poly3DCollection(m.triangles,facecolors=colors,edgecolors='none',rasterized=True))
    ax.set_xlim(40,280);ax.set_ylim(25,295);ax.set_zlim(0,310)
    ax.set_box_aspect((240,270,310));ax.view_init(elev=22,azim=-30);ax.set_axis_off()
    ax.set_title(f'V{i}: backing + rear wall + two webs',fontsize=11,pad=-2)
fig.suptitle('Wall-cradle r1 | support geometry only',fontsize=17,y=.98)
fig.text(.5,.065,'Outer walls are translucent here to reveal the webs. All walls print solid.',ha='center',fontsize=10)
fig.text(.5,.04,'Veneer and retained necks are omitted from this view. All support prints in copper silk.',ha='center',fontsize=10)
fig.text(.5,.015,'A2L / saved 55-degree veneer pose / 1.2 mm walls / no cutter openings / physical trial pending',ha='center',fontsize=10,color='#555555')
fig.subplots_adjust(left=.01,right=.99,bottom=.12,top=.83,wspace=0)
fig.savefig(OUT/'support-structure.png',dpi=160)
