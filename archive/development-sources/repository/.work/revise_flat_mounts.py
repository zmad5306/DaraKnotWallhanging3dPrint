from pathlib import Path
import json,re
path=Path('working/Dara-Photo-Frame-A1-Jointed.scad')
before=Path('.work/protruding-mounts-before-revision.scad')
if not before.exists():before.write_bytes(path.read_bytes())
s=before.read_text()
plan=json.loads(Path('.work/flat-mount-plan.json').read_text())
screws=[[r['m'],r['frame'],r['xy']]for r in plan['screws']]
pins=[[r['m'],r['frame'],r['xy'],int(r['slot']),r['angle']]for r in plan['pins']]
header='''// M mounting: 10 rear screws and reference washers; 12 locating dowels on the knot.
// M1/M3/M4/M6 have two screws each; M2/M5 have one. Every M has two locators.
// All screws and dowels are on full-height knot rails, clear of the lowered weave.
// M's rear stays at local Z=0: blind holes only, no projecting bosses or pads.
// The reference boss is a surrogate for material INSIDE M, not an external boss.
// Reference hardware: #6-19 x 1/2-inch pan-head plastic thread-forming screws,
// 12 mm rear counterbores, 4 mm clearance holes, 3.175 mm pilots and 1 mm washers.
// Adapt the reference's axial stack to the 10.5 mm M: 4 mm knot seat, 8.7 mm
// blind pilot. Engagement = 12.7-1-4 = 7.7 mm; tip clearance 1 mm; front cover 1.8 mm.
// The sample's 1.6 mm seat/12 mm pilot would not fit inside this flat-backed M.
// M bears directly on the original knot top at Z=13.5; front remains at Z=24.
// Knot counterbores end at Z=9.5; washers bear at Z=8.5..9.5.
// Each M section has a round locator hole and a secondary 0.8 mm axial relief slot.
// Integral knot pins are 4 mm diameter with 3 mm insertion and chamfered tips.
// M holes are 4.2 mm wide and 3.3 mm deep; neither the pins nor their roots
// touch the recessed weave. No support pedestals are added to the frame.
// Assemble and bond the lap sections first, lower M onto the pins, then install
// washers and screws from the rear. Screwdriver access clears photo hardware.
// The reference confirms lap rigidity, not the revised screw stack or dowel fit.
// This remains CAD only; no slicer settings or print projects are changed.
'''
s=re.sub(r'// M mounting:.*?(?=// M retains)',lambda _:header,s,count=1,flags=re.S)
s=s.replace('// Section mode centres one part at Z=0; M sections sit front-down, bosses up.',
'// Section mode centres one part at Z=0; M sections print with their flat rear down.')
start=s.index('boss_diameter = 10;');end=s.index('assert(dowel_clearance>=.1',start)
s=s[:start]+'''mount_bearing_z = letter_back_z*uniform_scale;
screw_pilot_diameter = 3.175;
screw_pilot_depth = 8.7;
screw_clearance_diameter = 4;
screw_counterbore_diameter = 12;
screw_seat_skin = 4;
washer_thickness = 1;
screw_length = 12.7;
dowel_diameter = 4;
dowel_projection = 3;
dowel_hole_depth = 3.3;
assert(abs(mount_bearing_z-13.5)<.000001);
assert(letter_depth*uniform_scale-screw_pilot_depth>=1.8-.000001);
assert(screw_pilot_depth-(screw_length-washer_thickness-screw_seat_skin)>=1-.000001);
'''+s[end:]
def module(name,body):
    global s
    s,n=re.subn(r'module '+name+r'\([^\n]*?\) \{.*?\n\}',lambda _:body,s,count=1,flags=re.S)
    assert n==1,name
module('M_boss','')
module('M_pilot','''module M_pilot() {
    // Blind bore wholly inside the original M body; no geometry below its rear.
    translate([0,0,-.02]) cylinder(d=screw_pilot_diameter,h=screw_pilot_depth+.02,$fn=64);
}''')
module('frame_screw_cuts','''module frame_screw_cuts() {
    seat_rear=mount_bearing_z-screw_seat_skin;
    // Rear counterbore and straight clearance through the full-height knot rail.
    translate([0,0,-.02]) cylinder(d=screw_counterbore_diameter,h=seat_rear+.02,$fn=96);
    translate([0,0,seat_rear-.01]) cylinder(d=screw_clearance_diameter,h=screw_seat_skin+.03,$fn=64);
}''')
module('locating_dowel','''module locating_dowel() {
    // Root directly in the full-height knot rail. No pedestal over the weave.
    top=letter_back_z*uniform_scale;
    translate([0,0,top-.02]) cylinder(d=dowel_diameter,h=dowel_projection-.5+.02,$fn=64);
    translate([0,0,top+dowel_projection-.5]) cylinder(d1=dowel_diameter,d2=dowel_diameter-.6,h=.5,$fn=64);
}''')
s=s.replace('            if(kind=="M") for(m=screw_mounts) if(m[0]==i) mount_xy(m[2]) M_boss();\n','')
s=s.replace('cylinder(d=3.5,h=12.7,$fn=40)','cylinder(d=3.5,h=screw_length,$fn=40)')
module('print_section','''module print_section(kind,i) {
    p=placement_list(kind)[i];
    // M has no added rear projections; retain its original rear-down placement.
    // Frame parts carrying original rear tracks keep the 3.2 mm Z allowance.
    translate([-p[1][0],-p[1][1],p[3]]) rotate([0,0,p[0]]) section_shape(kind,i);
}''')
s=s.replace('else if(view_mode=="M") translate([0,0,boss_projection]) section_group("M");',
'else if(view_mode=="M") section_group("M");')
s=s.replace('boss_diameter==10 && boss_projection==6.5 && mount_bearing_z==7 &&','mount_bearing_z==13.5 &&')
s=s.replace('screw_pilot_diameter==3.175 && screw_pilot_depth==12 &&','screw_pilot_diameter==3.175 && screw_pilot_depth==8.7 &&')
s=s.replace('screw_seat_skin==1.6 && boss_socket_clearance==.3 &&','screw_seat_skin==4 &&')
for key,data in [('screw_mounts',screws),('dowel_mounts',pins),('mount_cache_screws',screws),('mount_cache_dowels',pins)]:
    s,n=re.subn(r'^'+key+r' = .*?;$',key+' = '+json.dumps(data,separators=(',',':'))+';',s,count=1,flags=re.M)
    assert n==1,key
s=re.sub(r'^mount_preview_ready = .*$', 'mount_preview_ready = false; // Rebuild after native flat-back verification.',s,count=1,flags=re.M)
# Show the actual raised rails in the inspection map, including the lower weave.
s=s.replace('scale([uniform_scale,uniform_scale]) union() { knot_outline(); fabric_outline(); }',
'''scale([uniform_scale,uniform_scale]) fabric_outline();
    color([.61,.69,.64]) translate([0,0,.07]) linear_extrude(height=.02)
        scale([uniform_scale,uniform_scale]) knot_outline();''')
path.write_text(s)
oldplan=json.loads(Path('.work/mount-plan.json').read_text())
frames=sorted(set(r['frame']for r in plan['screws']+plan['pins']+oldplan['screws']+oldplan['pins']))
Path('.work/flat-mount-affected.json').write_text(json.dumps({'frame':frames,'M':list(range(6))}))
print('Revised flat-back mounts; sections to check:',frames, 'and M1-M6')
