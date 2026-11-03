from pathlib import Path
import json,sys
sys.path.insert(0,'.work')
from quadrant_v2 import *
selected=[]
for q in range(4):
 rr=[]
 for f in OUT.glob(f'quad-v2-{q}-*.json'):
  d=json.loads(f.read_text())
  if d['count']!=5:continue
  ps=[shape(p)for p in d['parts']];sizes=[fast_fit(envelope(p,INITIAL+d['joints']),True)[0]for p in ps]
  rr.append(((d['joint_count'],-min(sizes),-sum(sizes)),f,d))
 _,f,d=min(rr,key=lambda v:v[0]);print('selected',q,f.name);selected.append(d)
parts=[shape(p)for d in selected for p in d['parts']];joints=INITIAL+[j for d in selected for j in d['joints']]
parts.sort(key=lambda p:(-round(p.centroid.y/80),p.centroid.x))
for j in joints:
 d=local(shape(j['domain']),j);safe=[float(y)for y in np.arange(-j['span']/2+4,j['span']/2-3,.5)if d.covers(affinity.translate(PROFILES['pocket'].buffer(2),yoff=y))]
 assert safe
 j['keys']=[min(safe,key=lambda y:abs(y-j['span']*v))for v in [-1/3,1/3]]
 j['male']=next(i for i,p in enumerate(parts)if p.contains(Point(j['male_probe'])));j['female']=next(i for i,p in enumerate(parts)if p.contains(Point(j['female_probe'])))
for i,j in enumerate(joints):
 for k in joints[i+1:]:assert shape(j['domain']).intersection(shape(k['domain'])).area<.001
assert FRAME.symmetric_difference(unary_union(parts)).area<.0001
sizes=[fast_fit(envelope(p,joints),True)[0]for p in parts];assert max(sizes)<=LIMIT
r={'family':'frame','count':len(parts),'joint_count':len(joints),'parts':[mapping(p)for p in parts],'joints':joints,'maxdim':max(sizes),'min_span':min(sizes)}
(OUT/'frame-final.json').write_text(json.dumps(r))
print('final',len(parts),len(joints),min(sizes),max(sizes))
fig,axs=plt.subplots(1,2,figsize=(16,9),gridspec_kw={'width_ratios':[1.5,1]})
for ax,d in zip(axs,[r,json.loads((OUT/'M-201.json').read_text())]):
 for i,p in enumerate(map(shape,d['parts'])):draw(ax,p,plt.get_cmap('tab20')(i));ax.text(*p.representative_point().coords[0],str(i+1))
 ax.autoscale();ax.set_aspect('equal')
fig.savefig(OUT/'candidate-final.png',dpi=120)
