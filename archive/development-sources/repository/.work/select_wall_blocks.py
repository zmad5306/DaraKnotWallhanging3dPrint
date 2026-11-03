from plan_wall_blocks import *
def candidate(x,y):
 b=affinity.translate(BASE,x,y)
 if not FRAME.contains(b.buffer(2)) or b.distance(SWEEP)<3 or b.distance(PHOTOS)<3 or b.distance(HARDWARE)<3:return
 ky=y-6*(1 if y>0 else -1)
 slots=[]
 for dx in range(-54,55,2):
  k=box(x+dx-10.2,ky-5.2,x+dx+10.2,ky+5.2)
  owners=[i for i,m in enumerate(MASKS)if m.contains(k.buffer(2))]
  if owners and KNOT.contains(k.buffer(2)) and k.distance(DOMAINS)>=3:slots.append((dx,owners[0],k.distance(DOMAINS)))
 if len(slots)<2 or slots[-1][0]-slots[0][0]<30:return
 pair=[slots[0],slots[-1]]
 return dict(x=x,y=y,keys=pair,key_y=ky-y,sweep=b.distance(SWEEP),photo=b.distance(PHOTOS),hardware=b.distance(HARDWARE),edge=FRAME.boundary.distance(b))
results=[]
for x in range(80,201,2):
 for y in range(218,229,2):
  checks=[candidate(sx*x,sy*y)for sx,sy in [(-1,1),(1,1),(-1,-1),(1,-1)]]
  if all(checks):results.append((x*y,checks))
results.sort(key=lambda r:r[0],reverse=True)
print(json.dumps(results[:1],indent=2))
Path('.work/wall-blocks/selected.json').write_text(json.dumps(results[:1],indent=2))
if results:
 fig,ax=plt.subplots(figsize=(10,10));draw(ax,FRAME,'#d4dcd8');draw(ax,KNOT,'#b1bfb8');draw(ax,DOMAINS,'#daa7a4');draw(ax,SWEEP,'#e5b961')
 for i,r in enumerate(results[0][1]):
  draw(ax,affinity.translate(BASE,r['x'],r['y']),'#267b8d')
  for dx,owner,d in r['keys']:draw(ax,box(r['x']+dx-10,r['y']+r['key_y']-5,r['x']+dx+10,r['y']+r['key_y']+5),'#e8c55c')
  ax.text(r['x'],r['y']+28,f'B{i+1}',ha='center')
 ax.set(xlim=(-470,470),ylim=(-470,470),aspect='equal');ax.grid(alpha=.2);fig.savefig('.work/wall-blocks/selected.png',dpi=120)
