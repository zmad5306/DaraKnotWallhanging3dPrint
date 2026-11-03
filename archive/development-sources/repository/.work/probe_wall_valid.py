from plan_wall_blocks import *
from shapely.validation import explain_validity
k=affinity.translate(KEYS,130,214).buffer(2)
print('validity',KNOT.is_valid,explain_validity(KNOT),'contains',KNOT.contains(k),'covers',KNOT.covers(k),'intersect',KNOT.intersection(k).area,'area',k.area,'geom',k.wkt[:80])
print('keys',KEYS.is_valid,KEYS.bounds)
