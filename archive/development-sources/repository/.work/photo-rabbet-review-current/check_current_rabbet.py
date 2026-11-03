import sys,json,math,collections,zipfile
from pathlib import Path
sys.path.insert(0,'scripts')
from organize_root_projects import rows
from mesh_sections import mesh_slice
import shapely
from shapely.geometry import Point,LineString,Polygon
from shapely import affinity
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
out=Path('.work/photo-rabbet-review-current');ps=json.loads((out/'current-P2-paths.json').read_text())
s,oo=rows(Path('Knot.3mf'));o=oo[1];t=o['transform']
section=shapely.union_all([mesh_slice(p['mesh'],2.5) for p in o['parts'] if p['subtype']=='normal_part']).buffer(.0001).buffer(-.0001)
holes=[Polygon(h) for p in getattr(section,'geoms',[section]) for h in p.interiors];opening=max(holes,key=lambda p:p.area)
opening=affinity.affine_transform(opening,[t[0,0],t[0,1],t[1,0],t[1,1],t[0,3],t[1,3]])
roi=opening.boundary.buffer(5)
roof=[p for p in ps if p['feature']=='Support interface' and p['z']==2.2 and roi.intersects(LineString(p['segment']))]
wall=[p for p in ps if p['feature']=='Overhang wall' and p['z']==2.6 and roi.intersects(LineString(p['segment']))]
fill=[p for p in ps if p['feature']=='Bridge' and p['z']==2.6 and roi.intersects(LineString(p['segment']))]
roofgeom=shapely.union_all([LineString(p['segment']).buffer(p['width']/2,cap_style=2) for p in roof])
samples=[]
for p in wall:
 l=LineString(p['segment']);samples.extend(l.interpolate(x) for x in np.linspace(0,l.length,max(2,math.ceil(l.length/.1))))
d=np.array([p.distance(roofgeom) for p in samples])
chain=[];chains=[]
for p in wall:
 if chain and np.linalg.norm(np.array(chain[-1]['segment'][1])-p['segment'][0])>.01:chains.append(chain);chain=[]
 chain.append(p)
if chain:chains.append(chain)
report=dict(opening_bounds=list(opening.bounds),roof_segments=len(roof),wall_segments=len(wall),wall_length_mm=sum(LineString(p['segment']).length for p in wall),wall_speeds=sorted({p['speed'] for p in wall}),bridge_speeds=sorted({p['speed'] for p in fill}),roof_widths=sorted({p['width'] for p in roof}),wall_centerline_distance_to_roof_beads_mm=dict(min=float(d.min()),median=float(np.median(d)),max=float(d.max())),percent_with_roof_directly_under_centerline=float((d<.001).mean()*100),percent_with_roof_within_0_225mm=float((d<=.225).mean()*100),chains=[dict(length_mm=sum(LineString(p['segment']).length for p in c),segments=len(c),first=c[0]['segment'][0],last=c[-1]['segment'][1]) for c in chains])
print(json.dumps(report,indent=2));(out/'coverage.json').write_text(json.dumps(report,indent=2))
fig,axes=plt.subplots(1,2,figsize=(13,6))
for ax in axes:
 for title,pool,color,lw in [('Support roof, Z2.2',roof,'#c58b36',1),('First supported walls, Z2.6',wall,'#247d9a',1.6),('Bridge fill, printed later',fill,'#92b9c5',.5)]:
  ax.add_collection(LineCollection([p['segment'] for p in pool],colors=color,linewidths=lw,label=title))
 ax.set_aspect('equal');ax.grid(alpha=.2);ax.set_xlabel('Bed X (mm)');ax.set_ylabel('Bed Y (mm)')
axes[0].set(xlim=(opening.bounds[0]-8,opening.bounds[2]+8),ylim=(opening.bounds[1]-8,opening.bounds[3]+8));axes[0].legend(fontsize=8);axes[0].set_title('Current P2 photo rabbet: actual toolpaths')
worst=samples[int(d.argmax())];axes[1].set(xlim=(worst.x-8,worst.x+8),ylim=(worst.y-8,worst.y+8));axes[1].set_title('Largest horizontal gap to support roof')
fig.tight_layout();fig.savefig(out/'support-coverage.png',dpi=150)
