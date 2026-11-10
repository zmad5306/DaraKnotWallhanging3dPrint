// A2L Poop Bucket - parametric CAD.
// Units: millimeters. Body uses no imported meshes or external libraries.
// Printer interface dimensions are specified below.
// Bambu mark polygons follow the Bambu Studio splash logo.

/* [View] */
view_mode = "Bucket"; // [Bucket,Footprint]

/* [Front logo] */
logo_enabled = true;
logo_height = 32;
logo_center_x = 55;
logo_bottom_z = 40;
logo_depth = 0.6;

/* [Body] */
body_width = 110;
body_length = 255;
outer_corner_radius = 6;
wall_thickness = 2;
floor_thickness = 1.98;
low_wall_height = 58;
back_wall_height = 160.804;
// Rear end wall reaches the same height as the long back wall.
rear_wall_full_height = true;

/* [Triangular front wall] */
front_triangle_enabled = true;

/* [Sloped pillar wall] */
pillar_wall_slope_enabled = true;

/* [Printer catch chute] */
chute_enabled = true;
// Measured housing height plus clearance, rounded up to the print layer grid.
printer_housing_height_in = 2.464;
chute_clearance = 1;       // Minimum vertical clearance in millimeters
chute_layer_grid = 0.2;
chute_wall_height = ceil((printer_housing_height_in*25.4+chute_clearance)
                         /chute_layer_grid)*chute_layer_grid;
chute_height_offset = chute_wall_height - 58.026;
chute_reach = 22.296;      // Outermost projection from the wall
chute_tip_top_reach = 21.896;
chute_tip_top_height = 64.016 + chute_height_offset;
chute_tip_bottom_height = 62.348 + chute_height_offset;
chute_inner_height = 59.194 + chute_height_offset;
chute_top_root_reach = -1.696;
chute_top_root_height = 59.546 + chute_height_offset;
chute_bottom_root_reach = 0.268;
chute_bottom_root_height = 58.326 + chute_height_offset;
chute_front_setback = 8;
chute_pillar_setback = 4;

/* [Pillar opening] */
// Functional printer interface dimensions.
front_reach = 41.275;           // 1.625 in
rear_return = 15.621;          // 0.615 in
pillar_gap = 49.6568;          // Nominal pillar gap
inside_radius = 15.08125;      // 19/32 in
rear_tip_convex_radius = 12.7; // 1/2 in convex rear tip

/* [Opening placement] */
// Distance from the rear edge to the opening.
rear_edge_allowance = 12;

/* [Hidden] */
eps = 0.02;
arc_step_degrees = 0.75;

// X runs from the tall long wall toward the printer/open side.
// Y runs from the short front end toward the full-height rear end.
spine_x = body_width - front_reach;
upper_shoulder_y = body_length - rear_edge_allowance;
lower_shoulder_y = upper_shoulder_y - pillar_gap;
rear_tip_x = spine_x + rear_return;

upper_center = [spine_x + inside_radius,
                upper_shoulder_y - inside_radius];
tip_center_x = rear_tip_x - rear_tip_convex_radius;
center_dx = tip_center_x - upper_center[0];
center_distance = inside_radius + rear_tip_convex_radius;
// External tangency joins the concave pillar arc to the convex tip arc.
tip_center_y = upper_center[1]
    + sqrt(center_distance * center_distance - center_dx * center_dx);
tip_center = [tip_center_x, tip_center_y];
join_angle = atan2(tip_center_y - upper_center[1], center_dx);

function arc_points(c, radius, a0, a1, skip_first=false, skip_last=false) =
    let(n = max(2, ceil(abs(a1-a0)/arc_step_degrees)))
    [for (i=[skip_first ? 1 : 0 : n-(skip_last ? 1 : 0)])
        let(a = a0 + (a1-a0)*i/n)
        [c[0]+radius*cos(a), c[1]+radius*sin(a)]];

function footprint_points() = concat(
    [[outer_corner_radius, 0]],
    arc_points([body_width-outer_corner_radius, outer_corner_radius],
               outer_corner_radius, -90, 0),
    [[body_width, lower_shoulder_y]],
    arc_points([spine_x+inside_radius, lower_shoulder_y+inside_radius],
               inside_radius, -90, -180),
    arc_points(upper_center, inside_radius, 180, join_angle),
    arc_points(tip_center, rear_tip_convex_radius, join_angle-180, 0, true),
    [[rear_tip_x, body_length]],
    arc_points([outer_corner_radius, body_length-outer_corner_radius],
               outer_corner_radius, 90, 180),
    arc_points([outer_corner_radius, outer_corner_radius],
               outer_corner_radius, 180, 270, false, true)
);

module footprint() {
    polygon(points=footprint_points());
}

module wall_ring() {
    difference() {
        footprint();
        offset(delta=-wall_thickness) footprint();
    }
}

module tall_wall_region() {
    // The wider end of this strip includes the rounded outside corners.
    // Its intersection with the ring creates only wall stock, no shelf.
    union() {
        translate([-eps,-eps])
            square([outer_corner_radius+wall_thickness+eps,
                    body_length+2*eps]);
        if (rear_wall_full_height)
            translate([-eps,body_length-wall_thickness-eps])
                square([body_width+2*eps,wall_thickness+2*eps]);
    }
}

// Extrude an X/Z profile along Y.
module xz_prism(points, y_start, y_length) {
    translate([0,y_start+y_length,0])
        rotate([90,0,0])
            linear_extrude(height=y_length, convexity=10)
                polygon(points=points);
}

module triangular_front_wall() {
    // Follow the rounded wall profile, including both front corners.
    // The top slopes from full height at the back to the low printer-side wall.
    // Resolve the thin intersection so the triangular face is visible in F5.
    render(convexity=10) intersection() {
        linear_extrude(height=back_wall_height, convexity=10) wall_ring();
        xz_prism([
            [-eps,low_wall_height-eps],
            [body_width+eps,low_wall_height-eps],
            [body_width,low_wall_height],
            [outer_corner_radius+wall_thickness,back_wall_height],
            [-eps,back_wall_height]
        ], -eps, outer_corner_radius+2*eps);
    }
}

module printer_chute() {
    // The root is flush with the inner wall; the outer wall retains its full
    // height before the chute underside begins. The complete sloped section
    // rises as one unit; all heights are measured from the bucket bottom.
    xz_prism([
        [body_width-wall_thickness,low_wall_height-eps],
        [body_width,low_wall_height-eps],
        [body_width,chute_wall_height],
        [body_width+chute_bottom_root_reach,chute_bottom_root_height],
        [body_width+chute_reach,chute_tip_bottom_height],
        [body_width+chute_tip_top_reach,chute_tip_top_height],
        [body_width+chute_top_root_reach,chute_top_root_height],
        [body_width-wall_thickness,chute_inner_height]
    ], chute_front_setback,
       lower_shoulder_y-chute_pillar_setback-chute_front_setback);
}

module sloped_pillar_wall() {
    // Raise the wall along the pillar opening.
    // Start at the low front shoulder and meet the inside of the tall rear
    // wall continuously, including the concave and convex corner curves.
    slope_end_y = body_length-wall_thickness-eps;
    render(convexity=10) intersection() {
        linear_extrude(height=back_wall_height, convexity=10) wall_ring();
        translate([-eps,0,0])
            rotate([90,0,90])
                linear_extrude(height=body_width+2*eps, convexity=10)
                    polygon(points=[
                        [lower_shoulder_y,low_wall_height-eps],
                        [body_length+eps,low_wall_height-eps],
                        [body_length+eps,back_wall_height],
                        [slope_end_y,back_wall_height],
                        [lower_shoulder_y,low_wall_height]
                    ]);
    }
}

module bucket() {
    union() {
        linear_extrude(height=floor_thickness, convexity=10) footprint();
        linear_extrude(height=low_wall_height, convexity=10) wall_ring();
        linear_extrude(height=back_wall_height, convexity=10)
            intersection() {
                wall_ring();
                tall_wall_region();
            }
        if (front_triangle_enabled) triangular_front_wall();
        if (chute_enabled) printer_chute();
        if (pillar_wall_slope_enabled) sloped_pillar_wall();
    }
}

assert(body_width > front_reach+2*wall_thickness,
       "Body is too narrow for the pillar opening.");
assert(outer_corner_radius > wall_thickness,
       "Outer corner radius must exceed wall thickness.");
assert(pillar_gap > 2*inside_radius,
       "Pillar gap must exceed twice the inside radius.");
assert(abs(center_dx) < center_distance, "Rear tip blend has no tangent solution.");
assert(tip_center_y < body_length, "Increase rear edge allowance for the convex tip.");
assert(lower_shoulder_y > outer_corner_radius+wall_thickness,
       "Opening is too close to the front end.");
assert(back_wall_height >= low_wall_height && low_wall_height > floor_thickness,
       "Wall heights must exceed the floor thickness.");
assert(rear_return < front_reach, "Rear return must be shorter than front reach.");
assert(chute_reach > chute_tip_top_reach && chute_tip_top_height > chute_tip_bottom_height,
       "Chute edge must have positive thickness and reach.");
assert(chute_wall_height-printer_housing_height_in*25.4 >= chute_clearance,
       "Chute underside must clear the measured printer housing.");
assert(chute_wall_height >= low_wall_height && chute_inner_height > low_wall_height,
       "Chute must start above the full wall height.");
assert(chute_front_setback >= outer_corner_radius && chute_pillar_setback > 0,
       "Keep the chute clear of the front corner and pillar opening.");
assert(lower_shoulder_y-chute_pillar_setback > chute_front_setback,
       "No length remains for the chute.");
assert(chute_top_root_reach > -wall_thickness && chute_bottom_root_reach >= 0,
       "Chute must remain outside the collection cavity.");

// Original 94 x 122 SVG coordinates; source Y points down.
module bambu_mark_2d() {
    union() {
        polygon([[50.3856,45.5508],[50.3856,122],[94,122],[94,62.6627]]);
        polygon([[50.3856,0],[50.3856,38.2419],[94,55.3884],[94,0]]);
        polygon([[0,76.4838],[0,0],[43.6143,0],[43.6143,59.3373]]);
        polygon([[0,122],[0,83.7927],[43.6143,66.6462],[43.6143,122]]);
    }
}

// Cut inward from the front (negative Y), leaving a closed wall behind it.
module recessed_logo_cut() {
    translate([logo_center_x-94*logo_height/122/2,logo_depth,logo_bottom_z])
        rotate([90,0,0])
            linear_extrude(height=logo_depth+eps)
                scale([logo_height/122,logo_height/122])
                    translate([0,122]) mirror([0,1]) bambu_mark_2d();
}

module finished_bucket() {
    difference() {
        render(convexity=20) bucket();
        if (logo_enabled) recessed_logo_cut();
    }
}

assert(!logo_enabled || (logo_depth > 0 && logo_depth <= wall_thickness-1.2),
       "Leave at least 1.2 mm of wall behind the recessed logo.");

if (view_mode == "Footprint") color("gray") footprint();
else color("#555555") finished_bucket();
