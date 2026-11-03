from plan_wall_blocks import *
records=json.loads(Path('.work/wall-blocks/selected.json').read_text())[0][1]
for idx,r in enumerate(records):
 oldkeys=unary_union([box(r['x']+dx-10.2,r['y']+r['key_y']-5.2,r['x']+dx+10.2,r['y']+r['key_y']+5.2)for dx,_,_ in r['keys']])
 opts=[]
 for dx in range(-62,63):
  pt=Point(r['x']+dx,r['y']+r['key_y'])
  owners=[i for i,m in enumerate(MASKS)if m.contains(pt.buffer(5))]
  if owners and KNOT.contains(pt.buffer(5)) and pt.distance(DOMAINS)>7 and pt.distance(oldkeys)>6:opts.append((dx,owners[0]))
 print(idx,opts,flush=True)
