from repartition_search import *
from itertools import combinations
D=json.loads((OUT/'jointed-data.json').read_text());report={}
for kind,d in D.items():
 ps=list(map(shape,d['parts']));js=d['joints'];merges=[];neighbors=[];alllines=unary_union([shape(j['line'])for j in js])
 for a,b in combinations(range(len(ps)),2):
  shared=ps[a].boundary.intersection(ps[b].boundary)
  if shared.length<1:continue
  assert shared.difference(alllines.buffer(.001)).length<.001,(kind,a,b,'unjointed seam')
  joined=ps[a].union(ps[b]);remaining=[j for j in js if set([j['male'],j['female']])!={a,b}];dim=fast_fit(envelope(joined,remaining),True)[0];neighbors.append([a+1,b+1,dim])
  if dim<=253:merges.append([a+1,b+1,dim])
 report[kind]={'mergeable_neighbors':merges,'smallest_neighbor_pair':min(neighbors,key=lambda t:t[2]),'section_count':len(ps),'joint_count':len(js)}
 print(kind,report[kind],flush=True)
(OUT/'layout-checks.json').write_text(json.dumps(report,indent=2))
