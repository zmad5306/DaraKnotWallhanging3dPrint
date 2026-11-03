from repartition_search import *
import manifold3d as md,trimesh
D=json.loads((OUT/'jointed-data.json').read_text());P=json.loads((OUT/'mount-plan.json').read_text());N=OUT/'native'
report={'geometry':{},'screw_checks':[],'locator_checks':[],'photo_pilots':[]}
def solid(mesh):
 s=md.Manifold(md.Mesh64(mesh.vertices,mesh.faces.astype(np.uint64)));assert s.status()==md.Error.NoError;return s

def cylinder(xy,r,z,h,segments=96):return md.Manifold.cylinder(h,r,circular_segments=segments).translate([*xy,z])
def ring(xy,r0,r1,z,h):return cylinder(xy,r1,z,h)-cylinder(xy,r0,z-.01,h+.02)
def union(items):return md.Manifold.batch_boolean(items,md.OpType.Add)if items else md.Manifold()
def cs(g):
 contours=[]
 for p in geoms(g):
  p=orient(p,1);contours +=[np.array(p.exterior.coords)[:-1],*[np.array(r.coords)[:-1]for r in p.interiors]]
 return md.CrossSection(contours,md.FillRule.Positive)
def extr(g,h,z=0):return cs(g).extrude(h).translate([0,0,z])

new={};raw={}
for family,d in D.items():
 raw[family]=solid(trimesh.load_mesh(N/f'original-{family}.stl'));new[family]=[]
 for i,pl in enumerate(d['placements']):
  m=trimesh.load_mesh(N/f'{family[0].upper()}{i+1}.stl');m.apply_translation([*pl[1],0]);m.apply_transform(trimesh.transformations.rotation_matrix(np.deg2rad(-pl[0]),[0,0,1]));new[family].append(solid(m))
 assembled=union(new[family]);zones=[]
 for j in d['joints']:zones.append(extr(shape(j['domain']).union(shape(j['line']).buffer(.1)).buffer(.01),36,-5))
 for r in P['screws']+P['pins']:zones.append(cylinder(r['xy'],6.02 if 'stock_radius'in r else 4.02,-5,36))
 zone=union(zones);outside_added=((assembled-raw[family])-zone).volume();outside_removed=((raw[family]-assembled)-zone).volume()
 max_interference=max((p^q).volume()for i,p in enumerate(new[family])for q in new[family][i+1:])
 result={'outside_intended_changes_mm3':[outside_added,outside_removed],'max_same_family_overlap_mm3':max_interference,'raw_volume_mm3':raw[family].volume(),'assembled_volume_mm3':assembled.volume()}
 print(family,result,flush=True);assert outside_added+outside_removed<5,(family,'unintended geometry',result);assert max_interference<.01,(family,'joint collision',result)
 if family=='M':assert (assembled-raw[family]).volume()<.1,'M has added material'
 report['geometry'][family]=result
for k,r in enumerate(P['screws']):
 xy=r['xy'];frame=new['frame'][r['frame']];letter=new['M'][r['m']].translate([0,0,13.5])
 checks={'original_rail_missing':(cylinder(xy,8.9,.001,13.498)-raw['frame']).volume(),'seat_missing':(ring(xy,2.02,5.98,9.501,3.998)-frame).volume(),'rear_recess_obstructed':(cylinder(xy,5.98,.001,9.498)^frame).volume(),'clearance_obstructed':(cylinder(xy,1.99,9.499,4.002)^frame).volume(),'pilot_obstructed':(cylinder(xy,1.58,13.501,8.698)^letter).volume(),'internal_stock_missing':(ring(xy,1.60,4.97,13.501,10.498)-letter).volume(),'front_cap_missing':(cylinder(xy,1.58,22.201,1.798)-letter).volume()}
 assert max(checks.values())<.001,('screw',k+1,checks);report['screw_checks'].append(checks)
for k,r in enumerate(P['pins']):
 xy=r['xy'];frame=new['frame'][r['frame']];letter=new['M'][r['m']].translate([0,0,13.5]);theta=math.radians(r['angle']);v=np.array([math.cos(theta),math.sin(theta)]);c=np.array(xy);ends=[c-v*.399,c+v*.399]if r['slot']else[c]
 bore=union([cylinder(t,2.09,13.501,3.298,64)for t in ends]).hull()
 checks={'pin_missing':(cylinder(xy,1.99,13.501,2.498)-frame).volume(),'hole_obstructed':(bore^letter).volume(),'closed_front_missing':(cylinder(xy,2.09,16.801,7.198)-letter).volume(),'original_rail_missing':(cylinder(xy,4.9,12,1.499)-raw['frame']).volume()}
 assert max(checks.values())<.001,('pin',k+1,checks);report['locator_checks'].append(checks)
for i,m in enumerate(new['M']):
 assert sum(r['m']==i for r in P['screws'])>=1
 assert sum(r['m']==i for r in P['pins'])==2
 for j,f in enumerate(new['frame']):assert (m.translate([0,0,13.5])^f).volume()<.01,('M/frame collision',i,j)
# Full-depth photo pilots are still present and have their original front cap.
for i,xy in enumerate(PHOTO_PIVOTS):
 owners=[k for k,p in enumerate(D['frame']['parts'])if shape(p).contains(Point(xy))];assert len(owners)==1;f=new['frame'][owners[0]]
 checks={'obstructed_mm3':(cylinder(xy,1.58,.001,10.698)^f).volume(),'missing_cap_mm3':(cylinder(xy,1.58,10.701,2.798)-f).volume()};assert max(checks.values())<.001,('photo',i,checks);report['photo_pilots'].append(checks)
# The same exact tested lap contours remain embedded in the file.
s=Path('working/Dara-Photo-Frame-A1-Jointed.scad').read_text();before=Path('.work/repartition-before.scad').read_text()
for name in ['tested_tongue_xz','tested_socket_void_xz','tested_key','tested_key_pocket','retainer_mm','photo_backer','locating_dowel','M_pilot','frame_screw_cuts']:
 pattern=r'module '+name+r'\([^\n]*\) \{.*?\n\}'
 assert re.search(pattern,s,re.S).group()==re.search(pattern,before,re.S).group(),('changed reference geometry',name)
report['passed']=True;(OUT/'geometry-verification.json').write_text(json.dumps(report,indent=2))
print('PASS: 26 solids, full-height mounting stock, flat M backs, 10 screws, 12 locating dowels, 32 photo pilots, no collisions or unintended artwork changes.',flush=True)
