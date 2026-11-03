from plan_wall_blocks import *
old=json.loads(Path('.work/wall-blocks/selected.json').read_text())[0][1]
for i,(r,holes) in enumerate(zip(old,[[21,37],[-34,-6],[4,34],[-24,24]])):
 keys=unary_union([box(r['x']+dx-10.2,r['y']+r['key_y']-5.2,r['x']+dx+10.2,r['y']+r['key_y']+5.2)for dx,_,_ in r['keys']])
 for dx in holes:
  pt=Point(r['x']+dx,214*(1 if r['y']>0 else -1))
  print(i+1,dx,'rail edge',pt.distance(KNOT.boundary),'joint',pt.distance(DOMAINS),'slot',pt.distance(keys),'owner',[j+1 for j,m in enumerate(MASKS)if m.contains(pt.buffer(5))])
