from pathlib import Path
import json,re

path=Path('working/Dara-Photo-Frame-A1-Jointed.scad')
baseline=Path('.work/mounts-before.scad')
if not baseline.exists():baseline.write_bytes(path.read_bytes())
s=baseline.read_text()
p=json.loads(Path('.work/mount-plan.json').read_text())
screws=[[r['m'],r['frame'],r['xy']]for r in p['screws']]
pins=[[r['m'],r['frame'],r['xy'],1 if r['slot']else 0,r['angle']]for r in p['pins']]
compact=lambda x:json.dumps(x,separators=(',',':'))

s=s.replace('// Two keys per seam, spaced across each local rail. No screw/boss features added.',
'''// Two keys per seam, spaced across each local rail. Lap geometry is unchanged.
// M mounting: 10 rear screws, 10 reference washers, 12 integral locating dowels.
// M1/M3/M4/M6 have two screws each; M2/M5 have one. Every M has two locators.
// Screws: reference #6-19 x 1/2-inch pan-head plastic thread-forming screws.
// Reference seat: 12 mm rear recess, 4 mm clearance, 1.6 mm clamping skin.
// Reference boss: 10 mm OD, 14 mm stem + 3 mm base, 3.175 x 12 mm blind pilot.
// The 17 mm reference coupon depth is integrated into the 10.5 mm M body:
// its base and upper stem are embedded, leaving a 6.5 mm rear boss projection.
// This retains the M rear/front at Z=13.5/24 and leaves 5 mm closed pilot cover.
// Knot recess: boss bearing Z=7, counterbore ceiling Z=5.4, 1.6 mm seat between.
// A 10.3 mm top well accepts the boss; each 1 mm washer bears at Z=4.4..5.4.
// Screw length after washer and seat: 12.7-1-1.6 = 10.1 mm into the 12 mm pilot.
// Each M section uses one round locator hole and one 0.8 mm axial relief slot.
// Default pins are 4 mm diameter, 3 mm insertion; holes are 4.2 x 3.3 mm deep.
// Slot axes follow the locator pairs: transverse registration remains close.
// Small hidden pads bridge the weave where needed, supporting the M at Z=13.5.
// Assemble and bond the lap sections first, lower M onto the pins, then install
// the washers and screws from the rear. Screwdriver access clears photo hardware.
// The reference establishes joint rigidity; screw grip and these new dowel fits
// still need physical checking. This remains CAD only, with no slicer changes.''')
s=s.replace('// Original backers/retainers are preserved; M-to-frame mounting is outside this change.',
'// Original backers, retainers, artwork, lap seams and overall front height are preserved.')

settings='''/* [M attachment] */
show_mount_hardware = true; // Preview only: metal screws and separate reference washers.
mount_index = 1; // [1:10]
mount_cutaway = true;
mount_explode = 0; // [0:1:25]
// Diameter clearance, not clearance per side. Default is 0.10 mm per side.
dowel_clearance = 0.20; // [0.10:0.05:0.40]
// Extra total length of the secondary hole, along the line between both pins.
dowel_slot_relief = 0.80; // [0.40:0.10:1.20]

'''
s=s.replace('/* [Sections] */',settings+'/* [Sections] */',1)
s=s.replace('drawing:Original front drawing]',
'drawing:Original front drawing, mount_detail:Screw mount detail, mount_map:Mount locations, washer:Reference washer]')
s=s.replace('view_mode=="joint_detail" ? 220 :',
'view_mode=="joint_detail" || view_mode=="mount_detail" ? 220 : view_mode=="washer" ? 40 :')
s=s.replace('rabbet_overlap==4;',
'''rabbet_overlap==4 && dowel_clearance==.2 && dowel_slot_relief==.8 &&
    screw_mounts==mount_cache_screws && dowel_mounts==mount_cache_dowels && mount_preview_ready;''',1)
s=s.replace('module section_csg(kind,i) {','module unmounted_section_csg(kind,i) {',1)
s=s.replace('// Only parts carrying original rear tracks have Z=-3.2.\n    translate([-p[1][0],-p[1][1],p[3]])',
'''// Rear tracks reach -3.2; M bosses reach -6.5. Put the lowest point at Z=0.
    translate([-p[1][0],-p[1][1],kind=="M" ? boss_projection : p[3]])''')
s=s.replace('if(view_mode=="section") print_section(part_family,section_index-1);',
'''if(view_mode=="washer") tested_mount_washer();
    else if(view_mode=="mount_detail") mount_detail();
    else if(view_mode=="mount_map") mount_map();
    else if(view_mode=="section") print_section(part_family,section_index-1);''')
s=s.replace('section_group("frame",view_mode=="exploded" ? exploded_distance : 0);',
'''section_group("frame",view_mode=="exploded" ? exploded_distance : 0);
        if(view_mode=="assembly") mount_hardware_preview();''')

modules='''
// M ATTACHMENT. Values and coordinates below are finished millimetres.
// Records: [M section (0-based), knot section (0-based), XY].
// Locator records also store [secondary slot?, baseline angle].
boss_diameter = 10;
boss_stem_length = 14;
boss_base_thickness = 3;
boss_projection = boss_stem_length + boss_base_thickness - letter_depth*uniform_scale;
mount_bearing_z = letter_back_z*uniform_scale - boss_projection;
screw_pilot_diameter = 3.175;
screw_pilot_depth = 12;
screw_clearance_diameter = 4;
screw_counterbore_diameter = 12;
screw_seat_skin = 1.6;
washer_thickness = 1;
boss_socket_clearance = .3;
dowel_diameter = 4;
dowel_projection = 3;
dowel_hole_depth = 3.3;
assert(abs(boss_projection-6.5)<.000001 && abs(mount_bearing_z-7)<.000001);
assert(screw_pilot_depth < boss_projection+letter_depth*uniform_scale-2);
assert(dowel_clearance>=.1 && dowel_clearance<=.4);
assert(dowel_slot_relief>=.4 && dowel_slot_relief<=1.2);
assert(mount_index>=1 && mount_index<=len(screw_mounts) && floor(mount_index)==mount_index);

module mount_xy(xy) { translate([xy[0],xy[1],0]) children(); }
module M_boss() {
    // All of the original 3 mm coupon base and 7.5 mm of its stem are inside M.
    // Only the 6.5 mm protruding portion needs to be unioned with the body.
    translate([0,0,-boss_projection]) cylinder(d=boss_diameter,h=boss_projection+.03,$fn=80);
}
module M_pilot() {
    translate([0,0,-boss_projection-.02])
        cylinder(d=screw_pilot_diameter,h=screw_pilot_depth+.02,$fn=64);
}
module frame_screw_cuts() {
    seat_rear=mount_bearing_z-screw_seat_skin;
    // Rear driver/head recess, then the tested 4 mm screw clearance through skin.
    translate([0,0,-.02]) cylinder(d=screw_counterbore_diameter,h=seat_rear+.02,$fn=96);
    translate([0,0,seat_rear-.01]) cylinder(d=screw_clearance_diameter,h=screw_seat_skin+.03,$fn=64);
    // Recess the M boss to preserve the original front height.
    translate([0,0,mount_bearing_z])
        cylinder(d=boss_diameter+boss_socket_clearance,h=letter_back_z*uniform_scale-mount_bearing_z+.03,$fn=80);
}
module locating_dowel() {
    top=letter_back_z*uniform_scale;
    // Hidden 8 mm bearing pad also works over the lower woven backing.
    translate([0,0,8.7]) cylinder(d=8,h=top-8.7,$fn=64);
    translate([0,0,top-.02]) cylinder(d=dowel_diameter,h=dowel_projection-.5+.02,$fn=64);
    translate([0,0,top+dowel_projection-.5]) cylinder(d1=dowel_diameter,d2=dowel_diameter-.6,h=.5,$fn=64);
}
module locating_hole(secondary,angle) {
    rotate([0,0,angle]) {
        // Relief is axial only; the pair constrains both translation and rotation.
        hull() for(x=secondary ? [-dowel_slot_relief/2,dowel_slot_relief/2] : [0])
            translate([x,0,-.02]) cylinder(d=dowel_diameter+dowel_clearance,h=dowel_hole_depth+.02,$fn=64);
        hull() for(x=secondary ? [-dowel_slot_relief/2,dowel_slot_relief/2] : [0])
            translate([x,0,-.01]) cylinder(d1=dowel_diameter+dowel_clearance+.6,d2=dowel_diameter+dowel_clearance,h=.46,$fn=64);
    }
}
module section_csg(kind,i) {
    render(convexity=50) difference() {
        union() {
            unmounted_section_csg(kind,i);
            if(kind=="M") for(m=screw_mounts) if(m[0]==i) mount_xy(m[2]) M_boss();
            if(kind=="frame") for(d=dowel_mounts) if(d[1]==i) mount_xy(d[2]) locating_dowel();
        }
        if(kind=="M") {
            for(m=screw_mounts) if(m[0]==i) mount_xy(m[2]) M_pilot();
            for(d=dowel_mounts) if(d[0]==i) mount_xy(d[2]) locating_hole(d[3],d[4]);
        } else for(m=screw_mounts) if(m[1]==i) mount_xy(m[2]) frame_screw_cuts();
    }
}
module screw_preview() {
    // Nominal envelope only, not a printable or specified thread/head model.
    // 12.7 mm under-head length; selected metal #6-19 pan-head screw.
    under_head=mount_bearing_z-screw_seat_skin-washer_thickness;
    translate([0,0,under_head]) cylinder(d=3.5,h=12.7,$fn=40);
    translate([0,0,under_head-2.5]) cylinder(d=7,h=2.5,$fn=64);
}
module mount_hardware_preview() {
    // Background modifiers keep metal hardware and loose washers out of exports.
    if($preview && show_mount_hardware) for(m=screw_mounts) mount_xy(m[2]) {
        %color([.55,.57,.6]) screw_preview();
        %color([.85,.65,.25]) translate([0,0,mount_bearing_z-screw_seat_skin-washer_thickness]) tested_mount_washer();
    }
}
module mount_detail() {
    m=screw_mounts[mount_index-1];
    translate([-m[2][0],-m[2][1],0]) {
        color(knot_colour) render(convexity=50) intersection() {
            section_shape("frame",m[1]);
            mount_xy(m[2]) translate([-22,mount_cutaway ? 0 : -22,-4]) cube([44,mount_cutaway ? 22 : 44,40]);
        }
        color(letter_colour) translate([0,0,letter_back_z*uniform_scale+mount_explode])
            render(convexity=50) intersection() {
                section_shape("M",m[0]);
                mount_xy(m[2]) translate([-22,mount_cutaway ? 0 : -22,-7]) cube([44,mount_cutaway ? 22 : 44,22]);
            }
        if($preview && show_mount_hardware) mount_xy(m[2]) {
            %color([.5,.53,.57]) screw_preview();
            %color([.85,.65,.25]) translate([0,0,mount_bearing_z-screw_seat_skin-washer_thickness]) tested_mount_washer();
        }
    }
}
module mount_map() {
    // Plan for inspection; mount labels are never added to the print geometry.
    color([.82,.85,.82]) scale([uniform_scale,uniform_scale]) union() { knot_outline(); fabric_outline(); }
    color([.96,.91,.79,.6]) translate([0,0,.1]) scale([uniform_scale,uniform_scale]) letter_outline();
    for(k=[0:len(screw_mounts)-1]) mount_xy(screw_mounts[k][2]) translate([0,0,.3]) {
        color("firebrick") circle(d=12,$fn=48);
        color("black") translate([8,0]) text(str("S",k+1),size=6);
    }
    for(k=[0:len(dowel_mounts)-1]) mount_xy(dowel_mounts[k][2]) translate([0,0,.4]) {
        color("steelblue") circle(d=4,$fn=32);
        color("black") translate([5,0]) text(str("D",k+1),size=5);
    }
}
'''
ref=Path('reference/tested-lap-joints/Tested-Lap-Joints.scad').read_text()
washer=ref.split('module washer() {')[1].split('\n}')[0]
modules+='\n// Exact washer polyhedron from the tested SCAD reference.\nmodule tested_mount_washer() {'+washer+'\n}\n'
modules+='screw_mounts = '+compact(screws)+';\ndowel_mounts = '+compact(pins)+';\n'
modules+='mount_cache_screws = '+compact(screws)+';\nmount_cache_dowels = '+compact(pins)+';\n'
modules+='mount_preview_ready = false; // Set true only after rebuilding the checked preview cache.\n'
marker='// Section geometry is authored in finished mm outside the artwork scale.'
s=s.replace(marker,modules+'\n'+marker,1)
path.write_text(s)
Path('.work/mount-affected.json').write_text(json.dumps({'frame':sorted(set(r['frame']for r in p['screws']+p['pins'])),'M':list(range(6))}))
print('Updated CAD with',len(screws),'screw seats and',len(pins),'locators')
print(Path('.work/mount-affected.json').read_text())
