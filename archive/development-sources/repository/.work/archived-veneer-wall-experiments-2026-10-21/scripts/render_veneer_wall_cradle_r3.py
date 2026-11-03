"""Actual r3 geometry. Translucency in the cutaway is display-only."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'.work/python-libs'),str(ROOT/'scripts')]
import numpy as np
import trimesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from build_veneer_wall_cradle_r3 import WORK,OUT
from development_3mf import solid,mesh
import manifold3d as mf
base=mesh(solid(trimesh.load_mesh(WORK/"V2-production.ply",process=False)) ^ mf.Manifold.cube([330,320,1.6]))
fig=plt.figure(figsize=(14,7),facecolor='white')
for k in range(2):
 ax=fig.add_subplot(1,2,k+1,projection='3d')
 colors={'panel':(0.12,.46,.65,1 if k==0 else .14),'rear':(.4,.44,.49,1 if k==0 else .14),'webs':(.1,.62,.5,1),'upper':(.73,.4,.16,1 if k==0 else .18)}
 ax.add_collection3d(Poly3DCollection(base.triangles,facecolors=(.4,.44,.49,.7),edgecolors='none',rasterized=True))
 for name in ['rear','webs','panel','upper']:
  m=trimesh.load_mesh(WORK/f'V2-{name}.ply',process=False)
  ax.add_collection3d(Poly3DCollection(m.triangles,facecolors=colors[name],edgecolors='none',rasterized=True))
 ax.add_collection3d(Poly3DCollection([[[42,20,-1],[280,20,-1],[280,300,-1],[42,300,-1]]],facecolors=(.9,.91,.92,.5),edgecolors='#666',lw=.5))
 ax.set_xlim(40,280);ax.set_ylim(25,295);ax.set_zlim(0,310)
 ax.set_box_aspect((240,270,310));ax.view_init(elev=19,azim=-32);ax.set_axis_off()
 ax.set_title('Complete V2: veneer and solid walls' if k==0 else 'Cutaway: two broad internal webs',fontsize=13,pad=-3)
fig.suptitle('r3: continuous walls to the bed; no tall individual posts',fontsize=18,y=.97)
fig.text(.5,.08,'Copper: original veneer and necks | Blue: inclined wall | Gray: rear wall | Green: two connecting webs',ha='center',fontsize=11)
fig.text(.5,.045,'Front wall 1.2 mm; rear wall and webs 1.0 mm. Transparency only reveals the interior; all walls print solid.',ha='center',fontsize=10)
fig.text(.5,.015,'Actual saved mesh. Physical stiffness, bed adhesion and resistance to warping remain untested.',ha='center',fontsize=10)
fig.subplots_adjust(left=.01,right=.99,bottom=.12,top=.87,wspace=0)
OUT.mkdir(parents=True,exist_ok=True)
fig.savefig(OUT/'wall-structure.png',dpi=160)
