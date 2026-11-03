from plan_wall_blocks import *
from shapely.geometry import LineString
for y in [100,150,200,250,300]:
 print(y,'knot',KNOT.intersection(LineString([(0,y),(300,y)])).wkt,'frame',FRAME.intersection(LineString([(0,y),(300,y)])).wkt)
for sx,sy in [(-1,1),(1,1),(-1,-1),(1,-1)]:
 opts=[]
 for x in range(24,291,4):
  for y in range(100,341,4):
   r=assess(sx*x,sy*y)
   if r:opts.append(r)
 print('quadrant',sx,sy,'options',len(opts),opts[:2])
