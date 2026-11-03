// Rear photo hardware. All dimensions here are finished millimetres.
function u(mm) = mm / uniform_scale;
assert(backer_index >= 1 && backer_index <= 8 && floor(backer_index)==backer_index);
assert(backer_thickness > 0 && photo_allowance > 0);
assert(backer_clearance > 0 && backer_clearance < rabbet_overlap);
assert(rabbet_overlap <= 4.5, "Track roots start 5 mm outside the opening");
assert(slide_clearance >= 0.1 && slide_clearance <= 0.35);
assert(lock_rib >= 0 && lock_rib <= 0.4);
assert(backer_thickness + photo_allowance < knot_depth*uniform_scale - 2);

module photo_opening(i) {
    if (i==0) photo_loop_1();
    if (i==1) photo_loop_2();
    if (i==2) photo_loop_3();
    if (i==3) photo_loop_4();
    if (i==4) photo_loop_5();
    if (i==5) photo_loop_6();
    if (i==6) photo_loop_7();
    if (i==7) photo_loop_8();
}
// Local hardware X points outward from the photo; Y follows the boundary.
// Hardware itself is authored in real mm and converted back to master units.
module at_retainer(i,j) {
    translate(concat(photo_anchors[i][j],[0]))
        rotate([0,0,atan2(photo_normals[i][j][1],photo_normals[i][j][0])])
            scale([1/uniform_scale,1/uniform_scale,1/uniform_scale]) children();
}
module track_blank_mm() {
    translate([5,-5.5,-3.2]) cube([9,11,3.4]);
}
module track_channel_mm() {
    // Wide upper channel captures the slider flange; narrow rear opening
    // exposes its grip. Leave a 1 mm inner stop below the sliding tongue.
    translate([4.98,-3.5,-1.6]) cube([9.04,7,1.82]);
    translate([6,-2.3,-3.22]) cube([8.02,4.6,1.63]);
}
module photo_frame() {
    difference() {
        union() {
            knot_reference();
            for(i=[0:7],j=[0:3]) at_retainer(i,j) track_blank_mm();
        }
        for(i=[0:7]) {
            // Pocket opens from rear Z=0. Remaining rail forms the photo lip.
            translate([0,0,-u(0.02)])
                linear_extrude(height=u(backer_thickness+photo_allowance+0.02))
                    offset(delta=u(rabbet_overlap)) photo_opening(i);
            for(j=[0:3]) at_retainer(i,j) track_channel_mm();
        }
    }
}
module photo_backer(i) {
    linear_extrude(height=u(backer_thickness))
        offset(delta=u(rabbet_overlap-backer_clearance)) photo_opening(i);
}
module slider_mm() {
    flange_half = 3.5-slide_clearance;
    neck_half = 2.3-slide_clearance;
    // Flat photo-facing surface at Z=-clearance. Tongue overlaps the
    // backer edge by 6.7 mm with the default rabbet and backer clearance.
    union() {
        translate([6,-flange_half,-1.6+slide_clearance])
            cube([7.5,2*flange_half,1.6-2*slide_clearance]);
        translate([-3,-neck_half,-1.6+slide_clearance])
            cube([9.02,2*neck_half,1.6-2*slide_clearance]);
        translate([6,-neck_half,-3.2])
            cube([7.5,2*neck_half,1.6+slide_clearance+0.02]);
        // Grip projects rearward; push toward the photo to retain it.
        translate([11.5,-neck_half,-4.5]) cube([2,2*neck_half,1.32]);
        // Short tapered friction ribs seat at the inner end. Default
        // nominal interference is only 0.05 mm per side. Fit-test in PLA;
        // decrease lock_rib if tight, increase if the slider drifts out.
        for(side=[-1,1]) scale([1,side,1])
            translate([0,0,-1.6+slide_clearance])
                linear_extrude(height=1.6-2*slide_clearance)
                    polygon([[6,flange_half-0.02],[6.5,flange_half+lock_rib],
                             [7.8,flange_half+lock_rib],[10,flange_half],
                             [10,flange_half-0.02]]);
    }
}
// CAD-only fit sample: a section of frame, a backer edge, and its keeper.
// Release the keeper by moving it outward along +X; no snap arm is bent.
module fit_sample() {
    color(knot_colour) difference() {
        union() {
            translate([0,-10,0]) cube([18,20,6]);
            track_blank_mm();
        }
        translate([-0.02,-10.02,-0.02])
            cube([rabbet_overlap+0.02,20.04,backer_thickness+photo_allowance+0.02]);
        track_channel_mm();
    }
    if(show_backers) color(backer_colour)
        translate([-10,-9,0]) cube([10+rabbet_overlap-backer_clearance,18,backer_thickness]);
    if(show_retainers) color(retainer_colour)
        translate([retainers_open ? 12 : 0,0,0]) slider_mm();
}
module working_model() {
    if(view_mode=="drawing") reference_drawing();
    else if(view_mode=="backer")
        translate(-concat(photo_centres[backer_index-1],[0])) photo_backer(backer_index-1);
    else if(view_mode=="retainer") scale([1/uniform_scale,1/uniform_scale,1/uniform_scale]) slider_mm();
    else if(view_mode=="fit_sample") scale([1/uniform_scale,1/uniform_scale,1/uniform_scale]) fit_sample();
    else {
        reference_model();
        if(show_backers && view_mode!="frame") color(backer_colour)
            translate([0,0,view_mode=="exploded" ? -u(exploded_distance) : 0])
                for(i=[0:7]) photo_backer(i);
        if(show_retainers && view_mode!="frame") color(retainer_colour)
            for(i=[0:7],j=[0:3]) at_retainer(i,j)
                translate([retainers_open ? 12 : 0,0,view_mode=="exploded" ? -exploded_distance-8 : 0])
                    slider_mm();
    }
}
scale([uniform_scale,uniform_scale,uniform_scale]) working_model();
