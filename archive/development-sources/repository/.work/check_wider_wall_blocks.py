from plan_wall_blocks import *
for x,y in [(-196,224),(196,224),(-196,-224),(196,-224)]:
 b=affinity.translate(box(-70,-19,70,19).buffer(-2).buffer(2),x,y)
 print(x,y,'outside',b.difference(FRAME).area,'edge',b.distance(FRAME.boundary),'sweep',b.distance(SWEEP),'photo',b.distance(PHOTOS),'M hardware',b.distance(HARDWARE))
