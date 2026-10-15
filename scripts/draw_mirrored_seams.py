"""Plot the actual before/after cut axes against unchanged artwork."""
import json
from repartition_mirrored_frame import *
from matplotlib import pyplot as plt
from matplotlib.path import Path as MPath
from matplotlib.patches import PathPatch
from shapely.geometry.polygon import orient

def fill(ax,g,color,z=1,alpha=1):
    if g.is_empty:return
    for p in polys(g):
        p=orient(p,1);verts=[];codes=[]
        for r in [p.exterior,*p.interiors]:
            q=list(r.coords);verts+=q;codes += [MPath.MOVETO]+[MPath.LINETO]*(len(q)-2)+[MPath.CLOSEPOLY]
        ax.add_patch(PathPatch(MPath(verts,codes),facecolor=color,edgecolor='none',zorder=z,alpha=alpha))

def main():
    d=json.loads(PLAN.read_text());old=(BASE/REL).read_text();new=CAD.read_text()
    knot=artwork(new,'knot_outline');fabric=artwork(new,'fabric_outline').buffer(.1125,join_style=2);letter=artwork(new,'letter_outline');whole=knot.union(fabric)
    blue=fabric.buffer(2.75).difference(fabric.buffer(1.25)).intersection(knot)
    fig,axs=plt.subplots(1,2,figsize=(13,7),facecolor='#f4f1eb')
    for ax,text,title in zip(axs,[old,new],['Previous layout | 31 seams','Implemented layout | 32 seams']):
        ax.set_facecolor('#f4f1eb');fill(ax,whole,'#c2ab84');fill(ax,knot,'#fcfcf8',2);fill(ax,blue,'#295d8a',3)
        for p in polys(whole):ax.plot(*np.array(p.exterior.coords).T,color='#a6ada9',linewidth=.45,zorder=4)
        for j in read_array(text,'frame_joints'):
            g=line(j,4).intersection(whole).difference(letter)
            lines=[g] if g.geom_type=='LineString' else list(g.geoms)
            for q in lines:
                if q.is_empty:continue
                ax.plot(*np.array(q.coords).T,color='#a84435' if j[4]>100 else '#344e60',linewidth=1.25,zorder=5)
        fill(ax,letter,'#b97c55',6)
        ax.set(xlim=(-485,485),ylim=(-490,490),aspect='equal');ax.axis('off');ax.set_title(title,loc='left',fontsize=15,color='#203039',pad=15)
    fig.text(.5,.065,'20 frame sections in both layouts. New seams: 67.3-75.1 mm. Same 18 mm keyed laps.',ha='center',fontsize=12,color='#203039')
    fig.text(.5,.025,'Front-view schematic; seams emphasized for review. Artwork and M face are unchanged.',ha='center',fontsize=10,color='#647079')
    fig.subplots_adjust(left=.025,right=.975,top=.9,bottom=.11,wspace=.08)
    fig.savefig(REVIEW/'seam-comparison.png',dpi=170,facecolor=fig.get_facecolor());plt.close(fig)
    print(REVIEW/'seam-comparison.png')

if __name__=='__main__':main()
