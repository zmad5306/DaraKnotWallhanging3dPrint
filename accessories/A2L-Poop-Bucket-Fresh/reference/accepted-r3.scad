// A2L purge bucket - fresh parametric design preview r3, 2026-11-09.
// Units: millimeters. No imported meshes, libraries, logos or lettering.
// Uses measured/test-fitted printer interface dimensions only.
// This preview is not a sliced or physically qualified print release.

/* [View] */
view_mode = "Bucket"; // [Bucket,Footprint]

/* [New body] */
// +10 mm width away from the printer; +10 mm length toward the front.
// When seated on the same pillar, the rear end and chute entry stay aligned.
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
// Preview dimensions; confirm clearance to the printer before printing.
chute_reach = 18;          // Projection beyond the printer-side wall
chute_rise = 8;            // Outer edge rises above the 58 mm wall
chute_thickness = 2;       // Vertical section thickness
chute_inside_overlap = 4;  // Leads past the inside wall into the bucket
chute_front_setback = 8;
chute_pillar_setback = 4;

/* [Established A2L fit] */
// Distances are functional fit dimensions, not dimensions of the old shell.
front_reach = 41.275;           // 1.625 in after the 1/8 in shortening
rear_return = 15.621;          // 0.615 in
pillar_gap = 49.6568;          // Last narrowed sample's nominal shoulder gap
inside_radius = 15.08125;      // 19/32 in, selected during fit testing
rear_tip_convex_radius = 12.7; // 1/2 in, requested at the short rear tip

/* [Opening placement] */
// New rear-edge allowance; positions the opening in this new body.
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

// Extrude a freshly drawn X/Z profile along Y.
module xz_prism(points, y_start, y_length) {
    translate([0,y_start+y_length,0])
        rotate([90,0,0])
            linear_extrude(height=y_length, convexity=10)
                polygon(points=points);
}

module triangular_front_wall() {
    // Match the existing rounded wall stock, including both front corners.
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

function chute_top_z(x) = low_wall_height
    + (x-(body_width-wall_thickness))*chute_rise/(chute_reach+wall_thickness);

module printer_chute() {
    x_inner = body_width-wall_thickness-chute_inside_overlap;
    x_outer = body_width+chute_reach;
    // The top surface slopes down toward the bucket. Its root overlaps the
    // low wall as solid material; the inside edge has no raised catching ledge.
    xz_prism([
        [x_inner,chute_top_z(x_inner)-chute_thickness],
        [x_outer,chute_top_z(x_outer)-chute_thickness],
        [x_outer,chute_top_z(x_outer)],
        [x_inner,chute_top_z(x_inner)]
    ], chute_front_setback,
       lower_shoulder_y-chute_pillar_setback-chute_front_setback);
}

module sloped_pillar_wall() {
    // Raise only the existing wall ring. Its XY fit contour never moves.
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
assert(chute_reach > 0 && chute_rise > 0 && chute_thickness > 0,
       "Chute reach, rise and thickness must be positive.");
assert(chute_front_setback >= outer_corner_radius && chute_pillar_setback > 0,
       "Keep the chute clear of the front corner and pillar opening.");
assert(lower_shoulder_y-chute_pillar_setback > chute_front_setback,
       "No length remains for the chute.");
assert(chute_top_z(body_width)-chute_thickness < low_wall_height,
       "Chute root must overlap the low wall as solid material.");

echo("PREVIEW ONLY: new shell, established nominal fit dimensions");
echo("Body W/L/H", [body_width,body_length,back_wall_height]);
echo("Gap, inner R, convex R", [pillar_gap,inside_radius,rear_tip_convex_radius]);
echo("Chute reach/rise", [chute_reach,chute_rise]);

if (view_mode == "Footprint")
    color([0.25,0.42,0.53]) footprint();
else
    color([0.84,0.88,0.92]) bucket();
