from plan_wall_blocks import *
for sx,sy in [(-1,1),(1,1),(-1,-1),(1,-1)]:
 counts=[0]*7;opts=[]
 for x in range(80,241,2):
  for y in range(208,267,2):
   xx,yy=sx*x,sy*y;b=affinity.translate(BASE,xx,yy);k=affinity.translate(KEYS,xx,yy-6*sy)
   conditions=[FRAME.contains(b.buffer(2)),KNOT.contains(k.buffer(2)),b.distance(SWEEP)>=3,b.distance(PHOTOS)>=3,b.distance(HARDWARE)>=3,k.distance(DOMAINS)>=3,any(m.contains(k.buffer(3)) for m in MASKS)]
   for i in range(7):
    if all(conditions[:i+1]):counts[i]+=1
   if all(conditions[:6]):opts.append((xx,yy))
 print(sx,sy,counts,opts[:30],flush=True)
