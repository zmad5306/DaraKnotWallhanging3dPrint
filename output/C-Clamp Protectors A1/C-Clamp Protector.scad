// Dimensions in inches, converted exactly to millimeters.
inch = 25.4;
outer_diameter = 0.500 * inch;
hole_diameter = 0.420 * inch;
height = 0.300 * inch;
hole_depth = 0.150 * inch;
$fn = 256;
difference() {
    cylinder(d = outer_diameter, h = height);
    translate([0, 0, height - hole_depth])
        cylinder(d = hole_diameter, h = hole_depth + 0.01);
}
