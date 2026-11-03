from pathlib import Path
p=Path('.work/check_wall_blocks.py');s=p.read_text()
s=s.replace("OUT=ROOT/'.work/wall-blocks';", "OUT=ROOT/'.work/wall-blocks-screwed'; OUT.mkdir(exist_ok=True);")
s=s.replace("('baseline',OUT/'before.scad')", "('baseline',ROOT/'.work/wall-blocks/before.scad')")
s=s.replace('wall_slot_pair({i});','wall_frame_cuts({i});')
s=s.replace('positions=[[-196,222],[196,222],[-196,-222],[196,-222]]','positions=[[-196,224],[196,224],[-196,-224],[196,-224]]')
s=s.replace('pad=md.Manifold.cube([95,20,.2]).translate([-65,-10,0])','pad=md.Manifold.cube([95,20,.2]).translate([-65,(7 if i<2 else -7)-10,0])')
s=s.replace("cm,c=load(f'F{owner+1}-cached');", "cm,c=load(f'F{owner+1}-cached');")
s=s.replace("with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:list(pool.map(run,jobs))", "with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:list(pool.map(run,jobs))")
s=s.replace("add('fit-sample'", "for owner in [2,4,15,17]:\n add(f'F{owner+1}-cached',f'preview_section(\"frame\",{owner});')\nadd('fit-sample'")
s=s.replace(" name,path,extra=job\n", " name,path,extra=job\n if '--render-only' in sys.argv and 'cached' in name:return\n")
s=s.replace("'remaining_key_cover_mm':10.2", "'remaining_key_cover_mm':10.2,'remaining_pilot_cover_mm':2.8")
s=s.replace(" report['blocks'].append(checks)", """ # The new mounting screws are separate from the locating keys.
+ holes=[[21,37],[-34,-6],[4,34],[-24,24]][i]; sy=-10 if i<2 else 10
+ for hx in holes:
+  xy=[positions[i][0]+hx,positions[i][1]+sy]
+  bore=md.Manifold.cylinder(10.69,1.58,circular_segments=64).translate([*xy,.001])
+  cover=md.Manifold.cylinder(2.79,1.58,circular_segments=64).translate([*xy,10.705])
+  assert (bore^a).volume()<.001 and (cover-a).volume()<.001
+  head=md.Manifold.cylinder(2.5,3.5,circular_segments=64).translate([hx,sy,4.5])
+  shaft=md.Manifold.cylinder(3,1.99,circular_segments=64).translate([hx,sy,7])
+  assert ((head+shaft)^b).volume()<.001
+  seat=md.Manifold.cylinder(2.99,3.5,circular_segments=64).translate([hx,sy,7.005])-md.Manifold.cylinder(3.1,2.01,circular_segments=64).translate([hx,sy,7])
+  assert (seat-b).volume()<.001
+ checks.update(fastener_count=2,fastener_head_recess_mm=4.5,pilot_depth_mm=10.7,screw_engagement_mm=9.7)
+ report['blocks'].append(checks)""".replace('\n+','\n'))
p.write_text(s)
# Reuse exact original native comparison parts; only the revised solids need re-rendering.
import shutil
out=Path('.work/wall-blocks-screwed');out.mkdir(exist_ok=True)
for owner in [3,5,16,18]:
 for ext in ['stl','log']:shutil.copyfile(f'.work/wall-blocks/F{owner}-before.{ext}',out/f'F{owner}-before.{ext}')
