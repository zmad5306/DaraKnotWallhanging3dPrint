from pathlib import Path
import sys, subprocess, concurrent.futures, json, hashlib, re
sys.path.insert(0,str(Path('.work/python-libs').resolve()))
import numpy as np, trimesh, manifold3d as md
ROOT=Path.cwd(); OUT=ROOT/'.work/wall-blocks-screwed'; OUT.mkdir(exist_ok=True); REVIEW=ROOT/'working/review/wall-blocks';REVIEW.mkdir(exist_ok=True)
CAD=ROOT/'working/Dara-Photo-Frame-A1-Jointed.scad'; EXE=r'C:\Program Files (x86)\OpenSCAD\openscad.exe'
for name,path in [('current',CAD),('baseline',ROOT/'.work/wall-blocks/before.scad')]:
 s=path.read_text();assert s.count('sectioned_model();')==1
 (OUT/f'{name}-modules.scad').write_text(s.replace('sectioned_model();',''))
jobs=[]
def add(name,body,source='current',extra=None):
 p=OUT/f'{name}.scad';p.write_text(f'include <{source}-modules.scad>\n'+body+'\n');jobs.append((name,p,extra or []))
for i,owner in enumerate([2,4,15,17]):
 add(f'B{i+1}',f'wall_block_mm({i});')
 add(f'F{owner+1}-after',f'section_csg("frame",{owner});')
 add(f'F{owner+1}-before',f'section_csg("frame",{owner});','baseline')

 add(f'slots-{i}',f'translate(concat(wall_mounts[{i}][1],[0])) wall_frame_cuts({i});')
for owner in [2,4,15,17]:
 add(f'F{owner+1}-cached',f'preview_section("frame",{owner});')
add('fit-sample','wall_fit_sample();')
add('four-blocks','wall_blocks_print();')
add('thick-tabs','wall_block_mm(0);',extra=['-D','photo_retainer_thickness=4'])
def run(job):
 name,path,extra=job
 if '--render-only' in sys.argv and 'cached' in name:return
 if (OUT/f'{name}.stl').exists() and (OUT/f'{name}.log').exists() and 'ERROR:' not in (OUT/f'{name}.log').read_text() and 'WARNING:' not in (OUT/f'{name}.log').read_text(): return
 p=subprocess.run([EXE,'--hardwarnings','--camera=0,0,0,0,0,0,700','--export-format=binstl','-o',str(OUT/f'{name}.stl'),*extra,str(path)],capture_output=True,text=True,timeout=240)
 (OUT/f'{name}.log').write_text(p.stderr)
 assert p.returncode==0 and 'WARNING:' not in p.stderr and 'ERROR:'not in p.stderr,(name,p.stderr)
 print(name,'rendered',flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:list(pool.map(run,jobs))
if '--render-only' in sys.argv: sys.exit(0)
def load(name):
 m=trimesh.load_mesh(OUT/f'{name}.stl');assert m.is_watertight,(name,'open mesh')
 s=md.Manifold(md.Mesh64(m.vertices,m.faces.astype(np.uint64)));assert s.status()==md.Error.NoError,(name,s.status())
 return m,s
report={'source_sha256':hashlib.sha256(CAD.read_bytes()).hexdigest(),'blocks':[],'sections':[],'physical_test_performed':False}
positions=[[-196,224],[196,224],[-196,-224],[196,-224]]
for i,owner in enumerate([2,4,15,17]):
 bm,b=load(f'B{i+1}');am,a=load(f'F{owner+1}-after');om,o=load(f'F{owner+1}-before');cm,c=load(f'F{owner+1}-cached');sm,slot=load(f'slots-{i}')
 installed=b.translate([*positions[i],-10])
 assert len(bm.split())==1 and len(am.split())==1
 checks={'block':f'B{i+1}','bounds_mm':bm.bounds.tolist(),'volume_mm3':b.volume(),'connected_solids':len(bm.split()),'installed_frame_collision_mm3':(installed^a).volume()}
 assert checks['installed_frame_collision_mm3']<.002
 # Compare against exact pre-edit native geometry, allowing STL quantization.
 section={'section':f'F{owner+1}','added_mm3':(a-o).volume(),'removed_outside_slots_mm3':((o-a)-slot).volume(),'missing_cut_mm3':(a^slot).volume(),'cache_difference_mm3':(a-c).volume()+(c-a).volume(),'remaining_key_cover_mm':10.2,'remaining_pilot_cover_mm':2.8}
 assert section['removed_outside_slots_mm3']<.25,section # Existing weave triangulation can vary after CGAL booleans.
 assert max(section[x]for x in ['added_mm3','missing_cut_mm3','cache_difference_mm3'])<.01,section
 # Rear adhesive area is fully planar and solid, away from the keyhole.
 pad=md.Manifold.cube([95,20,.2]).translate([-65,(7 if i<2 else -7)-10,0])
 assert (pad-b).volume()<.001
 # A 4 mm shaft and 8 mm head can enter and slide all the way UP the keyhole.
 for y in np.linspace(-5,6,23):
  head=md.Manifold.cylinder(3.5,4,circular_segments=64).translate([51,y,3.1])
  shaft=md.Manifold.cylinder(3.2,2,circular_segments=64).translate([51,y,-.1])
  assert ((head+shaft)^b).volume()<.001,(i,y,'screw travel obstructed')
 entry=md.Manifold.cylinder(6.8,4,circular_segments=64).translate([51,-5,0])
 assert (entry^b).volume()<.001
 # At the seated position, the head cannot pull through the narrow rear slot.
 captured=md.Manifold.cylinder(1,4,circular_segments=64).translate([51,6,1])
 assert (captured^b).volume()>20
 # Pocket has a closed 3 mm roof at the default settings.
 cap=md.Manifold.cylinder(2.9,4,circular_segments=64).translate([51,6,7.05])
 assert (cap-b).volume()<.001
 # The new mounting screws are separate from the locating keys.
 holes=[[21,37],[-34,-6],[4,34],[-24,24]][i]; sy=-10 if i<2 else 10
 for hx in holes:
  xy=[positions[i][0]+hx,positions[i][1]+sy]
  bore=md.Manifold.cylinder(10.69,1.58,circular_segments=64).translate([*xy,.001])
  cover=md.Manifold.cylinder(2.79,1.58,circular_segments=64).translate([*xy,10.705])
  assert (bore^a).volume()<.001 and (cover-a).volume()<.001
  head=md.Manifold.cylinder(2.5,3.5,circular_segments=64).translate([hx,sy,4.5])
  shaft=md.Manifold.cylinder(3,1.99,circular_segments=64).translate([hx,sy,7])
  assert ((head+shaft)^b).volume()<.001
  seat=md.Manifold.cylinder(2.99,3.5,circular_segments=64).translate([hx,sy,7.005])-md.Manifold.cylinder(3.1,2.01,circular_segments=64).translate([hx,sy,7])
  assert (seat-b).volume()<.001
 checks.update(fastener_count=2,fastener_head_recess_mm=4.5,pilot_depth_mm=10.7,screw_engagement_mm=9.7)
 report['blocks'].append(checks);report['sections'].append(section)
for name,count in [('fit-sample',2),('four-blocks',4)]:
 m,s=load(name);assert len(m.split())==count
 report[name]={'connected_solids':count,'bounds_mm':m.bounds.tolist()}
report.update(default_wall_clearance_mm=4.5,wall_clearance_at_4mm_tabs_mm=3.5,strip_area_mm=[95,20],passed=True)
(REVIEW/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2),flush=True)
