from pathlib import Path
p=Path('working/Dara-Photo-Frame-A1-Jointed.scad')
s=p.read_bytes().decode('utf-8').replace('\r\n','\n')
def change(a,b):
 global s
 assert s.count(a)==1,(a[:80],s.count(a))
 s=s.replace(a,b)
change('/* [M attachment] */', '''// WALL MOUNTING: four separate bonded blocks B1-B4, each 140 x 28 x 10 mm.
// Two 20 x 10 x 3 mm locating keys per block enter blind rear slots.
// Keys locate the blocks; bond the keys AND mating faces before hanging.
// All wall faces are coplanar, 10 mm behind the knot (4.5 mm clear of
// the default photo tabs and nominal screw heads). Strip thickness is extra.
// Each flat rear has a clear 95 x 20 mm strip area and a separate keyhole.
// Keyholes accept a nominal 4 mm shaft / 8 mm head; lower the frame to seat.
// B1/B2 are upper left/right; B3/B4 lower left/right, viewed from the FRONT.
// Slots are on F3, F5, F16 and F18; each block's key pattern is different.
// Print wall_fit_sample and check the actual hardware and bonded fit first.
// No adhesive weight rating or physical load test is implied by this CAD.

/* [Wall mounting - finished mm] */
show_wall_blocks = true; // Assembly visibility only; slots always remain in the frame.
wall_mount_index = 1; // [1:4]
wall_standoff = 10; // [9:0.5:16]
wall_key_clearance = 0.20; // Per-side XY clearance; independent of the lap joints.
wall_key_depth_clearance = 0.30;
wall_screw_shaft_diameter = 4.5; // Includes clearance for a nominal 4 mm shaft.
wall_screw_head_diameter = 9; // Entry and hidden channel, including head clearance.
wall_screw_head_depth = 4; // Available depth INSIDE the block for the screw head.
wall_mount_explode = 12; // Detail view only; 0 shows the installed fit.
wall_block_colour = [0.18, 0.52, 0.59];

/* [M attachment] */''')
change('washer:Reference washer]', 'washer:Reference washer, wall_block:One keyed wall block, wall_blocks:Four wall blocks for printing, wall_mount_detail:Block and knot slot detail, wall_keyhole_detail:Section through screw keyhole, wall_fit_sample:Wall block and slot coupon]')
change('$vpr = view_mode=="retainer_detail"', '$vpr = view_mode=="wall_mount_detail" || view_mode=="wall_keyhole_detail" ? [120,0,20] : view_mode=="wall_block" || view_mode=="wall_blocks" || view_mode=="wall_fit_sample" ? [45,0,20] : view_mode=="retainer_detail"')
change('$vpd = view_mode=="section"', '$vpd = view_mode=="wall_block" || view_mode=="wall_mount_detail" || view_mode=="wall_keyhole_detail" ? 330 : view_mode=="wall_blocks" || view_mode=="wall_fit_sample" ? 480 : view_mode=="section"')
change('// M ATTACHMENT. Values and coordinates below are finished millimetres.', '''// WALL BLOCKS. All dimensions and coordinates here are finished millimetres.
// [frame section (0-based), installed XY, key Y offset, two local key X positions].
// Positions clear all rabbets, 360-degree tab sweeps, M screws and lap domains.
wall_mounts = [[2,[-196,222],-6,[4,54]], [4,[196,222],-6,[-54,14]],
               [15,[-196,-222],6,[-14,52]], [17,[196,-222],6,[-54,54]]];
wall_block_width = 140;
wall_block_height = 28;
wall_key_width = 20;
wall_key_height = 10;
wall_key_projection = 3;
wall_keyhole_x = 51;
wall_keyhole_entry_y = -5;
wall_keyhole_seat_y = 6; // +Y is up: screw moves here as the frame lowers.
wall_keyhole_lip = 3; // Solid wall-facing skin captures the screw head.
wall_photo_head_height = 2.5; // Same nominal head envelope as photo_screw_preview_mm.
assert(wall_mount_index>=1 && wall_mount_index<=4 && floor(wall_mount_index)==wall_mount_index);
assert(wall_standoff>=photo_retainer_thickness+wall_photo_head_height+2,
       "Wall blocks must clear the photo tabs and screw heads by at least 2 mm");
assert(wall_key_clearance>=.1 && wall_key_clearance<=.4);
assert(wall_key_depth_clearance>=.15 && wall_key_depth_clearance<=.6);
assert(wall_screw_shaft_diameter>=3.5 && wall_screw_shaft_diameter<=5);
assert(wall_screw_head_diameter>=wall_screw_shaft_diameter+3 && wall_screw_head_diameter<=10);
assert(wall_screw_head_depth>=3 && wall_standoff-wall_keyhole_lip-wall_screw_head_depth>=2,
       "Keep at least 2 mm of solid block above the screw head channel");
assert(wall_mount_explode>=0);

module wall_rounded_rect(w,h,r=1) {
    hull() for(x=[-w/2+r,w/2-r],y=[-h/2+r,h/2-r])
        translate([x,y]) circle(r=r,$fn=32);
}
module wall_keys_at(i) {
    m=wall_mounts[i];
    for(x=m[3]) translate([x,m[2],0]) children();
}
module wall_key() {
    // Small tip chamfer eases insertion without reducing the full-size root.
    translate([0,0,-.02]) linear_extrude(height=wall_key_projection-.5+.02)
        wall_rounded_rect(wall_key_width,wall_key_height);
    hull() {
        translate([0,0,wall_key_projection-.5]) linear_extrude(height=.01)
            wall_rounded_rect(wall_key_width,wall_key_height);
        translate([0,0,wall_key_projection-.01]) linear_extrude(height=.01)
            wall_rounded_rect(wall_key_width-.8,wall_key_height-.8,.6);
    }
}
module wall_slot() {
    c=wall_key_clearance;
    translate([0,0,-.02]) linear_extrude(height=wall_key_projection+wall_key_depth_clearance+.02)
        wall_rounded_rect(wall_key_width+2*c,wall_key_height+2*c,1+c);
    // Lead-in only at the rear mouth; no projections on a frame print.
    hull() {
        translate([0,0,-.02]) linear_extrude(height=.02)
            wall_rounded_rect(wall_key_width+2*c+.6,wall_key_height+2*c+.6,1+c+.3);
        translate([0,0,.4]) linear_extrude(height=.01)
            wall_rounded_rect(wall_key_width+2*c,wall_key_height+2*c,1+c);
    }
}
module wall_slot_pair(i) { wall_keys_at(i) wall_slot(); }
module wall_slots_for_section(i) {
    for(k=[0:3]) if(wall_mounts[k][0]==i)
        translate(concat(wall_mounts[k][1],[0])) wall_slot_pair(k);
}
function has_wall_slots(i) = len([for(m=wall_mounts) if(m[0]==i) 1])>0;

module wall_head_channel_2d(d) {
    hull() for(y=[wall_keyhole_entry_y,wall_keyhole_seat_y])
        translate([wall_keyhole_x,y]) circle(d=d,$fn=64);
}
module wall_keyhole_cut() {
    // Rear opening: round head entry below a narrow vertical shaft slot.
    translate([wall_keyhole_x,wall_keyhole_entry_y,-.02])
        cylinder(d=wall_screw_head_diameter,h=wall_keyhole_lip+wall_screw_head_depth+.02,$fn=64);
    translate([0,0,-.02]) linear_extrude(height=wall_keyhole_lip+.04)
        wall_head_channel_2d(wall_screw_shaft_diameter);
    // Hidden wide channel permits the head to slide behind the retaining lip.
    translate([0,0,wall_keyhole_lip]) linear_extrude(height=wall_screw_head_depth)
        wall_head_channel_2d(wall_screw_head_diameter);
}
module wall_block_mm(i) {
    // Print with the flat wall face at Z=0, keys pointing up.
    // Clear strip rectangle: X=-65..30, Y=-10..10 (95 x 20 mm).
    difference() {
        union() {
            linear_extrude(height=wall_standoff) wall_rounded_rect(wall_block_width,wall_block_height,2);
            translate([0,0,wall_standoff]) wall_keys_at(i) wall_key();
        }
        wall_keyhole_cut();
    }
}
module installed_wall_block(i,gap=0) {
    translate([0,0,-wall_standoff-gap]) wall_block_mm(i);
}
module wall_block_assembly(spread=0) {
    for(i=[0:3]) {
        m=wall_mounts[i];
        translate([m[1][0]+spread*m[1][0]/450,m[1][1]+spread*m[1][1]/450,0])
            color(wall_block_colour) installed_wall_block(i,spread>0 ? spread+16 : 0);
    }
}
module wall_blocks_print() {
    // Four separate blocks occupy 140 x 148 mm, all at Z=0 on one A1 bed.
    for(i=[0:3]) translate([0,60-i*40,0]) {
        color(wall_block_colour) wall_block_mm(i);
        if($preview && show_section_ids) %color("black") translate([-82,0,1])
            linear_extrude(height=.2) text(str("B",i+1),size=6,halign="center");
    }
    if($preview && show_plate_outline) a1_plate_outline();
}
module wall_fit_sample() {
    // Full-size matching block and slot coupon; keep both separate for printing.
    color(wall_block_colour) translate([0,-22,0]) wall_block_mm(wall_mount_index-1);
    color(knot_colour) translate([0,22,0]) difference() {
        linear_extrude(height=8) wall_rounded_rect(wall_block_width,wall_block_height,2);
        wall_slot_pair(wall_mount_index-1);
    }
}
module wall_mount_detail() {
    i=wall_mount_index-1; m=wall_mounts[i];
    color(knot_colour) intersection() {
        translate([-m[1][0],-m[1][1],0]) section_shape("frame",m[0]);
        translate([-75,-20,-.01]) cube([150,40,18]);
    }
    color(wall_block_colour) installed_wall_block(i,wall_mount_explode);
}
module wall_keyhole_detail() {
    // Cut through the screw axis; exposes the retaining lip and closed head channel.
    color(wall_block_colour) difference() {
        wall_block_mm(wall_mount_index-1);
        translate([wall_keyhole_x,-30,-1]) cube([40,60,wall_standoff+6]);
    }
}

// M ATTACHMENT. Values and coordinates below are finished millimetres.''')
change('} else for(m=screw_mounts) if(m[1]==i) mount_xy(m[2]) frame_screw_cuts();', '''} else {
            for(m=screw_mounts) if(m[1]==i) mount_xy(m[2]) frame_screw_cuts();
            wall_slots_for_section(i);
        }''')
change('if($preview && fast_preview && cached_shape_matches(kind)) preview_section(kind,i);', '''if($preview && fast_preview && cached_shape_matches(kind)) {
        // Embedded meshes predate the wall slots. Apply live slot cuts AFTER the
        // cache so every clearance setting matches native F6/section geometry.
        if(kind=="frame" && has_wall_slots(i)) render(convexity=50) difference() {
            preview_section(kind,i);
            wall_slots_for_section(i);
        } else preview_section(kind,i);
    }''')
change('if(view_mode=="washer") tested_mount_washer();', '''if(view_mode=="wall_block") color(wall_block_colour) wall_block_mm(wall_mount_index-1);
    else if(view_mode=="wall_blocks") wall_blocks_print();
    else if(view_mode=="wall_mount_detail") wall_mount_detail();
    else if(view_mode=="wall_keyhole_detail") wall_keyhole_detail();
    else if(view_mode=="wall_fit_sample") wall_fit_sample();
    else if(view_mode=="washer") tested_mount_washer();''')
change('section_group("frame",view_mode=="exploded" ? exploded_distance : 0);', '''section_group("frame",view_mode=="exploded" ? exploded_distance : 0);
        if(show_wall_blocks) wall_block_assembly(view_mode=="exploded" ? exploded_distance : 0);''')
p.write_bytes(s.replace('\n','\r\n').encode('utf-8'))
print('Added wall blocks, live rear slots, detail and print views.')
