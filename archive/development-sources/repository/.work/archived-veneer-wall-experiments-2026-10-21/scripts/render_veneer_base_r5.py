"""Exact horizontal mesh sections showing removal of the old base framework."""
import json
from pathlib import Path
import sys

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
from matplotlib.patches import PathPatch,Patch
from build_veneer_wall_cradle_r5 import OUT,WORK


def region(m,height=.1):
    path=m.section(plane_origin=[0,0,height],plane_normal=[0,0,1])
    result=Polygon()
    if path is not None:
        for loop in path.discrete:
            result=result.symmetric_difference(Polygon(loop[:,:2]).buffer(0))
    return result


def fill(ax,shape,color):
    for p in shapely.get_parts(shape):
        if p.geom_type!='Polygon' or p.is_empty:continue
        p=orient(p,1);verts=[];codes=[]
        for ring in [p.exterior,*p.interiors]:
            points=np.array(ring.coords);verts.extend(points)
            codes.extend([MPath.MOVETO]+[MPath.LINETO]*(len(points)-2)+[MPath.CLOSEPOLY])
        ax.add_patch(PathPatch(MPath(verts,codes),facecolor=color,edgecolor=color,lw=.2))


def model(revision,number):
    a=np.load(ROOT/f'.work/veneer-wall-cradle-{revision}/V{number}-candidate.npz')
    return trimesh.Trimesh(a['vertices'],a['faces'],process=False)


def draw(numbers,filename):
    fig,axes=plt.subplots(len(numbers),2,figsize=(11,5*len(numbers)+1),squeeze=False,facecolor='white')
    for row,i in enumerate(numbers):
        before=region(model('r4',i));after=region(model('r5',i))
        bands=region(trimesh.load_mesh(WORK/f'V{i}-bands.ply',process=False))
        walls=shapely.union_all([region(trimesh.load_mesh(WORK/f'V{i}-{name}.ply',process=False)) for name in ['panel','rear','webs']])
        bounds=before.union(after).bounds
        for j,ax in enumerate(axes[row]):
            fill(ax,before if j==0 else after,'#777f87' if j==0 else '#287a9c')
            if j:
                fill(ax,bands,'#de9c34');fill(ax,walls,'#287a9c')
            ax.set_aspect('equal');ax.set_xlim(bounds[0]-8,bounds[2]+8);ax.set_ylim(bounds[1]-8,bounds[3]+8)
            ax.set_xlabel('Printer X (mm)');ax.set_ylabel('Printer Y (mm)')
            ax.spines[['right','top']].set_visible(False)
            ax.set_title(f'V{i}: '+('r4 old base framework' if j==0 else 'r5 walls + two thin bed bands'),fontsize=12)
    fig.suptitle('Old frame removed; front and rear walls tied at the bed',fontsize=16,y=.985)
    fig.legend(handles=[Patch(color='#777f87',label='Previous footprint'),Patch(color='#287a9c',label='Wall footprint'),Patch(color='#de9c34',label='4 mm wide bands under connecting walls')],loc='lower center',bbox_to_anchor=(.5,.04),ncol=3,fontsize=9,frameon=False)
    fig.text(.5,.018,'Actual model section 0.1 mm above bed. Bands are 0.6 mm thick (three layers). Physical adhesion remains untested.',ha='center',fontsize=9)
    fig.subplots_adjust(left=.07,right=.98,bottom=.13 if len(numbers)==1 else .12,top=.9 if len(numbers)==1 else .95,hspace=.24,wspace=.25)
    OUT.mkdir(parents=True,exist_ok=True);fig.savefig(OUT/filename,dpi=170);plt.close(fig)


if __name__=='__main__':
    draw([2],'bed-base-before-after.png')
    draw([1,2,3],'all-bed-footprints.png')
