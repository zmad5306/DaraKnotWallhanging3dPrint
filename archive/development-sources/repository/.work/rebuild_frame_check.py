from design_sections import *
import manifold3d as md, trimesh
def cs(g):
    contours=[]
    for p in geoms(g):
        p=orient(p,1)
        contours += [np.array(p.exterior.coords)[:-1],*[np.array(r.coords)[:-1]for r in p.interiors]]
    return md.CrossSection(contours,md.FillRule.Positive)
def extr(g,h,z=0):return cs(g).extrude(h).translate([0,0,z])
frame=extr(KNOT,13.5)+extr(FABRIC,9)
threads=unary_union([box(x-.75,-460,x+.75,460)for x in range(-462,463,6)]+[box(-460,y-.75,460,y+.75)for y in range(-462,463,6)])
weave=extr(FABRIC.intersection(threads),.6,9)
tracks=[];channels=[]
for a,n in zip(anchors.reshape(-1,2),normals.reshape(-1,2)):
    def at(s):return s.rotate([0,0,math.degrees(math.atan2(n[1],n[0]))]).translate([*a,0])
    tracks.append(at(extr(box(5,-5.5,14,5.5),3.4,-3.2)))
    channels.append(at(extr(box(4.98,-3.5,14.02,3.5),1.82,-1.6)+extr(box(6,-2.3,14.02,2.3),1.63,-3.22)))
frame+=md.Manifold.batch_boolean(tracks,md.OpType.Add)
rabbets=[extr(outline('photo_loop_'+str(i)).buffer(4),2.02,-.02)for i in range(1,9)]
frame-=md.Manifold.batch_boolean(channels+rabbets,md.OpType.Add)
frame+=weave
m=frame.to_mesh64();mesh=trimesh.Trimesh(m.vert_properties[:,:3],m.tri_verts,process=False)
mesh.export('.work/jointed-independent-frame.ply',encoding='binary')
print('Independent original frame',frame.volume(),frame.num_tri(),len(frame.decompose()),mesh.is_watertight,flush=True)
cached=trimesh.load_mesh('.work/separate-frame-check.off')
s=md.Manifold(md.Mesh64(cached.vertices,cached.faces.astype(np.uint64)))
print('Cached original frame',s.volume(),'difference',(s-frame).volume()+(frame-s).volume(),flush=True)
