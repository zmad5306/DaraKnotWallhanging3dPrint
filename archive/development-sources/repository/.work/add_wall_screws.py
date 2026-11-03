from pathlib import Path
p=Path('working/Dara-Photo-Frame-A1-Jointed.scad');s=p.read_text()
def change(a,b):
 global s
 assert a in s,a[:100]
 s=s.replace(a,b)
change('four separate bonded blocks B1-B4, each 140 x 28 x 10 mm.','four separate screw-fastened blocks B1-B4, each 140 x 38 x 10 mm.')
change('// Keys locate the blocks; bond the keys AND mating faces before hanging.','''// Keys locate each block. Two recessed #6-19 x 1/2-inch screws per block
// fasten it to the KNOT, with the same 3.175 mm pilots and 4 mm clearance holes.
// 3 mm screw seats give 9.7 mm engagement, 1 mm tip clearance and 2.8 mm cover.
// Nominal screw heads lie 4.5 mm below the wall face; no washers are required.''')
change('// No adhesive weight rating or physical load test is implied by this CAD.','// No strip weight rating or physical load test is implied by this CAD.')
change('// [frame section (0-based), installed XY, key Y offset, two local key X positions].','''// [frame section (0-based), installed XY, key Y offset, two local key X positions,
//  screw Y offset, two local screw X positions, clear strip centre Y].''')
change('wall_mounts = [[2,[-196,222],-6,[4,54]], [4,[196,222],-6,[-54,14]],\n               [15,[-196,-222],6,[-14,52]], [17,[196,-222],6,[-54,54]]];', '''wall_mounts = [[2,[-196,224],-8,[4,54],-10,[21,37],7],
               [4,[196,224],-8,[-54,14],-10,[-34,-6],7],
               [15,[-196,-224],8,[-14,52],10,[4,34],-7],
               [17,[196,-224],8,[-54,54],10,[-24,24],-7]];''')
change('wall_block_height = 28;','''wall_block_height = 38;
wall_fastener_length = 12.7; // Same #6-19 x 1/2-inch pan-head screw as the photo tabs.
wall_fastener_seat = 3;
wall_fastener_pilot = screw_pilot_diameter;
wall_fastener_clearance = screw_clearance_diameter;
wall_fastener_pilot_depth = wall_fastener_length-wall_fastener_seat+1;
wall_fastener_counterbore = 9; // Nominal 7 mm head plus driver clearance.''')
change('assert(wall_mount_explode>=0);','''assert(wall_mount_explode>=0);
assert(knot_depth*uniform_scale-wall_fastener_pilot_depth>=2.8-.000001);
assert(wall_standoff-wall_fastener_seat-wall_photo_head_height>=2,
       "Block screw heads must stay recessed below the strip face");''')
change('module wall_slot_pair(i) { wall_keys_at(i) wall_slot(); }','''module wall_slot_pair(i) { wall_keys_at(i) wall_slot(); }
module wall_fasteners_at(i) {
    m=wall_mounts[i];
    for(x=m[5]) translate([x,m[4],0]) children();
}
module wall_fastener_pilot_cut() {
    translate([0,0,-.02]) cylinder(d=wall_fastener_pilot,h=wall_fastener_pilot_depth+.02,$fn=64);
}
module wall_frame_cuts(i) {
    wall_slot_pair(i);
    wall_fasteners_at(i) wall_fastener_pilot_cut();
}
module wall_fastener_block_cut() {
    // Counterbore opens from the wall face, leaving a 3 mm seat against the knot.
    translate([0,0,-.02]) cylinder(d=wall_fastener_counterbore,h=wall_standoff-wall_fastener_seat+.02,$fn=64);
    translate([0,0,wall_standoff-wall_fastener_seat-.01])
        cylinder(d=wall_fastener_clearance,h=wall_fastener_seat+.03,$fn=64);
}
module wall_fastener_preview(i,gap=0) {
    if($preview && show_mount_hardware) wall_fasteners_at(i)
        translate([0,0,-wall_fastener_seat-gap]) {
            %color([.55,.57,.6]) cylinder(d=3.5,h=wall_fastener_length,$fn=40);
            %color([.55,.57,.6]) translate([0,0,-wall_photo_head_height])
                cylinder(d=7,h=wall_photo_head_height,$fn=64);
        }
}''')
change('translate(concat(wall_mounts[k][1],[0])) wall_slot_pair(k);','translate(concat(wall_mounts[k][1],[0])) wall_frame_cuts(k);')
change('// Clear strip rectangle: X=-65..30, Y=-10..10 (95 x 20 mm).','''// Clear strip rectangle: X=-65..30, Y=m[6]-10..m[6]+10 (95 x 20 mm).
    // Fastener recesses occupy the opposite long edge; the strip covers none.''')
change('        wall_keyhole_cut();','        wall_keyhole_cut();\n        wall_fasteners_at(i) wall_fastener_block_cut();')
change('            color(wall_block_colour) installed_wall_block(i,spread>0 ? spread+16 : 0);','''            union() {
                color(wall_block_colour) installed_wall_block(i,spread>0 ? spread+16 : 0);
                wall_fastener_preview(i,spread>0 ? spread+16 : 0);
            }''')
change('140 x 148 mm','140 x 182 mm')
change('translate([0,60-i*40,0])','translate([0,72-i*48,0])')
change('translate([0,-22,0]) wall_block_mm','translate([0,-26,0]) wall_block_mm')
change('translate([0,22,0]) difference()', 'translate([0,26,0]) difference()')
change('linear_extrude(height=8) wall_rounded_rect','linear_extrude(height=knot_depth*uniform_scale) wall_rounded_rect')
change('        wall_slot_pair(wall_mount_index-1);','        wall_frame_cuts(wall_mount_index-1);')
change('translate([-75,-20,-.01]) cube([150,40,18]);','translate([-75,-24,-.01]) cube([150,48,18]);')
change('color(wall_block_colour) installed_wall_block(i,wall_mount_explode);','''color(wall_block_colour) installed_wall_block(i,wall_mount_explode);
    wall_fastener_preview(i,wall_mount_explode);''')
change('''wall_mounts==[[2,[-196,222],-6,[4,54]],[4,[196,222],-6,[-54,14]],
                  [15,[-196,-222],6,[-14,52]],[17,[196,-222],6,[-54,54]]]''','''wall_mounts==[[2,[-196,224],-8,[4,54],-10,[21,37],7],
                  [4,[196,224],-8,[-54,14],-10,[-34,-6],7],
                  [15,[-196,-224],8,[-14,52],10,[4,34],-7],
                  [17,[196,-224],8,[-54,54],10,[-24,24],-7]]''')
change('wall_key_width==20 && wall_key_height==10 && wall_key_projection==3;','''wall_key_width==20 && wall_key_height==10 && wall_key_projection==3 &&
    wall_fastener_pilot==3.175 && wall_fastener_pilot_depth==10.7;''')
# Evaluate compact block booleans once for reliable rear-face preview holes.
change('''    difference() {
        union() {
            linear_extrude(height=wall_standoff)''','''    render(convexity=20) difference() {
        union() {
            linear_extrude(height=wall_standoff)''')
p.write_bytes(s.replace('\n','\r\n').encode())
print('Added eight knot pilots and recessed block screws; preserved clear strip areas.')
