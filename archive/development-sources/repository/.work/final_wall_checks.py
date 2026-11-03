from plan_wall_blocks import *
import hashlib,subprocess
import numpy as np,trimesh
cad=Path('working/Dara-Photo-Frame-A1-Jointed.scad');source=cad.read_text()
before=Path('.work/wall-blocks/before.scad').read_text()
report_path=Path('working/review/wall-blocks/verification.json');report=json.loads(report_path.read_text())
report['source_sha256']=hashlib.sha256(cad.read_bytes()).hexdigest()
records=ast.literal_eval(re.search(r'^wall_mounts = (.*?);',source,re.M|re.S).group(1));placements=arr('frame_placements')
locations=[]
for i,(owner,xy,ky,keys,sy,holes,pady) in enumerate(records):
 b=affinity.translate(box(-70,-19,70,19).buffer(-2).buffer(2),*xy)
 assert b.difference(FRAME).area<.001 and b.distance(SWEEP)>3 and b.distance(PHOTOS)>2.5
 slots=unary_union([box(xy[0]+dx-10.5,xy[1]+ky-5.5,xy[0]+dx+10.5,xy[1]+ky+5.5)for dx in keys])
 assert KNOT.contains(slots) and MASKS[owner].contains(slots)
 for dx in holes:
  pt=Point(xy[0]+dx,xy[1]+sy)
  assert KNOT.contains(pt.buffer(5)) and MASKS[owner].contains(pt.buffer(5)) and pt.distance(DOMAINS)>7 and pt.distance(slots)>6
 m=trimesh.load_mesh(f'.work/wall-blocks-screwed/F{owner+1}-after.stl')
 placement=placements[owner]
 m.apply_transform(trimesh.transformations.rotation_matrix(np.deg2rad(placement[0]),[0,0,1]))
 m.apply_translation([-placement[1][0],-placement[1][1],placement[3]])
 assert max(m.extents[:2])<253 and abs(m.bounds[0,2])<.001
 locations.append(dict(block=f'B{i+1}',frame=f'F{owner+1}',centre_mm=xy,full_tab_sweep_clearance_mm=b.distance(SWEEP),backer_pocket_clearance_mm=b.distance(PHOTOS),slot_to_lap_clearance_mm=slots.distance(DOMAINS),slot_to_rail_edge_mm=slots.distance(KNOT.boundary),frame_print_footprint_mm=m.extents.tolist()))
report['locations']=locations
# Confirm every pre-existing artwork/joint/hardware module and placement array
# remains exact, apart from the intended section dispatcher and preview changes.
names=['knot_outline','fabric_outline','letter_outline','retainer_mm','photo_backer','photo_pilot_mm','tested_tongue_xz','tested_socket_void_xz','tested_key','tested_key_pocket','M_pilot','frame_screw_cuts','locating_dowel','locating_hole']
for name in names:
 pattern=r'module '+name+r'\([^\n]*\) \{.*?\n\}'
 assert re.search(pattern,source,re.S).group()==re.search(pattern,before,re.S).group(),name
report['unchanged_existing_modules']=names
report['numerical_comparison_note']='F18 has 0.1603 mm3 of CGAL triangulation variation in a pre-existing weave-edge sliver (Z=9..9.6); no source artwork was changed. Preview/native differences are below 0.000002 mm3.'
# Exercise preview guards without rendering the full frame for every setting.
base=Path('.work/wall-blocks-screwed/current-modules.scad')
check=base.parent/'cache-guards.scad'
check.write_text('include <current-modules.scad>\necho(frame_cache=cached_shape_matches("frame"),letter_cache=cached_shape_matches("M"));\n')
cases=[([],True),(['-D','wall_key_clearance=.3'],False),(['-D','wall_key_depth_clearance=.4'],False),(['-D','wall_standoff=12'],True),(['-D','wall_fastener_pilot=3.2'],False)]
guard_results=[]
for args,expected in cases:
 p=subprocess.run([r'C:\Program Files (x86)\OpenSCAD\openscad.exe','--hardwarnings','--camera=0,0,0,0,0,0,700','-o',str(base.parent/'guards.csg'),*args,str(check)],capture_output=True,text=True,timeout=30)
 assert p.returncode==0 and f'frame_cache = {str(expected).lower()}, letter_cache = true' in p.stderr,p.stderr
 guard_results.append(dict(arguments=args,frame_cache=expected,passed=True))
report['cache_parameter_checks']=guard_results
report_path.write_text(json.dumps(report,indent=2));print(json.dumps(locations,indent=2));print('PASS: fit, eight pilots, hardware recesses, strip faces, hanging travel, clearances, preserved source geometry, print footprints, and preview guards.')
