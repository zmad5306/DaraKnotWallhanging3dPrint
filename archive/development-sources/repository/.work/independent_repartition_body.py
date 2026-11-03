from repartition_search import *
import manifold3d as md,trimesh,time

def cs(g):
 contours=[]
 for p in geoms(g):
  p=orient(p,1);contours+=[np.array(p.exterior.coords)[:-1],*[np.array(r.coords)[:-1]for r in p.interiors]]
 return md.CrossSection(contours,md.FillRule.Positive)
def extr(g,h,z=0):return cs(g).extrude(h).translate([0,0,z])
def export(s,name):
 assert s.status()==md.Error.NoError
 m=s.to_mesh64();trimesh.Trimesh(m.vert_properties[:,:3],m.tri_verts,process=False).export(OUT/'native'/f'independent-{name}.stl');print(name,s.volume(),flush=True)
# Build the continuous reference directly from its artwork and original depths.
fabric=outline('fabric_outline').buffer(.1125,join_style=2)
base=extr(KNOT,13.5)+extr(fabric,9)
strands=[]
for i in range(-77,78):strands +=[box(i*6-.75,-458.7,i*6+.75,458.7),box(-458.7,i*6-.75,458.7,i*6+.75)]
weave=extr(fabric.intersection(unary_union(strands)),.6,9)
for i in range(1,9):base-=extr(outline('photo_loop_'+str(i)).buffer(4,join_style=2),2.02,-.02)
for xy in PHOTO_PIVOTS:base-=md.Manifold.cylinder(10.72,3.175/2,circular_segments=64).translate([*xy,-.02])
export(base+weave,'frame');export(extr(LETTER,10.5),'M')
