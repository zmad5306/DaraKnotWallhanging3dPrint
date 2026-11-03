"""Exact r5 mesh section, including veneer, fused neck and a tall bed tie."""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'.work/python-libs'),str(ROOT/'scripts')]
import numpy as np
import trimesh
import shapely
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.path import Path as MPath
from matplotlib.patches import PathPatch
from build_veneer_wall_cradle_r5 import WORK,OUT

a=np.load(WORK/'V2-candidate.npz')
m=trimesh.Trimesh(a['vertices'],a['faces'],process=False)
g=json.loads((ROOT/'working/bambu/Dara-Photo-Frame-A2L/M-geometry-validation.json').read_text())['skins'][1]
probe=np.array(g['carrier']['bond_probes_print_xyz_mm'][-1])
pose=np.array(g['assembly_to_printer']);normal=pose[:3,2]
path=m.section(plane_origin=[0,probe[1],0],plane_normal=[0,1,0]);region=Polygon()
for loop in path.discrete:region=region.symmetric_difference(Polygon(loop[:,[0,2]]))
c=float(normal@pose[:3,3]);nx,nz=normal[[0,2]]
def above(asmz):
    xs=[-100,500];zs=[(asmz+c-nx*x)/nz for x in xs]
    return Polygon([(xs[0],zs[0]),(xs[1],zs[1]),(xs[1],1000),(xs[0],1000)])
veneer=region.intersection(above(8.6))
neck=region.intersection(above(5.7)).difference(veneer)
carrier=region.difference(above(5.7))
def fill(ax,shape,color):
    for p in shapely.get_parts(shape):
        if p.geom_type!='Polygon' or p.is_empty:continue
        p=orient(p,1);verts=[];codes=[]
        for ring in [p.exterior,*p.interiors]:
            pts=np.array(ring.coords);verts.extend(pts)
            codes.extend([MPath.MOVETO]+[MPath.LINETO]*(len(pts)-2)+[MPath.CLOSEPOLY])
        ax.add_patch(PathPatch(MPath(verts,codes),facecolor=color,edgecolor=color,lw=.3))
fig,axes=plt.subplots(1,2,figsize=(11.5,6),gridspec_kw={'width_ratios':[1,1.25]},facecolor='white')
for ax in axes:
    fill(ax,carrier,'#287a9c');fill(ax,neck,'#bd3044');fill(ax,veneer,'#b87333')
    ax.set_aspect('equal');ax.grid(alpha=.15)
    ax.set_xlabel('Printer X (mm)');ax.set_ylabel('Height above bed (mm)')
px,pz=probe[[0,2]];xpost=px-normal[0]*2.25
axes[0].set_xlim(45,275);axes[0].set_ylim(-5,305)
axes[0].axhline(0,color='#333',lw=3)
axes[0].set_title('Continuous inclined wall reaches bed\nNo tall individual posts',fontsize=11)
axes[0].annotate('Bed',xy=(260,0),xytext=(190,20),arrowprops={'arrowstyle':'->','color':'#333'},fontsize=11)
axes[1].set_xlim(px-7,px+6);axes[1].set_ylim(pz-5,pz+5)
axes[1].set_title('Actual mesh section at its attachment\nred = fused neck; copper = veneer',fontsize=12)
axes[1].annotate('Fused neck',xy=(px,pz),xytext=(px+1,pz-3),arrowprops={'arrowstyle':'->','color':'#bd3044'},color='#bd3044',fontsize=12)
fig.suptitle('r5: veneer - fused neck - carrier - bed',fontsize=16,y=.98)
fig.text(.5,.025,'Exact V2 section. Blue is modeled carrier material. Physical anti-warp performance remains untested.',ha='center',fontsize=10)
fig.subplots_adjust(left=.08,right=.97,top=.84,bottom=.14,wspace=.38)
OUT.mkdir(parents=True,exist_ok=True)
fig.savefig(OUT/'bed-tie-detail.png',dpi=170)

