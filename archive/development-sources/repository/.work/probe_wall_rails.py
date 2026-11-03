from plan_wall_blocks import *
from shapely.geometry import LineString
for x in [70,100,150,190]:print(x,KNOT.intersection(LineString([(x,180),(x,280)])).wkt)
for x,y in [(130,214),(130,261),(-130,214)]:
 k=affinity.translate(KEYS,x,y);print(x,y,'missing',k.buffer(2).difference(KNOT).area,'keybounds',k.bounds)
