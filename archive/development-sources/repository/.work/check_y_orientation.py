import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import prepare_hammered_bands as b
report=json.loads((b.REVIEW/'geometry-validation.json').read_text())
for row in report['parts']:
 m=b.load_mesh(row['name']); pts=m.convex_hull.vertices
 fixed=pts@(b.rotation(90)@b.COMMON)[:3,:3].T
 options=[]
 for angle in b.np.arange(0,360,.5):
  t=b.rotation(90)@b.rotation(55,(1,0,0))@b.rotation(float(angle))
  p=pts@t[:3,:3].T;e=p.max(axis=0)-p.min(axis=0)
  if e[0]<230 and e[1]<230 and e[2]<235:options.append((e[2],angle,e))
 best=min(options,key=lambda a:a[0]) if options else None
 print(row['name'],'old yaw',row['yaw_deg'],'old extent',b.np.round(row['print_extent_mm'],1),'yaw90 extent',b.np.round(b.np.ptp(fixed,axis=0),1),'best',(best[1],b.np.round(best[2],1)) if best else None)
for path in [b.ROOT/'Dara.3mf',b.TEST]:
 f=b.read_zip(path);s=json.loads(f['Metadata/project_settings.config'])
 print(path.name,{k:v for k,v in s.items() if any(t in k for t in ['acceleration','jerk','slow_down','brim','travel_speed'])})
