from pathlib import Path
import ast, re, json, sys, math, hashlib
sys.path.insert(0,str(Path('.work/python-libs').resolve()))
import numpy as np
import trimesh
import manifold3d as md
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
from shapely import affinity

CAD=Path('working/Dara-Photo-Frame-A1-Jointed.scad')
OUT=Path('.work/photo-retainers')
s=CAD.read_text()
before=Path('.work/photo-retainers-before.scad').read_text()
report={'source':str(CAD),'parts':[],'pilots':[],'tabs':[], 'screw':{
    'description':'#6-19 x 1/2-inch pan-head plastic thread-forming screw',
    'under_head_length_mm':12.7,'tab_thickness_mm':3,'clearance_diameter_mm':4,
    'pilot_diameter_mm':3.175,'pilot_depth_mm':10.7,'penetration_mm':9.7,
    'tip_clearance_mm':1,'front_cover_mm':2.8,
    'physical_fit':'Provisional until printed coupon is checked with actual screw'}}

def value(name,text=s):
    return ast.literal_eval(re.search(r'^'+name+r' = (.*?);',text,re.M).group(1))
def module(name,text=s):
    return text.split('module '+name+'(')[1].split('\n}')[0]
def cached_mesh(kind,i,text=before):
    body=module(f'preview_{kind}_{i}',text)
    a,b=re.search(r'polyhedron\(points=(\[.*?\]),\s*faces=(\[.*?\]),convexity',body,re.S).groups()
    return trimesh.Trimesh(vertices=np.array(json.loads(a)),faces=np.array(json.loads(b))[:,::-1],process=False)
def solid(m):
    out=md.Manifold(md.Mesh64(np.asarray(m.vertices),np.array(m.faces,dtype=np.uint64)))
    assert out.status()==md.Error.NoError,out.status()
    return out
def cylinder(xy,r,z,h,n=96):
    return md.Manifold.cylinder(h,r,circular_segments=n).translate([*xy,z])
def union(items):
    return md.Manifold.batch_boolean(items,md.OpType.Add) if items else md.Manifold()
def world(g,a,angle):
    return g.rotate([0,0,angle]).translate([*a,0])
def outline(name,scale=.75):
    polys=[]
    for a,b in re.findall(r'polygon\(points = (\[.*?\]), paths = (\[.*?\]), convexity',module(name),re.S):
        pts=ast.literal_eval(a);paths=ast.literal_eval(b)
        polys.append(Polygon([pts[j] for j in paths[0]],[[pts[j]for j in p]for p in paths[1:]]))
    return affinity.scale(unary_union(polys),scale,scale,origin=(0,0))

# Design baselines must remain byte-for-byte identical, except frame Z placement.
for name in ['photo_anchors','photo_normals','photo_centres','frame_joints','M_joints',
             'frame_assembly_order','M_assembly_order','M_placements','frame_photos',
             'screw_mounts','dowel_mounts']:
    assert value(name)==value(name,before),('changed baseline',name)
assert value('frame_retainers')==value('frame_tracks',before)
for p,q in zip(value('frame_placements'),value('frame_placements',before)):
    assert p[:3]==q[:3] and p[3]==0
names=['knot_outline','fabric_outline','letter_outline','photo_backer',
       'tested_tongue_xz','tested_socket_void_xz','tested_key','tested_key_pocket']
names += [f'photo_loop_{i}'for i in range(1,9)]
names += [f'frame_mask_{i}'for i in range(30)] + [f'frame_joint_domain_{i}'for i in range(42)]
names += [f'M_mask_{i}'for i in range(6)] + [f'M_joint_domain_{i}'for i in range(5)]
names += [f'preview_M_{i}'for i in range(6)]
for name in names: assert module(name)==module(name,before),('changed geometry',name)
assert s.split('// M ATTACHMENT.')[1].split('// Section geometry')[0] == before.split('// M ATTACHMENT.')[1].split('// Section geometry')[0]

anchors=np.array(value('photo_anchors')).reshape(32,2)*.75
normals=np.array(value('photo_normals')).reshape(32,2)
angles=np.degrees(np.arctan2(normals[:,1],normals[:,0]))
centres=anchors+normals*9.5
schedule=value('frame_retainers')
parts=[]
for i,p in enumerate(value('frame_placements')):
    m=trimesh.load_mesh(OUT/f'F{i+1}.stl')
    assert m.is_watertight and m.is_winding_consistent and m.volume>0
    assert len(m.split())==1,('disconnected',i+1)
    assert abs(m.bounds[0,2])<1e-5 and max(m.extents[:2])<246,('print placement',i+1,m.bounds)
    size=m.extents.tolist()
    m.apply_translation([*p[1],0])
    m.apply_transform(trimesh.transformations.rotation_matrix(np.deg2rad(-p[0]),[0,0,1]))
    new=solid(m);old=solid(cached_mesh('frame',i));parts.append(new)
    # The original channel also removed 0.22 mm from the positive-Z rear skin.
    # Restore only that channel footprint; all other added material is forbidden.
    add_zones=[];remove_zones=[]
    for t in schedule[i]:
        a,angle=anchors[t],angles[t]
        add_zones.append(world(md.Manifold.cube([9.06,7.02,.241]).translate([4.97,-3.51,-.01]),a,angle))
        remove_zones.append(world(md.Manifold.cube([9.2,11.2,3.22]).translate([4.9,-5.6,-3.21]),a,angle))
        remove_zones.append(cylinder(centres[t],1.60,-.01,10.721))
    added_out=((new-old)-union(add_zones)).volume()
    removed_out=((old-new)-union(remove_zones)).volume()
    assert added_out+removed_out<.06,('unintended changes',i+1,added_out,removed_out)
    entry={'part':f'F{i+1}','size_mm':size,'minimum_print_z_mm':0,
           'watertight':True,'connected_solids':1,'outside_allowed_changes_mm3':[added_out,removed_out]}
    report['parts'].append(entry)
    print(f'F{i+1}: flat, connected, watertight; outside-change volume {added_out+removed_out:.6f}',flush=True)

knot=outline('knot_outline')
photos=[outline('photo_loop_'+str(i))for i in range(1,9)]
joints=unary_union([outline('frame_joint_domain_'+str(i),1)for i in range(42)])
tab=Point(-.5,0).buffer(5,resolution=64).union(Point(9.5,0).buffer(5,resolution=64)).convex_hull
all_tabs=[]
for t,xy in enumerate(centres):
    fi=next(i for i,v in enumerate(schedule)if t in v);new=parts[fi]
    bore=cylinder(xy,1.58,.001,10.698)
    cap=cylinder(xy,1.58,10.701,2.798)
    ring=cylinder(xy,4.7,.001,13.498)-cylinder(xy,1.61,0,13.5)
    checks={'bore_obstruction_mm3':(bore^new).volume(),
            'front_cover_missing_mm3':(cap-new).volume(),
            'surrounding_stock_missing_mm3':(ring-new).volume()}
    assert max(checks.values())<.001,('pilot',t+1,checks)
    pt=Point(xy);p=t//4
    joint_clear=pt.distance(joints)-1.5875
    assert joint_clear>3 and knot.covers(pt.buffer(4.7))
    report['pilots'].append({'retainer':t+1,'frame':fi+1,**checks,'joint_clearance_mm':joint_clear})
    def place(g):return affinity.translate(affinity.rotate(g,angles[t],origin=(0,0)),*anchors[t])
    closed=place(tab);opened=place(affinity.rotate(tab,90,origin=(9.5,0)))
    backer=photos[p].buffer(3.7)
    overlap=closed.intersection(backer).area;gap=opened.distance(backer)
    assert overlap>70 and gap>.5,('tab fit',t+1,overlap,gap)
    # Every intermediate position stays clear of every other retainer.
    swept=unary_union([place(affinity.rotate(tab,a,origin=(9.5,0))) for a in range(0,91,5)])
    all_tabs.append(swept)
    report['tabs'].append({'retainer':t+1,'closed_backer_overlap_mm2':overlap,'open_backer_clearance_mm':gap})
for i,t in enumerate(all_tabs):
    for q in all_tabs[i+1:]:assert not t.intersects(q),('tab sweeps overlap',i+1)

# No interference with other frame sections or the unchanged M assembly.
largest_overlap=0
for i,p in enumerate(parts):
    for q in parts[i+1:]:
        v=(p^q).volume();largest_overlap=max(v,largest_overlap)
        assert v<.01,('frame overlap',i+1,v)
    for j in range(6):
        letter=solid(cached_mesh('M',j)).translate([0,0,13.5])
        assert (p^letter).volume()<.01,('M overlap',i+1,j+1)

for name,height in [('tab',3),('tab-thin',2.5),('tab-thick',4)]:
    m=trimesh.load_mesh(OUT/(name+'.stl'))
    assert m.is_watertight and len(m.split())==1
    assert np.allclose(m.extents,[20,10,height],atol=1e-5) and abs(m.bounds[0,2])<1e-5
    obj=solid(m)
    # Identical cross-sections throughout: no overhangs or trapped cavities.
    assert abs(obj.slice(.01).area()-obj.slice(height-.01).area())<1e-6
    assert (obj^cylinder([5,0],1.99,0,height)).volume()<1e-6
sample=trimesh.load_mesh(OUT/'fit-sample.stl')
assert sample.is_watertight and len(sample.split())==3
assert all(abs(m.bounds[0,2])<1e-5 for m in sample.split())
thin=solid(trimesh.load_mesh(OUT/'fit-frame-thin.stl'))
assert (thin^cylinder([9.5,0],1.64,.001,11.198)).volume()<.001
assert (cylinder([9.5,0],1.64,11.201,2.298)-thin).volume()<.001
report['largest_frame_overlap_mm3']=largest_overlap
report['baseline_geometry_unchanged']=True
report['fit_sample_connected_solids']=3
report['tab_supports_required']=False
report['physical_test_performed']=False
(OUT/'verification.json').write_text(json.dumps(report,indent=2))
print('PASS: 30 frame sections, 32 blind pilots, 32 rotating tabs, fit coupon, and thickness variations.',flush=True)
